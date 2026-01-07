# Cloud LLM Integration Architecture
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/CLOUD_LLM_ARCHITECTURE.md
**Description:** High-level architecture for integrating cloud-based LLMs (Gemini, ChatGPT, Claude) with API, subscription, and CLI access methods
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Executive Summary

This document outlines a **zero-downtime, dynamic LLM switching architecture** that adds cloud LLM support (Google Gemini, OpenAI ChatGPT, Anthropic Claude) alongside existing local LLMs. The system enables users to:

- **Switch between local and cloud LLMs** without restarting
- **Access via three methods**: API keys, subscription service, or CLI
- **Maintain seamless continuity** with existing system while adding cloud capabilities

---

## 1. Current State Analysis

### Existing Architecture
```
Local LLMs Only (10 models on ports 8081-8092)
    ↓
Fixed Port Mapping (Hardcoded in llm_router.py)
    ↓
Restart Required for Model Changes
    ↓
No Cloud Provider Support
```

### Key Limitation
**Current bottleneck:** Model selection requires server restart because:
1. Port bindings are hardcoded at startup
2. LLM instances run as separate OS processes
3. UI only selects from pre-started servers

---

## 2. Proposed Architecture

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                           │
├──────────────────────┬──────────────────┬──────────────────────┤
│  Web UI (React)      │  CLI Client      │   Agent Library      │
│  - Model Dropdown    │  - Python CLI    │   - SearchClient     │
│  - Config Panel      │  - Direct calls  │   - Runtime access   │
└──────────────────────┴──────────────────┴──────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  New: Session Manager                                            │
│  - Tracks active LLM session (local or cloud)                   │
│  - No restarts needed for switching                              │
│                                                                   │
│  New: Cloud LLM Provider Manager                                │
│  - Abstraction layer for 3 cloud providers                       │
│  - Authentication & credential management                       │
│  - Dynamic instantiation without OS process overhead            │
│                                                                   │
│  Existing: LLM Router                                            │
│  - Routes to local LLMs (ports 8081-8092)                       │
│  - Task-based intelligent selection                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│              LLM Provider Abstraction Layer                       │
├──────────────────┬──────────────────┬───────────────────────────┤
│ Local LLMs       │ Cloud Providers  │ Provider Registry         │
│ (llama.cpp)      │ ┌──────────────┐ │                           │
│                  │ │ Gemini API   │ │ - Discoverable providers  │
│                  │ │ ChatGPT API  │ │ - Dynamic loading         │
│                  │ │ Claude API   │ │ - Fallback logic          │
│                  │ └──────────────┘ │                           │
└──────────────────┴──────────────────┴───────────────────────────┘
```

### 2.2 Core Components

#### A. **LLM Session Manager** (New)
Manages the currently active LLM without requiring process restarts.

```python
# src/myragdb/llm/session_manager.py

class LLMSession:
    """Represents currently active LLM (local or cloud)"""

    - provider_type: str  # "local", "gemini", "chatgpt", "claude"
    - model_id: str       # Model identifier
    - config: Dict        # Provider-specific config
    - auth_method: str    # "api_key", "subscription", "cli"
    - created_at: datetime
    - health_check()      # Verify connectivity

class SessionManager:
    """Manages LLM sessions dynamically"""

    def switch_llm(model_id, provider, auth_config):
        """Switch active LLM without restart"""
        # 1. Validate credentials
        # 2. Test connectivity
        # 3. Update session
        # Return: Success/failure with error details

    def get_active_session() -> LLMSession:
        """Get current active LLM"""

    def list_available_models(provider_type):
        """List models user can switch to"""
```

#### B. **Cloud LLM Provider Abstraction** (New)
Unified interface for all cloud providers.

```python
# src/myragdb/llm/providers/base_provider.py

class CloudLLMProvider(ABC):
    """Abstract base for cloud LLM providers"""

    @abstractmethod
    async def validate_credentials(config: Dict) -> bool:
        """Test API key or subscription"""

    @abstractmethod
    async def list_models() -> List[ModelInfo]:
        """Get available models"""

    @abstractmethod
    async def generate(prompt: str, model_id: str) -> str:
        """Generate response"""

    @abstractmethod
    async def stream(prompt: str, model_id: str) -> AsyncIterator[str]:
        """Stream response tokens"""

