# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/providers/provider_registry.py
# Description: Registry and factory for LLM provider instances
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Any, Dict, Optional

from myragdb.llm.providers.base_provider import CloudLLMProvider


class ProviderRegistry:
    """
    Central registry and factory for LLM providers.

    Business Purpose: Enable dynamic provider instantiation and discovery
    without hardcoding provider knowledge in other parts of system.

    Supports:
    - Local LLM providers (via wrapper)
    - Cloud providers (Gemini, ChatGPT, Claude)
    - Easy addition of new providers

    Example:
        registry = ProviderRegistry()

        # Get provider instance
        provider = registry.get_provider("gemini")

        # List all registered providers
        providers = registry.list_providers()
    """

    # Map of provider names to their class paths (for lazy loading)
    PROVIDER_CLASSES = {
        "gemini": "myragdb.llm.providers.gemini_provider:GeminiProvider",
        "chatgpt": "myragdb.llm.providers.chatgpt_provider:ChatGPTProvider",
        "claude": "myragdb.llm.providers.claude_provider:ClaudeProvider",
    }

    def __init__(self):
        """Initialize provider registry"""
        self._providers: Dict[str, CloudLLMProvider] = {}
        self._provider_cache: Dict[str, Any] = {}

    def register_provider(self, name: str, provider: CloudLLMProvider) -> None:
        """
        Register a provider instance.

        Args:
            name: Provider name (e.g., "gemini")
            provider: CloudLLMProvider instance
        """
        self._providers[name] = provider

    def get_provider(self, name: str) -> Optional[CloudLLMProvider]:
        """
        Get a provider instance by name.

        Args:
            name: Provider name (e.g., "gemini", "chatgpt", "claude")

        Returns:
            CloudLLMProvider instance, or None if not found

        Note: Attempts to load provider class if not already instantiated
        """
        # Check registered providers first
        if name in self._providers:
            return self._providers[name]

        # Check cache
        if name in self._provider_cache:
            return self._provider_cache[name]

        # Try to lazy-load provider class
        if name in self.PROVIDER_CLASSES:
            try:
                provider = self._load_provider_class(name)
                self._provider_cache[name] = provider
                return provider
            except ImportError:
                # Provider not installed - return None
                return None

        return None

    def list_providers(self) -> list:
        """
        List all available provider names.

        Returns:
            List of provider names that could be loaded
        """
        return list(self.PROVIDER_CLASSES.keys())

    def list_registered_providers(self) -> Dict[str, CloudLLMProvider]:
        """
        List all currently registered provider instances.

        Returns:
            Dict mapping provider name to instance
        """
        return dict(self._providers)

    def _load_provider_class(self, name: str) -> CloudLLMProvider:
        """
        Dynamically load provider class and instantiate it.

        Args:
            name: Provider name

        Returns:
            CloudLLMProvider instance

        Raises:
            ImportError if provider class cannot be loaded
        """
        class_path = self.PROVIDER_CLASSES[name]
        module_path, class_name = class_path.rsplit(":", 1)

        # Dynamic import
        module = __import__(module_path, fromlist=[class_name])
        provider_class = getattr(module, class_name)

        # Instantiate with no arguments (providers handle auth internally)
        return provider_class()

    def clear_cache(self) -> None:
        """Clear the provider instance cache"""
        self._provider_cache.clear()
