# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/auth/flows/api_key_flow.py
# Description: API Key authentication flow for direct credential setup
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import os
from pathlib import Path


@dataclass
class APIKey:
    """Represents a stored API key credential"""
    key_id: str
    api_key: str
    provider: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    description: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'key_id': self.key_id,
            'api_key': self.api_key,
            'provider': self.provider,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'APIKey':
        """Create from dictionary"""
        return cls(
            key_id=data['key_id'],
            api_key=data['api_key'],
            provider=data['provider'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            is_active=data.get('is_active', True),
            description=data.get('description', ''),
        )

    def is_expired(self) -> bool:
        """Check if API key has expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at


class APIKeyFlow:
    """
    API Key authentication flow for direct credential setup.

    Business Purpose: Allows users to directly provide API keys for cloud LLM providers
    without going through OAuth. Useful for automation, CI/CD, and programmatic access.

    Usage Example:
        flow = APIKeyFlow()
        api_key = flow.create_api_key(
            provider='claude',
            api_key='sk-ant-...',
            description='Production API key'
        )
        saved = flow.save_api_key(api_key)
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize API Key Flow.

        Args:
            storage_dir: Directory to store API keys. Defaults to ~/.myragdb/keys
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / '.myragdb' / 'keys'

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.api_keys_file = self.storage_dir / 'api_keys.json'

    def create_api_key(
        self,
        provider: str,
        api_key: str,
        description: str = "",
        expires_in_days: Optional[int] = None,
    ) -> APIKey:
        """
        Create a new API key credential.

        Args:
            provider: LLM provider name (claude, gpt-4, gemini)
            api_key: The actual API key value
            description: Optional human-readable description
            expires_in_days: Optional expiration in days

        Returns:
            APIKey instance
        """
        from uuid import uuid4
        key_id = f"{provider}-{uuid4().hex[:8]}"

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        return APIKey(
            key_id=key_id,
            api_key=api_key,
            provider=provider,
            expires_at=expires_at,
            description=description,
        )

    def save_api_key(self, api_key: APIKey) -> bool:
        """
        Save API key to encrypted storage.

        Args:
            api_key: APIKey instance to save

        Returns:
            True if successful, False otherwise
        """
        try:
            api_keys = self._load_api_keys()
            api_keys[api_key.key_id] = api_key.to_dict()

            with open(self.api_keys_file, 'w') as f:
                json.dump(api_keys, f, indent=2)

            # Restrict file permissions for security
            os.chmod(self.api_keys_file, 0o600)
            return True
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False

    def list_api_keys(self, provider: Optional[str] = None) -> list[APIKey]:
        """
        List all stored API keys, optionally filtered by provider.

        Args:
            provider: Optional provider name to filter by

        Returns:
            List of APIKey instances
        """
        api_keys = self._load_api_keys()
        keys = [APIKey.from_dict(data) for data in api_keys.values()]

        if provider:
            keys = [k for k in keys if k.provider == provider]

        # Filter out expired keys from results
        return [k for k in keys if not k.is_expired()]

    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """
        Get a specific API key by ID.

        Args:
            key_id: The key identifier

        Returns:
            APIKey instance or None if not found
        """
        api_keys = self._load_api_keys()
        if key_id in api_keys:
            key = APIKey.from_dict(api_keys[key_id])
            if not key.is_expired():
                return key
        return None

    def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke (deactivate) an API key.

        Args:
            key_id: The key identifier to revoke

        Returns:
            True if successful
        """
        try:
            api_keys = self._load_api_keys()
            if key_id in api_keys:
                api_keys[key_id]['is_active'] = False
                with open(self.api_keys_file, 'w') as f:
                    json.dump(api_keys, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Error revoking API key: {e}")
            return False

    def delete_api_key(self, key_id: str) -> bool:
        """
        Delete an API key completely.

        Args:
            key_id: The key identifier to delete

        Returns:
            True if successful
        """
        try:
            api_keys = self._load_api_keys()
            if key_id in api_keys:
                del api_keys[key_id]
                with open(self.api_keys_file, 'w') as f:
                    json.dump(api_keys, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False

    def _load_api_keys(self) -> dict:
        """Load API keys from storage"""
        if self.api_keys_file.exists():
            with open(self.api_keys_file, 'r') as f:
                return json.load(f)
        return {}
