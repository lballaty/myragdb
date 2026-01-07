# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/auth/flows/oauth_flow.py
# Description: OAuth authentication flow for web-based credential setup
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path
from uuid import uuid4


@dataclass
class OAuthToken:
    """Represents an OAuth token for a provider"""
    token_id: str
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    created_at: datetime = field(default_factory=datetime.now)
    scopes: list[str] = field(default_factory=list)
    user_email: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'token_id': self.token_id,
            'provider': self.provider,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'created_at': self.created_at.isoformat(),
            'scopes': self.scopes,
            'user_email': self.user_email,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'OAuthToken':
        """Create from dictionary"""
        return cls(
            token_id=data['token_id'],
            provider=data['provider'],
            access_token=data['access_token'],
            refresh_token=data.get('refresh_token'),
            token_type=data.get('token_type', 'Bearer'),
            expires_in=data.get('expires_in', 3600),
            created_at=datetime.fromisoformat(data['created_at']),
            scopes=data.get('scopes', []),
            user_email=data.get('user_email'),
        )

    def is_expired(self) -> bool:
        """Check if token has expired"""
        expiry = self.created_at + timedelta(seconds=self.expires_in)
        return datetime.now() > expiry

    def expires_at(self) -> datetime:
        """Get token expiration datetime"""
        return self.created_at + timedelta(seconds=self.expires_in)


