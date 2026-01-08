# Complete Implementation Roadmap - Q1 2026
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/IMPLEMENTATION_ROADMAP_2026_Q1.md
**Description:** Comprehensive, dependency-aware implementation plan for cloud GLLM and skills/agents completion
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Executive Summary

This roadmap provides a **complete, sequential implementation plan** with explicit dependencies for completing all pending work on the MyRAGDB platform:

- **Cloud GLLM Integration** (3 phases): Authentication, API endpoints, Web UI
- **Skills & Agents Exposure** (5 phases): REST API, CLI, advanced skills, templates, documentation

**Total Estimated Effort:** 120-150 hours across 8 sequential phases
**All phases respect architectural dependencies** - each phase can only start after prerequisites are complete

---

## Dependency Diagram

```
Phase 1: Cloud Auth Setup (Foundation)
├── API Key Method
├── OAuth Flow Setup
├── CLI Device Code Setup
└── CredentialStore Enhancements
       ↓
Phase 2: Cloud LLM API Endpoints
├── SessionManager API Integration
├── Provider Validation
├── Credential Management Endpoints
└── LLM Session Endpoints
       ↓
Phase 3: Cloud LLM Web UI
├── Cloud Provider Dropdown
├── Auth Method Selection
├── API Key Input Form
├── Subscription Login Button
└── CLI Login Display
       ↓
Phase 4: Agent Skills API Endpoints (Foundation)
├── Workflow Execution Endpoint
├── Template Discovery Endpoint
├── Skill Discovery Endpoint
└── Execution History Tracking
       ↓
Phase 5: Agent Skills CLI Commands
├── Workflow Execution Commands
├── Template Management Commands
├── Skill Management Commands
└── History & Logging Commands
       ↓
Phase 6: Advanced Skills Implementation
├── DataVisualizationSkill
├── CodeGenerationSkill
├── SlackIntegrationSkill
└── WebhookIntegrationSkill
       ↓
Phase 7: Example Templates & Library
├── Code Search Template
├── Code Analysis Template
├── Code Review Template
├── Documentation Generation Template
├── Error Analysis Template
├── Performance Analysis Template
├── Security Audit Template
├── Data Analysis Template
├── Integration Testing Template
└── Compliance Report Template
       ↓
Phase 8: Documentation & Testing
├── API Reference Documentation
├── CLI Reference Guide
├── Skill Development Tutorial
├── Template Creation Guide
├── Error Handling Guide
└── Integration Tests (All phases)
```

---

## PHASE 1: Cloud Authentication Setup (Foundation)
**Duration:** 8-10 hours | **Dependencies:** None (can start immediately)
**Status:** ⏳ Not started

### 1.1 API Key Authentication Method
**File:** `src/myragdb/llm/auth/api_key_auth.py` (NEW)

```python
# Purpose: Handle API key validation and storage

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

class ApiKeyValidator:
    """Validates API keys for each cloud provider"""

    async def validate_gemini_key(api_key: str) -> bool:
        """Test Gemini API key by making small API call"""

    async def validate_openai_key(api_key: str) -> bool:
        """Test OpenAI API key"""

    async def validate_anthropic_key(api_key: str) -> bool:
        """Test Claude API key"""

class ApiKeyAuthManager:
    """Manages API key authentication flow"""

    def store_api_key(provider: str, api_key: str) -> None:
        """Store encrypted API key in credential store"""

    def retrieve_api_key(provider: str) -> Optional[str]:
        """Get stored API key"""

    def delete_api_key(provider: str) -> None:
        """Remove stored API key"""
```

**Tasks:**
- [ ] Create `src/myragdb/llm/auth/` directory
- [ ] Create `src/myragdb/llm/auth/__init__.py`
- [ ] Implement `ApiKeyValidator` class with validation for each provider
- [ ] Implement `ApiKeyAuthManager` for storage/retrieval
- [ ] Add unit tests for validation logic
- [ ] Update `src/myragdb/llm/auth_config.py` to use validators

**Testing:**
- [ ] Test valid API keys (mock API responses)
- [ ] Test invalid API keys (error handling)
- [ ] Test key storage/retrieval
- [ ] Test key deletion

### 1.2 OAuth/Subscription Authentication Method
**File:** `src/myragdb/llm/auth/oauth_auth.py` (NEW)

```python
# Purpose: Handle OAuth flows for subscription-based auth

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class OAuthProvider(ABC):
    """Base class for OAuth providers"""

    @abstractmethod
    def get_auth_url(self) -> str:
        """Return OAuth authorization URL"""

    @abstractmethod
    async def handle_callback(code: str) -> Dict[str, Any]:
        """Exchange auth code for tokens"""

    @abstractmethod
    async def refresh_token(refresh_token: str) -> str:
        """Refresh access token"""

class GeminiOAuthProvider(OAuthProvider):
    """Google Gemini OAuth flow"""

class OpenAISubscriptionProvider(OAuthProvider):
    """OpenAI enterprise subscription OAuth"""

class AnthropicSubscriptionProvider(OAuthProvider):
    """Anthropic enterprise subscription SAML/OAuth"""

class OAuthAuthManager:
    """Manages OAuth authentication flows"""

    def initiate_auth(provider: str) -> Dict[str, str]:
        """Start OAuth flow, return auth URL"""

    async def handle_callback(provider: str, code: str) -> None:
        """Handle OAuth callback and store token"""

    async def refresh_credentials(provider: str) -> bool:
        """Check if tokens expired, refresh if needed"""
```

**Tasks:**
- [ ] Create `src/myragdb/llm/auth/oauth_auth.py`
- [ ] Implement `OAuthProvider` ABC with provider implementations
- [ ] Implement `OAuthAuthManager` for flow coordination
- [ ] Add callback URL handling
- [ ] Implement token refresh logic
- [ ] Add unit tests with mocked OAuth responses

**Testing:**
- [ ] Test OAuth flow initiation
- [ ] Test callback handling with mock codes
- [ ] Test token refresh
- [ ] Test expired token detection

### 1.3 CLI Device Code Authentication Method
**File:** `src/myragdb/llm/auth/cli_auth.py` (NEW)