# src/myragdb/llm/providers/gemini_provider.py
class GeminiProvider(CloudLLMProvider):
    def __init__(self, api_key: str = None, subscription_enabled: bool = False):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.subscription_enabled = subscription_enabled
        self.client = genai.Client(api_key=self.api_key)

    # Implementation for Gemini API

# src/myragdb/llm/providers/chatgpt_provider.py
class ChatGPTProvider(CloudLLMProvider):
    def __init__(self, api_key: str = None, subscription_enabled: bool = False):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.subscription_enabled = subscription_enabled
        self.client = OpenAI(api_key=self.api_key)

    # Implementation for ChatGPT API

# src/myragdb/llm/providers/claude_provider.py
class ClaudeProvider(CloudLLMProvider):
    def __init__(self, api_key: str = None, subscription_enabled: bool = False):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.subscription_enabled = subscription_enabled
        self.client = Anthropic(api_key=self.api_key)

    # Implementation for Claude API

# src/myragdb/llm/providers/provider_registry.py
class ProviderRegistry:
    PROVIDERS = {
        "gemini": GeminiProvider,
        "chatgpt": ChatGPTProvider,
        "claude": ClaudeProvider,
    }

    @classmethod
    def get_provider(provider_name: str) -> CloudLLMProvider:
        """Factory method to instantiate provider"""
```

#### C. **Auth Configuration Manager** (New)
Handles three access methods: API key, subscription, CLI.

```python
# src/myragdb/llm/auth_config.py

class AuthMethod(Enum):
    API_KEY = "api_key"           # Direct API key
    SUBSCRIPTION = "subscription" # Account/subscription-based
    CLI = "cli"                   # Via CLI login flow

class LLMAuthConfig:
    """Credentials for accessing cloud LLMs"""

    - provider: str              # "gemini", "chatgpt", "claude"
    - auth_method: AuthMethod
    - credentials: Dict          # Provider-specific creds
    - expires_at: Optional[datetime]  # For subscription tokens

    def is_valid() -> bool:
        """Check if credentials are still valid"""

    def refresh() -> bool:
        """Refresh credentials if needed"""

class CredentialStore:
    """Secure storage for LLM credentials"""

    def save_credentials(provider, auth_config):
        """Store in encrypted file or .env"""

    def load_credentials(provider) -> LLMAuthConfig:
        """Retrieve stored credentials"""

    def delete_credentials(provider):
        """Clear stored credentials"""
```

---

## 3. Implementation: Three Access Methods

### 3.1 Method 1: Direct API Key Access

**Use Case:** User has personal API keys for Gemini, ChatGPT, or Claude

#### API Endpoint
```
POST /llm/switch
{
    "provider": "gemini",
    "model_id": "gemini-pro",
    "auth_method": "api_key",
    "credentials": {
        "api_key": "your-api-key-here"
    }
}

Response:
{
    "success": true,
    "session": {
        "provider_type": "gemini",
        "model_id": "gemini-pro",
        "auth_method": "api_key",
        "status": "active"
    }
}
```

#### Web UI Implementation
```html
<!-- web-ui/llm-chat-tester.html -->

<div class="controls">
    <div class="control-group">
        <label>LLM Type</label>
        <select id="llmTypeDropdown" onchange="handleLLMTypeChange()">
            <option value="local">Local LLMs</option>
            <option value="cloud">Cloud LLMs</option>
        </select>
    </div>

    <!-- Local LLMs Section (existing) -->
    <div id="localLLMSection" class="control-group">
        <label>Local Model</label>
        <select id="localModelDropdown"></select>
        <button onclick="startLocalLLM()">Start</button>
    </div>

    <!-- Cloud LLMs Section (new) -->
    <div id="cloudLLMSection" style="display:none;" class="control-group">
        <label>Cloud Provider</label>
        <select id="cloudProviderDropdown" onchange="handleProviderChange()">
            <option value="gemini">Google Gemini</option>
            <option value="chatgpt">OpenAI ChatGPT</option>
            <option value="claude">Anthropic Claude</option>
        </select>

        <label>Authentication Method</label>
        <select id="authMethodDropdown" onchange="handleAuthMethodChange()">
            <option value="api_key">API Key</option>
            <option value="subscription">Subscription</option>
            <option value="cli">CLI Login</option>
        </select>

        <!-- API Key Section -->
        <div id="apiKeySection">
            <input type="password" id="apiKeyInput" placeholder="Enter API Key">
            <button onclick="switchToCloudLLM()">Switch to Cloud LLM</button>
        </div>

        <!-- Subscription Section -->
        <div id="subscriptionSection" style="display:none;">
            <button onclick="handleSubscriptionLogin()">Login with Account</button>
        </div>

        <!-- CLI Section -->
        <div id="cliSection" style="display:none;">
            <button onclick="handleCLILogin()">Login via CLI</button>
            <code id="cliCommand"></code>
        </div>
    </div>
