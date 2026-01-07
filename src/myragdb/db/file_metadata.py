# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/file_metadata.py
# Description: SQLite database for persistent file metadata tracking across server restarts
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

import sqlite3
import time
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class FileMetadataDatabase:
    """
    Persistent metadata storage for file indexing tracking.

    Business Purpose: Enables incremental indexing across server restarts by
    storing which files have been indexed and when, eliminating need to re-index
    all files after every restart.

    Example:
        db = FileMetadataDatabase('data/file_metadata.db')

        # Check if file needs re-indexing
        last_indexed = db.get_last_indexed_time('/path/to/file.py')
        if file_mtime > last_indexed:
            # File changed, re-index it
            index_file(file)
            db.update_file_metadata(file_path, repository, 'keyword')
    """

    def __init__(self, db_path: str = 'data/file_metadata.db'):
        """
        Initialize metadata database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """
        Create database and tables if they don't exist.

        Business Purpose: Initializes database schema on first run.
        """
        # Ensure data directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Read schema SQL
        schema_path = Path(__file__).parent / 'schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute schema
        with self._get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Business Purpose: Ensures connections are properly closed and
        handles transaction management.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
        finally:
            conn.close()

    def get_last_indexed_time(self, file_path: str) -> float:
        """
        Get when a file was last indexed.

        Args:
            file_path: Absolute path to file

        Returns:
            Unix timestamp of last indexing, or 0 if never indexed

        Example:
            last_indexed = db.get_last_indexed_time('/path/to/file.py')
            # Returns: 1735948800 (or 0 if never indexed)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT last_indexed FROM file_metadata WHERE file_path = ?',
                (file_path,)
            )
            row = cursor.fetchone()
            return float(row['last_indexed']) if row else 0.0

    def update_file_metadata(
        self,
        file_path: str,
        repository: str,
        index_type: str,
        last_modified: Optional[int] = None,
        content_hash: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> None:
        """
        Update or insert file metadata after indexing.

        Business Purpose: Records that a file has been indexed, enabling
        incremental indexing on next run.

        Args:
            file_path: Absolute path to file
            repository: Repository name
            index_type: 'keyword', 'vector', or 'both'
            last_modified: File's mtime (optional, will fetch if not provided)
            content_hash: SHA256 hash of content (optional)
            file_size: File size in bytes (optional)

        Example:
            db.update_file_metadata(
                '/path/to/file.py',
                'xLLMArionComply',
                'keyword',
                last_modified=1704067200
            )
        """
        now = int(time.time())

        # Get file stats if not provided
        if last_modified is None or file_size is None:
            try:
                stat = Path(file_path).stat()
                if last_modified is None:
                    last_modified = int(stat.st_mtime)
                if file_size is None:
                    file_size = stat.st_size
            except OSError:
                last_modified = now
                file_size = 0

        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO file_metadata (
                    file_path, repository, last_indexed, last_modified,
                    content_hash, file_size, index_type, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    repository = excluded.repository,
                    last_indexed = excluded.last_indexed,
                    last_modified = excluded.last_modified,
                    content_hash = excluded.content_hash,
                    file_size = excluded.file_size,
                    index_type = excluded.index_type,
                    updated_at = excluded.updated_at
            ''', (
                file_path, repository, now, last_modified,
                content_hash, file_size, index_type, now, now
            ))
            conn.commit()

    def batch_update_file_metadata(self, files: List[Dict[str, Any]]) -> None:
        """
        Batch update multiple files for better performance.

        Business Purpose: Efficiently updates metadata for many files
        during batch indexing operations.

        Args:
            files: List of dicts with keys: file_path, repository, index_type,
                   last_modified (optional), content_hash (optional), file_size (optional)

        Example:
            db.batch_update_file_metadata([
                {'file_path': '/path/1.py', 'repository': 'repo1', 'index_type': 'keyword'},
                {'file_path': '/path/2.py', 'repository': 'repo1', 'index_type': 'keyword'},
            ])
        """
        now = int(time.time())

        with self._get_connection() as conn:
            for file_data in files:
                file_path = file_data['file_path']
                repository = file_data['repository']
                index_type = file_data['index_type']
                last_modified = file_data.get('last_modified')
                content_hash = file_data.get('content_hash')
                file_size = file_data.get('file_size')

                # Get file stats if not provided
                if last_modified is None or file_size is None:
                    try:
                        stat = Path(file_path).stat()
                        if last_modified is None:
                            last_modified = int(stat.st_mtime)
                        if file_size is None:
                            file_size = stat.st_size
                    except OSError:
                        last_modified = now
                        file_size = 0

                conn.execute('''
                    INSERT INTO file_metadata (
                        file_path, repository, last_indexed, last_modified,
                        content_hash, file_size, index_type, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(file_path) DO UPDATE SET
                        repository = excluded.repository,
                        last_indexed = excluded.last_indexed,
                        last_modified = excluded.last_modified,
                        content_hash = excluded.content_hash,
                        file_size = excluded.file_size,
                        index_type = excluded.index_type,
                        updated_at = excluded.updated_at
                ''', (
                    file_path, repository, now, last_modified,
                    content_hash, file_size, index_type, now, now
                ))

            conn.commit()

    def remove_file(self, file_path: str) -> None:
        """
        Remove file metadata when file is deleted.

        Args:
            file_path: Absolute path to file
        """
        with self._get_connection() as conn:
            conn.execute('DELETE FROM file_metadata WHERE file_path = ?', (file_path,))
            conn.commit()

    def remove_repository_files(self, repository: str) -> int:
        """
        Remove all files from a repository.

        Args:
            repository: Repository name

        Returns:
            Number of files removed
        """
        with self._get_connection() as conn:
            cursor = conn.execute('DELETE FROM file_metadata WHERE repository = ?', (repository,))
            conn.commit()
            return cursor.rowcount

    def get_repository_file_count(self, repository: str) -> int:
        """
        Get count of indexed files for a repository.

        Args:
            repository: Repository name

        Returns:
            Number of files indexed for this repository
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT COUNT(*) as count FROM file_metadata WHERE repository = ?',
                (repository,)
            )
            row = cursor.fetchone()
            return row['count'] if row else 0

    def get_all_indexed_files(self, repository: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of all indexed files.

        Args:
            repository: Optional repository filter

        Returns:
            List of file metadata dicts
        """
        with self._get_connection() as conn:
            if repository:
                cursor = conn.execute(
                    'SELECT * FROM file_metadata WHERE repository = ?',
                    (repository,)
                )
            else:
                cursor = conn.execute('SELECT * FROM file_metadata')

            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dict with stats like total_files, repositories, etc.
        """
        with self._get_connection() as conn:
            # Total files
            cursor = conn.execute('SELECT COUNT(*) as count FROM file_metadata')
            total_files = cursor.fetchone()['count']

            # Files by repository
            cursor = conn.execute('''
                SELECT repository, COUNT(*) as count
                FROM file_metadata
                GROUP BY repository
            ''')
            by_repository = {row['repository']: row['count'] for row in cursor.fetchall()}

            # Files by index type
            cursor = conn.execute('''
                SELECT index_type, COUNT(*) as count
                FROM file_metadata
                GROUP BY index_type
            ''')
            by_index_type = {row['index_type']: row['count'] for row in cursor.fetchall()}

            return {
                'total_files': total_files,
                'by_repository': by_repository,
                'by_index_type': by_index_type
            }

    def calculate_content_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA256 hash of file content.

        Business Purpose: Enables deduplication by detecting identical
        content across different file paths.

        Args:
            file_path: Absolute path to file

        Returns:
            SHA256 hex digest, or None if file not readable
        """
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (OSError, IOError):
            return None

    def record_repository_indexing(
        self,
        repository: str,
        index_type: str,
        duration_seconds: float,
        total_files: int,
        total_size_bytes: int,
        is_initial: bool = False
    ) -> None:
        """
        Record indexing statistics for a repository.

        Business Purpose: Tracks indexing performance to enable estimation
        of future indexing times based on repository size. By correlating
        duration with file count and total size, users can predict how long
        a re-index will take.

        Args:
            repository: Repository name
            index_type: 'keyword' or 'vector'
            duration_seconds: How long the indexing took
            total_files: Number of files indexed
            total_size_bytes: Total size of indexed files
            is_initial: True if this is the first time indexing (initial),
                       False for incremental reindex

        Example:
            db.record_repository_indexing(
                repository='xLLMArionComply',
                index_type='keyword',
                duration_seconds=45.2,
                total_files=1234,
                total_size_bytes=5242880,
                is_initial=True
            )
        """
        now = int(time.time())

        with self._get_connection() as conn:
            # Check if we already have stats for this repo+index_type
            cursor = conn.execute(
                'SELECT initial_index_time_seconds FROM repository_stats WHERE repository = ? AND index_type = ?',
                (repository, index_type)
            )
            existing = cursor.fetchone()

            if is_initial or existing is None:
                # This is the initial index - record as initial
                conn.execute('''
                    INSERT INTO repository_stats (
                        repository, index_type, initial_index_time_seconds,
                        initial_index_timestamp, last_reindex_time_seconds,
                        last_reindex_timestamp, total_files_indexed, total_size_bytes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(repository, index_type) DO UPDATE SET
                        initial_index_time_seconds = excluded.initial_index_time_seconds,
                        initial_index_timestamp = excluded.initial_index_timestamp,
                        last_reindex_time_seconds = excluded.last_reindex_time_seconds,
                        last_reindex_timestamp = excluded.last_reindex_timestamp,
                        total_files_indexed = excluded.total_files_indexed,
                        total_size_bytes = excluded.total_size_bytes
                ''', (
                    repository, index_type, duration_seconds, now,
                    duration_seconds, now, total_files, total_size_bytes
                ))
            else:
                # This is a reindex - only update reindex fields
                conn.execute('''
                    UPDATE repository_stats
                    SET last_reindex_time_seconds = ?,
                        last_reindex_timestamp = ?,
                        total_files_indexed = ?,
                        total_size_bytes = ?
                    WHERE repository = ? AND index_type = ?
                ''', (
                    duration_seconds, now, total_files, total_size_bytes,
                    repository, index_type
                ))

            conn.commit()

    def get_repository_stats(self, repository: str, index_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get indexing statistics for a repository.

        Business Purpose: Retrieves historical indexing performance data
        to help estimate future indexing times and track performance trends.

        Args:
            repository: Repository name
            index_type: Optional filter for 'keyword' or 'vector'

        Returns:
            List of stats dicts with timing and size information

        Example:
            stats = db.get_repository_stats('xLLMArionComply', 'keyword')
            if stats:
                initial_time = stats[0]['initial_index_time_seconds']
                files_per_sec = stats[0]['total_files_indexed'] / initial_time
                print(f"Indexing rate: {files_per_sec:.1f} files/sec")
        """
        with self._get_connection() as conn:
            if index_type:
                cursor = conn.execute(
                    'SELECT * FROM repository_stats WHERE repository = ? AND index_type = ?',
                    (repository, index_type)
                )
            else:
                cursor = conn.execute(
                    'SELECT * FROM repository_stats WHERE repository = ?',
                    (repository,)
                )

            return [dict(row) for row in cursor.fetchall()]

    def get_all_repository_stats(self) -> List[Dict[str, Any]]:
        """
        Get indexing statistics for all repositories.

        Business Purpose: Provides overview of indexing performance across
        all repositories for system-wide analysis.

        Returns:
            List of all repository stats

        Example:
            all_stats = db.get_all_repository_stats()
            for stat in all_stats:
                print(f"{stat['repository']} ({stat['index_type']}): "
                      f"{stat['total_files_indexed']} files in "
                      f"{stat['initial_index_time_seconds']:.1f}s")
        """
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT * FROM repository_stats')
            return [dict(row) for row in cursor.fetchall()]

    # System-wide metadata methods (replaces metadata.json)

    def get_last_index_time(self) -> Optional[str]:
        """
        Get timestamp of last successful indexing run.

        Returns:
            ISO 8601 timestamp string or None if never indexed

        Example:
            last_time = db.get_last_index_time()
            if last_time:
                print(f"Last indexed: {last_time}")
            else:
                print("Never indexed")
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT value FROM system_metadata WHERE key = ?',
                ('last_index_time',)
            )
            row = cursor.fetchone()
            return row['value'] if row and row['value'] else None

    def set_last_index_time(self, timestamp: Optional[str] = None):
        """
        Record timestamp of successful indexing completion.

        Args:
            timestamp: ISO 8601 timestamp string or None to use current time

        Example:
            db.set_last_index_time("2026-01-06T15:59:00Z")
        """
        from datetime import datetime

        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"

        now = int(time.time())

        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO system_metadata (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            ''', ('last_index_time', timestamp, now))
            conn.commit()

    def get_search_stats(self) -> Dict[str, int]:
        """
        Get cumulative search statistics.

        Returns:
            Dictionary with total_searches and total_search_time_ms

        Example:
            stats = db.get_search_stats()
            if stats["total_searches"] > 0:
                avg_ms = stats["total_search_time_ms"] / stats["total_searches"]
                print(f"Average search time: {avg_ms:.2f}ms")
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT key, value FROM system_metadata
                WHERE key IN ('total_searches', 'total_search_time_ms')
            ''')

            stats = {
                'total_searches': 0,
                'total_search_time_ms': 0
            }

            for row in cursor:
                key = row['key']
                value = int(row['value']) if row['value'] else 0
                stats[key] = value

            return stats

    def record_search(self, search_time_ms: float):
        """
        Record a search operation and its duration.

        Business Purpose: Track search performance over time to identify
        degradation or improvements.

        Args:
            search_time_ms: Search duration in milliseconds

        Example:
            import time
            start = time.time()
            results = search_engine.search("query")
            duration_ms = (time.time() - start) * 1000
            db.record_search(duration_ms)
        """
        now = int(time.time())

        with self._get_connection() as conn:
            # Get current values
            cursor = conn.execute('''
                SELECT key, value FROM system_metadata
                WHERE key IN ('total_searches', 'total_search_time_ms')
            ''')

            current_values = {}
            for row in cursor:
                current_values[row['key']] = int(row['value']) if row['value'] else 0

            # Increment values
            new_total_searches = current_values.get('total_searches', 0) + 1
            new_total_time = current_values.get('total_search_time_ms', 0) + search_time_ms

            # Update database
            conn.execute('''
                INSERT INTO system_metadata (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            ''', ('total_searches', str(new_total_searches), now))

            conn.execute('''
                INSERT INTO system_metadata (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            ''', ('total_search_time_ms', str(int(new_total_time)), now))

            conn.commit()

    def clear_system_metadata(self):
        """
        Reset all system metadata to defaults.

        Business Purpose: Allow users to reset statistics without
        deleting the entire database.

        Example:
            db.clear_system_metadata()  # Reset all stats
        """
        now = int(time.time())

        with self._get_connection() as conn:
            conn.execute('''
                DELETE FROM system_metadata
                WHERE key IN ('last_index_time', 'total_searches', 'total_search_time_ms')
            ''')

            conn.execute('''
                INSERT INTO system_metadata (key, value, updated_at)
                VALUES ('last_index_time', NULL, ?)
            ''', (now,))

            conn.execute('''
                INSERT INTO system_metadata (key, value, updated_at)
                VALUES ('total_searches', '0', ?)
            ''', (now,))

            conn.execute('''
                INSERT INTO system_metadata (key, value, updated_at)
                VALUES ('total_search_time_ms', '0', ?)
            ''', (now,))

            conn.commit()


# Singleton instance for easy import (replaces MetadataStore)
_metadata_db_instance = None


def get_metadata_db() -> FileMetadataDatabase:
    """
    Get singleton instance of FileMetadataDatabase.

    Business Purpose: Provides a shared database connection across the application
    to avoid creating multiple connections and ensure consistent state.

    Returns:
        Singleton FileMetadataDatabase instance

    Example:
        from myragdb.db.file_metadata import get_metadata_db

        db = get_metadata_db()
        last_time = db.get_last_index_time()
    """
    global _metadata_db_instance
    if _metadata_db_instance is None:
        _metadata_db_instance = FileMetadataDatabase()
    return _metadata_db_instance
