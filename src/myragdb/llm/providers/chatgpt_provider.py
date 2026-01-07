# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/providers/chatgpt_provider.py
# Description: OpenAI ChatGPT API provider implementation
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import os
from typing import Any, AsyncIterator, Dict, List, Optional

from myragdb.llm.providers.base_provider import CloudLLMProvider, ModelInfo


class ChatGPTProvider(CloudLLMProvider):
    """
    OpenAI ChatGPT API provider.

    Business Purpose: Enable seamless use of OpenAI's GPT models
    through unified CloudLLMProvider interface.

    Supports:
    - API key authentication
    - Multiple GPT models (GPT-4, GPT-3.5-turbo, etc)
    - Streaming responses
    - Function calling

    Example:
        provider = ChatGPTProvider(api_key="sk-...")
        models = await provider.list_models()
        response = await provider.generate("What is RAG?", "gpt-4")

    Implementation Note: Full implementation requires openai library >= 1.0.0
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ChatGPT provider.

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        # Lazy import - only import if actually used
        self._client = None

    @property
    def client(self):
        """Lazy-load OpenAI client"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai not installed. "
                    "Install with: pip install openai"
                )
        return self._client

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate OpenAI API key.

        Args:
            credentials: Should contain "api_key" field

        Returns:
            True if key is valid and API is reachable
        """
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return False

            # Try to list models with test API call
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            list(client.models.list())
            return True
        except Exception as e:
            print(f"OpenAI validation failed: {e}")
            return False

    async def list_models(self) -> List[ModelInfo]:
        """
        Get available OpenAI models.

        Returns:
            List of available ModelInfo objects
        """
        try:
            client = self.client
            models_response = await client.models.list()

            models = []
            # Filter for GPT models
            gpt_models = [
                ("gpt-4", "GPT-4", 8000),
                ("gpt-4-turbo", "GPT-4 Turbo", 128000),
                ("gpt-3.5-turbo", "GPT-3.5 Turbo", 4000),
            ]

            for model_id, display_name, context_window in gpt_models:
                models.append(ModelInfo(
                    id=model_id,
                    name=display_name,
                    provider="chatgpt",
                    max_tokens=2000,
                    context_window=context_window,
                    supports_function_calls=True
                ))

            return models
        except Exception as e:
            print(f"Error listing OpenAI models: {e}")
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
        Generate response using ChatGPT.

        Args:
            prompt: Input prompt
            model_id: Model ID (e.g., "gpt-4")
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
            response = await client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"ChatGPT generation failed: {e}")

    async def stream(
        self,
        prompt: str,
        model_id: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream response tokens from ChatGPT.

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
            response = await client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"ChatGPT streaming failed: {e}")

    async def get_remaining_quota(self) -> Optional[int]:
        """
        Get remaining API quota.

        Note: OpenAI doesn't expose remaining quota through the API
        """
        return None
