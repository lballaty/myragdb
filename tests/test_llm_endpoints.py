# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/test_llm_endpoints.py
# Description: Integration tests for cloud LLM provider API endpoints
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from myragdb.api.server import app, get_llm_services
from myragdb.llm.session_manager import SessionManager, ProviderType, AuthMethodType


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def temp_config(monkeypatch):
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".myragdb"
        config_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("HOME", tmpdir)
        yield config_dir


class TestLLMSessionEndpoint:
    """Tests for GET /llm/session endpoint."""

    def test_get_session_not_configured(self, client, temp_config):
        """Test getting session when none is configured."""
        response = client.get("/llm/session")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_configured"
        assert data["provider_type"] is None
        assert data["model_id"] is None

    @patch('myragdb.api.server.get_llm_services')
    def test_get_session_active(self, mock_services, client):
        """Test getting active session."""
        # Mock the session manager
        mock_session_manager = MagicMock()
        mock_session = MagicMock()
        mock_session.provider_type = ProviderType.GEMINI
        mock_session.model_id = "gemini-pro"
        mock_session.auth_method = AuthMethodType.API_KEY
        mock_session.status = "active"

        mock_session_manager.get_active_session.return_value = mock_session
        mock_services.return_value = (mock_session_manager, None, None, None)

        response = client.get("/llm/session")
        assert response.status_code == 200
        data = response.json()
        assert data["provider_type"] == "gemini"
        assert data["model_id"] == "gemini-pro"
        assert data["auth_method"] == "api_key"
        assert data["status"] == "active"


class TestLLMProvidersEndpoint:
    """Tests for GET /llm/providers endpoint."""

    def test_get_providers_list(self, client):
        """Test getting list of available providers."""
        response = client.get("/llm/providers")
        assert response.status_code == 200
        data = response.json()

        # Should have providers list
        assert "providers" in data
        assert len(data["providers"]) >= 3  # At least Gemini, ChatGPT, Claude

        # Check provider structure
        provider = data["providers"][0]
        assert "name" in provider
        assert "provider_type" in provider
        assert "description" in provider
        assert "auth_methods" in provider
        assert "models" in provider

    def test_get_providers_includes_all_required(self, client):
        """Test that all required providers are included."""
        response = client.get("/llm/providers")
        data = response.json()

        provider_types = [p["provider_type"] for p in data["providers"]]
        assert "gemini" in provider_types
        assert "chatgpt" in provider_types
        assert "claude" in provider_types