```python
# Purpose: Handle device code flow for CLI-based authentication

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DeviceCodeResponse:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int

class CLIAuthManager:
    """Manages device code authentication for CLI"""

    async def request_device_code(provider: str) -> DeviceCodeResponse:
        """Get device code from provider"""

    async def poll_for_token(
        provider: str,
        device_code: str,
        timeout: int = 900
    ) -> Dict[str, Any]:
        """Poll until user authorizes and returns token"""

    async def display_instructions(response: DeviceCodeResponse) -> None:
        """Show user the login instructions"""
```

**Tasks:**
- [ ] Create `src/myragdb/llm/auth/cli_auth.py`
- [ ] Implement device code request for each provider
- [ ] Implement polling logic with exponential backoff
- [ ] Add timeout and error handling
- [ ] Add unit tests with mocked device code responses

**Testing:**
- [ ] Test device code request
- [ ] Test polling mechanism
- [ ] Test timeout handling
- [ ] Test user authorization scenarios

### 1.4 Enhanced CredentialStore
**File:** `src/myragdb/llm/auth_config.py` (ENHANCEMENT)

**Current:** Stores credentials with encryption
**Enhancement:** Add auth method tracking and validation

```python
# Add to existing LLMAuthConfig:

class LLMAuthConfig:
    """Enhanced credential configuration"""

    provider: str              # gemini, chatgpt, claude
    auth_method: str           # api_key, oauth, cli
    credentials: Dict[str, Any]
    expires_at: Optional[datetime]
    created_at: datetime
    last_validated_at: Optional[datetime]

    def is_valid(self) -> bool:
        """Check if credentials are still valid"""
        # Check expiry, validate with provider

    async def validate_with_provider(self) -> bool:
        """Validate by attempting small API call"""

    async def refresh_if_needed(self) -> bool:
        """Refresh if expiry approaching"""
```

**Tasks:**
- [ ] Add auth method field to `LLMAuthConfig`
- [ ] Add validation timestamp tracking
- [ ] Add `is_valid()` method with provider validation
- [ ] Add `refresh_if_needed()` method
- [ ] Update `CredentialStore` to handle all auth types
- [ ] Add comprehensive error handling

**Testing:**
- [ ] Test credential validation for each auth method
- [ ] Test expired credential detection
- [ ] Test automatic refresh
- [ ] Test validation error handling

### 1.5 Unit Tests for Authentication
**File:** `tests/unit/llm/test_auth.py` (NEW)

**Tasks:**
- [ ] Create test suite for API key validation
- [ ] Create test suite for OAuth flows (mocked)
- [ ] Create test suite for CLI device code
- [ ] Create test suite for credential storage
- [ ] Aim for 90%+ code coverage
- [ ] Test error scenarios and edge cases

---

## PHASE 2: Cloud LLM API Endpoints
**Duration:** 10-12 hours | **Dependencies:** Phase 1 (Authentication)
**Status:** ⏳ Not started

### 2.1 SessionManager API Integration
**File:** `src/myragdb/api/server.py` (ENHANCEMENT)

Add new endpoints to existing FastAPI server:

```python
# Endpoint 1: Get current LLM session
@app.get("/llm/session")
async def get_llm_session() -> LLMSessionResponse:
    """Get currently active LLM (local or cloud)"""
    # Returns: provider_type, model_id, auth_method, status

# Endpoint 2: List available providers and models
@app.get("/llm/providers")
async def list_providers() -> ProvidersListResponse:
    """List all available LLM providers (local + cloud)"""
    # Returns: local_models[], cloud_providers with their models

# Endpoint 3: Validate credentials
@app.post("/llm/validate-credentials")
async def validate_credentials(request: ValidateCredentialsRequest) -> ValidateCredentialsResponse:
    """Test API key or subscription credentials"""
    # Request: provider, auth_method, credentials
    # Returns: valid, message, remaining_quota

# Endpoint 4: Switch to different LLM (main switching endpoint)
@app.post("/llm/switch")
async def switch_llm(request: SwitchLLMRequest) -> SwitchLLMResponse:
    """Switch active LLM (local or cloud) - zero restart"""
    # Request: provider, model_id, auth_method, credentials
    # Returns: success, session details, or error
    # Side effect: Updates SessionManager

# Endpoint 5: Get list of authenticated providers
@app.get("/llm/authenticated")
async def list_authenticated_providers() -> AuthenticatedProvidersResponse:
    """List providers user has credentials for"""
    # Returns: list of providers with auth method

# Endpoint 6: Logout from provider
@app.post("/llm/logout/{provider}")
async def logout_provider(provider: str) -> LogoutResponse:
    """Clear credentials for a provider"""
    # Returns: success message
```

**Tasks:**
- [ ] Create `src/myragdb/api/models.py` enhancements for LLM endpoints
  - [ ] `LLMSessionResponse`
  - [ ] `ValidateCredentialsRequest/Response`
  - [ ] `SwitchLLMRequest/Response`
  - [ ] `ProvidersListResponse`
  - [ ] `AuthenticatedProvidersResponse`
  - [ ] `LogoutResponse`
- [ ] Implement all 6 endpoints in `server.py`
- [ ] Add error handling for each endpoint
- [ ] Add request validation with Pydantic
- [ ] Add logging for all operations
- [ ] Integrate with existing SessionManager

**Testing:**
- [ ] Test all endpoints with valid inputs
- [ ] Test all endpoints with invalid inputs
- [ ] Test error responses and status codes
- [ ] Test switching between local and cloud
- [ ] Test credential validation for each provider

### 2.2 Health Check & Monitoring
**File:** `src/myragdb/api/server.py` (ENHANCEMENT)

**Tasks:**
- [ ] Add LLM provider health check to `/health` endpoint
  - Check active LLM connectivity
  - Check credential validity
  - Return provider-specific metrics
- [ ] Create `/llm/health` endpoint for detailed LLM-only health
- [ ] Add monitoring/logging for LLM operations

