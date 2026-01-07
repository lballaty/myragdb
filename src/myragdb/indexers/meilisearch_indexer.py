# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/meilisearch_indexer.py
# Description: Meilisearch keyword indexing optimized for 2M+ files with 128GB RAM
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import meilisearch
from meilisearch.index import Index

from myragdb.indexers.file_scanner import ScannedFile
from myragdb.utils.id_generator import generate_document_id
from myragdb.config import settings as app_settings
from myragdb.db.file_metadata import FileMetadataDatabase


@dataclass
class MeilisearchResult:
    """
    Result from Meilisearch keyword search.

    Business Purpose: Represents a single search result with all information
    needed for display and hybrid ranking fusion.

    Example:
        result = MeilisearchResult(
            id="xK7JmH9vQpL2...",
            file_path="/path/to/file.py",
            repository="MyProject",
            score=0.95,
            snippet="def authenticate_user...",
            file_type=".py"
        )
    """
    id: str
    file_path: str
    repository: str
    score: float
    snippet: str
    file_type: str
    relative_path: str
    folder_name: str
    file_name: str


class MeilisearchIndexer:
    """
    Meilisearch keyword search indexer optimized for 2M+ files on 128GB RAM.

    Business Purpose: Provides ultra-fast keyword-based search using Meilisearch's
    Rust-based engine with memory-mapped indexes. Designed for massive scale
    with intelligent batching and incremental indexing.

    Architecture:
    - Searchable: file_name, folder_name, content (ranked in priority order)
    - Filterable: file_path, extension, last_modified, size (exact lookups)
    - Primary Key: Base64 hash of absolute path (matches ChromaDB IDs)
    - Batching: 50,000 documents per batch for optimal throughput
    - Memory: Configured for 32GiB max indexing memory

    Example:
        indexer = MeilisearchIndexer(
            host="http://localhost:7700",
            api_key="masterKey"
        )
        indexer.index_files(scanned_files, batch_size=50000)
        results = indexer.search("authentication", folder_filter="src/auth")
    """

    def __init__(
        self,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None
    ):
        """
        Initialize Meilisearch indexer.

        Args:
            host: Meilisearch server URL (defaults to config setting)
            api_key: Master API key for Meilisearch (defaults to config setting)
            index_name: Name of the Meilisearch index (defaults to config setting)
        """
        # Use config defaults if not provided
        host = host or app_settings.meilisearch_host
        api_key = api_key or app_settings.meilisearch_api_key
        index_name = index_name or app_settings.meilisearch_index

        # Initialize client with API key
        self.client = meilisearch.Client(host, api_key)
        self.index_name = index_name
        self.index: Index = self.client.index(index_name)
        self._configure_index()

        # Track last indexed time for incremental updates (persistent across restarts)
        self.metadata_db = FileMetadataDatabase()

    def _configure_index(self) -> None:
        """
        Configure Meilisearch index settings for optimal 2M+ file performance.

        Business Purpose: Sets up searchable attributes (inverted index for fuzzy search)
        and filterable attributes (lookup table for exact filtering), plus ranking rules
        to prioritize file_name > folder_name > content matches.

        Settings:
        - searchableAttributes: Ranked in priority order (affects relevance scoring)
        - filterableAttributes: Enable fast exact-match filtering
        - rankingRules: Control result ordering (typo tolerance, proximity, etc.)
        - displayedAttributes: All fields visible in results

        This configuration is optimized for:
        - Fast folder/file name matching
        - Scoped searches (filter by path/extension first, then search)
        - Typo-tolerant search
        - 128GB RAM with memory-mapped indexes
        """
        try:
            # Searchable attributes (inverted index - ranked priority)
            self.index.update_searchable_attributes([
                'file_name',       # Highest priority: exact file name matches
                'relative_path',   # High priority: full relative path matches
                'folder_name',     # Medium priority: immediate parent folder matches
                'directory_path',  # Medium priority: full directory path matches
                'content'          # Lower priority: content matches
            ])

            # Filterable attributes (lookup table - exact matches)
            self.index.update_filterable_attributes([
                'file_path',      # Full absolute path
                'relative_path',  # Relative path from repo root
                'directory_path', # Full parent directory path
                'extension',      # File type (.py, .md, .js, etc.)
                'last_modified',  # Timestamp for incremental indexing
                'size',           # File size in bytes
                'repository',     # Repository name (for backward compatibility)
                'source_type',    # Source type: 'repository' or 'directory'
                'source_id',      # Source ID: repository name or directory ID
                'folder_name'     # Folder name (also searchable)
            ])

            # Ranking rules (order matters - earlier rules have higher weight)
            self.index.update_ranking_rules([
                'words',      # Number of matching query words
                'typo',       # Fewer typos = higher rank
                'proximity',  # Closer words = higher rank
                'attribute',  # Earlier in searchableAttributes = higher rank
                'exactness'   # Exact matches rank higher
            ])

            print(f"[Meilisearch] Index '{self.index_name}' configured successfully")

        except Exception as e:
            print(f"[Meilisearch] Warning: Failed to configure index: {e}")
            print(f"[Meilisearch] Index may already exist - continuing...")

    def _create_document(self, scanned_file: ScannedFile) -> Dict[str, Any]:
        """
        Create Meilisearch document from scanned file.

        Business Purpose: Transforms file metadata into Meilisearch document format
        with deterministic Base64 ID matching ChromaDB for perfect parity. Supports
        both repository and directory sources via source_type and source_id fields.

        Args:
            scanned_file: Scanned file with metadata and content

        Returns:
            Dictionary ready for Meilisearch indexing

        Example:
            doc = self._create_document(scanned_file)
            # {
            #     'id': 'xK7JmH9vQpL2...',
            #     'file_path': '/path/to/file.py',
            #     'file_name': 'file.py',
            #     'folder_name': 'to',
            #     'source_type': 'repository' or 'directory',
            #     'source_id': 'MyProject' or '1',
            #     'content': 'def main()...',
            #     ...
            # }
        """
        file_path_obj = Path(scanned_file.file_path)

        # Generate deterministic ID (same as ChromaDB)
        doc_id = generate_document_id(scanned_file.file_path)

        # Extract folder name (parent directory name)
        folder_name = file_path_obj.parent.name

        # Truncate content to 100k chars for indexing performance
        # (full content stored in filesystem, this is for search only)
        content_truncated = scanned_file.content[:100000] if scanned_file.content else ""

        # Get file stats
        try:
            stat = os.stat(scanned_file.file_path)
            last_modified = int(stat.st_mtime)
            size = stat.st_size
        except OSError:
            last_modified = int(time.time())
            size = len(scanned_file.content) if scanned_file.content else 0

        # Determine source type and source ID
        if scanned_file.repository_name:
            source_type = 'repository'
            source_id = scanned_file.repository_name
        else:
            source_type = 'directory'
            source_id = str(scanned_file.directory_id)

        return {
            'id': doc_id,
            'file_path': scanned_file.file_path,
            'file_name': file_path_obj.name,
            'folder_name': folder_name,
            'directory_path': str(file_path_obj.parent),
            'extension': scanned_file.file_type,
            'repository': scanned_file.repository_name,  # Kept for backward compatibility
            'source_type': source_type,                  # New: 'repository' or 'directory'
            'source_id': source_id,                      # New: repo name or directory ID
            'relative_path': scanned_file.relative_path,
            'content': content_truncated,
            'last_modified': last_modified,
            'size': size
        }

    def index_file(self, scanned_file: ScannedFile) -> str:
        """
        Index a single file (use index_files_batch for production).

        Business Purpose: Adds or updates a single file in the search index.
        For 2M+ files, use index_files_batch instead for better performance.

        Args:
            scanned_file: File to index

        Returns:
            Document ID

        Example:
            doc_id = indexer.index_file(scanned_file)
            print(f"Indexed: {doc_id}")
        """
        doc = self._create_document(scanned_file)
        self.index.add_documents([doc])
        self.last_indexed_time[scanned_file.file_path] = time.time()
        return doc['id']

    def index_files_batch(
        self,
        files: List[ScannedFile],
        batch_size: int = 50000,
        incremental: bool = True
    ) -> int:
        """
        Index multiple files in batches (optimized for 2M+ files).

        Business Purpose: Efficiently indexes massive numbers of files by batching
        writes to Meilisearch. Uses 50k batch size for optimal throughput on 128GB RAM.
        Supports incremental indexing (only process changed files).

        Args:
            files: List of files to index
            batch_size: Documents per batch (default: 50,000 for optimal RAM usage)
            incremental: Only index files modified since last_indexed_time

        Returns:
            Number of files successfully indexed

        Example:
            # Full re-index
            count = indexer.index_files_batch(files, incremental=False)

            # Incremental update (only changed files)
            count = indexer.index_files_batch(files, incremental=True)
            print(f"Indexed {count} new/changed files")
        """
        indexed = 0
        batch_docs = []
        skipped_unchanged = 0

        start_time = time.time()
        print(f"[Meilisearch] Starting batch indexing: {len(files)} files, batch_size={batch_size}, incremental={incremental}")

        for i, scanned_file in enumerate(files):
            try:
                # Incremental indexing: skip if file hasn't changed
                if incremental:
                    try:
                        stat = os.stat(scanned_file.file_path)
                        file_mtime = stat.st_mtime
                        last_indexed = self.metadata_db.get_last_indexed_time(scanned_file.file_path)

                        if file_mtime <= last_indexed:
                            skipped_unchanged += 1
                            continue
                    except OSError:
                        pass  # File doesn't exist, skip mtime check

                # Create document
                doc = self._create_document(scanned_file)
                batch_docs.append(doc)

                # Update metadata database
                self.metadata_db.update_file_metadata(
                    scanned_file.file_path,
                    scanned_file.repository_name,
                    'keyword'
                )

                # Send batch when full
                if len(batch_docs) >= batch_size:
                    task = self.index.add_documents(batch_docs)
                    indexed += len(batch_docs)
                    print(f"[Meilisearch] Indexed batch: {indexed}/{len(files)} files (task_uid={task.task_uid})")
                    batch_docs = []

                # Progress logging every 10k files
                if (i + 1) % 10000 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    print(f"[Meilisearch] Progress: {i+1}/{len(files)} scanned ({rate:.1f} files/sec)")

            except Exception as e:
                print(f"[Meilisearch] Error indexing {scanned_file.file_path}: {e}")
                continue

        # Send remaining batch
        if batch_docs:
            task = self.index.add_documents(batch_docs)
            indexed += len(batch_docs)
            print(f"[Meilisearch] Indexed final batch: {indexed} files (task_uid={task.task_uid})")

        elapsed = time.time() - start_time
        rate = indexed / elapsed if elapsed > 0 else 0
        print(f"[Meilisearch] Batch indexing complete: {indexed} indexed, {skipped_unchanged} skipped (unchanged)")
        print(f"[Meilisearch] Performance: {rate:.1f} files/sec, {elapsed:.1f} seconds total")

        return indexed

    def index_directory(
        self,
        directory_path: str,
        directory_id: int,
        incremental: bool = True,
        batch_size: int = 50000
    ) -> int:
        """
        Index all files in a non-repository directory.

        Business Purpose: Scans a managed directory for indexable files and
        indexes them with source_type='directory' and source_id=directory_id.
        Supports incremental indexing to only update changed files.

        Args:
            directory_path: Absolute path to directory
            directory_id: Database ID of the managed directory
            incremental: Only index files modified since last indexing
            batch_size: Documents per batch (default: 50,000)

        Returns:
            Number of files successfully indexed

        Example:
            count = indexer.index_directory("/path/to/docs", directory_id=1)
            print(f"Indexed {count} files from directory")
        """
        from myragdb.indexers.file_scanner import DirectoryScanner

        print(f"[Meilisearch] Starting directory indexing: {directory_path} (ID={directory_id})")

        # Scan directory for files
        scanner = DirectoryScanner(directory_path, directory_id)
        files = list(scanner.scan())

        if not files:
            print(f"[Meilisearch] No files found in directory: {directory_path}")
            return 0

        print(f"[Meilisearch] Found {len(files)} files in directory, indexing...")

        # Use batch indexing for performance
        return self.index_files_batch(files, batch_size=batch_size, incremental=incremental)

    def search(
        self,
        query: str,
        limit: int = 10,
        folder_filter: Optional[str] = None,
        extension_filter: Optional[str] = None,
        repository_filter: Optional[str] = None,
        directories: Optional[List[int]] = None
    ) -> List[MeilisearchResult]:
        """
        Search indexed files using keyword search with optional filters.

        Business Purpose: Finds files matching query using typo-tolerant keyword search.
        Supports scoped searching (filter by folder/extension/source first, then search within
        that subset) for instant searches even with 2M+ files. Can filter by repositories
        or managed directories.

        Args:
            query: Search query string
            limit: Maximum number of results
            folder_filter: Filter to specific folder name (e.g., "src/auth")
            extension_filter: Filter by file extension (e.g., ".py")
            repository_filter: Filter by repository name
            directories: Optional list of directory IDs to search (None = all)

        Returns:
            List of MeilisearchResult objects sorted by relevance

        Example:
            # Basic search
            results = indexer.search("authentication flow", limit=10)

            # Directory-scoped search
            results = indexer.search(
                "config",
                directories=[1, 2],  # Search only in directories 1 and 2
                extension_filter=".py"
            )

            # Repository-specific search
            results = indexer.search(
                "JWT",
                repository_filter="MyProject"
            )
        """
        try:
            # Build filter expression
            filters = []
            if folder_filter:
                # Exact match on folder_name
                filters.append(f'folder_name = "{folder_filter}"')
            if extension_filter:
                filters.append(f'extension = "{extension_filter}"')
            if repository_filter:
                filters.append(f'repository = "{repository_filter}"')

            # Add directory filtering (multiple directories with OR logic)
            if directories:
                dir_filters = [f'source_id = "{d}"' for d in directories]
                if len(dir_filters) == 1:
                    filters.append(dir_filters[0])
                else:
                    # Multiple directories: (dir1 OR dir2 OR dir3)
                    filters.append(f"({' OR '.join(dir_filters)})")

            filter_str = ' AND '.join(filters) if filters else None

            # Execute search
            search_params = {
                'limit': limit,
                'attributesToHighlight': ['content'],
                'attributesToCrop': ['content'],
                'cropLength': 600,
                'showRankingScore': True,  # CRITICAL: Without this, _rankingScore returns 0
            }
            if filter_str:
                search_params['filter'] = filter_str

            response = self.index.search(query, search_params)

            # Convert to MeilisearchResult objects
            results = []
            for hit in response.get('hits', []):
                # Extract snippet (use highlighted content if available)
                snippet = ''
                if '_formatted' in hit and 'content' in hit['_formatted']:
                    snippet = hit['_formatted']['content'][:600]
                elif 'content' in hit:
                    snippet = hit['content'][:600]

                result = MeilisearchResult(
                    id=hit.get('id', ''),
                    file_path=hit.get('file_path', ''),
                    repository=hit.get('repository', ''),
                    score=hit.get('_rankingScore', 0.0),  # Meilisearch relevance score
                    snippet=snippet,
                    file_type=hit.get('extension', ''),
                    relative_path=hit.get('relative_path', ''),
                    folder_name=hit.get('folder_name', ''),
                    file_name=hit.get('file_name', '')
                )
                results.append(result)

            return results

        except Exception as e:
            print(f"[Meilisearch] Error during search: {e}")
            return []

    def get_document_count(self) -> int:
        """
        Get total number of indexed documents.

        Business Purpose: Provides statistics about index size for monitoring.

        Returns:
            Number of documents in index

        Example:
            count = indexer.get_document_count()
            print(f"Index contains {count:,} documents")
        """
        try:
            stats = self.index.get_stats()
            # stats is an IndexStats object, not a dict - access attribute directly
            return stats.number_of_documents if hasattr(stats, 'number_of_documents') else 0
        except Exception as e:
            print(f"[Meilisearch] Error getting document count: {e}")
            return 0

    def clear_index(self) -> None:
        """
        Delete all documents from index (WARNING: destructive).

        Business Purpose: Allows clean rebuild of index when needed.
        Use with caution - this removes all indexed data.

        Example:
            indexer.clear_index()
            # Re-index all files from scratch
        """
        try:
            task = self.index.delete_all_documents()
            print(f"[Meilisearch] Cleared index (task_uid={task.task_uid})")
            # Note: We don't clear metadata_db here as it persists across clears
        except Exception as e:
            print(f"[Meilisearch] Error clearing index: {e}")

    def delete_document(self, file_path: str) -> None:
        """
        Remove a document from the index.

        Business Purpose: Allows removal of deleted files from index
        to keep it in sync with filesystem.

        Args:
            file_path: Absolute path of file to remove

        Example:
            indexer.delete_document("/path/to/deleted/file.py")
        """
        try:
            doc_id = generate_document_id(file_path)
            task = self.index.delete_document(doc_id)
            print(f"[Meilisearch] Deleted document {doc_id} (task_uid={task.task_uid})")
            self.metadata_db.remove_file(file_path)
        except Exception as e:
            print(f"[Meilisearch] Error deleting document: {e}")

    def wait_for_pending_tasks(self, timeout: int = 300) -> bool:
        """
        Wait for all pending indexing tasks to complete.

        Business Purpose: Ensures all documents are fully indexed before
        performing searches or getting statistics. Useful after bulk indexing.

        Args:
            timeout: Maximum seconds to wait (default: 300 = 5 minutes)

        Returns:
            True if all tasks completed, False if timeout

        Example:
            indexer.index_files_batch(files)
            indexer.wait_for_pending_tasks()
            count = indexer.get_document_count()  # Now accurate
        """
        start = time.time()
        while True:
            try:
                tasks = self.client.get_tasks()
                pending = [t for t in tasks.get('results', [])
                          if t.get('status') in ['enqueued', 'processing']]

                if not pending:
                    print(f"[Meilisearch] All tasks completed")
                    return True

                if time.time() - start > timeout:
                    print(f"[Meilisearch] Timeout waiting for tasks: {len(pending)} still pending")
                    return False

                time.sleep(1)

            except Exception as e:
                print(f"[Meilisearch] Error waiting for tasks: {e}")
                return False
