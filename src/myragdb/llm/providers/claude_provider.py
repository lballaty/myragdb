# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/providers/claude_provider.py
# Description: Anthropic Claude API provider implementation
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import os
from typing import Any, AsyncIterator, Dict, List, Optional

from myragdb.llm.providers.base_provider import CloudLLMProvider, ModelInfo


class ClaudeProvider(CloudLLMProvider):
    """
    Anthropic Claude API provider.

    Business Purpose: Enable seamless use of Anthropic's Claude models
    through unified CloudLLMProvider interface.

    Supports:
    - API key authentication
    - Multiple Claude models (Opus, Sonnet, Haiku)
    - Streaming responses
    - Extended context windows (100k+ tokens)

    Example:
        provider = ClaudeProvider(api_key="sk-ant-...")
        models = await provider.list_models()
        response = await provider.generate("What is RAG?", "claude-3-opus")

    Implementation Note: Full implementation requires anthropic library >= 0.7.0
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        # Lazy import - only import if actually used
        self._client = None

    @property
    def client(self):
        """Lazy-load Anthropic client"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate Anthropic API key.

        Args:
            credentials: Should contain "api_key" field

        Returns:
            True if key is valid and API is reachable
        """
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return False

            # Try a simple API call to validate key
            client = self.client
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return bool(response.content)
        except Exception as e:
            print(f"Anthropic validation failed: {e}")
            return False

    async def list_models(self) -> List[ModelInfo]:
        """
        Get available Claude models.

        Returns:
            List of available ModelInfo objects
        """
        try:
            # Claude models available (hardcoded as Anthropic doesn't have list endpoint)
            models = [
                ModelInfo(
                    id="claude-3-opus-20240229",
                    name="Claude 3 Opus",
                    provider="claude",
                    max_tokens=4096,
                    context_window=200000,
                    supports_function_calls=True
                ),
                ModelInfo(
                    id="claude-3-sonnet-20240229",
                    name="Claude 3 Sonnet",
                    provider="claude",
                    max_tokens=4096,
                    context_window=200000,
                    supports_function_calls=True
                ),
                ModelInfo(
                    id="claude-3-haiku-20240307",
                    name="Claude 3 Haiku",
                    provider="claude",
                    max_tokens=4096,
                    context_window=200000,
                    supports_function_calls=True
                ),
            ]
            return models
        except Exception as e:
            print(f"Error listing Claude models: {e}")
            return []

    async def generate(
        self,
        prompt: str,
        model_id: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response using Claude.

        Args:
            prompt: Input prompt
            model_id: Model ID (e.g., "claude-3-opus-20240229")
            max_tokens: Maximum tokens to generate
            temperature: Temperature for randomness
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response

        Raises:
            Exception if generation fails
        """
        try:
            client = self.client
            response = await client.messages.create(
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            # Extract text from response
            text_content = next(
                (block.text for block in response.content if hasattr(block, "text")),
                ""
            )
            return text_content
        except Exception as e:
            raise RuntimeError(f"Claude generation failed: {e}")

    async def stream(
        self,
        prompt: str,
        model_id: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream response tokens from Claude.

        Args:
            prompt: Input prompt
            model_id: Model ID
            max_tokens: Maximum tokens
            temperature: Temperature
            **kwargs: Additional parameters

        Yields:
            Token strings as they become available
        """
        try:
            client = self.client
            with client.messages.stream(
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise RuntimeError(f"Claude streaming failed: {e}")

    async def get_remaining_quota(self) -> Optional[int]:
        """
        Get remaining API quota.

        Note: Anthropic doesn't expose remaining quota through the API
        """
        return None