</div>
```

#### JavaScript Implementation
```javascript
// web-ui/static/js/cloud-llm.js

async function switchToCloudLLM() {
    const provider = document.getElementById('cloudProviderDropdown').value;
    const authMethod = document.getElementById('authMethodDropdown').value;
    const apiKey = document.getElementById('apiKeyInput').value;

    const response = await fetch('/llm/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            provider: provider,
            model_id: getDefaultModelForProvider(provider),
            auth_method: authMethod,
            credentials: { api_key: apiKey }
        })
    });

    const result = await response.json();
    if (result.success) {
        displayActiveSession(result.session);
        // No restart needed - chat is ready immediately
    } else {
        showError(result.error);
    }
}
```

### 3.2 Method 2: Subscription-Based Access

**Use Case:** Organization uses subscription service with managed credentials

#### API Endpoint
```
POST /llm/switch
{
    "provider": "chatgpt",
    "model_id": "gpt-4",
    "auth_method": "subscription",
    "credentials": {
        "org_id": "org-123",
        "api_base": "https://api.company.com/openai"
    }
}
```

#### Web UI Implementation
```html
<button onclick="handleSubscriptionLogin()">
    Login with ChatGPT Enterprise
</button>

<script>
async function handleSubscriptionLogin() {
    // Redirect to OAuth/SAML login
    window.location.href = '/llm/auth/subscription/chatgpt';
}

// After successful login (via callback):
async function completeSubscriptionAuth(provider, token, org_id) {
    const response = await fetch('/llm/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            provider: provider,
            model_id: getDefaultModelForProvider(provider),
            auth_method: 'subscription',
            credentials: {
                access_token: token,
                org_id: org_id,
                api_base: getSubscriptionAPIBase(provider)
            }
        })
    });
}
</script>
```

#### Backend Implementation
```python
# src/myragdb/api/server.py

@app.post("/llm/auth/subscription/{provider}")
async def initiate_subscription_auth(provider: str):
    """Start OAuth/SAML flow for subscription-based auth"""

    if provider == "chatgpt":
        oauth_url = f"https://auth.openai.com/oauth/authorize?client_id={OPENAI_CLIENT_ID}&redirect_uri={REDIRECT_URI}"
        return {"oauth_url": oauth_url}

    elif provider == "claude":
        # Anthropic enterprise auth flow
        saml_url = f"https://auth.anthropic.com/saml?org={ORG_ID}"
        return {"saml_url": saml_url}

    # Similar for other providers

@app.get("/llm/auth/callback")
async def auth_callback(code: str, provider: str, state: str):
    """Handle OAuth callback"""

    # Exchange code for token
    token_response = await oauth_provider.exchange_code(code)

    # Store token securely
    credential_store.save_credentials(
        provider,
        LLMAuthConfig(
            provider=provider,
            auth_method=AuthMethod.SUBSCRIPTION,
            credentials={
                "access_token": token_response.access_token,
                "refresh_token": token_response.refresh_token,
                "expires_at": token_response.expires_at
            }
        )
    )

    # Redirect back to UI
    return RedirectResponse(f"/llm-chat-tester.html?status=authenticated")
```

### 3.3 Method 3: CLI-Based Authentication

**Use Case:** Developers prefer CLI-first workflow

#### CLI Implementation
```bash
# Command structure

# 1. List available cloud providers
python -m myragdb.cli llm list --cloud

# 2. Login to a cloud provider
python -m myragdb.cli llm login gemini --method api_key
# Prompts for API key securely

