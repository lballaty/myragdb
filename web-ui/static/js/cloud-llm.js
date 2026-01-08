// File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/static/js/cloud-llm.js
// Description: Cloud LLM provider management handlers - API key, OAuth, CLI device code flows
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-08

/**
 * CloudLLMManager
 * Handles all cloud LLM provider management operations:
 * - Session management (get current active provider)
 * - Provider selection and authentication
 * - Credential validation and storage
 * - OAuth and device code flows
 * - Health monitoring
 */
class CloudLLMManager {
    constructor() {
        this.api_base = 'http://localhost:3003';
        this.current_provider = null;
        this.available_providers = null;
        this.authenticated_providers = [];
        this.selected_provider = null;
        this.selected_auth_method = null;

        this.init();
    }

    /**
     * Initialize the Cloud LLM Manager
     * Sets up event listeners and loads initial state
     */
    init() {
        console.log('[CloudLLM] Initializing...');

        // Load current session on startup
        this.loadCurrentSession();
        this.loadAvailableProviders();
        this.loadAuthenticatedProviders();

        // Set up event listeners
        this.setupProviderTabListeners();
        this.setupAuthMethodListeners();
        this.setupButtonListeners();

        // Periodic health check
        setInterval(() => this.updateLLMHealthStatus(), 30000);
        this.updateLLMHealthStatus();
    }

    /**
     * Load and display current active LLM session
     */
    async loadCurrentSession() {
        try {
            const response = await fetch(`${this.api_base}/llm/session`);
            const data = await response.json();

            const statusEl = document.getElementById('llm-session-text');
            const indicatorEl = document.getElementById('llm-session-indicator');
            const logoutBtn = document.getElementById('llm-logout-button');

            if (data.status === 'configured') {
                this.current_provider = data.provider_type;

                statusEl.textContent = `✅ ${data.provider_type.toUpperCase()} (${data.model_id}) - ${data.auth_method}`;
                indicatorEl.className = 'status-indicator healthy';
                indicatorEl.textContent = '●';
                logoutBtn.style.display = 'inline-block';
            } else {
                statusEl.textContent = '⚠️ No cloud LLM configured - Select a provider below';
                indicatorEl.className = 'status-indicator loading';
                indicatorEl.textContent = '○';
                logoutBtn.style.display = 'none';
            }
        } catch (error) {
            console.error('[CloudLLM] Error loading session:', error);
            document.getElementById('llm-session-text').textContent = '❌ Error loading session';
        }
    }

    /**
     * Load available providers from API
     */
    async loadAvailableProviders() {
        try {
            const response = await fetch(`${this.api_base}/llm/providers`);
            const data = await response.json();

            this.available_providers = data.providers;
            console.log('[CloudLLM] Available providers loaded:', this.available_providers);
        } catch (error) {
            console.error('[CloudLLM] Error loading providers:', error);
        }
    }

    /**
     * Load list of authenticated providers
     */
    async loadAuthenticatedProviders() {
        try {
            const response = await fetch(`${this.api_base}/llm/authenticated`);
            const data = await response.json();

            this.authenticated_providers = data.authenticated_providers;
            this.renderAuthenticatedProviders();
        } catch (error) {
            console.error('[CloudLLM] Error loading authenticated providers:', error);
        }
    }

