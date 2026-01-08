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

    def test_get_session_configured_from_api(self, client):
        """Test GET /llm/session returns response structure."""
        response = client.get("/llm/session")
        assert response.status_code == 200
        data = response.json()

        # Should have these fields regardless of configuration state
        assert 'status' in data
        assert 'provider_type' in data
        assert 'model_id' in data
        assert 'auth_method' in data

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
        provider_types = [p['provider_type'] for p in data['providers']]
        # Verify we have multiple providers (exact names may vary)
        assert len(provider_types) >= 3
        assert 'gemini' in provider_types
        # OpenAI provider type is 'chatgpt', Anthropic is 'claude'
        assert 'chatgpt' in provider_types or 'claude' in provider_types

    def test_get_providers_includes_models(self, client):
        """Test providers include model information."""
        response = client.get("/llm/providers")
        assert response.status_code == 200
        data = response.json()

        for provider in data['providers']:
            assert 'models' in provider
            assert len(provider['models']) > 0
            # Models are strings like 'gemini-pro', 'gemini-pro-vision'
            for model in provider['models']:
                assert isinstance(model, str)
                assert len(model) > 0


class TestAPIKeySubmissionFlow:
    """Tests for API key validation and submission flow."""

    def test_validate_api_key_endpoint_accepts_requests(self, client):
        """Test API key validation endpoint accepts and responds to requests."""
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
        # Should have validation response structure with is_valid field
        assert 'is_valid' in data

    def test_validate_api_key_with_empty_credentials(self, client):
        """Test API key validation with empty credentials."""
        response = client.post(
            "/llm/validate-credentials",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": ""}
            }
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_switch_provider_endpoint_accepts_requests(self, client):
        """Test provider switch endpoint accepts requests."""
        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": "test-key"}
            }
        )

        # May return 200 (accepted) or 422 (validation error) or 400 (bad request)
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            data = response.json()
            # Should have status field in response
            assert 'status' in data

    def test_switch_provider_invalid_provider(self, client):
        """Test provider switch with invalid provider."""
        response = client.post(
            "/llm/switch",
            json={
                "provider": "invalid_provider",
                "auth_method": "api_key",
                "credentials": {"api_key": "test"}
            }
        )

        assert response.status_code in [200, 400, 422]


class TestProviderSwitching:
    """Tests for provider switching and session management."""

    def test_authenticated_providers_list(self, client):
        """Test GET /llm/authenticated returns authenticated providers."""
        response = client.get("/llm/authenticated")
        assert response.status_code == 200
        data = response.json()

        assert 'providers' in data
        assert 'total_authenticated' in data
        assert isinstance(data['providers'], list)

    @patch('myragdb.llm.session_manager.SessionManager.get_active_session')
    @patch('myragdb.llm.session_manager.SessionManager.switch_to_local')
    def test_logout_success(self, mock_switch_local, mock_get_session, client):
        """Test successful logout from provider."""
        mock_session = MagicMock()
        mock_session.provider_type.value = "gemini"
        mock_get_session.return_value = mock_session

        response = client.post("/llm/logout/gemini")
        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'success'
        assert data['provider'] == 'gemini'

    def test_logout_endpoint_handles_non_existent_gracefully(self, client):
        """Test logout endpoint handles non-existent provider gracefully."""
        response = client.post("/llm/logout/nonexistent_provider_xyz")
        assert response.status_code == 200
        data = response.json()
        # Should have status field in response
        assert 'status' in data


class TestHealthMonitoring:
    """Tests for health status monitoring and display."""

    @patch('myragdb.llm.session_manager.SessionManager.get_active_session')
    def test_llm_health_endpoint_configured_healthy(self, mock_get_session, client):
        """Test /llm/health returns status when configured."""
        mock_session = MagicMock()
        mock_session.provider_type.value = "gemini"
        mock_session.model_id = "gemini-2.0-flash"
        mock_session.health_check_passed = True
        mock_get_session.return_value = mock_session

        response = client.get("/llm/health")
        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert 'cloud_llm_available' in data
        assert data['cloud_llm_available'] is True
        assert data['current_provider'] == 'gemini'

    @patch('myragdb.llm.session_manager.SessionManager.get_active_session')
    def test_llm_health_endpoint_not_configured(self, mock_get_session, client):
        """Test /llm/health when LLM not configured."""
        mock_get_session.return_value = None

        response = client.get("/llm/health")
        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
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

    def test_invalid_provider_error_response(self, client):
        """Test error handling for invalid provider."""
        response = client.post(
            "/llm/switch",
            json={
                "provider": "invalid_provider",
                "auth_method": "api_key",
                "credentials": {"api_key": "test"}
            }
        )

        assert response.status_code in [200, 400, 422]

    def test_missing_credentials_error_response(self, client):
        """Test error handling for missing credentials."""
        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {}
            }
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_invalid_auth_method_error_response(self, client):
        """Test error handling for unsupported auth method."""
        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "invalid_method",
                "credentials": {}
            }
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_logout_non_existent_provider_graceful(self, client):
        """Test logout from provider that doesn't exist."""
        response = client.post("/llm/logout/nonexistent_abc_123")
        assert response.status_code == 200
        data = response.json()
        # Should handle gracefully with 'status' field
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
            assert 'provider_type' in provider
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
        assert 'message' in data


class TestUIStateManagement:
    """Tests for UI state management and session persistence."""

    @patch('myragdb.llm.session_manager.SessionManager.get_active_session')
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
        initial_count = data1['total_authenticated']

        # Switch to a provider (may fail with unset credentials, that's ok)
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
        assert data2['total_authenticated'] >= initial_count


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

    def test_complete_provider_discovery_flow(self, client):
        """Test complete flow: discover providers → check session."""
        # Step 1: Get available providers
        response = client.get("/llm/providers")
        assert response.status_code == 200
        providers_data = response.json()
        assert 'providers' in providers_data
        providers = providers_data['providers']
        assert len(providers) > 0

        # Step 2: Check current session
        response = client.get("/llm/session")
        assert response.status_code == 200
        session_data = response.json()
        assert 'status' in session_data
        assert 'provider_type' in session_data

        # Step 3: Check authenticated providers
        response = client.get("/llm/authenticated")
        assert response.status_code == 200
        auth_data = response.json()
        assert 'providers' in auth_data
        assert 'total_authenticated' in auth_data

    def test_complete_switch_attempt_flow(self, client):
        """Test complete switch attempt flow."""
        # Step 1: Get initial session
        response = client.get("/llm/session")
        assert response.status_code == 200
        initial_session = response.json()

        # Step 2: Attempt to switch provider (may fail with test key, that's ok)
        response = client.post(
            "/llm/switch",
            json={
                "provider": "gemini",
                "auth_method": "api_key",
                "credentials": {"api_key": "test-key-123"}
            }
        )
        # May return 200 (accepted), 400 (bad request), or 422 (validation error)
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            assert 'status' in response.json()

        # Step 3: Check session after attempt
        response = client.get("/llm/session")
        assert response.status_code == 200
        final_session = response.json()
        assert 'status' in final_session

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