python -m myragdb.cli llm login claude --method subscription
# Opens browser for OAuth, then polls for completion

python -m myragdb.cli llm login chatgpt --method cli
# Generates device code and polls for completion

# 3. List authenticated providers
python -m myragdb.cli llm list-auth

# 4. Switch to cloud LLM
python -m myragdb.cli llm switch gemini --model gemini-pro

# 5. Show current session
python -m myragdb.cli llm status

# 6. Logout
python -m myragdb.cli llm logout gemini
```

#### CLI Implementation Code
```python
# src/myragdb/cli.py (new commands)

@click.group()
def llm():
    """LLM management commands"""
    pass

@llm.command()
@click.option('--cloud', is_flag=True, help='Show cloud providers')
def list(cloud):
    """List available LLMs"""
    if cloud:
        providers_info = ProviderRegistry.list_all()
        for provider in providers_info:
            click.echo(f"{provider.name}: {', '.join(provider.models)}")
    else:
        # Show local LLMs (existing logic)
        pass

@llm.command()
@click.argument('provider')
@click.option('--method', type=click.Choice(['api_key', 'subscription', 'cli']))
def login(provider, method):
    """Authenticate with cloud provider"""

    if method == 'api_key':
        api_key = click.prompt('Enter API Key', hide_input=True)
        credential_store.save_credentials(
            provider,
            LLMAuthConfig(
                provider=provider,
                auth_method=AuthMethod.API_KEY,
                credentials={'api_key': api_key}
            )
        )
        click.echo(f"✓ Logged in to {provider} via API Key")

    elif method == 'subscription':
        # OAuth flow
        auth_manager = SubscriptionAuthManager(provider)
        oauth_url = auth_manager.get_oauth_url()
        click.echo(f"Opening browser for login...")
        webbrowser.open(oauth_url)

        # Poll for completion
        token = auth_manager.wait_for_callback(timeout=300)
        credential_store.save_credentials(provider, token)
        click.echo(f"✓ Logged in to {provider} via subscription")

    elif method == 'cli':
        # Device code flow
        auth_manager = CLIAuthManager(provider)
        device_code_response = auth_manager.request_device_code()

        click.echo(f"Your login code: {device_code_response.user_code}")
        click.echo(f"Visit: {device_code_response.verification_uri}")

        token = auth_manager.wait_for_device_code(
            device_code=device_code_response.device_code,
            timeout=900  # 15 minutes
        )
        credential_store.save_credentials(provider, token)
        click.echo(f"✓ Logged in to {provider} via CLI")

@llm.command()
@click.argument('provider')
@click.option('--model', required=False)
def switch(provider, model):
    """Switch to cloud LLM"""

    # Get stored credentials
    auth_config = credential_store.load_credentials(provider)
    if not auth_config:
        click.echo(f"✗ Not authenticated with {provider}. Run: cli llm login {provider}")
        return

    # Get provider instance
    cloud_provider = ProviderRegistry.get_provider(provider)

    # Validate credentials
    is_valid = cloud_provider.validate_credentials(auth_config.credentials)
    if not is_valid:
        click.echo(f"✗ Credentials invalid for {provider}")
        return

    # Get available models
    models = cloud_provider.list_models()
    if not model:
        click.echo("Available models:")
        for m in models:
            click.echo(f"  - {m.id}: {m.name}")
        model = click.prompt('Select model', type=click.Choice([m.id for m in models]))

    # Switch session (no restart!)
    response = requests.post('http://localhost:3002/llm/switch', json={
        'provider': provider,
        'model_id': model,
        'auth_method': auth_config.auth_method.value,
        'credentials': auth_config.credentials
    })

    if response.status_code == 200:
        session = response.json()['session']
        click.echo(f"✓ Switched to {session['provider_type']} {session['model_id']}")
    else:
        click.echo(f"✗ Switch failed: {response.json()['error']}")

@llm.command()
def status():
    """Show current LLM session"""
    response = requests.get('http://localhost:3002/llm/session')
    session = response.json()

    click.echo(f"Active LLM: {session['provider_type']}/{session['model_id']}")
    click.echo(f"Auth Method: {session['auth_method']}")
    click.echo(f"Status: {session['status']}")

