# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/auth/auth_manager.py
# Description: Main authentication manager orchestrating all auth flows
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

from .flows.api_key_flow import APIKeyFlow, APIKey
from .flows.oauth_flow import OAuthFlow, OAuthToken
from .flows.device_code_flow import DeviceCodeFlow, DeviceCode


class AuthMethod(Enum):
    """Authentication method types"""
    API_KEY = "api_key"
    OAUTH = "oauth"
    DEVICE_CODE = "device_code"


@dataclass
class UserCredential:
    """Represents a user's stored credential"""
    credential_id: str
    provider: str
    auth_method: AuthMethod
    identifier: str  # Email, API key ID, user code, etc.
    is_active: bool = True
    is_default: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'credential_id': self.credential_id,
            'provider': self.provider,
            'auth_method': self.auth_method.value,
            'identifier': self.identifier,
            'is_active': self.is_active,
            'is_default': self.is_default,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UserCredential':
        """Create from dictionary"""
        return cls(
            credential_id=data['credential_id'],
            provider=data['provider'],
            auth_method=AuthMethod(data['auth_method']),
            identifier=data['identifier'],
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
        )


class AuthenticationManager:
    """
    Main authentication manager for MyRAGDB.

    Business Purpose: Provides unified interface to all authentication methods
    (API Key, OAuth, Device Code). Manages credentials across providers and
    authentication methods. Supports multiple credentials per user/provider.

    Supports:
    - API Key authentication (direct key setup)
    - OAuth authentication (web-based provider consent)
    - Device Code authentication (CLI without terminal leakage)

    Usage Example:
        auth = AuthenticationManager()

        # API Key method
        cred = auth.authenticate_with_api_key('claude', 'sk-ant-...')

        # OAuth method
        url = auth.initiate_oauth('claude')
        cred = auth.complete_oauth('claude', auth_code)

        # Device code method
        device = auth.initiate_device_code('claude')
        cred = auth.complete_device_code(device.device_code)

        # Get default credential for provider
        cred = auth.get_credential('claude')
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize Authentication Manager.

        Args:
            storage_dir: Directory to store credentials. Defaults to ~/.myragdb
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / '.myragdb'

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_file = self.storage_dir / 'credentials.json'

        # Initialize flows
        self.api_key_flow = APIKeyFlow(str(self.storage_dir / 'keys'))
        self.oauth_flow = OAuthFlow(str(self.storage_dir / 'oauth'))
        self.device_code_flow = DeviceCodeFlow(str(self.storage_dir / 'device'))

    # ========================================================================
    # API Key Authentication
    # ========================================================================

    def authenticate_with_api_key(
        self,
        provider: str,
        api_key: str,
        description: str = "",
        set_as_default: bool = True,
    ) -> Optional[UserCredential]:
        """
        Authenticate using an API key.

        Args:
            provider: Provider name (claude, gpt, gemini)
            api_key: The API key value
            description: Optional description
            set_as_default: Whether to set as default for provider

        Returns:
            UserCredential instance if successful
        """
        # Create and save API key
        api_key_obj = self.api_key_flow.create_api_key(
            provider=provider,
            api_key=api_key,
            description=description,
        )

        if not self.api_key_flow.save_api_key(api_key_obj):
            return None

        # Create credential reference
        credential = UserCredential(
            credential_id=api_key_obj.key_id,
            provider=provider,
            auth_method=AuthMethod.API_KEY,
            identifier=api_key_obj.key_id,
            is_default=set_as_default,
        )

        return self._save_credential(credential)

    def list_api_key_credentials(self, provider: Optional[str] = None) -> list[UserCredential]:
        """List API key credentials"""
        credentials = self._load_credentials()
        result = []

        for cred_data in credentials.values():
            cred = UserCredential.from_dict(cred_data)
            if cred.auth_method == AuthMethod.API_KEY:
                if provider is None or cred.provider == provider:
                    result.append(cred)

        return result

    # ========================================================================
    # OAuth Authentication
    # ========================================================================

    def initiate_oauth(self, provider: str) -> Optional[str]:
        """
        Initiate OAuth authentication.

        Args:
            provider: Provider name

        Returns:
            Authorization URL to redirect user to
        """
        try:
            return self.oauth_flow.get_authorization_url(provider)
        except ValueError as e:
            print(f"OAuth initiation failed: {e}")
            return None

    def complete_oauth(
        self,
        provider: str,
        auth_code: str,
        state: Optional[str] = None,
        set_as_default: bool = True,
    ) -> Optional[UserCredential]:
        """
        Complete OAuth authentication with authorization code.

        Args:
            provider: Provider name
            auth_code: Authorization code from provider
            state: State parameter for validation
            set_as_default: Whether to set as default

        Returns:
            UserCredential instance if successful
        """
        try:
            token = self.oauth_flow.exchange_code_for_token(
                provider=provider,
                auth_code=auth_code,
                state=state,
            )

            if not token:
                return None

            if not self.oauth_flow.save_token(token):
                return None

            # Create credential reference
            credential = UserCredential(
                credential_id=token.token_id,
                provider=provider,
                auth_method=AuthMethod.OAUTH,
                identifier=token.user_email or token.token_id,
                is_default=set_as_default,
            )

            return self._save_credential(credential)
        except Exception as e:
            print(f"OAuth completion failed: {e}")
            return None

    def list_oauth_credentials(self, provider: Optional[str] = None) -> list[UserCredential]:
        """List OAuth credentials"""
        credentials = self._load_credentials()
        result = []

        for cred_data in credentials.values():
            cred = UserCredential.from_dict(cred_data)
            if cred.auth_method == AuthMethod.OAUTH:
                if provider is None or cred.provider == provider:
                    result.append(cred)

        return result

    # ========================================================================
    # Device Code Authentication
    # ========================================================================

    def initiate_device_code(self, provider: str) -> Optional[DeviceCode]:
        """
        Initiate device code authentication.

        Args:
            provider: Provider name

        Returns:
            DeviceCode instance with user_code and verification_url
        """
        try:
            return self.device_code_flow.initiate_device_flow(provider)
        except ValueError as e:
            print(f"Device code initiation failed: {e}")
            return None

    def complete_device_code(
        self,
        device_code: str,
        set_as_default: bool = True,
    ) -> Optional[UserCredential]:
        """
        Complete device code authentication by polling for approval.

        Args:
            device_code: Device code from initiate_device_code
            set_as_default: Whether to set as default

        Returns:
            UserCredential instance if approved
        """
        try:
            # Poll for approval
            access_token = self.device_code_flow.poll_for_approval(device_code)
            if not access_token:
                return None

            # Get device code details
            device = self.device_code_flow._get_device_code(device_code)
            if not device:
                return None

            # Create credential reference
            credential = UserCredential(
                credential_id=device_code,
                provider=device.provider,
                auth_method=AuthMethod.DEVICE_CODE,
                identifier=device.user_code,
                is_default=set_as_default,
            )

            return self._save_credential(credential)
        except Exception as e:
            print(f"Device code completion failed: {e}")
            return None

    def list_device_code_credentials(self, provider: Optional[str] = None) -> list[UserCredential]:
        """List device code credentials"""
        credentials = self._load_credentials()
        result = []

        for cred_data in credentials.values():
            cred = UserCredential.from_dict(cred_data)
            if cred.auth_method == AuthMethod.DEVICE_CODE:
                if provider is None or cred.provider == provider:
                    result.append(cred)

        return result

    # ========================================================================
    # Credential Management
    # ========================================================================

    def get_credential(self, provider: str) -> Optional[UserCredential]:
        """
        Get default credential for a provider.

        Args:
            provider: Provider name

        Returns:
            UserCredential instance or None if not found
        """
        credentials = self._load_credentials()
        for cred_data in credentials.values():
            cred = UserCredential.from_dict(cred_data)
            if cred.provider == provider and cred.is_active and cred.is_default:
                return cred
        return None

    def list_credentials(self, provider: Optional[str] = None) -> list[UserCredential]:
        """
        List all credentials, optionally filtered by provider.

        Args:
            provider: Optional provider name to filter

        Returns:
            List of UserCredential instances
        """
        credentials = self._load_credentials()
        result = []

        for cred_data in credentials.values():
            cred = UserCredential.from_dict(cred_data)
            if cred.is_active:
                if provider is None or cred.provider == provider:
                    result.append(cred)

        return result

    def set_default_credential(self, credential_id: str) -> bool:
        """
        Set a credential as default for its provider.

        Args:
            credential_id: Credential ID

        Returns:
            True if successful
        """
        try:
            credentials = self._load_credentials()
            if credential_id not in credentials:
                return False

            target_cred = UserCredential.from_dict(credentials[credential_id])

            # Unset other defaults for this provider
            for cred_id, cred_data in credentials.items():
                cred = UserCredential.from_dict(cred_data)
                if cred.provider == target_cred.provider:
                    cred.is_default = False
                    credentials[cred_id] = cred.to_dict()

            # Set new default
            target_cred.is_default = True
            credentials[credential_id] = target_cred.to_dict()

            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)

            return True
        except Exception as e:
            print(f"Error setting default credential: {e}")
            return False

    def revoke_credential(self, credential_id: str) -> bool:
        """
        Revoke a credential.

        Args:
            credential_id: Credential ID

        Returns:
            True if successful
        """
        try:
            credentials = self._load_credentials()
            if credential_id not in credentials:
                return False

            cred = UserCredential.from_dict(credentials[credential_id])
            cred.is_active = False
            credentials[credential_id] = cred.to_dict()

            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)

            # Also revoke from underlying flow
            if cred.auth_method == AuthMethod.API_KEY:
                self.api_key_flow.revoke_api_key(credential_id)
            elif cred.auth_method == AuthMethod.OAUTH:
                self.oauth_flow.revoke_token(credential_id)

            return True
        except Exception as e:
            print(f"Error revoking credential: {e}")
            return False

    def delete_credential(self, credential_id: str) -> bool:
        """
        Delete a credential completely.

        Args:
            credential_id: Credential ID

        Returns:
            True if successful
        """
        try:
            credentials = self._load_credentials()
            if credential_id not in credentials:
                return False

            cred = UserCredential.from_dict(credentials[credential_id])
            del credentials[credential_id]

            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)

            # Also delete from underlying flow
            if cred.auth_method == AuthMethod.API_KEY:
                self.api_key_flow.delete_api_key(credential_id)
            elif cred.auth_method == AuthMethod.OAUTH:
                self.oauth_flow.revoke_token(credential_id)

            return True
        except Exception as e:
            print(f"Error deleting credential: {e}")
            return False

    # ========================================================================
    # Private Methods
    # ========================================================================

    def _save_credential(self, credential: UserCredential) -> Optional[UserCredential]:
        """Save credential metadata"""
        try:
            credentials = self._load_credentials()

            # If setting as default, unset others for this provider
            if credential.is_default:
                for cred_id, cred_data in credentials.items():
                    cred = UserCredential.from_dict(cred_data)
                    if cred.provider == credential.provider:
                        cred.is_default = False
                        credentials[cred_id] = cred.to_dict()

            credentials[credential.credential_id] = credential.to_dict()

            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)

            return credential
        except Exception as e:
            print(f"Error saving credential: {e}")
            return None

    def _load_credentials(self) -> dict:
        """Load credentials from storage"""
        if self.credentials_file.exists():
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        return {}
