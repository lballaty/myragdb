# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/auth/api_key_auth.py
# Description: API key validation and secure storage for cloud LLM providers
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

"""
API Key Authentication

Handles validation and secure storage of API keys for cloud providers:
- Google Gemini
- OpenAI ChatGPT
- Anthropic Claude

Uses cryptographic encryption (Fernet) for secure key storage.
"""

import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported cloud LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ApiKeyValidationResult:
    """Result of API key validation"""
    is_valid: bool
    provider: ProviderType
    message: str
    remaining_quota: Optional[int] = None
    error_code: Optional[str] = None


class ApiKeyValidator:
    """
    Validates API keys for cloud LLM providers.

    Each provider requires a test API call to validate the key:
    - Gemini: models.list() API call
    - OpenAI: models.list() API call
    - Anthropic: count_tokens() API call (minimal usage)

    Business Purpose: Ensures credentials are valid before storing them,
    providing immediate feedback to users about authentication issues.

    Example:
        validator = ApiKeyValidator()
        result = await validator.validate_gemini_key("your-api-key")
        if result.is_valid:
            print("Gemini API key is valid!")
        else:
            print(f"Validation failed: {result.message}")
    """

    async def validate_gemini_key(self, api_key: str) -> ApiKeyValidationResult:
        """
        Validate Google Gemini API key.

        Makes a minimal API call (models.list) to verify key validity.

        Args:
            api_key: Google Gemini API key to validate

        Returns:
            ApiKeyValidationResult with validation status and details
        """
        try:
            # Import here to avoid circular dependencies
            import google.generativeai as genai

            genai.configure(api_key=api_key)

            # Test with minimal API call
            models = genai.list_models()
            available_models = [m for m in models if 'gemini' in m.name.lower()]

            if available_models:
                logger.info(f"Gemini API key validated successfully. Found {len(available_models)} available models.")
                return ApiKeyValidationResult(
                    is_valid=True,
                    provider=ProviderType.GEMINI,
                    message=f"Valid Gemini API key. {len(available_models)} models available.",
                    remaining_quota=None
                )
            else:
                return ApiKeyValidationResult(
                    is_valid=False,
                    provider=ProviderType.GEMINI,
                    message="Valid API key but no Gemini models available in this region",
                    error_code="NO_MODELS_AVAILABLE"
                )

        except Exception as e:
            error_message = str(e)
            logger.warning(f"Gemini API key validation failed: {error_message}")

            error_code = "INVALID_KEY"
            if "invalid" in error_message.lower():
                error_code = "INVALID_KEY"
            elif "quota" in error_message.lower():
                error_code = "QUOTA_EXCEEDED"
            elif "permission" in error_message.lower():
                error_code = "PERMISSION_DENIED"

            return ApiKeyValidationResult(
                is_valid=False,
                provider=ProviderType.GEMINI,
                message=f"Gemini validation failed: {error_message}",
                error_code=error_code
            )

    async def validate_openai_key(self, api_key: str) -> ApiKeyValidationResult:
        """
        Validate OpenAI API key.

        Makes a minimal API call (models.list) to verify key validity.

        Args:
            api_key: OpenAI API key to validate

        Returns:
            ApiKeyValidationResult with validation status and details
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            # Test with minimal API call
            models = client.models.list()
            gpt_models = [m for m in models.data if 'gpt' in m.id.lower()]

            if gpt_models:
                logger.info(f"OpenAI API key validated successfully. Found {len(gpt_models)} available GPT models.")
                return ApiKeyValidationResult(
                    is_valid=True,
                    provider=ProviderType.OPENAI,
                    message=f"Valid OpenAI API key. {len(gpt_models)} GPT models available.",
                    remaining_quota=None
                )
            else:
                return ApiKeyValidationResult(
                    is_valid=False,
                    provider=ProviderType.OPENAI,
                    message="Valid API key but no GPT models available",
                    error_code="NO_MODELS_AVAILABLE"
                )

        except Exception as e:
            error_message = str(e)
            logger.warning(f"OpenAI API key validation failed: {error_message}")

            error_code = "INVALID_KEY"
            if "invalid" in error_message.lower() or "401" in error_message:
                error_code = "INVALID_KEY"
            elif "quota" in error_message.lower() or "429" in error_message:
                error_code = "QUOTA_EXCEEDED"
            elif "permission" in error_message.lower() or "403" in error_message:
                error_code = "PERMISSION_DENIED"

            return ApiKeyValidationResult(
                is_valid=False,
                provider=ProviderType.OPENAI,
                message=f"OpenAI validation failed: {error_message}",
                error_code=error_code
            )

    async def validate_anthropic_key(self, api_key: str) -> ApiKeyValidationResult:
        """
        Validate Anthropic Claude API key.

        Makes a minimal API call (count_tokens) to verify key validity.
        This uses minimal quota while confirming authentication.

        Args:
            api_key: Anthropic API key to validate

        Returns:
            ApiKeyValidationResult with validation status and details
        """
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)

            # Test with minimal API call - count tokens uses no tokens
            token_count = client.beta.messages.count_tokens(
                model="claude-3-opus-20240229",
                messages=[{"role": "user", "content": "test"}],
                betas=["interleave-thinking-and-responding-20250514"],
            )

            logger.info(f"Anthropic API key validated successfully.")
            return ApiKeyValidationResult(
                is_valid=True,
                provider=ProviderType.ANTHROPIC,
                message="Valid Anthropic API key. Claude models available.",
                remaining_quota=None
            )

        except Exception as e:
            error_message = str(e)
            logger.warning(f"Anthropic API key validation failed: {error_message}")

            error_code = "INVALID_KEY"
            if "invalid" in error_message.lower() or "401" in error_message:
                error_code = "INVALID_KEY"
            elif "quota" in error_message.lower() or "429" in error_message:
                error_code = "QUOTA_EXCEEDED"
            elif "permission" in error_message.lower() or "403" in error_message:
                error_code = "PERMISSION_DENIED"

            return ApiKeyValidationResult(
                is_valid=False,
                provider=ProviderType.ANTHROPIC,
                message=f"Anthropic validation failed: {error_message}",
                error_code=error_code
            )

    async def validate_key(self, provider: ProviderType, api_key: str) -> ApiKeyValidationResult:
        """
        Validate API key for any supported provider.

        Routes to provider-specific validation method.

        Args:
            provider: Which provider to validate for
            api_key: API key to validate

        Returns:
            ApiKeyValidationResult with validation status
        """
        if provider == ProviderType.GEMINI:
            return await self.validate_gemini_key(api_key)
        elif provider == ProviderType.OPENAI:
            return await self.validate_openai_key(api_key)
        elif provider == ProviderType.ANTHROPIC:
            return await self.validate_anthropic_key(api_key)
        else:
            return ApiKeyValidationResult(
                is_valid=False,
                provider=provider,
                message=f"Unknown provider: {provider}",
                error_code="UNKNOWN_PROVIDER"
            )


class ApiKeyAuthManager:
    """
    Manages API key authentication lifecycle.

    Responsibilities:
    - Store API keys securely (encrypted with Fernet)
    - Retrieve API keys for use
    - Delete/revoke stored API keys
    - Track last used timestamps

    Business Purpose: Central management of API key credentials with
    secure encryption at rest.

    Example:
        manager = ApiKeyAuthManager()
        manager.store_api_key(ProviderType.GEMINI, "sk-abc123")
        key = manager.retrieve_api_key(ProviderType.GEMINI)
        manager.delete_api_key(ProviderType.GEMINI)
    """

    def __init__(self, credential_store=None):
        """
        Initialize API key auth manager.

        Args:
            credential_store: CredentialStore instance (optional, uses default if None)
        """
        from myragdb.llm.auth_config import CredentialStore

        self.credential_store = credential_store or CredentialStore()
        self.validator = ApiKeyValidator()

    async def validate_and_store(
        self,
        provider: ProviderType,
        api_key: str
    ) -> tuple[bool, str]:
        """
        Validate API key and store it if valid.

        Args:
            provider: Provider type (gemini, openai, anthropic)
            api_key: API key to validate and store

        Returns:
            Tuple of (success: bool, message: str)
        """
        validation_result = await self.validator.validate_key(provider, api_key)

        if validation_result.is_valid:
            self.store_api_key(provider, api_key)
            return True, f"API key validated and stored for {provider.value}"
        else:
            return False, validation_result.message

    def store_api_key(self, provider: ProviderType, api_key: str) -> None:
        """
        Store API key securely.

        Args:
            provider: Provider type
            api_key: API key to store (will be encrypted)
        """
        self.credential_store.store_credential(
            provider=provider.value,
            auth_method="api_key",
            credentials={"api_key": api_key}
        )
        logger.info(f"API key stored securely for provider: {provider.value}")

    def retrieve_api_key(self, provider: ProviderType) -> Optional[str]:
        """
        Retrieve stored API key.

        Args:
            provider: Provider type to retrieve key for

        Returns:
            Decrypted API key or None if not found
        """
        credentials = self.credential_store.retrieve_credential(
            provider=provider.value,
            auth_method="api_key"
        )

        if credentials and isinstance(credentials, dict):
            return credentials.get("api_key")
        return None

    def delete_api_key(self, provider: ProviderType) -> None:
        """
        Delete/revoke stored API key.

        Args:
            provider: Provider type to delete key for
        """
        self.credential_store.delete_credential(
            provider=provider.value,
            auth_method="api_key"
        )
        logger.info(f"API key deleted for provider: {provider.value}")

    def has_stored_key(self, provider: ProviderType) -> bool:
        """
        Check if API key is stored for a provider.

        Args:
            provider: Provider type to check

        Returns:
            True if key is stored, False otherwise
        """
        return self.retrieve_api_key(provider) is not None
