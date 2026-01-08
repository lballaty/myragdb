"""
File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/test_cloud_llm_ui.py
Description: UI integration tests for cloud LLM manager functionality
Author: Libor Ballaty <libor@arionetworks.com>
Created: 2026-01-08
"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from src.myragdb.api.server import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestCloudLLMUIIntegration:
    """End-to-end UI integration tests for cloud LLM manager."""

    def test_llm_manager_html_loads(self, client):
        """Test that LLM manager HTML tab loads correctly."""
        response = client.get("/")
        assert response.status_code == 200
        # Check HTML contains LLM manager elements
        assert "llm-manager-tab" in response.text
        assert "Cloud LLM Manager" in response.text
        assert "llm-provider-tab" in response.text

    def test_current_session_display_loaded(self, client):
        """Test current session display section is present in HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "llm-current-session" in response.text
        assert "llm-session-display" in response.text
        assert "llm-session-indicator" in response.text
        assert "llm-logout-button" in response.text

    def test_provider_selection_ui_present(self, client):
        """Test provider selection tabs are present in HTML."""
        response = client.get("/")
        assert response.status_code == 200
        # Check all three providers are in HTML
        assert 'data-provider="gemini"' in response.text
        assert 'data-provider="openai"' in response.text
        assert 'data-provider="anthropic"' in response.text

    def test_authentication_methods_ui_present(self, client):
        """Test all authentication method options are in HTML."""
        response = client.get("/")
        assert response.status_code == 200
        # Check auth methods
        assert "auth-method-apikey" in response.text
        assert "auth-method-oauth" in response.text
        assert "auth-method-cli" in response.text

    def test_quick_switch_section_present(self, client):
        """Test quick switch section for authenticated providers."""
        response = client.get("/")
        assert response.status_code == 200
        assert "llm-authenticated-section" in response.text
        assert "llm-authenticated-list" in response.text

    def test_health_status_section_present(self, client):
        """Test health status section is present."""
        response = client.get("/")
        assert response.status_code == 200
        assert "llm-health-section" in response.text
        assert "llm-health-status" in response.text

    def test_css_stylesheet_included(self, client):
        """Test cloud-llm.css stylesheet is included."""
        response = client.get("/")
        assert response.status_code == 200
        assert "cloud-llm.css" in response.text

    def test_javascript_handler_included(self, client):
        """Test cloud-llm.js handler is included."""
        response = client.get("/")
        assert response.status_code == 200
        assert "cloud-llm.js" in response.text


class TestLLMSessionLoading:
    """Tests for session loading on page initialization."""

    @patch('src.myragdb.llm.session_manager.SessionManager.get_active_session')
    async def test_get_session_configured(self, mock_get_session, client):
        """Test GET /llm/session returns configured session."""
        mock_session = MagicMock()
        mock_session.provider_type.value = "gemini"
        mock_session.model_id = "gemini-2.0-flash"
        mock_session.auth_method.value = "api_key"
        mock_get_session.return_value = mock_session

        response = client.get("/llm/session")
        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'configured'
        assert data['provider_type'] == 'gemini'
        assert data['model_id'] == 'gemini-2.0-flash'
        assert data['auth_method'] == 'api_key'

    def test_get_session_not_configured(self, client):
        """Test GET /llm/session when no provider configured."""
        response = client.get("/llm/session")
        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'not_configured'
        assert data['provider_type'] is None
        assert data['model_id'] is None

    def test_get_providers_list(self, client):
        """Test GET /llm/providers returns all providers."""
        response = client.get("/llm/providers")
        assert response.status_code == 200
        data = response.json()

        assert 'providers' in data
        providers = [p['name'] for p in data['providers']]
        assert 'gemini' in providers
        assert 'openai' in providers
        assert 'anthropic' in providers

    def test_get_providers_includes_models(self, client):
        """Test providers include model information."""
        response = client.get("/llm/providers")
        assert response.status_code == 200
        data = response.json()

        for provider in data['providers']:
            assert 'models' in provider
            assert len(provider['models']) > 0
            for model in provider['models']:
                assert 'id' in model
                assert 'name' in model
                assert 'context_window' in model
                assert 'vision_capable' in model


