# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/migration_manager.py
# Description: Database schema migration manager for applying incremental schema updates
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import sqlite3
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manage database schema migrations.

    Business Purpose: Track and apply incremental schema changes, enabling
    safe database evolution while maintaining backward compatibility across
    server restarts and version updates.

    Example:
        manager = MigrationManager(db_path, migrations_dir)
        manager.apply_pending_migrations()  # Runs on server startup
    """

    def __init__(self, db_path: str, migrations_dir: str):
        """
        Initialize migration manager.

        Args:
            db_path: Path to SQLite database file
            migrations_dir: Directory containing migration SQL files
        """
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        self.conn = None

    def connect(self) -> sqlite3.Connection:
        """
        Create database connection.

        Returns:
            sqlite3.Connection object
        """
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_schema_version_table(self):
        """Create schema_version table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at INTEGER NOT NULL
            )
            """
        )
        self.conn.commit()

    def get_current_schema_version(self) -> int:
        """
        Get current database schema version.

        Returns:
            Current schema version (0 if no migrations applied)
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
        except sqlite3.OperationalError:
            # schema_version table doesn't exist yet
            return 0

    def _get_migration_files(self) -> List[Tuple[int, Path]]:
        """
        Get all available migration files sorted by version.

        Returns:
            List of (version_number, file_path) tuples sorted by version
        """
        migrations = []
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            try:
                # Parse version from filename: 001_description.sql → 1
                version_str = file_path.stem.split("_")[0]
                version = int(version_str)
                migrations.append((version, file_path))
            except (ValueError, IndexError):
                logger.warning(f"Skipping migration file with invalid name: {file_path}")
                continue
        return migrations

    def _read_migration_file(self, file_path: Path) -> str:
        """
        Read migration SQL from file.

        Args:
            file_path: Path to migration SQL file

        Returns:
            SQL content (with comments preserved for documentation)
        """
        with open(file_path, "r") as f:
            return f.read()

    def apply_migration(self, version: int, sql_content: str) -> bool:
        """
        Apply a single migration to the database.

        Args:
            version: Migration version number
            sql_content: SQL content to execute

        Returns:
            True if migration succeeded, False otherwise
        """
        try:
            cursor = self.conn.cursor()

            # Execute migration SQL
            # Note: sqlite3 doesn't support multiple statements in one execute(),
            # so we split on ';' and execute separately
            for statement in sql_content.split(";"):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)

            # Record migration in schema_version table
            import time
            cursor.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (version, int(time.time()))
            )
            self.conn.commit()

            logger.info(f"Successfully applied migration version {version}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error applying migration version {version}: {e}")
            self.conn.rollback()
            return False

    def apply_pending_migrations(self) -> bool:
        """
        Apply all pending migrations to the database.

        Business Purpose: Called on server startup to ensure database schema
        is current without requiring manual administration.

        Returns:
            True if all migrations succeeded, False if any failed
        """
        try:
            self.connect()
            self._ensure_schema_version_table()

            current_version = self.get_current_schema_version()
            logger.info(f"Current schema version: {current_version}")

            migrations = self._get_migration_files()

            if not migrations:
                logger.info("No migrations found")
                return True

            pending_migrations = [(v, f) for v, f in migrations if v > current_version]

            if not pending_migrations:
                logger.info(f"Database is current (version {current_version})")
                return True

            logger.info(f"Found {len(pending_migrations)} pending migrations")

            for version, file_path in pending_migrations:
                logger.info(f"Applying migration {version}: {file_path.name}")
                sql_content = self._read_migration_file(file_path)

                if not self.apply_migration(version, sql_content):
                    logger.error(f"Failed to apply migration {version}")
                    return False

            logger.info("All pending migrations applied successfully")
            return True

        except Exception as e:
            logger.error(f"Unexpected error during migrations: {e}")
            return False
        finally:
            self.close()

    def get_migration_status(self) -> dict:
        """
        Get detailed migration status.

        Returns:
            Dict with migration information
        """
        try:
            self.connect()
            self._ensure_schema_version_table()

            current_version = self.get_current_schema_version()
            migrations = self._get_migration_files()
            max_version = max([v for v, _ in migrations]) if migrations else 0

            return {
                "current_version": current_version,
                "available_version": max_version,
                "is_current": current_version == max_version,
                "pending_count": max(0, max_version - current_version),
                "migrations": [
                    {
                        "version": v,
                        "file": f.name,
                        "status": "applied" if v <= current_version else "pending"
                    }
                    for v, f in migrations
                ]
            }

        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            return {
                "current_version": 0,
                "available_version": 0,
                "is_current": False,
                "error": str(e)
            }
        finally:
            self.close()