@llm.command()
def list_auth():
    """List authenticated providers"""
    providers = credential_store.list_authenticated_providers()

    if not providers:
        click.echo("No authenticated providers")
        return

    for provider in providers:
        auth_config = credential_store.load_credentials(provider)
        click.echo(f"{provider}: {auth_config.auth_method.value}")

@llm.command()
@click.argument('provider')
def logout(provider):
    """Logout from cloud provider"""
    credential_store.delete_credentials(provider)
    click.echo(f"✓ Logged out from {provider}")
```

---

## 4. API Changes Required

### 4.1 New Endpoints

```python
# GET /llm/session
# Returns current active LLM session

# POST /llm/switch
# Switch active LLM (local or cloud)
# No restart required

# GET /llm/providers
# List all available providers (local + cloud)

# POST /llm/validate-credentials
# Test API key or subscription credentials

# GET /llm/auth/subscription/{provider}
# Initiate subscription-based auth flow

# GET /llm/auth/callback
# OAuth/subscription callback handler

# POST /llm/logout
# Clear credentials for a provider
```

### 4.2 Modified Endpoints

```python
# GET /llm/models
# Now returns both local AND cloud models
# Format:
# {
#     "local": [...],
#     "cloud": {
#         "gemini": [...],
#         "chatgpt": [...],
#         "claude": [...]
#     }
# }
```

---

## 5. Configuration

### 5.1 Environment Variables

```bash
# Cloud provider API keys (optional - can be set via UI)
GOOGLE_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...

# Subscription settings
OPENAI_ORG_ID=...
ANTHROPIC_ORG_ID=...

# OAuth settings (for subscription auth)
OAUTH_REDIRECT_URI=http://localhost:3002/llm/auth/callback
OPENAI_OAUTH_CLIENT_ID=...
OPENAI_OAUTH_CLIENT_SECRET=...
```

### 5.2 Configuration File

```yaml
# config/llm.yaml

providers:
  local:
    enabled: true
    ports:
      8081: "phi3"
      8085: "qwen-coder-7b"
      8086: "hermes-3-8b"
      8087: "llama-3.1-8b"
      8092: "deepseek-r1-qwen-32b"

  cloud:
    gemini:
      enabled: true
      models:
        - id: "gemini-pro"
          name: "Gemini Pro"
          max_tokens: 32000
        - id: "gemini-pro-vision"
          name: "Gemini Pro Vision"
          max_tokens: 32000
      auth_methods:
        - "api_key"
        - "subscription"

    chatgpt:
      enabled: true
      models:
        - id: "gpt-4"
          name: "GPT-4"
          max_tokens: 8000
        - id: "gpt-3.5-turbo"
          name: "GPT-3.5 Turbo"
          max_tokens: 4000
      auth_methods:
        - "api_key"
        - "subscription"
        - "cli"

    claude:
      enabled: true
      models:
        - id: "claude-3-opus"
          name: "Claude 3 Opus"
          max_tokens: 100000
        - id: "claude-3-sonnet"
          name: "Claude 3 Sonnet"
          max_tokens: 100000
      auth_methods:
        - "api_key"
        - "subscription"

# Credential storage
credentials:
  storage_type: "encrypted_file"  # or "env", "secrets_manager"
  location: "~/.myragdb/credentials.json"
  encryption: true
```

---

## 6. Data Models

```python
# src/myragdb/api/models.py (additions)

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

class AuthMethodType(str, Enum):
    API_KEY = "api_key"
    SUBSCRIPTION = "subscription"
    CLI = "cli"

class ProviderType(str, Enum):
    LOCAL = "local"
    GEMINI = "gemini"
    CHATGPT = "chatgpt"
    CLAUDE = "claude"

class CloudModel(BaseModel):
    id: str
    name: str
    provider: ProviderType
    max_tokens: int
    supports_vision: bool = False
    supports_function_calls: bool = False

class LLMSession(BaseModel):
    provider_type: ProviderType
    model_id: str
    auth_method: AuthMethodType
    created_at: datetime
    status: str  # "active", "inactive", "error"
    error_message: Optional[str] = None

class SwitchLLMRequest(BaseModel):
    provider: str
    model_id: str
    auth_method: AuthMethodType
    credentials: Dict[str, Any]

