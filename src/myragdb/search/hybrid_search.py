# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/search/hybrid_search.py
# Description: Hybrid search engine combining Meilisearch and ChromaDB with RRF fusion
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer, MeilisearchResult
from myragdb.indexers.vector_indexer import VectorIndexer
from myragdb.llm.query_rewriter import QueryRewriter, RewrittenQuery
from myragdb.config import load_repositories_config


@dataclass
class HybridSearchResult:
    """
    Result from hybrid search combining keyword and semantic scores.

    Business Purpose: Represents a single search result with both keyword (Meilisearch)
    and semantic (ChromaDB) ranking information, plus the fused RRF score used for
    final ranking.

    Example:
        result = HybridSearchResult(
            document_id="xK7JmH9vQpL2...",
            file_path="/path/to/file.py",
            rrf_score=0.156,
            keyword_rank=3,
            semantic_rank=1,
            keyword_score=0.95,
            semantic_distance=0.23,
            snippet="def authenticate_user...",
            repository="MyProject"
        )
    """
    document_id: str            # Base64 hash ID (same across Meili + Chroma)
    file_path: str              # Absolute path to file
    rrf_score: float            # Reciprocal Rank Fusion score (higher = better)
    keyword_rank: Optional[int] # Rank in Meilisearch results (None if not in top-N)
    semantic_rank: Optional[int] # Rank in ChromaDB results (None if not in top-N)
    keyword_score: float        # Meilisearch relevance score (0.0-1.0)
    semantic_distance: float    # ChromaDB distance (lower = better)
    snippet: str                # Content preview
    repository: str             # Repository name
    file_name: str              # File name only
    relative_path: str          # Relative path from repository root


