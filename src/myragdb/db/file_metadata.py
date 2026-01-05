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