class SwitchLLMResponse(BaseModel):
    success: bool
    session: Optional[LLMSession] = None
    error: Optional[str] = None

class ValidateCredentialsRequest(BaseModel):
    provider: str
    auth_method: AuthMethodType
    credentials: Dict[str, Any]

class ValidateCredentialsResponse(BaseModel):
    valid: bool
    message: str
    remaining_quota: Optional[int] = None

class ListAuthResponse(BaseModel):
    authenticated_providers: List[str]
    details: Dict[str, Dict[str, Any]]
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `session_manager.py` (LLMSession, SessionManager)
- [ ] Create `auth_config.py` (AuthConfig, CredentialStore)
- [ ] Add data models to `api/models.py`
- [ ] Create `/llm/session` endpoint (read current session)

### Phase 2: Cloud Provider Abstraction (Week 2)
- [ ] Create `providers/base_provider.py` (CloudLLMProvider ABC)
- [ ] Create `providers/gemini_provider.py`
- [ ] Create `providers/chatgpt_provider.py`
- [ ] Create `providers/claude_provider.py`
- [ ] Create `providers/provider_registry.py`

### Phase 3: API Key Access Method (Week 2-3)
- [ ] Implement `/llm/switch` endpoint
- [ ] Implement `/llm/validate-credentials` endpoint
- [ ] Update UI to show cloud provider dropdown
- [ ] Test with manual API keys

### Phase 4: Subscription Access Method (Week 3-4)
- [ ] Implement OAuth flows for each provider
- [ ] Create `/llm/auth/subscription/{provider}` endpoints
- [ ] Create `/llm/auth/callback` endpoint
- [ ] Add subscription UI section
- [ ] Test with real subscription accounts

### Phase 5: CLI Access Method (Week 4-5)
- [ ] Create CLI commands (login, switch, status, etc.)
- [ ] Implement device code flow for CLI
- [ ] Implement browser-based OAuth for CLI
- [ ] Test CLI workflows
- [ ] Add documentation

### Phase 6: Integration & Testing (Week 5-6)
- [ ] Integration tests for all providers
- [ ] Credential persistence tests
- [ ] Session switching performance tests
- [ ] Error handling and recovery tests
- [ ] Update existing chat tester to use new system

### Phase 7: Documentation & Deployment (Week 6)
- [ ] API documentation
- [ ] CLI documentation
- [ ] Web UI user guide
- [ ] Configuration guide
- [ ] Troubleshooting guide

---

## 8. Key Design Decisions

### 8.1 No Restart Required
**Why:** Session-based switching instead of process management
- Cloud providers use API calls (no process overhead)
- Local LLMs already running on fixed ports
- Session manager tracks which provider is "active"

### 8.2 Unified Provider Interface
**Why:** Same abstraction for all providers
- Easy to add new cloud providers later
- Consistent error handling
- Fallback logic works uniformly

### 8.3 Multiple Auth Methods Per Provider
**Why:** Flexibility for different use cases
- Personal developers → API keys
- Organizations → Subscriptions
- Teams → CLI for automation
- All three methods can coexist

### 8.4 Credential Encryption
**Why:** Security by default
- Never store API keys in plaintext
- Support environment variables + encrypted files
- Easy rotation of credentials

---

## 9. Error Handling & Resilience

### 9.1 Invalid Credentials
```python
# User provides wrong API key
POST /llm/switch with invalid key

# Response:
{
    "success": false,
    "error": "Invalid API key for gemini. Please verify and try again.",
    "error_code": "INVALID_CREDENTIALS"
}
```

### 9.2 Rate Limiting
```python
# Cloud provider rate limit exceeded
{
    "success": false,
    "error": "Gemini API rate limit exceeded. Try again in 1 minute.",
    "error_code": "RATE_LIMITED",
    "retry_after": 60
}
```

### 9.3 Network Errors
```python
# Cloud provider API unreachable
{
    "success": false,
    "error": "Cannot reach Gemini API. Check your internet connection.",
    "error_code": "NETWORK_ERROR",
    "fallback_suggestion": "switch_to_local_llm"
}
```

