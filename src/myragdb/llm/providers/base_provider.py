# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/providers/base_provider.py
# Description: Abstract base class for cloud LLM providers
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Information about an available model"""
    id: str
    name: str
    provider: str
    max_tokens: int
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    supports_vision: bool = False
    supports_function_calls: bool = False
    context_window: int = 4000


class CloudLLMProvider(ABC):
    """
    Abstract base class for cloud LLM providers.

    Business Purpose: Define unified interface for all cloud LLM providers
    so that application code doesn't need to know provider-specific details.

    Implementations should override:
    - validate_credentials(): Check API key/token validity
    - list_models(): Return available models
    - generate(): Synchronous text generation
    - stream(): Streaming text generation
    - get_remaining_quota(): Return usage info if available

    Example:
        # This works the same for Gemini, ChatGPT, or Claude
        provider = ProviderRegistry.get_provider("gemini")
        models = await provider.list_models()
        response = await provider.generate(prompt, model_id)
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize provider with optional API key"""
        self.api_key = api_key

    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate that credentials are correct and API is accessible.

        Business Purpose: Before switching to this provider, verify the user's
        credentials are valid and the provider is reachable.

        Args:
            credentials: Provider-specific credential dict
                Example: {"api_key": "sk-..."}
                Example: {"access_token": "...", "refresh_token": "..."}

        Returns:
            True if credentials valid and provider accessible, False otherwise

        Note: Should NOT raise exceptions, just return False if invalid
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """
        Get list of available models for this provider.

        Business Purpose: Show user which models they can use with this provider.

        Returns:
            List of ModelInfo objects available to the authenticated user

        Raises:
            Exception if unable to fetch model list
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model_id: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text response synchronously.

        Business Purpose: Call the provider's API to generate text based on prompt.

        Args:
            prompt: Input prompt text
            model_id: Which model to use (e.g., "gemini-pro")
            max_tokens: Maximum tokens to generate
            temperature: Temperature for randomness (0.0-2.0)
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response

        Raises:
            Exception if generation fails
        """
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        model_id: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate text response as stream of tokens.

        Business Purpose: Enable real-time token streaming for better UX.

        Args:
            prompt: Input prompt text
            model_id: Which model to use
            max_tokens: Maximum tokens to generate
            temperature: Temperature for randomness
            **kwargs: Provider-specific parameters

        Yields:
            Token strings as they become available

        Raises:
            Exception if streaming fails
        """
        pass

    @abstractmethod
    async def get_remaining_quota(self) -> Optional[int]:
        """
        Get remaining quota for API usage.

        Business Purpose: Show user how much quota remains, enable fallback
        to local LLMs if quota exhausted.

        Returns:
            Remaining tokens/requests, or None if not available

        Note: Not all providers support this - return None if unavailable
        """
        pass