class HybridSearchEngine:
    """
    Hybrid search engine combining Meilisearch keyword search and ChromaDB semantic search.

    Business Purpose: Provides best-of-both-worlds search by combining fast keyword
    matching (Meilisearch) with semantic understanding (ChromaDB), using Reciprocal
    Rank Fusion to merge results intelligently.

    Architecture:
    1. Query Rewrite: phi3 (port 8081) transforms query into keywords + semantic_intent + filters
    2. Parallel Execution: Meilisearch and ChromaDB searched simultaneously
    3. RRF Fusion: Merge results using Reciprocal Rank Fusion (k=60)
    4. Return top-N results sorted by RRF score

    Performance (2M files on M4 Max):
    - Query rewrite: ~1-2s (phi3)
    - Keyword search: <50ms (Meilisearch)
    - Semantic search: ~150ms (ChromaDB)
    - Total: ~150-250ms (parallel execution)

    Example:
        engine = HybridSearchEngine(
            meilisearch_indexer=meili_indexer,
            vector_indexer=vector_indexer,
            query_rewriter=query_rewriter
        )

        # Natural language query
        results = await engine.hybrid_search(
            "Can you find that cleanup script in my Projects folder?"
        )

        # Returns results sorted by RRF score (keyword + semantic fusion)
        for r in results:
            print(f"RRF: {r.rrf_score:.3f} - {r.file_path}")
    """

    def __init__(
        self,
        meilisearch_indexer: MeilisearchIndexer,
        vector_indexer: VectorIndexer,
        query_rewriter: Optional[QueryRewriter] = None,
        rrf_k: int = 60
    ):
        """
        Initialize hybrid search engine.

        Args:
            meilisearch_indexer: Meilisearch keyword indexer
            vector_indexer: ChromaDB vector indexer
            query_rewriter: Optional query rewriter (creates default if None)
            rrf_k: RRF smoothing constant (default: 60, per research best practice)
        """
        self.meilisearch = meilisearch_indexer
        self.vector = vector_indexer
        self.query_rewriter = query_rewriter or QueryRewriter()
        self.rrf_k = rrf_k

        # Load repository priorities for score weighting
        self.repo_priorities = self._load_repository_priorities()

    def _load_repository_priorities(self) -> Dict[str, float]:
        """
        Load repository priority weights from configuration.

        Business Purpose: Applies priority weighting to search results so that
        documents from high-priority repositories rank higher than low-priority ones.

        Priority weights:
        - high: 1.5x multiplier
        - medium: 1.0x (no change)
        - low: 0.7x multiplier

        Returns:
            Dictionary mapping repository name to priority multiplier
        """
        priority_weights = {
            "high": 1.5,
            "medium": 1.0,
            "low": 0.7
        }

        try:
            repo_config = load_repositories_config()
            return {
                repo.name: priority_weights.get(repo.priority, 1.0)
                for repo in repo_config.repositories
            }
        except Exception as e:
            print(f"[HybridSearch] Warning: Could not load repository priorities: {e}")
            return {}

    def reciprocal_rank_fusion(
        self,
        meili_results: List[MeilisearchResult],
        chroma_doc_ids: List[str],
        chroma_distances: List[float],
        k: int = 60
    ) -> Dict[str, float]:
        """
        Merge keyword and semantic results using Reciprocal Rank Fusion.

        Business Purpose: Combines rankings from two different search engines
        (keyword vs semantic) into a single unified score. Documents appearing
        in both result sets get higher scores.

        Formula: Score(d) = Σ(r ∈ {Meili, Chroma}) 1 / (k + rank_r(d))
        Where k=60 is a smoothing constant from research literature.

        Args:
            meili_results: Meilisearch keyword results
            chroma_doc_ids: ChromaDB document IDs (in rank order)
            chroma_distances: ChromaDB distances (lower = better)
            k: Smoothing constant (default: 60)

        Returns:
            Dictionary mapping document ID to RRF score
        """
        scores: Dict[str, float] = {}

        # Process Meilisearch ranks
        for rank, hit in enumerate(meili_results, start=1):
            doc_id = hit.id
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

        # Process ChromaDB ranks
        for rank, doc_id in enumerate(chroma_doc_ids, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

        return scores

    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        rewrite_query: bool = True,
        repository_filter: Optional[str] = None,
        folder_filter: Optional[str] = None,
        extension_filter: Optional[str] = None,
        directories: Optional[List[int]] = None
    ) -> List[HybridSearchResult]:
        """
        Execute hybrid search combining keyword and semantic search with RRF fusion.

        Business Purpose: Provides intelligent search that understands both exact
        keyword matches and semantic meaning, returning most relevant results based
        on combined ranking from both approaches. Supports filtering by repositories
        and managed directories.

        Args:
            query: User query (natural language or keywords)
            limit: Maximum number of results to return
            rewrite_query: Use LLM to rewrite query for optimization (default: True)
            repository_filter: Optional repository name filter
            folder_filter: Optional folder name filter (overrides query rewriter)
            extension_filter: Optional extension filter (overrides query rewriter)
            directories: Optional list of directory IDs to search (None = all)

        Returns:
            List of HybridSearchResult sorted by RRF score (descending)
        """
        # Step 1: Query rewriting (if enabled)
        if rewrite_query:
            try:
                rewritten = await self.query_rewriter.rewrite(query)
                keywords = rewritten.keywords
                semantic_intent = rewritten.semantic_intent

                # Use query rewriter's extracted filters if not explicitly provided
                if folder_filter is None and rewritten.filters.folder_name:
                    folder_filter = rewritten.filters.folder_name
                if extension_filter is None and rewritten.filters.extension:
                    # Use first extension if multiple provided
                    extension_filter = rewritten.filters.extension[0] if rewritten.filters.extension else None

                print(f"[HybridSearch] Rewritten query:")
                print(f"  Keywords: {keywords}")
                print(f"  Semantic: {semantic_intent}")
                print(f"  Filters: folder={folder_filter}, extension={extension_filter}")
            except Exception as e:
                print(f"[HybridSearch] Query rewrite failed: {e}, using original query")
                keywords = query
                semantic_intent = query
        else:
            keywords = query
            semantic_intent = query

        # Step 2: Parallel execution
        fetch_limit = limit * 3

        async def fetch_meilisearch() -> List[MeilisearchResult]:
            """Fetch keyword results from Meilisearch."""
            try:
                results = self.meilisearch.search(
                    query=keywords,
                    limit=fetch_limit,
                    repository_filter=repository_filter,
                    folder_filter=folder_filter,
                    extension_filter=extension_filter,
                    directories=directories
                )
                print(f"[HybridSearch] Meilisearch returned {len(results)} results")
                return results
            except Exception as e:
                print(f"[HybridSearch] Meilisearch error: {e}")
                return []

        async def fetch_chromadb() -> tuple[List[str], List[float]]:
            """Fetch semantic results from ChromaDB."""
            try:
                # Build where clause for filters
                # ChromaDB supports: single filter as dict, or multiple filters with $and
                where_clause = None
                filters_list = []

                if repository_filter:
                    filters_list.append({"repository": repository_filter})

                if directories:
                    # Directory IDs are stored as strings in metadata
                    directory_ids_str = [str(d) for d in directories]
                    # Create OR condition for multiple directories
                    dir_conditions = [{"source_id": str(d)} for d in directories]
                    if len(dir_conditions) == 1:
                        filters_list.append(dir_conditions[0])
                    else:
                        filters_list.append({"$or": dir_conditions})

                # Combine all filters with AND if multiple
                if len(filters_list) == 0:
                    where_clause = None
                elif len(filters_list) == 1:
                    where_clause = filters_list[0]
                else:
                    where_clause = {"$and": filters_list}

                results = self.vector.collection.query(
                    query_texts=[semantic_intent],
                    n_results=fetch_limit,
                    where=where_clause
                )
                doc_ids = results['ids'][0] if results['ids'] else []
                distances = results['distances'][0] if results['distances'] else []
                print(f"[HybridSearch] ChromaDB returned {len(doc_ids)} results")
                return doc_ids, distances
            except Exception as e:
                print(f"[HybridSearch] ChromaDB error: {e}")
                return [], []

        # Execute in parallel
        meili_results, (chroma_ids, chroma_distances) = await asyncio.gather(
            fetch_meilisearch(),
            fetch_chromadb()
        )

        # Step 3: RRF fusion
        rrf_scores = self.reciprocal_rank_fusion(
            meili_results=meili_results,
            chroma_doc_ids=chroma_ids,
            chroma_distances=chroma_distances,
            k=self.rrf_k
        )

        # Step 4: Build unified results
        meili_lookup: Dict[str, tuple[MeilisearchResult, int]] = {
            r.id: (r, rank) for rank, r in enumerate(meili_results, start=1)
        }
        chroma_lookup: Dict[str, tuple[int, float]] = {
            doc_id: (rank, dist)
            for rank, (doc_id, dist) in enumerate(zip(chroma_ids, chroma_distances), start=1)
        }

        hybrid_results: List[HybridSearchResult] = []
        for doc_id, rrf_score in rrf_scores.items():
            keyword_rank = None
            keyword_score = 0.0
            file_path = ""
            snippet = ""
            repository = ""
            file_name = ""
            relative_path = ""

            if doc_id in meili_lookup:
                meili_result, rank = meili_lookup[doc_id]
                keyword_rank = rank
                keyword_score = meili_result.score
                file_path = meili_result.file_path
                snippet = meili_result.snippet
                repository = meili_result.repository
                file_name = meili_result.file_name
                relative_path = meili_result.relative_path

            semantic_rank = None
            semantic_distance = 1.0

            if doc_id in chroma_lookup:
                rank, dist = chroma_lookup[doc_id]
                semantic_rank = rank
                semantic_distance = dist

            if not file_path and doc_id in chroma_ids:
                try:
                    metadata = self.vector.collection.get(ids=[doc_id])
                    if metadata and 'metadatas' in metadata and metadata['metadatas']:
                        meta = metadata['metadatas'][0]
                        file_path = meta.get('file_path', '')
                        repository = meta.get('repository', '')
                        file_name = meta.get('file_name', '')
                        relative_path = meta.get('relative_path', '')
                        snippet = meta.get('content', '')[:200]
                except Exception as e:
                    print(f"[HybridSearch] Error fetching ChromaDB metadata: {e}")

            # Apply repository priority weighting to RRF score
            priority_multiplier = self.repo_priorities.get(repository, 1.0)
            weighted_rrf_score = rrf_score * priority_multiplier

            hybrid_results.append(HybridSearchResult(
                document_id=doc_id,
                file_path=file_path,
                rrf_score=weighted_rrf_score,
                keyword_rank=keyword_rank,
                semantic_rank=semantic_rank,
                keyword_score=keyword_score,
                semantic_distance=semantic_distance,
                snippet=snippet,
                repository=repository,
                file_name=file_name,
                relative_path=relative_path
            ))

        # Step 5: Sort and return
        hybrid_results.sort(key=lambda x: x.rrf_score, reverse=True)
        final_results = hybrid_results[:limit]

        print(f"[HybridSearch] Returning top {len(final_results)} results (RRF fusion)")
        return final_results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics from both Meilisearch and ChromaDB indexes.

        Business Purpose: Provides index size and health information for monitoring.

        Returns:
            Dictionary with stats from both indexers
        """
        return {
            "keyword_documents": self.meilisearch.get_document_count(),
            "vector_chunks": self.vector.get_document_count()
        }
