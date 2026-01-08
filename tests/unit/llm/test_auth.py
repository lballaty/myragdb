# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/unit/llm/test_auth.py
# Description: Comprehensive unit tests for cloud LLM authentication
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

"""
Unit Tests for Cloud LLM Authentication

Tests all three authentication methods:
1. API Key authentication (Gemini, OpenAI, Anthropic)
2. OAuth 2.0 authentication
3. CLI device code flow

Uses mocking to avoid real API calls.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from myragdb.llm.auth.api_key_auth import (
    ApiKeyValidator,
    ApiKeyAuthManager,
    ProviderType,
    ApiKeyValidationResult,
)
from myragdb.llm.auth.oauth_auth import (
    OAuthAuthManager,
    GoogleOAuthProvider,
    OpenAIOAuthProvider,
    AnthropicOAuthProvider,
    OAuthToken,
    OAuthProvider,
)
from myragdb.llm.auth.cli_auth import (
    CLIAuthManager,
    DeviceCodeProvider,
)


# ============================================================================
# API Key Validation Tests
# ============================================================================

class TestApiKeyValidator:
    """Test API key validation for all providers"""

    @pytest.fixture
    def validator(self):
        """Create API key validator"""
        return ApiKeyValidator()

    @pytest.mark.asyncio
    async def test_validate_gemini_key_success(self, validator):
        """Test successful Gemini API key validation"""
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.list_models') as mock_list:
                # Mock successful response
                mock_model = Mock()
                mock_model.name = "gemini-pro"
                mock_list.return_value = [mock_model]

                result = await validator.validate_gemini_key("valid-key")

                assert result.is_valid is True
                assert result.provider == ProviderType.GEMINI
                assert "valid" in result.message.lower()
                mock_configure.assert_called_once_with(api_key="valid-key")

    @pytest.mark.asyncio
    async def test_validate_gemini_key_invalid(self, validator):
        """Test invalid Gemini API key"""
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.list_models') as mock_list:
                # Mock error response
                mock_list.side_effect = Exception("Invalid API Key")

                result = await validator.validate_gemini_key("invalid-key")

                assert result.is_valid is False
                assert result.provider == ProviderType.GEMINI
                assert result.error_code == "INVALID_KEY"

    @pytest.mark.asyncio
    async def test_validate_openai_key_success(self, validator):
        """Test successful OpenAI API key validation"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            # Mock models list
            mock_model = Mock()
            mock_model.id = "gpt-4"
            mock_models = Mock()
            mock_models.data = [mock_model]
            mock_client.models.list.return_value = mock_models

            result = await validator.validate_openai_key("valid-key")

            assert result.is_valid is True
            assert result.provider == ProviderType.OPENAI
            assert "valid" in result.message.lower()

    @pytest.mark.asyncio
    async def test_validate_openai_key_invalid(self, validator):
        """Test invalid OpenAI API key"""
        with patch('openai.OpenAI') as mock_openai:
            mock_openai.side_effect = Exception("Invalid authentication")

            result = await validator.validate_openai_key("invalid-key")

            assert result.is_valid is False
            assert result.provider == ProviderType.OPENAI
            assert result.error_code == "INVALID_KEY"

    @pytest.mark.asyncio
    async def test_validate_anthropic_key_success(self, validator):
        """Test successful Anthropic API key validation"""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            # Mock token count (minimal API call)
            mock_beta = Mock()
            mock_messages = Mock()
            mock_messages.count_tokens.return_value = Mock(input_tokens=5)
            mock_beta.messages = mock_messages
            mock_client.beta = mock_beta

            result = await validator.validate_anthropic_key("valid-key")

            assert result.is_valid is True
            assert result.provider == ProviderType.ANTHROPIC

    @pytest.mark.asyncio
    async def test_validate_anthropic_key_invalid(self, validator):
        """Test invalid Anthropic API key"""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_anthropic.side_effect = Exception("Invalid API key")

            result = await validator.validate_anthropic_key("invalid-key")

            assert result.is_valid is False
            assert result.provider == ProviderType.ANTHROPIC
            assert result.error_code == "INVALID_KEY"

    @pytest.mark.asyncio
    async def test_validate_key_gemini(self, validator):
        """Test validate_key routing to Gemini"""
        with patch.object(validator, 'validate_gemini_key') as mock_validate:
            mock_validate.return_value = ApiKeyValidationResult(
                is_valid=True,
                provider=ProviderType.GEMINI,
                message="Valid",
            )

            result = await validator.validate_key(ProviderType.GEMINI, "test-key")

            assert result.is_valid is True
            mock_validate.assert_called_once_with("test-key")

    @pytest.mark.asyncio
    async def test_validate_key_unknown_provider(self, validator):
        """Test validate_key with unknown provider"""
        result = await validator.validate_key("unknown", "test-key")

        assert result.is_valid is False
        assert result.error_code == "UNKNOWN_PROVIDER"


