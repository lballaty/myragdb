# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/llm_config.py
# Description: Persistent LLM provider configuration storage in SQLite database
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

import sqlite3
import time
from typing import Optional, Dict, Any
from pathlib import Path


class LLMProviderConfigDatabase:
    """
    Persist LLM provider configuration across browser sessions and server restarts.

    Business Purpose: Store user's selected cloud LLM provider and authentication method
    in the database so the choice persists across all browsers and application restarts.
    Enables consistent LLM provider experience across devices.

    Example:
        db = LLMProviderConfigDatabase()
        db.set_current_provider('claude', 'api_key')
        provider = db.get_current_provider()  # Returns: ('claude', 'api_key')
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize LLM configuration database handler.

        Args:
            db_path: Path to SQLite database (uses default file_metadata.db if not provided)
        """
        if db_path is None:
            # Use the default metadata database
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "file_metadata.db")

        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_current_provider(self) -> Optional[tuple[str, Optional[str]]]:
        """
        Get the currently selected LLM provider.

        Business Purpose: Returns user's globally selected cloud LLM provider
        and authentication method for use across all browser instances.

        Returns:
            Tuple of (provider_name, auth_method) or None if not configured

        Example:
            provider, auth_method = db.get_current_provider()
            if provider == 'claude':
                # Use Claude API
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT current_provider, current_auth_method FROM llm_session_config WHERE id = 1"
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return (row[0], row[1])
            return None

        except Exception as e:
            print(f"Error reading current LLM provider: {e}")
            return None

    def set_current_provider(self, provider_name: str, auth_method: Optional[str] = None) -> bool:
        """
        Set the currently selected LLM provider globally.

        Business Purpose: Persists user's provider selection across all browser instances
        and application restarts.

        Args:
            provider_name: Provider identifier (e.g., 'claude', 'chatgpt', 'gemini')
            auth_method: Authentication method ('api_key', 'oauth', 'device_code')

        Returns:
            True if successful, False otherwise

        Example:
            success = db.set_current_provider('claude', 'api_key')
            # Provider selection now persists globally
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            timestamp = int(time.time())

            cursor.execute(
                """
                UPDATE llm_session_config
                SET current_provider = ?, current_auth_method = ?, updated_at = ?
                WHERE id = 1
                """,
                (provider_name, auth_method, timestamp)
            )

            conn.commit()
            conn.close()

            return cursor.rowcount > 0

        except Exception as e:
            print(f"Error setting current LLM provider: {e}")
            return False

    def clear_current_provider(self) -> bool:
        """
        Clear the currently selected LLM provider (revert to local LLM).

        Business Purpose: Allows user to switch back to local LLM across all instances.

        Returns:
            True if successful, False otherwise

        Example:
            db.clear_current_provider()
            # All browsers will now use local LLM
        """
        return self.set_current_provider(None, None)

    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration details for a specific provider.

        Args:
            provider_name: Provider identifier

        Returns:
            Dictionary with provider configuration or None if not found

        Example:
            config = db.get_provider_config('claude')
            if config:
                print(f"Auth method: {config['auth_method']}")
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT provider_name, display_name, enabled, auth_method,
                       configured_at, last_used_at, notes
                FROM llm_provider_config
                WHERE provider_name = ?
                """,
                (provider_name,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "provider_name": row[0],
                    "display_name": row[1],
                    "enabled": bool(row[2]),
                    "auth_method": row[3],
                    "configured_at": row[4],
                    "last_used_at": row[5],
                    "notes": row[6]
                }
            return None

        except Exception as e:
            print(f"Error reading provider config: {e}")
            return None

    def update_provider_config(
        self,
        provider_name: str,
        display_name: str,
        auth_method: Optional[str] = None,
        enabled: bool = True
    ) -> bool:
        """
        Update configuration for a provider.

        Args:
            provider_name: Provider identifier
            display_name: User-friendly name
            auth_method: Authentication method used
            enabled: Whether provider is active

        Returns:
            True if successful, False otherwise

        Example:
            db.update_provider_config('claude', 'Claude (Anthropic)', 'api_key', True)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            timestamp = int(time.time())

            cursor.execute(
                """
                INSERT OR REPLACE INTO llm_provider_config
                (provider_name, display_name, enabled, auth_method, configured_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (provider_name, display_name, enabled, auth_method, timestamp, timestamp)
            )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Error updating provider config: {e}")
            return False

    def mark_provider_used(self, provider_name: str) -> bool:
        """
        Update timestamp when a provider is used.

        Args:
            provider_name: Provider identifier

        Returns:
            True if successful, False otherwise

        Example:
            db.mark_provider_used('claude')  # Records usage time
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            timestamp = int(time.time())

            cursor.execute(
                """
                UPDATE llm_provider_config
                SET last_used_at = ?, updated_at = ?
                WHERE provider_name = ?
                """,
                (timestamp, timestamp, provider_name)
            )

            conn.commit()
            conn.close()

            return cursor.rowcount > 0

        except Exception as e:
            print(f"Error marking provider used: {e}")
            return False
