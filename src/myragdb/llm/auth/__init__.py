# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/auth/__init__.py
# Description: Cloud LLM authentication module - API key, OAuth, and CLI device code flows
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

"""
MyRAGDB Cloud LLM Authentication Module

Provides three authentication methods for cloud LLM providers:
1. API Key authentication - Direct API key validation and storage
2. OAuth authentication - OAuth 2.0 subscription flows
3. CLI Device Code authentication - Device code flow for CLI environments
"""

from .api_key_auth import ApiKeyValidator, ApiKeyAuthManager
from .oauth_auth import OAuthProvider, OAuthAuthManager, GoogleOAuthProvider, OpenAIOAuthProvider, AnthropicOAuthProvider
from .cli_auth import CLIAuthManager, DeviceCodeResponse

__all__ = [
    'ApiKeyValidator',
    'ApiKeyAuthManager',
    'OAuthProvider',
    'OAuthAuthManager',
    'GoogleOAuthProvider',
    'OpenAIOAuthProvider',
    'AnthropicOAuthProvider',
    'CLIAuthManager',
    'DeviceCodeResponse',
]