**Testing:**
- [ ] Test health check with healthy provider
- [ ] Test health check with unavailable provider
- [ ] Test health check with invalid credentials

### 2.3 Integration Tests
**File:** `tests/integration/llm/test_api_endpoints.py` (NEW)

**Tasks:**
- [ ] Test complete flow: validate → switch → use → logout
- [ ] Test error recovery scenarios
- [ ] Test credential persistence across restarts
- [ ] Test session state consistency

---

## PHASE 3: Cloud LLM Web UI
**Duration:** 8-10 hours | **Dependencies:** Phase 2 (API Endpoints)
**Status:** ⏳ Not started

### 3.1 Cloud LLM Dropdown UI Component
**File:** `web-ui/llm-chat-tester.html` (ENHANCEMENT)

**Current State:** Shows only local LLMs
**Enhancement:** Add cloud provider selection

```html
<!-- Replace existing LLM selection with tabs -->
<div class="llm-type-selector">
    <button class="tab-button active" onclick="switchTab('local')">Local LLMs</button>
    <button class="tab-button" onclick="switchTab('cloud')">Cloud LLMs</button>
</div>

<!-- Local LLM Tab (existing) -->
<div id="localLLMTab" class="tab-content active">
    <!-- Existing local model dropdown -->
</div>

<!-- Cloud LLM Tab (new) -->
<div id="cloudLLMTab" class="tab-content" style="display:none;">
    <div class="cloud-llm-controls">
        <div class="control-group">
            <label>Cloud Provider</label>
            <select id="cloudProviderSelect" onchange="handleCloudProviderChange()">
                <option value="">-- Select Provider --</option>
                <option value="gemini">Google Gemini</option>
                <option value="chatgpt">OpenAI ChatGPT</option>
                <option value="claude">Anthropic Claude</option>
            </select>
        </div>

        <div class="control-group">
            <label>Authentication Method</label>
            <select id="authMethodSelect" onchange="handleAuthMethodChange()">
                <option value="">-- Select Method --</option>
                <option value="api_key">API Key</option>
                <option value="oauth">Subscription/OAuth</option>
                <option value="cli">CLI Login</option>
            </select>
        </div>

        <!-- API Key Section -->
        <div id="apiKeySection" class="auth-section" style="display:none;">
            <input type="password" id="apiKeyInput" placeholder="Paste your API key...">
            <small>Your API key is only sent to the local server and never stored in plaintext</small>
            <button onclick="switchToCloudLLM()">Switch to Cloud LLM</button>
        </div>

        <!-- OAuth Section -->
        <div id="oauthSection" class="auth-section" style="display:none;">
            <p>Click below to login with your account</p>
            <button onclick="initiateOAuthLogin()">Login with Account</button>
            <div id="oauthStatus"></div>
        </div>

        <!-- CLI Section -->
        <div id="cliSection" class="auth-section" style="display:none;">
            <p>Run this command in your terminal:</p>
            <code id="cliCommand"></code>
            <button onclick="copyToClipboard('cliCommand')">Copy Command</button>
            <p id="cliStatus">Waiting for CLI login...</p>
        </div>

        <!-- Current Session Display -->
        <div id="sessionInfo" class="session-info" style="display:none;">
            <h4>Active Cloud Session</h4>
            <p>Provider: <span id="activeProvider"></span></p>
            <p>Model: <span id="activeModel"></span></p>
            <p>Auth Method: <span id="activeAuthMethod"></span></p>
            <button onclick="logout()">Logout</button>
        </div>
    </div>
</div>
```

**Tasks:**
- [ ] Create HTML structure for cloud LLM tab
- [ ] Create CSS for cloud controls styling
- [ ] Implement tab switching logic
- [ ] Create form sections for each auth method

### 3.2 Cloud LLM JavaScript Logic
**File:** `web-ui/static/js/cloud-llm.js` (NEW)

```javascript
// Global state
let cloudLLMState = {
    provider: null,
    authMethod: null,
    sessionInfo: null,
    isLoading: false
};

// Tab switching
function switchTab(tabName) {
    // Show/hide local vs cloud tabs
}

// Provider change handler
async function handleCloudProviderChange() {
    const provider = document.getElementById('cloudProviderSelect').value;
    cloudLLMState.provider = provider;

    // Fetch available models for provider
    const response = await fetch(`/llm/providers?provider=${provider}`);
    const models = await response.json();

    // Update UI with available models
    updateAvailableModels(models);
}

// Auth method change handler
function handleAuthMethodChange() {
    const method = document.getElementById('authMethodSelect').value;
    cloudLLMState.authMethod = method;

    // Show appropriate auth section
    document.getElementById('apiKeySection').style.display = method === 'api_key' ? 'block' : 'none';
    document.getElementById('oauthSection').style.display = method === 'oauth' ? 'block' : 'none';
    document.getElementById('cliSection').style.display = method === 'cli' ? 'block' : 'none';
}

// API Key login
async function switchToCloudLLM() {
    const provider = document.getElementById('cloudProviderSelect').value;
    const apiKey = document.getElementById('apiKeyInput').value;

    if (!provider || !apiKey) {
        showError('Please select provider and enter API key');
        return;
    }

    cloudLLMState.isLoading = true;

    try {
        const response = await fetch('/llm/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: provider,
                model_id: 'default', // Let backend choose
                auth_method: 'api_key',
                credentials: { api_key: apiKey }
            })
        });

        const result = await response.json();

        if (result.success) {
            cloudLLMState.sessionInfo = result.session;
            displayActiveSession(result.session);
            showSuccess(`Switched to ${provider}`);
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError(`Failed to switch: ${error.message}`);
    } finally {
        cloudLLMState.isLoading = false;
    }
}

// OAuth login
async function initiateOAuthLogin() {
    const provider = document.getElementById('cloudProviderSelect').value;

    const response = await fetch(`/llm/auth/subscription/${provider}`);
    const { oauth_url } = await response.json();

    // Open OAuth window
    window.location.href = oauth_url;
}

// CLI login with polling
async function initiateCLILogin() {
    const provider = document.getElementById('cloudProviderSelect').value;

    const response = await fetch(`/llm/auth/cli/request`, {
        method: 'POST',
        body: JSON.stringify({ provider })
    });

    const { device_code, user_code, verification_uri } = await response.json();

    // Display instructions
    document.getElementById('cliCommand').textContent =
        `myragdb cli llm login ${provider} --code ${user_code}`;

    // Poll for completion
    pollForCLICompletion(provider, device_code);
}

// Display active session
function displayActiveSession(session) {
    document.getElementById('sessionInfo').style.display = 'block';
    document.getElementById('activeProvider').textContent = session.provider_type;
    document.getElementById('activeModel').textContent = session.model_id;
    document.getElementById('activeAuthMethod').textContent = session.auth_method;

    // Hide auth forms
    document.getElementById('apiKeySection').style.display = 'none';
    document.getElementById('oauthSection').style.display = 'none';
    document.getElementById('cliSection').style.display = 'none';
}

// Logout
async function logout() {
    const provider = cloudLLMState.sessionInfo.provider_type;

    const response = await fetch(`/llm/logout/${provider}`, {
        method: 'POST'
    });

    if (response.ok) {
        cloudLLMState.sessionInfo = null;
        document.getElementById('sessionInfo').style.display = 'none';
        showSuccess(`Logged out from ${provider}`);
    }
}

// Helper: Copy to clipboard
function copyToClipboard(elementId) {
    const text = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(text);
    showSuccess('Copied to clipboard');
}

// Helper: Show error
function showError(message) {
    // Use existing error display
}

// Helper: Show success
function showSuccess(message) {
    // Use existing success display
}
```