class TestValidateCredentialsEndpoint:
    """Tests for POST /llm/validate-credentials endpoint."""

    @patch('myragdb.api.server.get_llm_services')
    def test_validate_valid_credentials(self, mock_services, client):
        """Test validating valid API key credentials."""
        # Mock the validator
        mock_validator = AsyncMock()
        validation_result = MagicMock()
        validation_result.is_valid = True
        validation_result.message = "Credentials validated successfully"
        validation_result.error_code = None

        mock_validator.validate_key.return_value = validation_result
        mock_services.return_value = (None, None, None, mock_validator)

        response = client.post(
            "/llm/validate-credentials",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": "test-api-key"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["provider"] == "gemini"
        assert data["message"] == "Credentials validated successfully"

    @patch('myragdb.api.server.get_llm_services')
    def test_validate_invalid_credentials(self, mock_services, client):
        """Test validating invalid API key credentials."""
        # Mock the validator
        mock_validator = AsyncMock()
        validation_result = MagicMock()
        validation_result.is_valid = False
        validation_result.message = "Invalid API key"
        validation_result.error_code = "invalid_key"

        mock_validator.validate_key.return_value = validation_result
        mock_services.return_value = (None, None, None, mock_validator)

        response = client.post(
            "/llm/validate-credentials",
            json={
                "provider": "chatgpt",
                "auth_method": "api_key",
                "credentials": {"api_key": "invalid-key"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["provider"] == "chatgpt"
        assert data["error_code"] == "invalid_key"

    def test_validate_unsupported_auth_method(self, client):
        """Test validating with unsupported auth method."""
        response = client.post(
            "/llm/validate-credentials",
            json={
                "provider": "gemini",
                "auth_method": "unsupported",
                "credentials": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["error_code"] == "unsupported_auth_method"


class TestSwitchLLMEndpoint:
    """Tests for POST /llm/switch endpoint."""

    @patch('myragdb.api.server.get_llm_services')
    def test_switch_provider_success(self, mock_services, client):
        """Test successfully switching to a different provider."""
        # Mock services
        mock_session_manager = AsyncMock()
        mock_cred_store = MagicMock()
        mock_api_key_auth_mgr = MagicMock()
        mock_validator = AsyncMock()

        # Mock validator response
        validation_result = MagicMock()
        validation_result.is_valid = True
        validation_result.message = "Credentials validated successfully"
        validation_result.error_code = None

        mock_validator.validate_key.return_value = validation_result

        # Mock new session
        new_session = MagicMock()
        new_session.provider_type = ProviderType.GEMINI
        new_session.model_id = "gemini-pro"
        new_session.auth_method = AuthMethodType.API_KEY
        new_session.status = "active"

        mock_session_manager.switch_to_cloud.return_value = new_session

        mock_services.return_value = (
            mock_session_manager,
            mock_cred_store,
            mock_api_key_auth_mgr,
            mock_validator
        )

        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "model_id": "gemini-pro",
                "auth_method": "api_key",
                "credentials": {"api_key": "test-api-key"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["new_session"]["provider_type"] == "gemini"
        assert data["new_session"]["model_id"] == "gemini-pro"

    @patch('myragdb.api.server.get_llm_services')
    def test_switch_provider_invalid_credentials(self, mock_services, client):
        """Test switching with invalid credentials."""
        # Mock services
        mock_session_manager = AsyncMock()
        mock_cred_store = MagicMock()
        mock_api_key_auth_mgr = MagicMock()
        mock_validator = AsyncMock()

        # Mock validator response - invalid
        validation_result = MagicMock()
        validation_result.is_valid = False
        validation_result.message = "Invalid API key"
        validation_result.error_code = "invalid_key"

        mock_validator.validate_key.return_value = validation_result

        mock_services.return_value = (
            mock_session_manager,
            mock_cred_store,
            mock_api_key_auth_mgr,
            mock_validator
        )

        response = client.post(
            "/llm/switch",
            json={
                "provider": "chatgpt",
                "model_id": "gpt-4",
                "auth_method": "api_key",
                "credentials": {"api_key": "invalid-key"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["new_session"] is None


class TestAuthenticatedProvidersEndpoint:
    """Tests for GET /llm/authenticated endpoint."""

    @patch('myragdb.api.server.get_llm_services')
    def test_get_authenticated_providers(self, mock_services, client):
        """Test getting list of authenticated providers."""
        mock_cred_store = MagicMock()
        mock_cred_store.list_authenticated_providers.return_value = ["gemini", "chatgpt"]

        mock_services.return_value = (None, mock_cred_store, None, None)

        response = client.get("/llm/authenticated")
        assert response.status_code == 200
        data = response.json()
        assert data["providers"] == ["gemini", "chatgpt"]
        assert data["total_authenticated"] == 2

    @patch('myragdb.api.server.get_llm_services')
    def test_get_authenticated_providers_empty(self, mock_services, client):
        """Test getting authenticated providers when none are configured."""
        mock_cred_store = MagicMock()
        mock_cred_store.list_authenticated_providers.return_value = []

        mock_services.return_value = (None, mock_cred_store, None, None)

        response = client.get("/llm/authenticated")
        assert response.status_code == 200
        data = response.json()
        assert data["providers"] == []
        assert data["total_authenticated"] == 0


class TestLogoutEndpoint:
    """Tests for POST /llm/logout/{provider} endpoint."""

    @patch('myragdb.api.server.get_llm_services')
    def test_logout_provider_success(self, mock_services, client):
        """Test successfully logging out from a provider."""
        mock_session_manager = MagicMock()
        mock_cred_store = MagicMock()

        # Mock that current session is not for logged out provider
        mock_session = MagicMock()
        mock_session.provider_type = ProviderType.CHATGPT
        mock_session_manager.get_active_session.return_value = mock_session

        mock_services.return_value = (mock_session_manager, mock_cred_store, None, None)

        response = client.post("/llm/logout/gemini")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["provider"] == "gemini"
        mock_cred_store.delete_credentials.assert_called_once_with("gemini")

    @patch('myragdb.api.server.get_llm_services')
    def test_logout_current_provider_switches_to_local(self, mock_services, client):
        """Test that logging out current provider switches to local."""
        mock_session_manager = MagicMock()
        mock_cred_store = MagicMock()

        # Mock that current session is for logged out provider
        mock_session = MagicMock()
        mock_session.provider_type = ProviderType.GEMINI
        mock_session_manager.get_active_session.return_value = mock_session
        # Make switch_to_local an AsyncMock so it can be awaited
        mock_session_manager.switch_to_local = AsyncMock()

        mock_services.return_value = (mock_session_manager, mock_cred_store, None, None)

        response = client.post("/llm/logout/gemini")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Should have called switch_to_local
        mock_session_manager.switch_to_local.assert_called_once_with("phi3")


class TestLLMEndpointsErrorHandling:
    """Tests for error handling in LLM endpoints."""

    @patch('myragdb.api.server.get_llm_services')
    def test_session_endpoint_error_handling(self, mock_services, client):
        """Test error handling in session endpoint."""
        mock_services.side_effect = Exception("Service error")

        response = client.get("/llm/session")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    @patch('myragdb.api.server.get_llm_services')
    def test_providers_endpoint_error_handling(self, mock_services, client):
        """Test error handling in providers endpoint."""
        mock_services.side_effect = Exception("Service error")

        response = client.get("/llm/providers")
        assert response.status_code == 200
        data = response.json()
        assert data["providers"] == []
        assert data["current_provider"] is None

    @patch('myragdb.api.server.get_llm_services')
    def test_authenticated_endpoint_error_handling(self, mock_services, client):
        """Test error handling in authenticated providers endpoint."""
        mock_services.side_effect = Exception("Service error")

        response = client.get("/llm/authenticated")
        assert response.status_code == 200
        data = response.json()
        assert data["providers"] == []
        assert data["total_authenticated"] == 0