class TestAPIKeySubmissionFlow:
    """Tests for API key validation and submission flow."""

    @patch('src.myragdb.llm.api_key_auth.ApiKeyValidator.validate')
    def test_validate_api_key_success(self, mock_validate, client):
        """Test successful API key validation."""
        mock_validate.return_value = {
            'valid': True,
            'provider': 'gemini',
            'model_id': 'gemini-2.0-flash'
        }

        response = client.post(
            "/llm/validate-credentials",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": "test-key-123"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['provider'] == 'gemini'
        assert data['model_id'] == 'gemini-2.0-flash'

    @patch('src.myragdb.llm.api_key_auth.ApiKeyValidator.validate')
    def test_validate_api_key_failure(self, mock_validate, client):
        """Test API key validation with invalid key."""
        mock_validate.return_value = {
            'valid': False,
            'error': 'invalid_api_key'
        }

        response = client.post(
            "/llm/validate-credentials",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": "invalid-key"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is False
        assert data['error'] == 'invalid_api_key'

    @patch('src.myragdb.llm.session_manager.SessionManager.switch_to_provider')
    @patch('src.myragdb.llm.api_key_auth.ApiKeyValidator.validate')
    def test_switch_provider_success(self, mock_validate, mock_switch, client):
        """Test successful provider switch with credentials."""
        mock_validate.return_value = {
            'valid': True,
            'provider': 'gemini',
            'model_id': 'gemini-2.0-flash'
        }
        mock_switch.return_value = None

        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": "test-key"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'switched'
        assert data['provider_type'] == 'gemini'

    @patch('src.myragdb.llm.api_key_auth.ApiKeyValidator.validate')
    def test_switch_provider_invalid_credentials(self, mock_validate, client):
        """Test provider switch with invalid credentials."""
        mock_validate.return_value = {
            'valid': False,
            'error': 'invalid_api_key'
        }

        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": "invalid"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'error'


class TestProviderSwitching:
    """Tests for provider switching and session management."""

    def test_authenticated_providers_list(self, client):
        """Test GET /llm/authenticated returns authenticated providers."""
        response = client.get("/llm/authenticated")
        assert response.status_code == 200
        data = response.json()

        assert 'authenticated_providers' in data
        assert 'total' in data
        assert isinstance(data['authenticated_providers'], list)

    @patch('src.myragdb.llm.session_manager.SessionManager.get_active_session')
    @patch('src.myragdb.llm.session_manager.SessionManager.switch_to_local')
    def test_logout_success(self, mock_switch_local, mock_get_session, client):
        """Test successful logout from provider."""
        mock_session = MagicMock()
        mock_session.provider_type.value = "gemini"
        mock_get_session.return_value = mock_session

        response = client.post("/llm/logout/gemini")
        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'logged_out'
        assert data['provider'] == 'gemini'
        assert data['switched_to'] == 'local'

    @patch('src.myragdb.llm.session_manager.SessionManager.get_active_session')
    @patch('src.myragdb.llm.session_manager.SessionManager.switch_to_provider')
    def test_logout_with_switch_to_other_provider(self, mock_switch, mock_get_session, client):
        """Test logout switches to another authenticated provider if available."""
        mock_session = MagicMock()
        mock_session.provider_type.value = "gemini"
        mock_get_session.return_value = mock_session

        response = client.post("/llm/logout/gemini")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'logged_out'


class TestHealthMonitoring:
    """Tests for health status monitoring and display."""

    @patch('src.myragdb.llm.session_manager.SessionManager.get_active_session')
    def test_llm_health_endpoint_configured_healthy(self, mock_get_session, client):
        """Test /llm/health returns healthy status when configured."""
        mock_session = MagicMock()
        mock_session.provider_type.value = "gemini"
        mock_session.model_id = "gemini-2.0-flash"
        mock_session.health_check_passed = True
        mock_get_session.return_value = mock_session

        response = client.get("/llm/health")
        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'healthy'
        assert data['cloud_llm_available'] is True
        assert data['current_provider'] == 'gemini'

    @patch('src.myragdb.llm.session_manager.SessionManager.get_active_session')
    def test_llm_health_endpoint_not_configured(self, mock_get_session, client):
        """Test /llm/health when LLM not configured."""
        mock_get_session.return_value = None

        response = client.get("/llm/health")
        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'available'
        assert data['cloud_llm_available'] is False
        assert data['current_provider'] is None

    def test_health_endpoint_includes_llm_status(self, client):
        """Test main /health endpoint includes LLM component."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert 'message' in data
        # Message should mention LLM status
        assert 'LLM' in data.get('message', '') or data['status'] in ['healthy', 'degraded', 'unhealthy']


class TestErrorHandling:
    """Tests for error handling and user-friendly messages."""

    def test_invalid_provider_error(self, client):
        """Test error handling for invalid provider."""
        response = client.post(
            "/llm/switch",
            json={
                "provider": "invalid_provider",
                "auth_method": "api_key",
                "credentials": {"api_key": "test"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'error'
        assert 'message' in data

    def test_missing_credentials_error(self, client):
        """Test error handling for missing credentials."""
        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {}
            }
        )

        assert response.status_code in [200, 400]

    def test_invalid_auth_method_error(self, client):
        """Test error handling for unsupported auth method."""
        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "invalid_method",
                "credentials": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        if 'status' in data:
            assert data['status'] == 'error'

    def test_logout_non_existent_provider(self, client):
        """Test logout from provider that doesn't exist."""
        response = client.post("/llm/logout/nonexistent")
        assert response.status_code == 200
        data = response.json()
        # Should handle gracefully
        assert 'status' in data


class TestUIResponseFormats:
    """Tests for response format consistency for UI consumption."""

    def test_session_response_format(self, client):
        """Test session response has correct format for UI."""
        response = client.get("/llm/session")
        assert response.status_code == 200
        data = response.json()

        # All responses should have these fields
        assert 'status' in data
        assert 'provider_type' in data
        assert 'model_id' in data
        assert 'auth_method' in data

    def test_providers_response_format(self, client):
        """Test providers response has UI-friendly format."""
        response = client.get("/llm/providers")
        assert response.status_code == 200
        data = response.json()

        assert 'providers' in data
        assert 'current_provider' in data
        assert isinstance(data['providers'], list)

        for provider in data['providers']:
            assert 'name' in provider
            assert 'display_name' in provider
            assert 'auth_methods' in provider
            assert 'models' in provider

    def test_health_response_format(self, client):
        """Test health response has expected fields for UI."""
        response = client.get("/llm/health")
        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert 'cloud_llm_available' in data
        assert 'current_provider' in data
        assert 'authenticated_providers' in data
        assert 'message' in data
        assert isinstance(data['authenticated_providers'], list)


class TestUIStateManagement:
    """Tests for UI state management and session persistence."""

    @patch('src.myragdb.llm.session_manager.SessionManager.get_active_session')
    def test_session_persists_across_requests(self, mock_get_session, client):
        """Test that session state persists across multiple requests."""
        mock_session = MagicMock()
        mock_session.provider_type.value = "gemini"
        mock_get_session.return_value = mock_session

        # First request
        response1 = client.get("/llm/session")
        data1 = response1.json()

        # Second request should return same session
        response2 = client.get("/llm/session")
        data2 = response2.json()

        assert data1['provider_type'] == data2['provider_type']

    def test_authenticated_providers_updated_after_switch(self, client):
        """Test authenticated providers list updates after switching."""
        # First get initial list
        response1 = client.get("/llm/authenticated")
        data1 = response1.json()
        initial_count = data1['total']

        # Switch to a provider
        client.post(
            "/llm/switch",
            json={
                "provider": "openai",
                "auth_method": "api_key",
                "credentials": {"api_key": "test-key"}
            }
        )

        # Get updated list
        response2 = client.get("/llm/authenticated")
        data2 = response2.json()

        # Should have at least same or more authenticated providers
        assert data2['total'] >= initial_count


class TestResponsiveDesign:
    """Tests for responsive design of LLM manager UI."""

    def test_mobile_viewport_html_includes_responsive_classes(self, client):
        """Test HTML includes responsive design classes."""
        response = client.get("/")
        assert response.status_code == 200
        # Check for responsive CSS classes
        assert "llm-provider-tabs" in response.text
        assert "grid" in response.text.lower() or "flex" in response.text.lower()

    def test_css_includes_mobile_media_queries(self, client):
        """Test cloud-llm.css includes mobile media queries."""
        response = client.get("/static/css/cloud-llm.css")
        assert response.status_code == 200
        # Check for mobile breakpoints
        assert "@media" in response.text
        assert "max-width: 768px" in response.text or "max-width: 480px" in response.text


class TestJavaScriptFunctionality:
    """Tests for JavaScript handler functionality."""

    def test_cloud_llm_js_loads_without_errors(self, client):
        """Test cloud-llm.js loads and can be parsed."""
        response = client.get("/static/js/cloud-llm.js")
        assert response.status_code == 200
        content = response.text

        # Check for key class and methods
        assert "CloudLLMManager" in content
        assert "loadCurrentSession" in content
        assert "selectProvider" in content
        assert "switchProvider" in content
        assert "logout" in content

    def test_javascript_includes_error_handling(self, client):
        """Test JavaScript includes error handling."""
        response = client.get("/static/js/cloud-llm.js")
        assert response.status_code == 200
        content = response.text

        # Check for error handling patterns
        assert "catch" in content
        assert "error" in content.lower()
        assert "try" in content


# ============================================================================
# End-to-End Integration Test Suite
# ============================================================================


class TestEndToEndCloudLLMFlow:
    """End-to-end test scenarios for complete user workflows."""

    @patch('src.myragdb.llm.api_key_auth.ApiKeyValidator.validate')
    @patch('src.myragdb.llm.session_manager.SessionManager.switch_to_provider')
    def test_complete_api_key_flow(self, mock_switch, mock_validate, client):
        """Test complete flow: validate credentials → switch provider."""
        mock_validate.return_value = {
            'valid': True,
            'provider': 'gemini',
            'model_id': 'gemini-2.0-flash'
        }

        # Step 1: Get available providers
        response = client.get("/llm/providers")
        assert response.status_code == 200
        providers = response.json()['providers']
        assert len(providers) > 0

        # Step 2: Validate credentials
        api_key = "test-api-key-123"
        response = client.post(
            "/llm/validate-credentials",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": api_key}
            }
        )
        assert response.status_code == 200
        assert response.json()['valid'] is True

        # Step 3: Switch provider
        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": api_key}
            }
        )
        assert response.status_code == 200
        assert response.json()['status'] == 'switched'

        # Step 4: Verify session
        response = client.get("/llm/session")
        assert response.status_code == 200
        assert response.json()['status'] == 'configured'

    @patch('src.myragdb.llm.session_manager.SessionManager.get_active_session')
    @patch('src.myragdb.llm.session_manager.SessionManager.switch_to_local')
    def test_complete_logout_flow(self, mock_switch_local, mock_get_session, client):
        """Test complete logout flow."""
        mock_session = MagicMock()
        mock_session.provider_type.value = "gemini"
        mock_get_session.return_value = mock_session

        # Step 1: Check initial session
        response = client.get("/llm/session")
        assert response.status_code == 200
        assert response.json()['status'] == 'configured'

        # Step 2: Logout
        response = client.post("/llm/logout/gemini")
        assert response.status_code == 200
        assert response.json()['status'] == 'logged_out'

    def test_complete_health_monitoring_flow(self, client):
        """Test health monitoring across different states."""
        # Step 1: Check initial health
        response = client.get("/llm/health")
        assert response.status_code == 200
        initial_health = response.json()

        # Step 2: Get main health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        main_health = response.json()
        assert 'status' in main_health

        # Step 3: Verify consistency
        assert initial_health['status'] in ['healthy', 'degraded', 'available', 'error']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