**Tasks:**
- [ ] Create `web-ui/static/js/cloud-llm.js`
- [ ] Implement all handler functions
- [ ] Implement API communication
- [ ] Implement polling for CLI completion
- [ ] Add error handling and user feedback
- [ ] Add loading states

### 3.3 CSS Styling
**File:** `web-ui/static/css/cloud-llm.css` (NEW)

**Tasks:**
- [ ] Create cloud LLM specific styles
- [ ] Style tabs and form controls
- [ ] Style session info display
- [ ] Make responsive for mobile
- [ ] Match existing design system

### 3.4 Load Current Session on Page Init
**File:** `web-ui/static/js/app.js` (ENHANCEMENT)

**Tasks:**
- [ ] On page load, call `/llm/session`
- [ ] Display current active LLM (local or cloud)
- [ ] Pre-populate UI with current provider/auth method
- [ ] Show session info if already authenticated

**Testing:**
- [ ] Test UI loads current session
- [ ] Test provider selection
- [ ] Test auth method selection
- [ ] Test API key submission
- [ ] Test OAuth flow (mocked)
- [ ] Test CLI login (mocked)
- [ ] Test logout

---

## PHASE 4: Agent Skills API Endpoints (Foundation)
**Duration:** 12-14 hours | **Dependencies:** None (Agent framework already exists)
**Status:** ⏳ Not started

### 4.1 Workflow Execution Endpoints
**File:** `src/myragdb/api/server.py` (ENHANCEMENT)

```python
# New endpoints for workflow execution:

@app.post("/workflows/execute")
async def execute_workflow(request: WorkflowExecutionRequest) -> WorkflowExecutionResponse:
    """Execute a workflow with parameters"""
    # Request: template_name, parameters, options
    # Returns: execution_id, status, results

@app.post("/workflows/execute-custom")
async def execute_custom_workflow(request: CustomWorkflowRequest) -> WorkflowExecutionResponse:
    """Execute a custom workflow (not from template)"""
    # Request: workflow definition (steps, skills, variables)
    # Returns: execution results

@app.get("/workflows/execution/{execution_id}")
async def get_execution_status(execution_id: str) -> ExecutionStatusResponse:
    """Get status and progress of running/completed execution"""
    # Returns: status, progress, partial_results, errors

@app.get("/workflows/history")
async def get_execution_history(
    limit: int = 50,
    offset: int = 0,
    filter_by: Optional[str] = None
) -> ExecutionHistoryResponse:
    """Get history of workflow executions"""
    # Returns: list of past executions with results
```

**Tasks:**
- [ ] Create Pydantic models:
  - [ ] `WorkflowExecutionRequest`
  - [ ] `CustomWorkflowRequest`
  - [ ] `WorkflowExecutionResponse`
  - [ ] `ExecutionStatusResponse`
  - [ ] `ExecutionHistoryResponse`
- [ ] Integrate with existing `AgentOrchestrator`
- [ ] Implement execution ID tracking
- [ ] Add parameter validation
- [ ] Add error handling
- [ ] Add request logging

### 4.2 Template Discovery Endpoints
**File:** `src/myragdb/api/server.py` (ENHANCEMENT)

```python
@app.get("/templates")
async def list_templates() -> TemplatesListResponse:
    """List all available workflow templates"""
    # Returns: template_name, description, parameters

@app.get("/templates/{template_name}")
async def get_template_details(template_name: str) -> TemplateDetailsResponse:
    """Get detailed info about a template"""
    # Returns: full template definition, schema, example execution

@app.get("/templates/validate")
async def validate_template(request: ValidateTemplateRequest) -> ValidateTemplateResponse:
    """Validate template syntax and parameter compatibility"""
    # Returns: valid, errors, warnings
```

**Tasks:**
- [ ] Create Pydantic models for template responses
- [ ] Integrate with `TemplateEngine` for discovery
- [ ] Implement template validation logic
- [ ] Add template schema exposition
- [ ] Add example execution data

### 4.3 Skill Discovery Endpoints
**File:** `src/myragdb/api/server.py` (ENHANCEMENT)

```python
@app.get("/skills")
async def list_skills() -> SkillsListResponse:
    """List all available skills"""
    # Returns: skill_name, description, input_schema, output_schema

@app.get("/skills/{skill_name}")
async def get_skill_details(skill_name: str) -> SkillDetailsResponse:
    """Get detailed info about a skill"""
    # Returns: full schema, examples, error types

@app.post("/skills/validate")
async def validate_skill_input(request: ValidateSkillRequest) -> ValidateSkillResponse:
    """Validate input against skill's input schema"""
    # Returns: valid, errors
```