### 9.4 Credential Expiry
```python
# Subscription token expired
# SessionManager detects during health check
# Attempts automatic refresh
# If refresh fails, prompts user to re-authenticate
```

---

## 10. Example: Complete User Journey

### Scenario: User switches from local Phi-3 to Gemini

#### Step 1: User visits Web UI
- Sees current session: "Local LLM / phi3"
- Clicks "Switch LLM" button

#### Step 2: Select Cloud Provider
- Chooses dropdown: "Cloud LLMs"
- Selects: "Google Gemini"
- Selects auth method: "API Key"

#### Step 3: Provide Credentials
- Pastes API key into secure input field
- Clicks "Switch to Cloud LLM"

#### Step 4: Backend Validation
```python
# Backend receives request
POST /llm/switch {
    "provider": "gemini",
    "model_id": "gemini-pro",
    "auth_method": "api_key",
    "credentials": {"api_key": "..."}
}

# SessionManager.switch_llm() runs:
1. Validates API key format
2. Tests connectivity: calls Gemini API with test prompt
3. Gets list of available models
4. Updates session to "gemini/gemini-pro"
5. Returns success response
```

#### Step 5: Immediate Use
- **No restart needed**
- Chat interface immediately accepts new prompts
- Prompts sent to Gemini API instead of local port
- Context/history maintained (if desired)

#### Step 6: Switch Back to Local
```bash
# Via CLI, switch back anytime
python -m myragdb.cli llm switch phi3

# Immediate: Local LLM is now active
```

---

## 11. Comparison: Before vs After

### Before (Current)
```
User wants to switch from Phi-3 to Gemini:
1. Stop current local LLM
2. Navigate to "LLM Manager" tab
3. Select Gemini (if option existed)
4. Configure API key
5. Click "Start" → External script runs
6. Wait for process to start (~30-60 seconds)
7. Go back to chat tester
8. Begin chatting

Total time: 2-3 minutes
Requires: Full UI flow, process overhead
```

### After (Proposed)
```
User wants to switch from Phi-3 to Gemini:
1. Click cloud provider dropdown (already in chat tester)
2. Select "Gemini"
3. Paste API key
4. Click "Switch" → API call validates
5. Begin chatting

Total time: 10-15 seconds
Requires: Just credential + one click
Benefit: No restart, no process overhead, immediate use
```

---

## 12. Dependencies Required

```python
# requirements.txt additions

# Cloud provider SDKs
google-generativeai>=0.3.0  # Gemini API
openai>=1.0.0              # ChatGPT API
anthropic>=0.7.0           # Claude API

# Authentication
authlib>=1.2.0             # OAuth/SAML
cryptography>=41.0.0       # Credential encryption
pydantic-settings>=2.0.0   # Config management

# Testing
pytest-asyncio>=0.21.0     # Async test support
responses>=0.23.0          # Mock HTTP responses
aioresponses>=0.7.4        # Mock async HTTP
```

---

## 13. Testing Strategy

### Unit Tests
- Each provider implementation (mock API calls)
- SessionManager switching logic
- CredentialStore encryption/decryption
- Auth flow (mocked OAuth)

### Integration Tests
- Real API calls to cloud providers (with test credentials)
- Session persistence across requests
- Error handling and recovery
- Credential refresh flows

### End-to-End Tests
- Web UI workflow (Selenium/Playwright)
- CLI commands
- Chat tester with cloud LLM
- Switching between providers

---

## 14. Security Considerations

### API Key Security
- Never log API keys
- Encrypt at rest (encryption module)
- Clear in memory after use
- Support environment variables (CI/CD safe)

### Subscription Token Security
- Store refresh tokens securely
- Implement automatic refresh before expiry
- Audit token usage
- Support token rotation

### Rate Limiting
- Implement client-side rate limiting
- Show user when approaching quota
- Graceful degradation when rate limited

### Audit Logging
- Log all provider switches
- Log auth attempts
- Track quota usage
- Alert on unusual activity

---

## 15. Next Steps

1. **Review architecture** with team
2. **Approve implementation approach** (start with API key method)
3. **Begin Phase 1 development** (Week 1)
4. **Create detailed API specifications** for each endpoint
5. **Design database schema** for credential storage (if needed)

---

**Questions:** libor@arionetworks.com