# ============================================================================
# API Key Auth Manager Tests
# ============================================================================

class TestApiKeyAuthManager:
    """Test API key authentication manager"""

    @pytest.fixture
    def mock_credential_store(self):
        """Create mock credential store"""
        return Mock()

    @pytest.fixture
    def manager(self, mock_credential_store):
        """Create API key auth manager"""
        manager = ApiKeyAuthManager(credential_store=mock_credential_store)
        manager.validator = Mock()
        return manager

    @pytest.mark.asyncio
    async def test_validate_and_store_success(self, manager):
        """Test successful validation and storage"""
        manager.validator.validate_key = AsyncMock(
            return_value=ApiKeyValidationResult(
                is_valid=True,
                provider=ProviderType.GEMINI,
                message="Valid",
            )
        )

        success, message = await manager.validate_and_store(ProviderType.GEMINI, "test-key")

        assert success is True
        assert "validated" in message.lower()
        manager.credential_store.store_credential.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_store_failure(self, manager):
        """Test failed validation"""
        manager.validator.validate_key = AsyncMock(
            return_value=ApiKeyValidationResult(
                is_valid=False,
                provider=ProviderType.GEMINI,
                message="Invalid key",
                error_code="INVALID_KEY",
            )
        )

        success, message = await manager.validate_and_store(ProviderType.GEMINI, "invalid-key")

        assert success is False
        assert "Invalid" in message
        manager.credential_store.store_credential.assert_not_called()

    def test_store_api_key(self, manager):
        """Test storing API key"""
        manager.store_api_key(ProviderType.GEMINI, "test-key")

        manager.credential_store.store_credential.assert_called_once_with(
            provider="gemini",
            auth_method="api_key",
            credentials={"api_key": "test-key"}
        )

    def test_retrieve_api_key(self, manager):
        """Test retrieving API key"""
        manager.credential_store.retrieve_credential.return_value = {"api_key": "test-key"}

        result = manager.retrieve_api_key(ProviderType.GEMINI)

        assert result == "test-key"
        manager.credential_store.retrieve_credential.assert_called_once_with(
            provider="gemini",
            auth_method="api_key"
        )

    def test_retrieve_api_key_not_found(self, manager):
        """Test retrieving non-existent API key"""
        manager.credential_store.retrieve_credential.return_value = None

        result = manager.retrieve_api_key(ProviderType.GEMINI)

        assert result is None

    def test_delete_api_key(self, manager):
        """Test deleting API key"""
        manager.delete_api_key(ProviderType.GEMINI)

        manager.credential_store.delete_credential.assert_called_once_with(
            provider="gemini",
            auth_method="api_key"
        )

    def test_has_stored_key_exists(self, manager):
        """Test checking for stored key when it exists"""
        with patch.object(manager, 'retrieve_api_key', return_value="test-key"):
            result = manager.has_stored_key(ProviderType.GEMINI)

            assert result is True

    def test_has_stored_key_not_exists(self, manager):
        """Test checking for stored key when it doesn't exist"""
        with patch.object(manager, 'retrieve_api_key', return_value=None):
            result = manager.has_stored_key(ProviderType.GEMINI)

            assert result is False


