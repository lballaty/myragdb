# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/providers/gemini_provider.py
# Description: Google Gemini API provider implementation
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import os
from typing import Any, AsyncIterator, Dict, List, Optional

from myragdb.llm.providers.base_provider import CloudLLMProvider, ModelInfo


class GeminiProvider(CloudLLMProvider):
    """
    Google Gemini API provider.

    Business Purpose: Enable seamless use of Google's Gemini models
    through unified CloudLLMProvider interface.

    Supports:
    - API key authentication
    - Multiple Gemini models (Pro, Pro Vision, etc)
    - Streaming responses
    - Context windows up to 32k+ tokens

    Example:
        provider = GeminiProvider(api_key="your-api-key")
        models = await provider.list_models()
        response = await provider.generate("What is RAG?", "gemini-pro")

    Implementation Note: Full implementation requires google-generativeai library
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
        """
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        # Lazy import - only import if actually used
        self._client = None

    @property
    def client(self):
        """Lazy-load Gemini client"""
        if self._client is None:
            try:
                import google.generativeai as genai
                if self.api_key:
                    genai.configure(api_key=self.api_key)
                self._client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai not installed. "
                    "Install with: pip install google-generativeai"
                )
        return self._client

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate Gemini API key.

        Args:
            credentials: Should contain "api_key" field

        Returns:
            True if key is valid and API is reachable
        """
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return False

            # Try to list models (will fail if key invalid)
            genai = self.client
            list(genai.list_models())
            return True
        except Exception as e:
            print(f"Gemini validation failed: {e}")
            return False

    async def list_models(self) -> List[ModelInfo]:
        """
        Get available Gemini models.

        Returns:
            List of available ModelInfo objects
        """
        try:
            genai = self.client
            models = []
            for model in genai.list_models():
                if "gemini" in model.name.lower():
                    models.append(ModelInfo(
                        id=model.name.split("/")[-1],
                        name=model.display_name,
                        provider="gemini",
                        max_tokens=model.output_token_limit or 2048,
                        context_window=32000,
                        supports_vision="vision" in model.name.lower()
                    ))
            return models
        except Exception as e:
            print(f"Error listing Gemini models: {e}")
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
        Generate response using Gemini.

        Args:
            prompt: Input prompt
            model_id: Model ID (e.g., "gemini-pro")
            max_tokens: Maximum tokens to generate
            temperature: Temperature for randomness
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response

        Raises:
            Exception if generation fails
        """
        try:
            genai = self.client
            model = genai.GenerativeModel(model_id)
            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {e}")

    async def stream(
        self,
        prompt: str,
        model_id: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream response tokens from Gemini.

        Note: google-generativeai SDK is synchronous, so this
        yields text chunks as they arrive.

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
            genai = self.client
            model = genai.GenerativeModel(model_id)
            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }

            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise RuntimeError(f"Gemini streaming failed: {e}")

    async def get_remaining_quota(self) -> Optional[int]:
        """
        Get remaining API quota.

        Note: Gemini doesn't expose quota directly through API
        """
        return None
