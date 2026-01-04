# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/bm25_indexer.py
# Description: BM25 keyword indexing and search using Whoosh
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.scoring import BM25F
from whoosh.writing import AsyncWriter

from myragdb.indexers.file_scanner import ScannedFile
from myragdb.config import settings


@dataclass
class BM25SearchResult:
    """
    Result from BM25 keyword search.

    Business Purpose: Represents a single search result with all information
    needed for display and ranking.

    Example:
        result = BM25SearchResult(
            file_path="/path/to/file.py",
            repository="MyProject",
            score=0.85,
            snippet="def authenticate_user...",
            file_type=".py"
        )
    """
    file_path: str
    repository: str
    score: float
    snippet: str
    file_type: str
    relative_path: str


class BM25Indexer:
    """
    BM25 keyword search indexer using Whoosh.

    Business Purpose: Provides fast keyword-based search using the BM25
    probabilistic ranking algorithm. Good for exact term matching and
    traditional information retrieval.

    Example:
        indexer = BM25Indexer()
        indexer.index_file(scanned_file)
        results = indexer.search("authentication flow")
        for result in results:
            print(f"{result.file_path}: {result.score}")
    """

    def __init__(self, index_dir: Optional[str] = None):
        """
        Initialize BM25 indexer.

        Args:
            index_dir: Directory to store Whoosh index (defaults to config)
        """
        self.index_dir = index_dir or os.path.join(settings.index_dir, "bm25")
        self.schema = self._create_schema()
        self.ix = self._get_or_create_index()

    def _create_schema(self) -> Schema:
        """
        Create Whoosh schema for document indexing.

        Business Purpose: Defines the structure of indexed documents,
        specifying what fields are searchable and how they're stored.

        Returns:
            Whoosh Schema object
        """
        return Schema(
            file_path=ID(stored=True, unique=True),
            repository=ID(stored=True),
            content=TEXT(stored=False),  # Searchable but not stored (saves space)
            file_type=KEYWORD(stored=True),
            relative_path=ID(stored=True),
            # Store snippet separately for retrieval
            content_preview=TEXT(stored=True)
        )

    def _get_or_create_index(self):
        """
        Get existing index or create new one.

        Business Purpose: Manages index lifecycle, creating new index if
        needed or opening existing one for updates.

        Returns:
            Whoosh Index object
        """
        index_path = Path(self.index_dir)
        index_path.mkdir(parents=True, exist_ok=True)

        if index.exists_in(str(index_path)):
            return index.open_dir(str(index_path))
        else:
            return index.create_in(str(index_path), self.schema)

    def index_file(self, scanned_file: ScannedFile) -> None:
        """
        Index a single file.

        Business Purpose: Adds or updates a file in the search index,
        making it discoverable through keyword search.

        Args:
            scanned_file: File to index

        Example:
            from myragdb.indexers.file_scanner import scan_repository
            scanner = FileScanner(repo_config)
            for file in scanner.scan():
                indexer.index_file(file)
        """
        try:
            # Create preview (first 500 chars for snippet generation)
            preview = scanned_file.content[:500] if len(scanned_file.content) > 500 else scanned_file.content

            writer = AsyncWriter(self.ix)
            writer.update_document(
                file_path=scanned_file.file_path,
                repository=scanned_file.repository_name,
                content=scanned_file.content,
                file_type=scanned_file.file_type,
                relative_path=scanned_file.relative_path,
                content_preview=preview
            )
            writer.commit()

        except Exception as e:
            print(f"Error indexing file {scanned_file.file_path}: {e}")
            raise

    def index_files(self, files: List[ScannedFile], batch_size: int = 100) -> int:
        """
        Index multiple files in batches.

        Business Purpose: Efficiently indexes large numbers of files by
        batching writes, improving performance.

        Args:
            files: List of files to index
            batch_size: Number of files per batch

        Returns:
            Number of files successfully indexed

        Example:
            files = scan_repository(repo_config)
            indexed_count = indexer.index_files(files)
            print(f"Indexed {indexed_count} files")
        """
        indexed = 0
        writer = AsyncWriter(self.ix)

        try:
            for i, scanned_file in enumerate(files):
                try:
                    # Create preview
                    preview = scanned_file.content[:500] if len(scanned_file.content) > 500 else scanned_file.content

                    writer.update_document(
                        file_path=scanned_file.file_path,
                        repository=scanned_file.repository_name,
                        content=scanned_file.content,
                        file_type=scanned_file.file_type,
                        relative_path=scanned_file.relative_path,
                        content_preview=preview
                    )
                    indexed += 1

                    # Commit batch
                    if (i + 1) % batch_size == 0:
                        writer.commit()
                        print(f"Indexed {i + 1} files...")
                        writer = AsyncWriter(self.ix)

                except Exception as e:
                    print(f"Error indexing {scanned_file.file_path}: {e}")
                    continue

            # Commit remaining
            writer.commit()

        except Exception as e:
            print(f"Error during batch indexing: {e}")
            writer.cancel()
            raise

        return indexed

    def search(
        self,
        query: str,
        limit: int = 10,
        repository: Optional[str] = None
    ) -> List[BM25SearchResult]:
        """
        Search indexed files using BM25 keyword search.

        Business Purpose: Finds files matching keyword query using
        probabilistic ranking. Good for exact term matching.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            repository: Optional repository filter

        Returns:
            List of BM25SearchResult objects sorted by relevance

        Example:
            results = indexer.search("JWT authentication", limit=5)
            for result in results:
                print(f"{result.relative_path}: {result.score:.2f}")
                print(f"  {result.snippet}")
        """
        results = []

        try:
            with self.ix.searcher(weighting=BM25F()) as searcher:
                # Parse query for content field
                parser = MultifieldParser(
                    ["content", "file_path", "relative_path"],
                    schema=self.ix.schema
                )
                q = parser.parse(query)

                # Execute search
                search_results = searcher.search(q, limit=limit)

                for hit in search_results:
                    # Check repository filter
                    if repository and hit['repository'] != repository:
                        continue

                    # Generate snippet from stored preview
                    snippet = hit.get('content_preview', '')[:200]

                    result = BM25SearchResult(
                        file_path=hit['file_path'],
                        repository=hit['repository'],
                        score=hit.score,
                        snippet=snippet,
                        file_type=hit.get('file_type', ''),
                        relative_path=hit['relative_path']
                    )
                    results.append(result)

        except Exception as e:
            print(f"Error during search: {e}")
            raise

        return results

    def get_document_count(self) -> int:
        """
        Get total number of indexed documents.

        Business Purpose: Provides statistics about index size for
        monitoring and reporting.

        Returns:
            Number of documents in index

        Example:
            count = indexer.get_document_count()
            print(f"Index contains {count} documents")
        """
        with self.ix.searcher() as searcher:
            return searcher.doc_count_all()

    def clear_index(self) -> None:
        """
        Delete all documents from index.

        Business Purpose: Allows clean rebuild of index when needed.

        Example:
            indexer.clear_index()
            # Re-index all files
        """
        writer = self.ix.writer()
        writer.commit(mergetype=None)

    def delete_document(self, file_path: str) -> None:
        """
        Remove a document from the index.

        Business Purpose: Allows removal of deleted files from index
        to keep it in sync with filesystem.

        Args:
            file_path: Path of file to remove

        Example:
            indexer.delete_document("/path/to/deleted/file.py")
        """
        writer = self.ix.writer()
        writer.delete_by_term('file_path', file_path)
        writer.commit()
