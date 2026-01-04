# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/search/hybrid_search.py
# Description: Hybrid search combining BM25 keyword and vector semantic search
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass

from myragdb.indexers.bm25_indexer import BM25Indexer, BM25SearchResult
from myragdb.indexers.vector_indexer import VectorIndexer, VectorSearchResult
from myragdb.config import settings


@dataclass
class HybridSearchResult:
    """
    Combined result from hybrid search.

    Business Purpose: Represents a search result with scores from both
    BM25 and vector search, providing comprehensive relevance assessment.

    Example:
        result = HybridSearchResult(
            file_path="/path/to/file.py",
            repository="MyProject",
            combined_score=0.89,
            bm25_score=0.85,
            vector_score=0.92,
            snippet="...",
            file_type=".py"
        )
    """
    file_path: str
    repository: str
    combined_score: float
    bm25_score: Optional[float]
    vector_score: Optional[float]
    snippet: str
    file_type: str
    relative_path: str


class HybridSearchEngine:
    """
    Combines BM25 keyword search with vector semantic search.

    Business Purpose: Provides best-of-both-worlds search by combining
    keyword matching (BM25) with semantic understanding (vectors).
    BM25 is good for exact terms, vectors understand meaning.

    Example:
        engine = HybridSearchEngine()
        results = engine.search("JWT authentication")
        # Gets both exact JWT matches AND semantically similar auth docs
    """

    def __init__(
        self,
        bm25_indexer: Optional[BM25Indexer] = None,
        vector_indexer: Optional[VectorIndexer] = None,
        bm25_weight: Optional[float] = None,
        vector_weight: Optional[float] = None
    ):
        """
        Initialize hybrid search engine.

        Args:
            bm25_indexer: BM25 indexer instance (creates new if None)
            vector_indexer: Vector indexer instance (creates new if None)
            bm25_weight: Weight for BM25 scores (defaults to config)
            vector_weight: Weight for vector scores (defaults to config)
        """
        self.bm25_indexer = bm25_indexer or BM25Indexer()
        self.vector_indexer = vector_indexer or VectorIndexer()
        self.bm25_weight = bm25_weight or settings.bm25_weight
        self.vector_weight = vector_weight or settings.vector_weight

    def search(
        self,
        query: str,
        limit: int = 10,
        repository: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[HybridSearchResult]:
        """
        Perform hybrid search combining BM25 and vector results.

        Business Purpose: Searches using both keyword matching and semantic
        similarity, then combines and ranks results. Finds documents that
        match either exact terms OR meaning.

        Args:
            query: Search query string
            limit: Maximum number of results
            repository: Optional repository filter
            min_score: Minimum combined score threshold

        Returns:
            List of HybridSearchResult sorted by combined score

        Example:
            engine = HybridSearchEngine()
            results = engine.search("how to authenticate users", limit=5)
            for r in results:
                print(f"{r.relative_path}: {r.combined_score:.2f}")
                print(f"  BM25: {r.bm25_score:.2f}, Vector: {r.vector_score:.2f}")
        """
        # Get more results from each engine, then merge
        fetch_limit = limit * 3

        # Execute both searches (synchronous for now, can parallelize later)
        bm25_results = self.bm25_indexer.search(
            query=query,
            limit=fetch_limit,
            repository=repository
        )

        vector_results = self.vector_indexer.search(
            query=query,
            limit=fetch_limit,
            repository=repository
        )

        # Merge and rank results
        merged_results = self._merge_results(bm25_results, vector_results)

        # Filter by minimum score
        filtered_results = [r for r in merged_results if r.combined_score >= min_score]

        # Return top results
        return filtered_results[:limit]

    def _merge_results(
        self,
        bm25_results: List[BM25SearchResult],
        vector_results: List[VectorSearchResult]
    ) -> List[HybridSearchResult]:
        """
        Merge and rank results from both search engines.

        Business Purpose: Combines results from BM25 and vector search,
        normalizes scores, and calculates weighted combined score.

        Args:
            bm25_results: Results from BM25 search
            vector_results: Results from vector search

        Returns:
            List of HybridSearchResult sorted by combined score

        Algorithm:
        1. Normalize BM25 scores to 0-1 range
        2. Vector scores already normalized (similarity)
        3. For each unique file:
           - If in both: combine_score = (bm25_weight * bm25_score) + (vector_weight * vector_score)
           - If only BM25: combined_score = bm25_weight * bm25_score
           - If only vector: combined_score = vector_weight * vector_score
        4. Sort by combined score descending
        """
        # Normalize BM25 scores
        normalized_bm25 = self._normalize_bm25_scores(bm25_results)

        # Build file-to-result maps
        bm25_map = {r.file_path: r for r in normalized_bm25}
        vector_map = {r.file_path: r for r in vector_results}

        # Get all unique files
        all_files = set(bm25_map.keys()) | set(vector_map.keys())

        # Merge results
        merged = []
        for file_path in all_files:
            bm25_result = bm25_map.get(file_path)
            vector_result = vector_map.get(file_path)

            # Calculate combined score
            bm25_score = bm25_result.score if bm25_result else 0.0
            vector_score = vector_result.score if vector_result else 0.0

            combined_score = (
                self.bm25_weight * bm25_score +
                self.vector_weight * vector_score
            )

            # Use snippet from higher-scoring source
            if bm25_score > vector_score and bm25_result:
                snippet = bm25_result.snippet
                repository = bm25_result.repository
                file_type = bm25_result.file_type
                relative_path = bm25_result.relative_path
            elif vector_result:
                snippet = vector_result.snippet
                repository = vector_result.repository
                file_type = vector_result.file_type
                relative_path = vector_result.relative_path
            else:
                continue  # Shouldn't happen

            result = HybridSearchResult(
                file_path=file_path,
                repository=repository,
                combined_score=combined_score,
                bm25_score=bm25_score if bm25_result else None,
                vector_score=vector_score if vector_result else None,
                snippet=snippet,
                file_type=file_type,
                relative_path=relative_path
            )
            merged.append(result)

        # Sort by combined score descending
        merged.sort(key=lambda x: x.combined_score, reverse=True)

        return merged

    def _normalize_bm25_scores(
        self,
        results: List[BM25SearchResult]
    ) -> List[BM25SearchResult]:
        """
        Normalize BM25 scores to 0-1 range.

        Business Purpose: BM25 scores are unbounded, so we normalize them
        to be comparable with vector similarity scores (which are 0-1).

        Args:
            results: BM25 search results

        Returns:
            Results with normalized scores

        Normalization:
        - Find max score in result set
        - Divide all scores by max
        - If no results or all scores are 0, return as-is
        """
        if not results:
            return []

        # Find max score
        max_score = max(r.score for r in results)

        if max_score == 0:
            return results

        # Normalize
        normalized = []
        for result in results:
            normalized_score = result.score / max_score
            normalized_result = BM25SearchResult(
                file_path=result.file_path,
                repository=result.repository,
                score=normalized_score,
                snippet=result.snippet,
                file_type=result.file_type,
                relative_path=result.relative_path
            )
            normalized.append(normalized_result)

        return normalized

    def get_stats(self) -> Dict[str, int]:
        """
        Get indexing statistics.

        Business Purpose: Provides visibility into index size and health.

        Returns:
            Dictionary with statistics

        Example:
            stats = engine.get_stats()
            print(f"BM25 docs: {stats['bm25_documents']}")
            print(f"Vector chunks: {stats['vector_chunks']}")
        """
        return {
            "bm25_documents": self.bm25_indexer.get_document_count(),
            "vector_chunks": self.vector_indexer.get_document_count()
        }