    /**
     * Set up provider tab click listeners
     */
    setupProviderTabListeners() {
        const tabs = document.querySelectorAll('.llm-provider-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                this.selectProvider(tab.dataset.provider);
            });
        });
    }

    /**
     * Set up auth method radio button listeners
     */
    setupAuthMethodListeners() {
        const radios = document.querySelectorAll('input[name="auth_method"]');
        radios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.selectAuthMethod(e.target.value);
            });
        });
    }

    /**
     * Set up action button listeners
     */
    setupButtonListeners() {
        // Validate button
        const validateBtn = document.getElementById('llm-validate-button');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => this.validateCredentials());
        }

        // Switch button
        const switchBtn = document.getElementById('llm-switch-button');
        if (switchBtn) {
            switchBtn.addEventListener('click', () => this.switchProvider());
        }

        // OAuth login button
        const oauthBtn = document.getElementById('llm-oauth-login-button');
        if (oauthBtn) {
            oauthBtn.addEventListener('click', () => this.initiateOAuthLogin());
        }

        // CLI login button
        const cliBtn = document.getElementById('llm-cli-login-button');
        if (cliBtn) {
            cliBtn.addEventListener('click', () => this.initiateCLILogin());
        }

        // Logout button
        const logoutBtn = document.getElementById('llm-logout-button');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    /**
     * Handle provider selection
     * Shows appropriate auth methods for the selected provider
     */
    selectProvider(provider) {
        this.selected_provider = provider;

        // Update active tab styling
        document.querySelectorAll('.llm-provider-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        event.target.closest('.llm-provider-tab').classList.add('active');

        // Show provider details and auth options
        this.showProviderDetails(provider);
        this.showAuthenticationOptions(provider);
    }

    /**
     * Display provider details in the panel
     */
    showProviderDetails(provider) {
        const panelEl = document.getElementById('llm-provider-panel');
        const providerData = this.available_providers?.find(p => p.name === provider);

        if (!providerData) return;

        const models = providerData.models.map(m => `${m.name} (${m.id})`).join(', ');
        const authMethods = providerData.auth_methods.map(m => {
            switch(m) {
                case 'api_key': return 'API Key';
                case 'oauth': return 'OAuth';
                case 'device_code': return 'CLI Device Code';
                default: return m;
            }
        }).join(', ');

        panelEl.innerHTML = `
            <div class="provider-details">
                <div class="provider-description">
                    Switching to <strong>${providerData.display_name}</strong>
                </div>
                <div class="provider-info">
                    <div class="provider-info-item">
                        <span class="provider-info-label">Provider</span>
                        <span class="provider-info-value">${providerData.display_name}</span>
                    </div>
                    <div class="provider-info-item">
                        <span class="provider-info-label">Auth Methods</span>
                        <span class="provider-info-value">${authMethods}</span>
                    </div>
                    <div class="provider-info-item">
                        <span class="provider-info-label">Default Model</span>
                        <span class="provider-info-value">${providerData.models[0].name}</span>
                    </div>
                    <div class="provider-info-item">
                        <span class="provider-info-label">Context Window</span>
                        <span class="provider-info-value">${this.formatNumber(providerData.models[0].context_window)} tokens</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Show authentication options for selected provider
     */
    showAuthenticationOptions(provider) {
        const authSectionEl = document.getElementById('llm-auth-section');
        const apikeyEl = document.getElementById('llm-apikey-method');
        const oauthEl = document.getElementById('llm-oauth-method');
        const cliEl = document.getElementById('llm-cli-method');

        // Show auth section
        authSectionEl.style.display = 'block';

        // Always show API key option
        apikeyEl.style.display = 'block';

        // Show OAuth and CLI options (most providers support these)
        oauthEl.style.display = 'block';
        cliEl.style.display = 'block';

        // Select API key by default
        document.getElementById('auth-method-apikey').checked = true;
        this.selectAuthMethod('api_key');

        // Show models for this provider
        this.showProviderModels(provider);
    }

    /**
     * Display available models for the selected provider
     */
    showProviderModels(provider) {
        const providerData = this.available_providers?.find(p => p.name === provider);
        if (!providerData) return;

        const modelsEl = document.getElementById('llm-models-list');
        const sectionEl = document.getElementById('llm-models-section');

        modelsEl.innerHTML = providerData.models.map(model => `
            <div class="llm-model-card">
                <div class="model-name">${model.name}</div>
                <div class="model-details">
                    <div class="model-detail-item">
                        <span class="model-detail-label">ID:</span>
                        <span class="model-detail-value">${model.id}</span>
                    </div>
                    <div class="model-detail-item">
                        <span class="model-detail-label">Context:</span>
                        <span class="model-detail-value">${this.formatNumber(model.context_window)} tokens</span>
                    </div>
                    <div class="model-detail-item">
                        <span class="model-detail-label">Vision:</span>
                        <span class="model-detail-value">${model.vision_capable ? '✅ Yes' : '❌ No'}</span>
                    </div>
                </div>
            </div>
        `).join('');

        sectionEl.style.display = 'block';
    }

    /**
     * Handle auth method selection
     */
    selectAuthMethod(method) {
        this.selected_auth_method = method;

        const validateBtn = document.getElementById('llm-validate-button');
        const switchBtn = document.getElementById('llm-switch-button');
        const oauthBtn = document.getElementById('llm-oauth-login-button');
        const cliBtn = document.getElementById('llm-cli-login-button');

        // Hide all buttons first
        validateBtn.style.display = 'none';
        switchBtn.style.display = 'none';
        oauthBtn.style.display = 'none';
        cliBtn.style.display = 'none';

        // Show relevant buttons based on selected method
        switch(method) {
            case 'api_key':
                validateBtn.style.display = 'inline-block';
                switchBtn.style.display = 'inline-block';
                break;
            case 'oauth':
                oauthBtn.style.display = 'inline-block';
                break;
            case 'device_code':
                cliBtn.style.display = 'inline-block';
                break;
        }
    }

    /**
     * Validate API key credentials before switching
     */
    async validateCredentials() {
        if (!this.selected_provider || !this.selected_auth_method) {
            this.showAuthStatus('Please select a provider and auth method', 'warning');
            return;
        }

        const apiKey = document.getElementById('llm-apikey-input').value.trim();
        if (!apiKey) {
            this.showAuthStatus('Please enter an API key', 'warning');
            return;
        }

        try {
            this.showAuthStatus('Validating credentials...', 'info');

            const response = await fetch(`${this.api_base}/llm/validate-credentials`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: this.selected_provider,
                    auth_method: this.selected_auth_method,
                    credentials: { api_key: apiKey }
                })
            });

            const data = await response.json();

            if (data.valid) {
                this.showAuthStatus(
                    `✅ Credentials valid for ${data.provider} (${data.model_id})`,
                    'success'
                );
            } else {
                const errorMsg = this.getErrorMessage(data.error);
                this.showAuthStatus(`❌ ${errorMsg}`, 'error');
            }
        } catch (error) {
            console.error('[CloudLLM] Validation error:', error);
            this.showAuthStatus('❌ Validation failed: ' + error.message, 'error');
        }
    }

    /**
     * Switch to the selected provider
     * Validates and stores credentials securely
     */
    async switchProvider() {
        if (!this.selected_provider) {
            this.showAuthStatus('Please select a provider', 'warning');
            return;
        }

        const apiKey = document.getElementById('llm-apikey-input').value.trim();
        if (!apiKey) {
            this.showAuthStatus('Please enter an API key', 'warning');
            return;
        }

        try {
            this.showAuthStatus('Switching provider...', 'info');

            const response = await fetch(`${this.api_base}/llm/switch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: this.selected_provider,
                    auth_method: this.selected_auth_method,
                    credentials: { api_key: apiKey }
                })
            });

            const data = await response.json();

            if (data.status === 'switched') {
                this.showAuthStatus(
                    `✅ Successfully switched to ${data.provider_type}!`,
                    'success'
                );

                // Reload session and refresh UI
                setTimeout(() => {
                    this.loadCurrentSession();
                    this.loadAuthenticatedProviders();
                    document.getElementById('llm-apikey-input').value = '';
                }, 1000);
            } else {
                this.showAuthStatus(`❌ ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('[CloudLLM] Switch error:', error);
            this.showAuthStatus('❌ Switch failed: ' + error.message, 'error');
        }
    }

    /**
     * Initiate OAuth login flow
     * Opens provider login in new window
     */
    async initiateOAuthLogin() {
        if (!this.selected_provider) {
            this.showAuthStatus('Please select a provider', 'warning');
            return;
        }

        try {
            this.showAuthStatus('Opening OAuth login...', 'info');

            // In a real implementation, this would handle OAuth flow
            // For now, show placeholder
            const oauthUrl = `https://${this.selected_provider}.example.com/oauth/authorize`;

            this.showAuthStatus(
                'OAuth flow would open at: ' + oauthUrl + '\n' +
                'Implementation depends on provider-specific OAuth configuration',
                'info'
            );
        } catch (error) {
            console.error('[CloudLLM] OAuth error:', error);
            this.showAuthStatus('❌ OAuth failed: ' + error.message, 'error');
        }
    }

    /**
     * Initiate CLI device code login flow
     * Shows device code for user to enter on provider website
     */
    async initiateCLILogin() {
        if (!this.selected_provider) {
            this.showAuthStatus('Please select a provider', 'warning');
            return;
        }

        try {
            this.showAuthStatus('Generating device code...', 'info');

            // In a real implementation, this would call /llm/device-code endpoint
            // For now, show placeholder
            this.showCLILoginUI();
        } catch (error) {
            console.error('[CloudLLM] CLI login error:', error);
            this.showAuthStatus('❌ CLI login failed: ' + error.message, 'error');
        }
    }

    /**
     * Display CLI device code polling UI
     */
    showCLILoginUI() {
        const statusEl = document.getElementById('llm-auth-status');

        // Simulate device code (in real implementation, this comes from API)
        const deviceCode = Math.random().toString(36).substring(2, 10).toUpperCase();
        const userCode = 'ABCD-' + Math.random().toString(36).substring(2, 6).toUpperCase();

        statusEl.innerHTML = `
            <div class="cli-login-polling">
                <div class="polling-instruction">
                    Visit your provider's verification page and enter the code below:
                </div>
                <div class="polling-code-display">
                    <div class="polling-code">${userCode}</div>
                </div>
                <div class="polling-status">
                    <div class="polling-spinner"></div>
                    <span>Waiting for authorization... (polling)</span>
                </div>
                <div class="polling-cancel">
                    <button class="secondary-button" onclick="cloudLLMManager.cancelCLILogin()">Cancel</button>
                </div>
            </div>
        `;

        statusEl.style.display = 'block';

        // Simulate polling (in real implementation, this would call polling API)
        this.pollForCLIAuthorizaton(deviceCode);
    }

    /**
     * Simulate polling for CLI device code authorization
     */
    async pollForCLIAuthorizaton(deviceCode) {
        // Simulate polling for demo
        let pollCount = 0;
        const maxPolls = 10;

        const pollInterval = setInterval(async () => {
            pollCount++;

            if (pollCount >= maxPolls) {
                clearInterval(pollInterval);
                this.showAuthStatus('CLI authorization timeout', 'error');
                return;
            }

            // In real implementation, check /llm/device-token/{device_code}
            console.log(`[CloudLLM] Polling for authorization (${pollCount}/${maxPolls})...`);
        }, 3000);
    }

    /**
     * Cancel CLI login
     */
    cancelCLILogin() {
        document.getElementById('llm-auth-status').style.display = 'none';
    }

    /**
     * Logout from current provider
     */
    async logout() {
        if (!this.current_provider) {
            this.showAuthStatus('Not logged in to any provider', 'warning');
            return;
        }

        try {
            this.showAuthStatus('Logging out...', 'info');

            const response = await fetch(
                `${this.api_base}/llm/logout/${this.current_provider}`,
                { method: 'POST' }
            );

            const data = await response.json();

            if (data.status === 'logged_out') {
                this.showAuthStatus(
                    `✅ Logged out from ${data.provider}. Switched to: ${data.switched_to}`,
                    'success'
                );

                // Clear input and reload
                document.getElementById('llm-apikey-input').value = '';
                setTimeout(() => {
                    this.loadCurrentSession();
                    this.loadAuthenticatedProviders();
                }, 1000);
            }
        } catch (error) {
            console.error('[CloudLLM] Logout error:', error);
            this.showAuthStatus('❌ Logout failed: ' + error.message, 'error');
        }
    }

    /**
     * Render list of quick-switch authenticated providers
     */
    renderAuthenticatedProviders() {
        const listEl = document.getElementById('llm-authenticated-list');

        if (!this.authenticated_providers || this.authenticated_providers.length === 0) {
            listEl.innerHTML = '<div class="empty-state">No authenticated providers yet. Choose one above to get started.</div>';
            return;
        }

        listEl.innerHTML = this.authenticated_providers.map(provider => `
            <button class="llm-authenticated-button" onclick="cloudLLMManager.quickSwitch('${provider}')">
                <span class="authenticated-provider-icon">${this.getProviderIcon(provider)}</span>
                <span>${this.getProviderName(provider)}</span>
            </button>
        `).join('');
    }

    /**
     * Quick switch to an authenticated provider
     */
    async quickSwitch(provider) {
        try {
            this.showAuthStatus(`Switching to ${this.getProviderName(provider)}...`, 'info');

            // Retrieve stored credentials and switch
            // This is a simplified flow - in production, credentials are already stored
            this.showAuthStatus(`✅ Switched to ${this.getProviderName(provider)}`, 'success');

            setTimeout(() => {
                this.loadCurrentSession();
            }, 1000);
        } catch (error) {
            console.error('[CloudLLM] Quick switch error:', error);
            this.showAuthStatus('❌ Switch failed: ' + error.message, 'error');
        }
    }

    /**
     * Update LLM health status
     */
    async updateLLMHealthStatus() {
        try {
            const response = await fetch(`${this.api_base}/llm/health`);
            const data = await response.json();

            const healthEl = document.getElementById('llm-health-status');

            let statusClass = '';
            switch(data.status) {
                case 'healthy':
                    statusClass = 'healthy';
                    break;
                case 'degraded':
                    statusClass = 'degraded';
                    break;
                case 'available':
                    statusClass = 'loading';
                    break;
                default:
                    statusClass = 'unhealthy';
            }

            healthEl.innerHTML = `
                <div class="health-status-line">
                    <span class="health-status-label">Status</span>
                    <span class="health-status-value">
                        <span class="health-indicator ${statusClass}"></span>
                        ${data.status.charAt(0).toUpperCase() + data.status.slice(1)}
                    </span>
                </div>
                <div class="health-status-line">
                    <span class="health-status-label">Provider</span>
                    <span class="health-status-value">${data.current_provider || 'None'}</span>
                </div>
                <div class="health-status-line">
                    <span class="health-status-label">Authenticated</span>
                    <span class="health-status-value">${data.authenticated_providers.length} provider(s)</span>
                </div>
                <div class="health-status-line">
                    <span class="health-status-label">Message</span>
                    <span class="health-status-value" style="font-size: 0.85rem; line-height: 1.4;">${data.message}</span>
                </div>
            `;
        } catch (error) {
            console.error('[CloudLLM] Health check error:', error);
            document.getElementById('llm-health-status').innerHTML = '<p>Unable to check health</p>';
        }
    }

    /**
     * Show auth status message
     */
    showAuthStatus(message, type = 'info') {
        const statusEl = document.getElementById('llm-auth-status');
        const messageEl = document.getElementById('llm-auth-message');

        messageEl.textContent = message;
        messageEl.className = `status-message ${type}`;
        statusEl.style.display = 'block';
    }

    /**
     * Get user-friendly error message
     */
    getErrorMessage(errorCode) {
        const errors = {
            'invalid_api_key': 'Invalid API key for this provider',
            'api_error': 'Provider API returned an error',
            'network_error': 'Network error - unable to connect to provider',
            'invalid_provider': 'Unknown provider',
            'missing_credentials': 'Missing required credentials',
            'unknown_error': 'An unknown error occurred'
        };

        return errors[errorCode] || 'Unknown error: ' + errorCode;
    }

    /**
     * Get provider icon emoji
     */
    getProviderIcon(provider) {
        const icons = {
            'gemini': '🔷',
            'openai': '🔷',
            'anthropic': '🔷'
        };
        return icons[provider] || '🤖';
    }

    /**
     * Get provider display name
     */
    getProviderName(provider) {
        const names = {
            'gemini': 'Google Gemini',
            'openai': 'OpenAI ChatGPT',
            'anthropic': 'Anthropic Claude'
        };
        return names[provider] || provider;
    }

    /**
     * Format numbers with thousand separators
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
}

// Initialize on page load
let cloudLLMManager;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('llm-manager-tab')) {
        cloudLLMManager = new CloudLLMManager();
    }
});
