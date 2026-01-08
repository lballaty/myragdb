# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/auth/oauth_auth.py
# Description: OAuth 2.0 authentication flows for cloud LLM providers
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

"""
OAuth 2.0 Authentication

Handles OAuth flows for cloud providers using subscription-based authentication:
- Google Gemini (via Google Cloud OAuth)
- OpenAI (via subscription account)
- Anthropic (via subscription account)

Manages token acquisition, refresh, and expiration handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import time
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class OAuthProvider(str, Enum):
    """Supported OAuth providers"""
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class OAuthToken:
    """OAuth token with expiration tracking"""
    access_token: str
    token_type: str = "Bearer"
    expires_at: Optional[float] = None
    refresh_token: Optional[str] = None
    scopes: list = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if token has expired"""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at

    def is_expiring_soon(self, threshold_seconds: int = 300) -> bool:
        """Check if token is expiring within threshold (default 5 minutes)"""
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - threshold_seconds)


@dataclass
class OAuthAuthorizationRequest:
    """OAuth authorization request details"""
    provider: OAuthProvider
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list
    state: str = ""


@dataclass
class OAuthAuthorizationResponse:
    """OAuth authorization response from provider"""
    provider: OAuthProvider
    authorization_code: str
    state: str
    error: Optional[str] = None


class OAuthProviderBase(ABC):
    """
    Abstract base class for OAuth providers.

    Each provider must implement:
    - get_authorization_url(): Generate OAuth authorization URL
    - exchange_code_for_token(): Exchange auth code for access token
    - refresh_access_token(): Refresh expired access token
    - validate_token(): Verify token is still valid

    Business Purpose: Provides pluggable OAuth integration for different
    cloud providers with consistent interface.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize OAuth provider.

        Args:
            client_id: OAuth application client ID
            client_secret: OAuth application client secret
            redirect_uri: Redirect URI registered with provider
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @abstractmethod
    async def get_authorization_url(self, scopes: list, state: str = "") -> str:
        """
        Generate OAuth authorization URL for user to visit.

        Args:
            scopes: OAuth scopes to request
            state: State parameter for CSRF protection

        Returns:
            Full authorization URL
        """
        pass

    @abstractmethod
    async def exchange_code_for_token(
        self,
        authorization_code: str
    ) -> OAuthToken:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Code from OAuth callback

        Returns:
            OAuthToken with access_token and expiration info
        """
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> OAuthToken:
        """
        Refresh expired access token using refresh token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            New OAuthToken with refreshed access_token
        """
        pass

    @abstractmethod
    async def validate_token(self, access_token: str) -> bool:
        """
        Validate that access token is still valid.

        Args:
            access_token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        pass


class GoogleOAuthProvider(OAuthProviderBase):
    """
    Google OAuth provider for Gemini API access.

    Implements OAuth 2.0 Authorization Code Flow for Google Cloud.
    """

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    VALIDATE_URL = "https://oauth2.googleapis.com/tokeninfo"

    async def get_authorization_url(self, scopes: list, state: str = "") -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            scopes: OAuth scopes (e.g., "https://www.googleapis.com/auth/generative-language")
            state: CSRF protection state

        Returns:
            Full authorization URL
        """
        scope_str = "+".join(scopes) if scopes else "https://www.googleapis.com/auth/generative-language"

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scope_str,
        }
        if state:
            params["state"] = state

        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZATION_URL}?{param_str}"

    async def exchange_code_for_token(self, authorization_code: str) -> OAuthToken:
        """
        Exchange authorization code for Google access token.

        Args:
            authorization_code: Authorization code from callback

        Returns:
            OAuthToken with access_token and expiration
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "code": authorization_code,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "grant_type": "authorization_code",
                    }
                )
                response.raise_for_status()
                data = response.json()

                expires_at = time.time() + data.get("expires_in", 3600) if "expires_in" in data else None

                return OAuthToken(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_at=expires_at,
                    refresh_token=data.get("refresh_token"),
                    scopes=data.get("scope", "").split()
                )

        except Exception as e:
            logger.error(f"Failed to exchange Google authorization code: {e}")
            raise

    async def refresh_access_token(self, refresh_token: str) -> OAuthToken:
        """
        Refresh Google access token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            New OAuthToken with refreshed access_token
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    }
                )
                response.raise_for_status()
                data = response.json()

                expires_at = time.time() + data.get("expires_in", 3600) if "expires_in" in data else None

                return OAuthToken(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_at=expires_at,
                    refresh_token=refresh_token,  # Keep original refresh token
                    scopes=data.get("scope", "").split()
                )

        except Exception as e:
            logger.error(f"Failed to refresh Google access token: {e}")
            raise

    async def validate_token(self, access_token: str) -> bool:
        """
        Validate Google access token.

        Args:
            access_token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.VALIDATE_URL,
                    params={"access_token": access_token}
                )
                return response.status_code == 200

        except Exception as e:
            logger.warning(f"Failed to validate Google token: {e}")
            return False


class OpenAIOAuthProvider(OAuthProviderBase):
    """
    OpenAI OAuth provider for ChatGPT API access via subscription.

    Note: OpenAI primarily uses API keys, but this implements
    OAuth for subscription-based access management.
    """

    AUTHORIZATION_URL = "https://auth.openai.com/authorize"
    TOKEN_URL = "https://auth.openai.com/oauth/authorize"
    VALIDATE_URL = "https://api.openai.com/v1/models"

    async def get_authorization_url(self, scopes: list, state: str = "") -> str:
        """
        Generate OpenAI OAuth authorization URL.

        Args:
            scopes: OAuth scopes
            state: CSRF protection state

        Returns:
            Full authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes) if scopes else "openai",
        }
        if state:
            params["state"] = state

        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZATION_URL}?{param_str}"

    async def exchange_code_for_token(self, authorization_code: str) -> OAuthToken:
        """
        Exchange authorization code for OpenAI access token.

        Args:
            authorization_code: Authorization code from callback

        Returns:
            OAuthToken with access_token
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "code": authorization_code,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "grant_type": "authorization_code",
                    }
                )
                response.raise_for_status()
                data = response.json()

                # OpenAI tokens typically don't expire
                return OAuthToken(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_at=None,
                    refresh_token=data.get("refresh_token"),
                )

        except Exception as e:
            logger.error(f"Failed to exchange OpenAI authorization code: {e}")
            raise

    async def refresh_access_token(self, refresh_token: str) -> OAuthToken:
        """
        Refresh OpenAI access token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            New OAuthToken
        """
        # OpenAI tokens typically don't expire, but implement for completeness
        logger.warning("OpenAI tokens typically don't expire, refresh may not be needed")
        raise NotImplementedError("OpenAI refresh token flow not implemented")

    async def validate_token(self, access_token: str) -> bool:
        """
        Validate OpenAI access token.

        Args:
            access_token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.VALIDATE_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                return response.status_code == 200

        except Exception as e:
            logger.warning(f"Failed to validate OpenAI token: {e}")
            return False


