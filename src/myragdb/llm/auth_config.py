# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/auth_config.py
# Description: Authentication configuration and secure credential storage for cloud LLMs
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet


class AuthMethodType(str, Enum):
    """Supported authentication methods"""
    API_KEY = "api_key"
    SUBSCRIPTION = "subscription"
    CLI = "cli"


class LLMAuthConfig:
    """
    Stores authentication configuration for cloud LLMs.

    Business Purpose: Hold provider-specific auth info with validation
    and expiry tracking.

    Example:
        config = LLMAuthConfig(
            provider="gemini",
            auth_method=AuthMethodType.API_KEY,
            credentials={"api_key": "..."}
        )
    """

    def __init__(
        self,
        provider: str,
        auth_method: AuthMethodType,
        credentials: Dict[str, Any],
        expires_at: Optional[datetime] = None
    ):
        self.provider = provider
        self.auth_method = auth_method
        self.credentials = credentials
        self.expires_at = expires_at

    def is_valid(self) -> bool:
        """
        Check if credentials are still valid.

        Returns:
            True if credentials not expired and have required fields
        """
        # Check expiry
        if self.expires_at and datetime.now() > self.expires_at:
            return False

        # Validate required fields based on auth method
        if self.auth_method == AuthMethodType.API_KEY:
            return "api_key" in self.credentials and bool(self.credentials["api_key"])
        elif self.auth_method == AuthMethodType.SUBSCRIPTION:
            return "access_token" in self.credentials and bool(self.credentials["access_token"])
        elif self.auth_method == AuthMethodType.CLI:
            return "device_code" in self.credentials or "access_token" in self.credentials

        return False


class CredentialStore:
    """
    Secure storage for cloud LLM credentials.

    Business Purpose: Store API keys and tokens securely with encryption.
    Supports multiple storage backends: encrypted files, environment variables.

    Security: Uses Fernet (symmetric encryption) with file-based key storage.
    Key is stored in ~/.myragdb/.key with restricted permissions.

    Example:
        store = CredentialStore()

        # Save API key
        store.save_credentials("gemini", LLMAuthConfig(
            provider="gemini",
            auth_method=AuthMethodType.API_KEY,
            credentials={"api_key": "..."}
        ))

        # Load and use
        config = store.load_credentials("gemini")
        api_key = config.credentials["api_key"]
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize credential store.

        Args:
            storage_path: Path to store encrypted credentials file
        """
        self.storage_path = storage_path or str(Path.home() / ".myragdb" / "credentials.json")
        self._cipher_suite = self._get_cipher_suite()
        self._credentials_cache: Dict[str, LLMAuthConfig] = {}

    def save_credentials(self, provider: str, config: LLMAuthConfig) -> None:
        """
        Save credentials securely.

        Args:
            provider: Provider name (gemini, chatgpt, claude)
            config: LLMAuthConfig with credentials to save
        """
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

        # Load existing credentials
        credentials = self._load_all_credentials()

        # Add/update provider credentials
        credentials[provider] = {
            "auth_method": config.auth_method.value,
            "credentials": self._encrypt_credentials(config.credentials),
            "expires_at": config.expires_at.isoformat() if config.expires_at else None
        }

        # Write encrypted file
        with open(self.storage_path, "w") as f:
            json.dump(credentials, f, indent=2)

        # Update cache
        self._credentials_cache[provider] = config

    def load_credentials(self, provider: str) -> Optional[LLMAuthConfig]:
        """
        Load credentials for a provider.

        Priority:
        1. In-memory cache
        2. Environment variable (PROVIDER_API_KEY)
        3. Encrypted file storage

        Args:
            provider: Provider name

        Returns:
            LLMAuthConfig if found, None otherwise
        """
        # Try cache first
        if provider in self._credentials_cache:
            return self._credentials_cache[provider]

        # Try environment variable
        env_key = f"{provider.upper()}_API_KEY"
        if env_key in os.environ:
            config = LLMAuthConfig(
                provider=provider,
                auth_method=AuthMethodType.API_KEY,
                credentials={"api_key": os.environ[env_key]}
            )
            self._credentials_cache[provider] = config
            return config

        # Try file storage
        if not Path(self.storage_path).exists():
            return None

        try:
            with open(self.storage_path, "r") as f:
                all_credentials = json.load(f)

            if provider not in all_credentials:
                return None

            cred_data = all_credentials[provider]
            decrypted = self._decrypt_credentials(cred_data["credentials"])

            config = LLMAuthConfig(
                provider=provider,
                auth_method=AuthMethodType[cred_data["auth_method"].upper()],
                credentials=decrypted,
                expires_at=datetime.fromisoformat(cred_data["expires_at"])
                if cred_data.get("expires_at") else None
            )

            self._credentials_cache[provider] = config
            return config

        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None

    def delete_credentials(self, provider: str) -> None:
        """
        Delete credentials for a provider (logout).

        Args:
            provider: Provider name
        """
        credentials = self._load_all_credentials()
        if provider in credentials:
            del credentials[provider]

            with open(self.storage_path, "w") as f:
                json.dump(credentials, f, indent=2)

        # Clear cache
        if provider in self._credentials_cache:
            del self._credentials_cache[provider]

    def list_authenticated_providers(self) -> list:
        """
        List all providers with saved credentials.

        Returns:
            List of provider names
        """
        if not Path(self.storage_path).exists():
            return []

        try:
            with open(self.storage_path, "r") as f:
                credentials = json.load(f)
            return list(credentials.keys())
        except Exception:
            return []

    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials dictionary"""
        plaintext = json.dumps(credentials).encode()
        encrypted = self._cipher_suite.encrypt(plaintext)
        return encrypted.decode()

    def _decrypt_credentials(self, encrypted: str) -> Dict[str, Any]:
        """Decrypt credentials"""
        decrypted = self._cipher_suite.decrypt(encrypted.encode())
        return json.loads(decrypted.decode())

    def _get_cipher_suite(self) -> Fernet:
        """
        Get or create encryption key.

        Key is stored in ~/.myragdb/.key with restricted permissions.
        """
        key_path = Path.home() / ".myragdb" / ".key"

        if key_path.exists():
            with open(key_path, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_path, "wb") as f:
                f.write(key)
            # Restrict permissions to user only
            os.chmod(key_path, 0o600)

        return Fernet(key)

    def _load_all_credentials(self) -> Dict:
        """Load all credentials from file"""
        if not Path(self.storage_path).exists():
            return {}

        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