**Tasks:**
- [ ] Create Pydantic models for skill responses
- [ ] Integrate with `SkillRegistry` for discovery
- [ ] Implement schema exposition
- [ ] Add example inputs/outputs
- [ ] Add validation endpoint

### 4.4 Execution History & Monitoring
**File:** `src/myragdb/db/execution_history.py` (NEW)

```python
# Purpose: Track workflow executions for history/monitoring

from sqlalchemy import Column, String, DateTime, JSON, Integer
from datetime import datetime

class ExecutionRecord:
    """Stores workflow execution history"""

    id: str              # Unique execution ID
    template_name: str   # Which template was executed
    status: str          # running, completed, failed
    started_at: datetime
    completed_at: Optional[datetime]
    parameters: Dict     # Input parameters
    results: Dict        # Execution results
    errors: List[str]    # Any errors encountered
    duration_ms: int     # Total execution time
```

**Tasks:**
- [ ] Create `src/myragdb/db/execution_history.py`
- [ ] Create SQLite table schema for execution records
- [ ] Implement execution tracking in `WorkflowEngine`
- [ ] Implement history retrieval methods
- [ ] Add pagination support
- [ ] Add filtering by template/status/date

### 4.5 Integration Tests
**File:** `tests/integration/agent/test_workflow_api.py` (NEW)

**Tasks:**
- [ ] Test workflow execution via API
- [ ] Test template discovery
- [ ] Test skill discovery
- [ ] Test execution history
- [ ] Test error scenarios
- [ ] Test concurrent executions

---

## PHASE 5: Agent Skills CLI Commands
**Duration:** 8-10 hours | **Dependencies:** Phase 4 (API Endpoints)
**Status:** ⏳ Not started

### 5.1 Workflow CLI Commands
**File:** `src/myragdb/cli.py` (ENHANCEMENT)

```bash
# Add new command group for workflows:

@click.group()
def workflows():
    """Manage and execute workflows"""
    pass

@workflows.command()
def list():
    """List all available workflows"""
    # Call GET /templates
    # Display as table with name, description, parameter count

@workflows.command()
@click.argument('template_name')
def info(template_name):
    """Show detailed info about a workflow"""
    # Call GET /templates/{template_name}
    # Display template definition, parameters, example

@workflows.command()
@click.argument('template_name')
@click.option('--param', multiple=True, help='Template parameter (key=value)')
def execute(template_name, param):
    """Execute a workflow with parameters"""
    # Parse parameters: --param name=John --param age=30
    # Call POST /workflows/execute
    # Show real-time progress
    # Display results

@workflows.command()
def history():
    """Show workflow execution history"""
    # Call GET /workflows/history
    # Display as table with execution ID, template, status, timestamp

@workflows.command()
@click.argument('execution_id')
def status(execution_id):
    """Check status of running/completed execution"""
    # Call GET /workflows/execution/{execution_id}
    # Display status, progress, partial results
```

**Tasks:**
- [ ] Add `@click.group()` for workflows in `cli.py`
- [ ] Implement `list()` command with table formatting
- [ ] Implement `info()` command with schema display
- [ ] Implement `execute()` command with parameter parsing
  - [ ] Parameter parsing from `--param key=value` format
  - [ ] Real-time progress display (polling /workflows/execution/{id})
  - [ ] Result formatting (table/JSON output)
- [ ] Implement `history()` command with pagination
- [ ] Implement `status()` command with progress bar
- [ ] Add error handling for all commands

### 5.2 Skills CLI Commands
**File:** `src/myragdb/cli.py` (ENHANCEMENT)

```bash
@click.group()
def skills():
    """Manage available skills"""
    pass

@skills.command()
def list():
    """List all available skills"""
    # Call GET /skills
    # Display as table with skill name, description, required params

@skills.command()
@click.argument('skill_name')
def info(skill_name):
    """Show detailed info about a skill"""
    # Call GET /skills/{skill_name}
    # Display full schema, examples, error types
```

**Tasks:**
- [ ] Add `@click.group()` for skills in `cli.py`
- [ ] Implement `list()` command
- [ ] Implement `info()` command with schema display
- [ ] Format output for readability

### 5.3 Template Management CLI Commands
**File:** `src/myragdb/cli.py` (ENHANCEMENT)

```bash
@workflows.command()
@click.argument('template_file')
def validate(template_file):
    """Validate a workflow template file"""
    # Load template from file
    # Call POST /templates/validate
    # Display validation results

@workflows.command()
@click.argument('template_file')
def create(template_file):
    """Create a new workflow template"""
    # Interactive template creation wizard
    # Save to templates directory
```

**Tasks:**
- [ ] Implement `validate()` command for template files
- [ ] Implement `create()` command with wizard
- [ ] Add template file validation

### 5.4 Testing
**File:** `tests/integration/cli/test_workflow_commands.py` (NEW)

**Tasks:**
- [ ] Test workflow list command
- [ ] Test workflow execute command
- [ ] Test parameter parsing
- [ ] Test error handling
- [ ] Test output formatting

---

## PHASE 6: Advanced Skills Implementation
**Duration:** 20-24 hours | **Dependencies:** Phase 1 (Cloud Auth)
**Status:** ⏳ Not started

### 6.1 DataVisualization Skill
**File:** `src/myragdb/agent/skills/data_visualization_skill.py` (NEW)

```python
from myragdb.agent.skills import Skill
from typing import Dict, Any, List, Optional

class DataVisualizationSkill(Skill):
    """Generate interactive charts and visualizations"""

    def __init__(self):
        super().__init__(
            name="data_visualization",
            description="Generate charts, graphs, and visual analytics from data"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "chart_type": {
                "type": "string",
                "required": True,
                "enum": ["line", "bar", "pie", "doughnut", "scatter", "bubble", "radar", "heatmap"],
                "description": "Type of chart to generate"
            },
            "title": {
                "type": "string",
                "required": True,
                "description": "Chart title"
            },
            "labels": {
                "type": "array",
                "required": False,
                "description": "X-axis or category labels"
            },
            "datasets": {
                "type": "array",
                "required": True,
                "description": "Data series"
            },
            "export_format": {
                "type": "string",
                "required": False,
                "enum": ["json", "html", "svg", "png"],
                "default": "html",
                "description": "Output format"
            }
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualization"""
        # Validate inputs
        # Generate chart with Chart.js or matplotlib
        # Export in requested format
        # Return chart data/HTML/image
```

