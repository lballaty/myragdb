# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/auth/cli_auth.py
# Description: Device code authentication flow for CLI environments
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

"""
CLI Device Code Authentication

Implements OAuth 2.0 Device Authorization Grant (RFC 8628) for CLI environments.

This flow is ideal for CLI applications where users cannot easily open browsers:
1. Client requests device code from provider
2. User visits provider's URL and enters user code
3. Client polls for token while user authorizes
4. Token returned once user completes authorization

Supports exponential backoff polling with configurable intervals.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum
import asyncio
import time
import logging

logger = logging.getLogger(__name__)


class DeviceCodeProvider(str, Enum):
    """Providers supporting device code flow"""
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class DeviceCodeResponse:
    """Response from device code request"""
    device_code: str
    user_code: str
    verification_url: str
    expires_in: int  # Seconds until codes expire
    interval: int  # Polling interval in seconds (minimum)
    message: str  # User-friendly message with instructions


@dataclass
class DeviceCodeToken:
    """Token obtained via device code flow"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None


class CLIAuthManager:
    """
    Manages device code authentication for CLI environments.

    Device Code Flow Process:
    1. Call request_device_code() to get user_code and verification_url
    2. User visits verification_url and enters user_code
    3. Call poll_for_token() to wait for authorization
    4. Token returned once user completes authorization in browser

    Business Purpose: Enable CLI users to authenticate with cloud providers
    without being able to handle OAuth redirects.

    Example:
        manager = CLIAuthManager()
        device_code = await manager.request_device_code(DeviceCodeProvider.GOOGLE)
        print(f"Visit {device_code.verification_url}")
        print(f"Enter code: {device_code.user_code}")

        token = await manager.poll_for_token(
            DeviceCodeProvider.GOOGLE,
            device_code
        )
        print(f"Authenticated! Token: {token.access_token}")
    """

    def __init__(self, credential_store=None):
        """
        Initialize CLI auth manager.

        Args:
            credential_store: CredentialStore instance (optional)
        """
        from myragdb.llm.auth_config import CredentialStore

        self.credential_store = credential_store or CredentialStore()

    async def request_device_code(
        self,
        provider: DeviceCodeProvider
    ) -> DeviceCodeResponse:
        """
        Request device code from provider.

        Args:
            provider: Provider to request code from

        Returns:
            DeviceCodeResponse with user code and verification URL
        """
        if provider == DeviceCodeProvider.GOOGLE:
            return await self._request_google_device_code()
        elif provider == DeviceCodeProvider.OPENAI:
            return await self._request_openai_device_code()
        elif provider == DeviceCodeProvider.ANTHROPIC:
            return await self._request_anthropic_device_code()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _request_google_device_code(self) -> DeviceCodeResponse:
        """Request device code from Google"""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/device/code",
                    data={
                        "client_id": "YOUR_GOOGLE_CLIENT_ID",  # Will be loaded from config
                        "scope": "https://www.googleapis.com/auth/generative-language",
                    }
                )
                response.raise_for_status()
                data = response.json()

                return DeviceCodeResponse(
                    device_code=data["device_code"],
                    user_code=data["user_code"],
                    verification_url=data["verification_url"],
                    expires_in=data["expires_in"],
                    interval=data.get("interval", 5),
                    message=(
                        f"Visit: {data['verification_url']}\n"
                        f"Enter code: {data['user_code']}"
                    )
                )

        except Exception as e:
            logger.error(f"Failed to request Google device code: {e}")
            raise

    async def _request_openai_device_code(self) -> DeviceCodeResponse:
        """Request device code from OpenAI"""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/auth/device",
                    headers={
                        "Content-Type": "application/json",
                    },
                    json={
                        "client_id": "YOUR_OPENAI_CLIENT_ID",  # Will be loaded from config
                    }
                )
                response.raise_for_status()
                data = response.json()

                return DeviceCodeResponse(
                    device_code=data["device_code"],
                    user_code=data["user_code"],
                    verification_url=data["verification_uri"],
                    expires_in=data["expires_in"],
                    interval=data.get("interval", 5),
                    message=(
                        f"Visit: {data['verification_uri']}\n"
                        f"Enter code: {data['user_code']}"
                    )
                )

        except Exception as e:
            logger.error(f"Failed to request OpenAI device code: {e}")
            raise

    async def _request_anthropic_device_code(self) -> DeviceCodeResponse:
        """Request device code from Anthropic"""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://auth.anthropic.com/device",
                    headers={
                        "Content-Type": "application/json",
                    },
                    json={
                        "client_id": "YOUR_ANTHROPIC_CLIENT_ID",  # Will be loaded from config
                    }
                )
                response.raise_for_status()
                data = response.json()

                return DeviceCodeResponse(
                    device_code=data["device_code"],
                    user_code=data["user_code"],
                    verification_url=data["verification_url"],
                    expires_in=data["expires_in"],
                    interval=data.get("interval", 5),
                    message=(
                        f"Visit: {data['verification_url']}\n"
                        f"Enter code: {data['user_code']}"
                    )
                )

        except Exception as e:
            logger.error(f"Failed to request Anthropic device code: {e}")
            raise

    async def poll_for_token(
        self,
        provider: DeviceCodeProvider,
        device_code_response: DeviceCodeResponse,
        timeout_seconds: int = 900  # 15 minutes
    ) -> Optional[DeviceCodeToken]:
        """
        Poll for token while user authorizes.

        Implements exponential backoff:
        - Start with interval from device_code_response
        - Increase by 50% each poll (up to max of 120 seconds)
        - Continue until token received or timeout

        Args:
            provider: Provider to poll
            device_code_response: Device code response from request
            timeout_seconds: Max time to wait (default 15 minutes)

        Returns:
            DeviceCodeToken if authorized, None if timeout/error
        """
        if provider == DeviceCodeProvider.GOOGLE:
            return await self._poll_google_token(device_code_response, timeout_seconds)
        elif provider == DeviceCodeProvider.OPENAI:
            return await self._poll_openai_token(device_code_response, timeout_seconds)
        elif provider == DeviceCodeProvider.ANTHROPIC:
            return await self._poll_anthropic_token(device_code_response, timeout_seconds)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _poll_google_token(
        self,
        device_code_response: DeviceCodeResponse,
        timeout_seconds: int
    ) -> Optional[DeviceCodeToken]:
        """Poll Google for token with exponential backoff"""
        import httpx

        start_time = time.time()
        current_interval = device_code_response.interval

        while time.time() - start_time < timeout_seconds:
            try:
                await asyncio.sleep(current_interval)

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": "YOUR_GOOGLE_CLIENT_ID",
                            "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
                            "device_code": device_code_response.device_code,
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        logger.info("Google device code authorization successful")

                        return DeviceCodeToken(
                            access_token=data["access_token"],
                            token_type=data.get("token_type", "Bearer"),
                            expires_in=data.get("expires_in"),
                            refresh_token=data.get("refresh_token"),
                        )

                    elif response.status_code == 428:
                        # Still waiting for user authorization
                        logger.debug("Waiting for user authorization...")
                        # Increase interval with exponential backoff (50% increase, max 120s)
                        current_interval = min(int(current_interval * 1.5), 120)
                        continue

                    elif response.status_code == 400:
                        data = response.json()
                        error = data.get("error")

                        if error == "access_denied":
                            logger.error("User denied authorization")
                            return None
                        elif error == "expired_token":
                            logger.error("Device code expired")
                            return None
                        else:
                            logger.error(f"Authorization error: {error}")
                            continue

                    else:
                        logger.error(f"Unexpected response: {response.status_code}")
                        current_interval = min(int(current_interval * 1.5), 120)
                        continue

            except Exception as e:
                logger.error(f"Error polling Google token: {e}")
                current_interval = min(int(current_interval * 1.5), 120)
                continue

        logger.error("Device code polling timeout - user did not authorize")
        return None

    async def _poll_openai_token(
        self,
        device_code_response: DeviceCodeResponse,
        timeout_seconds: int
    ) -> Optional[DeviceCodeToken]:
        """Poll OpenAI for token with exponential backoff"""
        import httpx

        start_time = time.time()
        current_interval = device_code_response.interval

        while time.time() - start_time < timeout_seconds:
            try:
                await asyncio.sleep(current_interval)

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.openai.com/v1/auth/token",
                        headers={"Content-Type": "application/json"},
                        json={
                            "client_id": "YOUR_OPENAI_CLIENT_ID",
                            "client_secret": "YOUR_OPENAI_CLIENT_SECRET",
                            "device_code": device_code_response.device_code,
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        logger.info("OpenAI device code authorization successful")

                        return DeviceCodeToken(
                            access_token=data["access_token"],
                            token_type=data.get("token_type", "Bearer"),
                            expires_in=data.get("expires_in"),
                            refresh_token=data.get("refresh_token"),
                        )

                    elif response.status_code == 428:
                        # Still waiting for user authorization
                        logger.debug("Waiting for user authorization...")
                        current_interval = min(int(current_interval * 1.5), 120)
                        continue

                    elif response.status_code == 400:
                        data = response.json()
                        error = data.get("error")

                        if error == "access_denied":
                            logger.error("User denied authorization")
                            return None
                        elif error == "expired_token":
                            logger.error("Device code expired")
                            return None
                        else:
                            logger.error(f"Authorization error: {error}")
                            continue

                    else:
                        logger.error(f"Unexpected response: {response.status_code}")
                        current_interval = min(int(current_interval * 1.5), 120)
                        continue

            except Exception as e:
                logger.error(f"Error polling OpenAI token: {e}")
                current_interval = min(int(current_interval * 1.5), 120)
                continue

        logger.error("Device code polling timeout - user did not authorize")
        return None

    async def _poll_anthropic_token(
        self,
        device_code_response: DeviceCodeResponse,
        timeout_seconds: int
    ) -> Optional[DeviceCodeToken]:
        """Poll Anthropic for token with exponential backoff"""
        import httpx

        start_time = time.time()
        current_interval = device_code_response.interval

        while time.time() - start_time < timeout_seconds:
            try:
                await asyncio.sleep(current_interval)

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://auth.anthropic.com/token",
                        headers={"Content-Type": "application/json"},
                        json={
                            "client_id": "YOUR_ANTHROPIC_CLIENT_ID",
                            "client_secret": "YOUR_ANTHROPIC_CLIENT_SECRET",
                            "device_code": device_code_response.device_code,
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        logger.info("Anthropic device code authorization successful")

                        return DeviceCodeToken(
                            access_token=data["access_token"],
                            token_type=data.get("token_type", "Bearer"),
                            expires_in=data.get("expires_in"),
                            refresh_token=data.get("refresh_token"),
                        )

                    elif response.status_code == 428:
                        # Still waiting for user authorization
                        logger.debug("Waiting for user authorization...")
                        current_interval = min(int(current_interval * 1.5), 120)
                        continue

                    elif response.status_code == 400:
                        data = response.json()
                        error = data.get("error")

                        if error == "access_denied":
                            logger.error("User denied authorization")
                            return None
                        elif error == "expired_token":
                            logger.error("Device code expired")
                            return None
                        else:
                            logger.error(f"Authorization error: {error}")
                            continue

                    else:
                        logger.error(f"Unexpected response: {response.status_code}")
                        current_interval = min(int(current_interval * 1.5), 120)
                        continue

            except Exception as e:
                logger.error(f"Error polling Anthropic token: {e}")
                current_interval = min(int(current_interval * 1.5), 120)
                continue

        logger.error("Device code polling timeout - user did not authorize")
        return None

    def store_token(
        self,
        provider: DeviceCodeProvider,
        token: DeviceCodeToken
    ) -> None:
        """
        Store device code token securely.

        Args:
            provider: Provider that issued token
            token: Token to store
        """
        self.credential_store.store_credential(
            provider=provider.value,
            auth_method="device_code",
            credentials={
                "access_token": token.access_token,
                "token_type": token.token_type,
                "expires_in": token.expires_in,
                "refresh_token": token.refresh_token,
            }
        )
        logger.info(f"Device code token stored for provider: {provider.value}")

    def retrieve_token(self, provider: DeviceCodeProvider) -> Optional[DeviceCodeToken]:
        """
        Retrieve stored device code token.

        Args:
            provider: Provider to retrieve token for

        Returns:
            DeviceCodeToken or None if not found
        """
        credentials = self.credential_store.retrieve_credential(
            provider=provider.value,
            auth_method="device_code"
        )

        if credentials and isinstance(credentials, dict):
            return DeviceCodeToken(
                access_token=credentials.get("access_token"),
                token_type=credentials.get("token_type", "Bearer"),
                expires_in=credentials.get("expires_in"),
                refresh_token=credentials.get("refresh_token"),
            )
        return None

    def delete_token(self, provider: DeviceCodeProvider) -> None:
        """
        Delete/revoke stored device code token.

        Args:
            provider: Provider to delete token for
        """
        self.credential_store.delete_credential(
            provider=provider.value,
            auth_method="device_code"
        )
        logger.info(f"Device code token deleted for provider: {provider.value}")