class OAuthFlow:
    """
    OAuth authentication flow for web-based credential setup.

    Business Purpose: Enables users to authenticate via OAuth with cloud LLM providers.
    Provides secure, web-based authorization without exposing API keys directly.
    Supports token refresh for long-lived sessions.

    OAuth Providers Supported:
    - Google (Gemini)
    - OpenAI (ChatGPT)
    - Anthropic (Claude)

    Usage Example:
        flow = OAuthFlow()
        auth_url = flow.get_authorization_url('claude')
        # User visits auth_url, consents, redirected with code
        token = flow.exchange_code_for_token('claude', auth_code)
        flow.save_token(token)
    """

    # Provider OAuth configurations
    PROVIDER_CONFIGS = {
        'claude': {
            'auth_url': 'https://auth.anthropic.com/authorize',
            'token_url': 'https://auth.anthropic.com/token',
            'scopes': ['read', 'write'],
        },
        'gpt': {
            'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/generativeai'],
        },
        'gemini': {
            'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/generativeai'],
        },
    }

    def __init__(self, storage_dir: Optional[str] = None, callback_url: str = "http://localhost:8000/auth/callback"):
        """
        Initialize OAuth Flow.

        Args:
            storage_dir: Directory to store tokens. Defaults to ~/.myragdb/oauth
            callback_url: OAuth callback URL for redirects
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / '.myragdb' / 'oauth'

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.tokens_file = self.storage_dir / 'tokens.json'
        self.callback_url = callback_url

    def get_authorization_url(self, provider: str, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            provider: Provider name (claude, gpt, gemini)
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        if provider not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider: {provider}")

        config = self.PROVIDER_CONFIGS[provider]
        state = state or uuid4().hex

        # Store state for validation
        self._store_oauth_state(provider, state)

        params = {
            'client_id': f'{provider}_client_id',  # Should be configured
            'response_type': 'code',
            'scope': ' '.join(config['scopes']),
            'redirect_uri': self.callback_url,
            'state': state,
        }

        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{config['auth_url']}?{query_string}"

    def exchange_code_for_token(
        self,
        provider: str,
        auth_code: str,
        state: Optional[str] = None,
    ) -> Optional[OAuthToken]:
        """
        Exchange authorization code for access token.

        Args:
            provider: Provider name
            auth_code: Authorization code from OAuth provider
            state: State parameter for CSRF validation

        Returns:
            OAuthToken instance or None if exchange failed
        """
        if provider not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider: {provider}")

        # Validate state parameter
        if state and not self._validate_oauth_state(provider, state):
            raise ValueError("Invalid OAuth state parameter")

        config = self.PROVIDER_CONFIGS[provider]

        # In production, this would make an HTTP request to the token_url
        # For now, we return a mock token
        token = OAuthToken(
            token_id=f"oauth-{provider}-{uuid4().hex[:8]}",
            provider=provider,
            access_token=auth_code,  # In production, exchange for real token
            refresh_token=None,
            expires_in=3600,
            scopes=config['scopes'],
        )

        return token

    def refresh_token(self, token_id: str) -> Optional[OAuthToken]:
        """
        Refresh an expired OAuth token.

        Args:
            token_id: Token identifier

        Returns:
            New OAuthToken or None if refresh failed
        """
        token = self.get_token(token_id)
        if not token or not token.refresh_token:
            return None

        # In production, use refresh_token to get new access_token
        token.access_token = f"refreshed_{uuid4().hex[:16]}"
        token.created_at = datetime.now()

        self.save_token(token)
        return token

    def save_token(self, token: OAuthToken) -> bool:
        """
        Save OAuth token to storage.

        Args:
            token: OAuthToken instance

        Returns:
            True if successful
        """
        try:
            tokens = self._load_tokens()
            tokens[token.token_id] = token.to_dict()

            with open(self.tokens_file, 'w') as f:
                json.dump(tokens, f, indent=2)

            # Restrict file permissions
            import os
            os.chmod(self.tokens_file, 0o600)
            return True
        except Exception as e:
            print(f"Error saving OAuth token: {e}")
            return False

    def get_token(self, token_id: str) -> Optional[OAuthToken]:
        """
        Get OAuth token by ID.

        Args:
            token_id: Token identifier

        Returns:
            OAuthToken or None if not found
        """
        tokens = self._load_tokens()
        if token_id in tokens:
            token = OAuthToken.from_dict(tokens[token_id])
            return token if not token.is_expired() else None
        return None

    def list_tokens(self, provider: Optional[str] = None) -> list[OAuthToken]:
        """
        List all OAuth tokens, optionally filtered by provider.

        Args:
            provider: Optional provider name to filter

        Returns:
            List of OAuthToken instances
        """
        tokens = self._load_tokens()
        token_list = [OAuthToken.from_dict(data) for data in tokens.values()]

        if provider:
            token_list = [t for t in token_list if t.provider == provider]

        return [t for t in token_list if not t.is_expired()]

    def revoke_token(self, token_id: str) -> bool:
        """
        Revoke an OAuth token.

        Args:
            token_id: Token identifier

        Returns:
            True if successful
        """
        try:
            tokens = self._load_tokens()
            if token_id in tokens:
                del tokens[token_id]
                with open(self.tokens_file, 'w') as f:
                    json.dump(tokens, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Error revoking token: {e}")
            return False

    def _load_tokens(self) -> dict:
        """Load tokens from storage"""
        if self.tokens_file.exists():
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        return {}

    def _store_oauth_state(self, provider: str, state: str) -> None:
        """Store OAuth state for validation"""
        states_file = self.storage_dir / 'states.json'
        states = {}
        if states_file.exists():
            with open(states_file, 'r') as f:
                states = json.load(f)

        states[f"{provider}_{state}"] = {
            'created_at': datetime.now().isoformat(),
        }

        with open(states_file, 'w') as f:
            json.dump(states, f, indent=2)

    def _validate_oauth_state(self, provider: str, state: str) -> bool:
        """Validate OAuth state parameter"""
        states_file = self.storage_dir / 'states.json'
        if not states_file.exists():
            return False

        with open(states_file, 'r') as f:
            states = json.load(f)

        state_key = f"{provider}_{state}"
        if state_key not in states:
            return False

        # State is valid, remove it
        del states[state_key]
        with open(states_file, 'w') as f:
            json.dump(states, f, indent=2)

        return True