**Tasks:**
- [ ] Create `src/myragdb/agent/skills/data_visualization_skill.py`
- [ ] Implement chart generation for all types
- [ ] Support Chart.js for HTML/interactive output
- [ ] Support matplotlib for PNG/SVG output
- [ ] Implement export format conversion
- [ ] Add styling/theming options
- [ ] Test with various data types

**Testing:**
- [ ] Test each chart type
- [ ] Test each export format
- [ ] Test with large datasets
- [ ] Test error handling

### 6.2 Code Generation Skill
**File:** `src/myragdb/agent/skills/code_generation_skill.py` (NEW)

```python
class CodeGenerationSkill(Skill):
    """Generate, refactor, and optimize code"""

    def __init__(self):
        super().__init__(
            name="code_generation",
            description="Generate, refactor, test, and document code"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "language": {
                "type": "string",
                "required": True,
                "enum": ["python", "javascript", "typescript", "java", "go", "rust", "cpp", "sql"],
                "description": "Programming language"
            },
            "action": {
                "type": "string",
                "required": True,
                "enum": ["generate", "refactor", "generate_tests", "format", "document", "optimize"],
                "description": "What to do with the code"
            },
            "code": {
                "type": "string",
                "required": False,
                "description": "Existing code (for refactor, optimize, document)"
            },
            "description": {
                "type": "string",
                "required": False,
                "description": "What code to generate (for generate action)"
            },
            "context": {
                "type": "object",
                "required": False,
                "description": "Additional context for generation"
            }
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate or process code using LLM"""
        # Call active LLM for code generation/processing
        # Format output appropriately
        # Return generated code with metadata
```

**Tasks:**
- [ ] Create `src/myragdb/agent/skills/code_generation_skill.py`
- [ ] Implement code generation action
- [ ] Implement code refactoring action
- [ ] Implement test generation action
- [ ] Implement code formatting action
- [ ] Implement documentation generation action
- [ ] Implement code optimization action
- [ ] Integrate with active LLM (cloud or local)

**Testing:**
- [ ] Test each action
- [ ] Test each language
- [ ] Test with various code styles
- [ ] Test error handling

### 6.3 Slack Integration Skill
**File:** `src/myragdb/agent/skills/slack_integration_skill.py` (NEW)

```python
class SlackIntegrationSkill(Skill):
    """Send messages and notifications to Slack"""

    def __init__(self):
        super().__init__(
            name="slack_integration",
            description="Send messages, files, and notifications to Slack"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "webhook_url": {
                "type": "string",
                "required": True,
                "description": "Slack webhook URL"
            },
            "message": {
                "type": "string",
                "required": True,
                "description": "Message text"
            },
            "channel": {
                "type": "string",
                "required": False,
                "description": "Target channel (overrides webhook)"
            },
            "attachments": {
                "type": "array",
                "required": False,
                "description": "Slack message attachments"
            },
            "thread_ts": {
                "type": "string",
                "required": False,
                "description": "Thread timestamp (for replies)"
            }
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to Slack"""
        # Validate webhook URL
        # Format message and attachments
        # POST to Slack webhook
        # Return response with message TS and channel
```

**Tasks:**
- [ ] Create `src/myragdb/agent/skills/slack_integration_skill.py`
- [ ] Implement Slack webhook messaging
- [ ] Support formatted messages (blocks format)
- [ ] Support file uploads
- [ ] Support threaded messages
- [ ] Implement error handling for Slack API errors
- [ ] Add credential/webhook storage

**Testing:**
- [ ] Test message sending with mock webhook
- [ ] Test formatting
- [ ] Test error handling

### 6.4 Webhook Integration Skill
**File:** `src/myragdb/agent/skills/webhook_integration_skill.py` (NEW)

```python
class WebhookIntegrationSkill(Skill):
    """Call external APIs and webhooks"""

    def __init__(self):
        super().__init__(
            name="webhook_integration",
            description="Call external HTTP endpoints and APIs"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "url": {
                "type": "string",
                "required": True,
                "description": "Webhook/API URL"
            },
            "method": {
                "type": "string",
                "required": False,
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "default": "POST",
                "description": "HTTP method"
            },
            "headers": {
                "type": "object",
                "required": False,
                "description": "Custom headers"
            },
            "payload": {
                "type": "object",
                "required": False,
                "description": "Request body"
            },
            "timeout": {
                "type": "integer",
                "required": False,
                "default": 30,
                "description": "Request timeout in seconds"
            }
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call webhook/API"""
        # Validate URL
        # Prepare request
        # Make HTTP request with timeout
        # Parse and return response
```

**Tasks:**
- [ ] Create `src/myragdb/agent/skills/webhook_integration_skill.py`
- [ ] Implement HTTP request handling (async)
- [ ] Support all HTTP methods
- [ ] Support custom headers and auth
- [ ] Implement response parsing
- [ ] Add timeout handling
- [ ] Implement error handling

**Testing:**
- [ ] Test each HTTP method
- [ ] Test custom headers
- [ ] Test timeout handling
- [ ] Test error responses

### 6.5 Update SkillRegistry
**File:** `src/myragdb/agent/skills/registry.py` (ENHANCEMENT)

**Tasks:**
- [ ] Register all 4 new advanced skills
- [ ] Update skill discovery to include new skills
- [ ] Test skill discovery endpoints return all skills

---

## PHASE 7: Example Templates & Template Library
**Duration:** 10-12 hours | **Dependencies:** Phase 6 (Advanced Skills)
**Status:** ⏳ Not started

### 7.1 Create Templates Directory Structure
**Directory:** `src/myragdb/templates/` (NEW)