class AnthropicOAuthProvider(OAuthProviderBase):
    """
    Anthropic OAuth provider for Claude API access via subscription.

    Similar to OpenAI, Anthropic primarily uses API keys but this
    implements OAuth for subscription management.
    """

    AUTHORIZATION_URL = "https://auth.anthropic.com/authorize"
    TOKEN_URL = "https://auth.anthropic.com/token"
    VALIDATE_URL = "https://api.anthropic.com/v1/models"

    async def get_authorization_url(self, scopes: list, state: str = "") -> str:
        """
        Generate Anthropic OAuth authorization URL.

        Args:
            scopes: OAuth scopes
            state: CSRF protection state

        Returns:
            Full authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes) if scopes else "anthropic",
        }
        if state:
            params["state"] = state

        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZATION_URL}?{param_str}"

    async def exchange_code_for_token(self, authorization_code: str) -> OAuthToken:
        """
        Exchange authorization code for Anthropic access token.

        Args:
            authorization_code: Authorization code from callback

        Returns:
            OAuthToken with access_token
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "code": authorization_code,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "grant_type": "authorization_code",
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Anthropic tokens typically don't expire
                return OAuthToken(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_at=None,
                    refresh_token=data.get("refresh_token"),
                )

        except Exception as e:
            logger.error(f"Failed to exchange Anthropic authorization code: {e}")
            raise

    async def refresh_access_token(self, refresh_token: str) -> OAuthToken:
        """
        Refresh Anthropic access token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            New OAuthToken
        """
        # Anthropic tokens typically don't expire
        logger.warning("Anthropic tokens typically don't expire, refresh may not be needed")
        raise NotImplementedError("Anthropic refresh token flow not implemented")

    async def validate_token(self, access_token: str) -> bool:
        """
        Validate Anthropic access token.

        Args:
            access_token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.VALIDATE_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                return response.status_code == 200

        except Exception as e:
            logger.warning(f"Failed to validate Anthropic token: {e}")
            return False


class OAuthAuthManager:
    """
    Manages OAuth authentication lifecycle.

    Responsibilities:
    - Manage OAuth providers
    - Store and retrieve OAuth tokens
    - Handle token refresh automatically
    - Track token expiration

    Business Purpose: Central management of OAuth tokens with automatic
    refresh and expiration handling.

    Example:
        manager = OAuthAuthManager()
        url = await manager.get_authorization_url("google", scopes)
        token = await manager.exchange_code("google", auth_code)
        valid = await manager.validate_token("google", token.access_token)
    """

    def __init__(self, credential_store=None):
        """
        Initialize OAuth auth manager.

        Args:
            credential_store: CredentialStore instance (optional)
        """
        from myragdb.llm.auth_config import CredentialStore

        self.credential_store = credential_store or CredentialStore()
        self.providers: Dict[str, OAuthProviderBase] = {}

    def register_provider(
        self,
        provider_name: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> None:
        """
        Register an OAuth provider.

        Args:
            provider_name: Name of provider (google, openai, anthropic)
            client_id: OAuth application client ID
            client_secret: OAuth application client secret
            redirect_uri: OAuth redirect URI
        """
        if provider_name.lower() == "google":
            self.providers[provider_name] = GoogleOAuthProvider(
                client_id, client_secret, redirect_uri
            )
        elif provider_name.lower() == "openai":
            self.providers[provider_name] = OpenAIOAuthProvider(
                client_id, client_secret, redirect_uri
            )
        elif provider_name.lower() == "anthropic":
            self.providers[provider_name] = AnthropicOAuthProvider(
                client_id, client_secret, redirect_uri
            )
        else:
            raise ValueError(f"Unknown OAuth provider: {provider_name}")

        logger.info(f"Registered OAuth provider: {provider_name}")

    async def get_authorization_url(
        self,
        provider_name: str,
        scopes: list,
        state: str = ""
    ) -> str:
        """
        Get authorization URL for user to visit.

        Args:
            provider_name: Provider to authorize with
            scopes: OAuth scopes to request
            state: CSRF protection state

        Returns:
            Authorization URL
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider not registered: {provider_name}")

        return await provider.get_authorization_url(scopes, state)

    async def exchange_code(
        self,
        provider_name: str,
        authorization_code: str
    ) -> OAuthToken:
        """
        Exchange authorization code for access token.

        Args:
            provider_name: Provider to exchange with
            authorization_code: Authorization code from callback

        Returns:
            OAuthToken with access_token and expiration info
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider not registered: {provider_name}")

        token = await provider.exchange_code_for_token(authorization_code)

        # Store token
        self.credential_store.store_credential(
            provider=provider_name,
            auth_method="oauth",
            credentials={
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "expires_at": token.expires_at,
                "token_type": token.token_type,
            }
        )

        return token

    async def get_valid_token(self, provider_name: str) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.

        Args:
            provider_name: Provider to get token for

        Returns:
            Valid access token or None if not found/expired
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider not registered: {provider_name}")

        # Retrieve stored token
        credentials = self.credential_store.retrieve_credential(
            provider=provider_name,
            auth_method="oauth"
        )

        if not credentials:
            return None

        token = OAuthToken(
            access_token=credentials.get("access_token"),
            expires_at=credentials.get("expires_at"),
            refresh_token=credentials.get("refresh_token"),
            token_type=credentials.get("token_type", "Bearer")
        )

        # Check if token is expired or expiring soon
        if token.is_expiring_soon():
            if token.refresh_token:
                try:
                    new_token = await provider.refresh_access_token(token.refresh_token)

                    # Update stored token
                    self.credential_store.store_credential(
                        provider=provider_name,
                        auth_method="oauth",
                        credentials={
                            "access_token": new_token.access_token,
                            "refresh_token": new_token.refresh_token,
                            "expires_at": new_token.expires_at,
                            "token_type": new_token.token_type,
                        }
                    )

                    return new_token.access_token

                except Exception as e:
                    logger.error(f"Failed to refresh token for {provider_name}: {e}")
                    return None
            else:
                logger.warning(f"Token expired and no refresh token available for {provider_name}")
                return None

        return token.access_token

    async def validate_token(self, provider_name: str, access_token: str) -> bool:
        """
        Validate that access token is still valid.

        Args:
            provider_name: Provider that issued token
            access_token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider not registered: {provider_name}")

        return await provider.validate_token(access_token)

    def delete_token(self, provider_name: str) -> None:
        """
        Delete/revoke stored OAuth token.

        Args:
            provider_name: Provider to delete token for
        """
        self.credential_store.delete_credential(
            provider=provider_name,
            auth_method="oauth"
        )
        logger.info(f"OAuth token deleted for provider: {provider_name}")