# ============================================================================
# OAuth Tests
# ============================================================================

class TestGoogleOAuthProvider:
    """Test Google OAuth provider"""

    @pytest.fixture
    def provider(self):
        """Create Google OAuth provider"""
        return GoogleOAuthProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:3000/callback"
        )

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, provider):
        """Test generating authorization URL"""
        url = await provider.get_authorization_url(
            scopes=["https://www.googleapis.com/auth/generative-language"],
            state="test-state"
        )

        assert "accounts.google.com" in url
        assert "client_id=test-client-id" in url
        assert "state=test-state" in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, provider):
        """Test exchanging code for token"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "test-access-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "test-refresh-token",
                "scope": "https://www.googleapis.com/auth/generative-language",
            }
            mock_response.raise_for_status = Mock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            token = await provider.exchange_code_for_token("test-code")

            assert token.access_token == "test-access-token"
            assert token.token_type == "Bearer"
            assert token.refresh_token == "test-refresh-token"

    @pytest.mark.asyncio
    async def test_refresh_access_token(self, provider):
        """Test refreshing access token"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "new-access-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/generative-language",
            }
            mock_response.raise_for_status = Mock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            token = await provider.refresh_access_token("test-refresh-token")

            assert token.access_token == "new-access-token"

    @pytest.mark.asyncio
    async def test_validate_token_valid(self, provider):
        """Test validating valid token"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await provider.validate_token("test-token")

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, provider):
        """Test validating invalid token"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 401

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await provider.validate_token("invalid-token")

            assert result is False


class TestOAuthToken:
    """Test OAuth token expiration tracking"""

    def test_token_not_expired(self):
        """Test token that hasn't expired"""
        import time
        future_time = time.time() + 3600
        token = OAuthToken(
            access_token="test-token",
            expires_at=future_time
        )

        assert token.is_expired() is False

    def test_token_is_expired(self):
        """Test expired token"""
        import time
        past_time = time.time() - 3600
        token = OAuthToken(
            access_token="test-token",
            expires_at=past_time
        )

        assert token.is_expired() is True

    def test_token_no_expiry(self):
        """Test token with no expiry"""
        token = OAuthToken(
            access_token="test-token",
            expires_at=None
        )

        assert token.is_expired() is False

    def test_token_expiring_soon(self):
        """Test token expiring soon"""
        import time
        soon_time = time.time() + 200  # Less than default 300s threshold
        token = OAuthToken(
            access_token="test-token",
            expires_at=soon_time
        )

        assert token.is_expiring_soon() is True

    def test_token_not_expiring_soon(self):
        """Test token not expiring soon"""
        import time
        later_time = time.time() + 3600
        token = OAuthToken(
            access_token="test-token",
            expires_at=later_time
        )

        assert token.is_expiring_soon() is False


class TestOAuthAuthManager:
    """Test OAuth authentication manager"""

    @pytest.fixture
    def mock_credential_store(self):
        """Create mock credential store"""
        return Mock()

    @pytest.fixture
    def manager(self, mock_credential_store):
        """Create OAuth auth manager"""
        return OAuthAuthManager(credential_store=mock_credential_store)

    def test_register_provider_google(self, manager):
        """Test registering Google provider"""
        manager.register_provider(
            "google",
            "client-id",
            "client-secret",
            "http://localhost/callback"
        )

        assert "google" in manager.providers
        assert isinstance(manager.providers["google"], GoogleOAuthProvider)

    def test_register_provider_openai(self, manager):
        """Test registering OpenAI provider"""
        manager.register_provider(
            "openai",
            "client-id",
            "client-secret",
            "http://localhost/callback"
        )

        assert "openai" in manager.providers
        assert isinstance(manager.providers["openai"], OpenAIOAuthProvider)

    def test_register_provider_anthropic(self, manager):
        """Test registering Anthropic provider"""
        manager.register_provider(
            "anthropic",
            "client-id",
            "client-secret",
            "http://localhost/callback"
        )

        assert "anthropic" in manager.providers
        assert isinstance(manager.providers["anthropic"], AnthropicOAuthProvider)

    def test_register_provider_unknown(self, manager):
        """Test registering unknown provider"""
        with pytest.raises(ValueError):
            manager.register_provider(
                "unknown",
                "client-id",
                "client-secret",
                "http://localhost/callback"
            )

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, manager):
        """Test getting authorization URL"""
        manager.register_provider(
            "google",
            "client-id",
            "client-secret",
            "http://localhost/callback"
        )

        url = await manager.get_authorization_url(
            "google",
            scopes=["https://www.googleapis.com/auth/generative-language"]
        )

        assert "accounts.google.com" in url
        assert "client_id=client-id" in url

    def test_delete_token(self, manager):
        """Test deleting OAuth token"""
        manager.delete_token("google")

        manager.credential_store.delete_credential.assert_called_once_with(
            provider="google",
            auth_method="oauth"
        )