```
templates/
├── code_search.yaml
├── code_analysis.yaml
├── code_review.yaml
├── documentation_generation.yaml
├── error_analysis.yaml
├── performance_analysis.yaml
├── security_audit.yaml
├── data_analysis.yaml
├── integration_testing.yaml
└── compliance_report.yaml
```

**Tasks:**
- [ ] Create `src/myragdb/templates/` directory
- [ ] Create `templates/` directory at project root for user templates

### 7.2 Template 1: Code Search
**File:** `src/myragdb/templates/code_search.yaml`

```yaml
name: "code_search"
description: "Search for code across repositories"
parameters:
  query:
    type: string
    required: true
    description: "What to search for"
  repository:
    type: string
    required: false
    description: "Limit to specific repository"
  file_type:
    type: string
    required: false
    description: "Filter by file type (.py, .js, etc.)"

steps:
  - id: search
    skill: search
    input:
      query: "{{ query }}"
      repositories: ["{{ repository }}"]
      file_types: ["{{ file_type }}"]
      limit: 20

  - id: format_results
    skill: report
    input:
      format: markdown
      search_results: "{{ search.results }}"
      title: "Code Search Results"

output:
  results: "{{ search.results }}"
  report: "{{ format_results.output }}"
```

**Tasks:**
- [ ] Create all 10 template YAML files
- [ ] Each template should demonstrate different skill combinations
- [ ] Include comprehensive parameter documentation
- [ ] Include example usage
- [ ] Add error handling strategies

### 7.3 Template 2-10: Create Remaining Templates
- [ ] Code Analysis Template
- [ ] Code Review Template
- [ ] Documentation Generation Template
- [ ] Error Analysis Template
- [ ] Performance Analysis Template
- [ ] Security Audit Template
- [ ] Data Analysis Template
- [ ] Integration Testing Template
- [ ] Compliance Report Template

**Tasks for each template:**
- [ ] Define clear purpose and use case
- [ ] Design parameter schema
- [ ] Create workflow steps using available skills
- [ ] Add error handling
- [ ] Document with examples

### 7.4 Built-in Template Library
**File:** `src/myragdb/agent/templates/library.py` (ENHANCEMENT)

**Tasks:**
- [ ] Update TemplateLibrary to auto-load built-in templates
- [ ] Support user-provided template directory
- [ ] Test template discovery includes all 10 templates

### 7.5 Template Documentation
**File:** `TEMPLATE_REFERENCE.md` (NEW)

**Tasks:**
- [ ] Document each template with:
  - [ ] Purpose and use cases
  - [ ] Required parameters
  - [ ] Example execution
  - [ ] Output structure
  - [ ] Customization tips

---

## PHASE 8: Documentation & Testing
**Duration:** 12-14 hours | **Dependencies:** All previous phases
**Status:** ⏳ Not started

### 8.1 API Reference Documentation
**File:** `API_REFERENCE_UPDATED.md` (ENHANCEMENT/NEW)

**Add sections for:**
- [ ] LLM Session Management endpoints (POST /llm/switch, GET /llm/session, etc.)
- [ ] Workflow Execution endpoints (POST /workflows/execute, GET /workflows/history, etc.)
- [ ] Template Discovery endpoints (GET /templates, GET /templates/{name})
- [ ] Skill Discovery endpoints (GET /skills, GET /skills/{name})
- [ ] Request/response examples for each endpoint
- [ ] Error codes and handling
- [ ] Authentication methods documentation

**Tasks:**
- [ ] Write comprehensive API reference
- [ ] Include cURL examples for all endpoints
- [ ] Include Python client examples
- [ ] Add troubleshooting section

### 8.2 CLI Reference Guide
**File:** `CLI_REFERENCE_UPDATED.md` (ENHANCEMENT/NEW)

**Document:**
- [ ] `myragdb llm` commands (login, switch, status, logout)
- [ ] `myragdb workflows` commands (list, execute, history, status)
- [ ] `myragdb skills` commands (list, info)
- [ ] Parameter specifications for each command
- [ ] Example command executions
- [ ] Common use cases

**Tasks:**
- [ ] Write comprehensive CLI reference
- [ ] Include real command examples
- [ ] Add troubleshooting tips

### 8.3 Skill Development Tutorial
**File:** `SKILL_DEVELOPMENT_TUTORIAL.md` (ENHANCEMENT)

**Enhance existing guide with:**
- [ ] Step-by-step skill creation walkthrough
- [ ] Real examples building a simple skill
- [ ] Testing skills locally
- [ ] Registering custom skills
- [ ] Publishing skills

**Tasks:**
- [ ] Create comprehensive tutorial
- [ ] Include working code examples
- [ ] Test tutorial instructions work end-to-end

### 8.4 Template Creation Guide
**File:** `TEMPLATE_CREATION_GUIDE.md` (NEW)

**Cover:**
- [ ] Template YAML structure
- [ ] Skill composition patterns
- [ ] Parameter definition
- [ ] Variable interpolation
- [ ] Error handling in templates
- [ ] Testing templates

**Tasks:**
- [ ] Write template creation guide
- [ ] Include 3-4 detailed examples
- [ ] Cover best practices

### 8.5 Error Handling & Troubleshooting
**File:** `TROUBLESHOOTING_GUIDE.md` (NEW)

**Cover common issues:**
- [ ] Invalid API credentials
- [ ] LLM provider connection errors
- [ ] Workflow execution failures
- [ ] Skill validation errors
- [ ] Template parsing errors
- [ ] Performance issues

**Tasks:**
- [ ] Write troubleshooting guide
- [ ] Include debugging tips
- [ ] Add common solutions

### 8.6 Comprehensive Test Suite
**File:** `tests/integration/` (NEW)

**Create tests for:**
- [ ] Complete user flows (auth → switch → use)
- [ ] Workflow execution end-to-end
- [ ] All skill operations
- [ ] Template parsing and execution
- [ ] Error scenarios and recovery
- [ ] Concurrent operations

**Tasks:**
- [ ] Write 50+ integration tests
- [ ] Achieve 85%+ code coverage
- [ ] Test error paths
- [ ] Test edge cases
- [ ] Document test approach

### 8.7 Update Main README
**File:** `README.md` (ENHANCEMENT)

**Add sections:**
- [ ] Cloud LLM Integration overview
- [ ] Skills & Agents platform overview
- [ ] Quick start for each feature
- [ ] Links to detailed documentation
- [ ] Architecture diagrams

**Tasks:**
- [ ] Update README with new features
- [ ] Add feature overview sections
- [ ] Add links to detailed docs
- [ ] Include visual diagrams

### 8.8 Final Integration & Validation
**Tasks:**
- [ ] Test complete user journey: local → cloud LLM switching
- [ ] Test complete agent journey: execute workflow → get results
- [ ] Test all documentation examples work
- [ ] Performance testing and optimization
- [ ] Security review of all new code
- [ ] Code quality review

---

## Implementation Checklist by Phase

### Phase 1: Cloud Authentication (8-10 hours) ⏳
- [ ] Create auth module structure
- [ ] Implement API key validation
- [ ] Implement OAuth flow setup
- [ ] Implement CLI device code
- [ ] Enhance CredentialStore
- [ ] Write unit tests
- **Commit:** "feat: implement cloud authentication methods (API key, OAuth, CLI)"

### Phase 2: Cloud LLM API Endpoints (10-12 hours) ⏳
- [ ] Create LLM API models
- [ ] Implement all 6 endpoints
- [ ] Add error handling
- [ ] Add logging
- [ ] Write integration tests
- **Commit:** "feat: implement cloud LLM API endpoints for zero-restart switching"

### Phase 3: Cloud LLM Web UI (8-10 hours) ⏳
- [ ] Create HTML structure
- [ ] Create CSS styles
- [ ] Create JavaScript logic
- [ ] Load current session on init
- [ ] Test all flows
- **Commit:** "feat: implement cloud LLM web UI with provider selection and auth"

### Phase 4: Agent Skills API Endpoints (12-14 hours) ⏳
- [ ] Create workflow execution endpoints
- [ ] Create template discovery endpoints
- [ ] Create skill discovery endpoints
- [ ] Create execution history tracking
- [ ] Write integration tests
- **Commit:** "feat: implement agent workflow and skill API endpoints"

### Phase 5: Agent Skills CLI Commands (8-10 hours) ⏳
- [ ] Create workflow commands
- [ ] Create skills commands
- [ ] Create template management commands
- [ ] Test all commands
- **Commit:** "feat: implement workflow and skill CLI commands"

### Phase 6: Advanced Skills (20-24 hours) ⏳
- [ ] Implement DataVisualization skill
- [ ] Implement CodeGeneration skill
- [ ] Implement SlackIntegration skill
- [ ] Implement WebhookIntegration skill
- [ ] Update SkillRegistry
- [ ] Test all skills
- **Commit:** "feat: implement advanced skills (visualization, code gen, integrations)"

### Phase 7: Example Templates (10-12 hours) ⏳
- [ ] Create 10 example templates
- [ ] Document each template
- [ ] Create template reference guide
- [ ] Test template discovery
- **Commit:** "feat: add 10 example workflow templates and template library"

### Phase 8: Documentation & Testing (12-14 hours) ⏳
- [ ] Update API reference
- [ ] Create CLI reference
- [ ] Create skill development tutorial
- [ ] Create template creation guide
- [ ] Create troubleshooting guide
- [ ] Write comprehensive tests
- [ ] Update README
- **Final Commit:** "docs: comprehensive documentation and final testing"

---

## Dependency Summary

```
Phase 1 (Auth) ─────────┐
                        ├──→ Phase 2 (API) ─────┐
                        │                       ├──→ Phase 3 (UI)
Phase 4 (Skills API) ───────────────────────────┤
                                                ├──→ Phase 5 (CLI) ─┐
                                    Phase 6 (Advanced Skills) ─────┤
                                                      │             ├──→ Phase 7 (Templates)
                                                      └─────────────┘
                                                            │
                                                            ├──→ Phase 8 (Docs & Tests)
```

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API credential leaks | Low | High | Enforce encryption, no logging, .env fallback |
| LLM provider downtime | Medium | Medium | Fallback to local LLM, health checks, retry logic |
| Concurrent executions | Medium | Medium | Execution ID tracking, state isolation |
| Template syntax errors | Medium | Low | Validation endpoint, comprehensive testing |
| Large workflow results | Low | Medium | Streaming responses, result pagination |

---

## Success Criteria

### Phase 1-3: Cloud GLLM Complete
- ✅ Users can switch between local and cloud LLMs without restart
- ✅ Three auth methods working (API key, OAuth, CLI)
- ✅ Web UI shows current active LLM
- ✅ No breaking changes to existing code

### Phase 4-5: Agent Skills Exposed
- ✅ Users can execute workflows via API
- ✅ Users can execute workflows via CLI
- ✅ All skills discoverable
- ✅ All templates discoverable

### Phase 6-7: Advanced Features
- ✅ 4 new advanced skills functional
- ✅ 10 example templates provided
- ✅ Users can build custom skills
- ✅ Users can build custom templates

### Phase 8: Production Ready
- ✅ Comprehensive documentation
- ✅ 85%+ test coverage
- ✅ Zero performance regression
- ✅ All examples work end-to-end

---

## Effort Estimation

| Phase | Tasks | Hours | Week |
|-------|-------|-------|------|
| 1 | Auth Methods | 8-10 | Week 1 |
| 2 | API Endpoints | 10-12 | Week 1-2 |
| 3 | Web UI | 8-10 | Week 2 |
| 4 | Skills API | 12-14 | Week 2-3 |
| 5 | Skills CLI | 8-10 | Week 3 |
| 6 | Advanced Skills | 20-24 | Week 3-4 |
| 7 | Templates | 10-12 | Week 4 |
| 8 | Docs & Tests | 12-14 | Week 4-5 |
| **TOTAL** | **83 tasks** | **120-150 hours** | **5 weeks** |

---

**Questions:** libor@arionetworks.com