# ============================================================================
# CLI Device Code Tests
# ============================================================================

class TestCLIAuthManager:
    """Test CLI device code authentication"""

    @pytest.fixture
    def mock_credential_store(self):
        """Create mock credential store"""
        return Mock()

    @pytest.fixture
    def manager(self, mock_credential_store):
        """Create CLI auth manager"""
        return CLIAuthManager(credential_store=mock_credential_store)

    @pytest.mark.asyncio
    async def test_request_device_code_google(self, manager):
        """Test requesting device code from Google"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = Mock()
            mock_response.json.return_value = {
                "device_code": "test-device-code",
                "user_code": "TEST-CODE",
                "verification_url": "https://www.google.com/device",
                "expires_in": 1800,
                "interval": 5,
            }
            mock_response.raise_for_status = Mock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            device_code = await manager.request_device_code(DeviceCodeProvider.GOOGLE)

            assert device_code.device_code == "test-device-code"
            assert device_code.user_code == "TEST-CODE"
            assert device_code.verification_url == "https://www.google.com/device"

    def test_store_token(self, manager):
        """Test storing device code token"""
        from myragdb.llm.auth.cli_auth import DeviceCodeToken

        token = DeviceCodeToken(
            access_token="test-token",
            token_type="Bearer",
            expires_in=3600
        )

        manager.store_token(DeviceCodeProvider.GOOGLE, token)

        manager.credential_store.store_credential.assert_called_once()

    def test_retrieve_token(self, manager):
        """Test retrieving device code token"""
        from myragdb.llm.auth.cli_auth import DeviceCodeToken

        manager.credential_store.retrieve_credential.return_value = {
            "access_token": "test-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": None,
        }

        token = manager.retrieve_token(DeviceCodeProvider.GOOGLE)

        assert token is not None
        assert token.access_token == "test-token"

    def test_delete_token(self, manager):
        """Test deleting device code token"""
        manager.delete_token(DeviceCodeProvider.GOOGLE)

        manager.credential_store.delete_credential.assert_called_once()


# ============================================================================
# Integration Tests
# ============================================================================

class TestAuthIntegration:
    """Integration tests for auth components"""

    @pytest.mark.asyncio
    async def test_api_key_flow(self):
        """Test complete API key authentication flow"""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.list_models') as mock_list:
                mock_model = Mock()
                mock_model.name = "gemini-pro"
                mock_list.return_value = [mock_model]

                # Create components
                validator = ApiKeyValidator()
                manager = ApiKeyAuthManager()

                # Validate and store
                result = await validator.validate_gemini_key("test-key")
                assert result.is_valid is True

                manager.store_api_key(ProviderType.GEMINI, "test-key")

                # Check stored
                assert manager.has_stored_key(ProviderType.GEMINI) is True

                # Clean up
                manager.delete_api_key(ProviderType.GEMINI)
                assert manager.has_stored_key(ProviderType.GEMINI) is False
