# Cloud LLM Architecture - Visual Diagrams
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/CLOUD_LLM_DIAGRAMS.md
**Description:** Visual representations of the cloud LLM integration architecture
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## 1. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                  │
├──────────────────┬──────────────────┬──────────────────┬─────────────────────┤
│ Web UI           │ CLI              │ Agent Library    │ SDK Integrations    │
│                  │                  │                  │                     │
│ • Model dropdown │ • llm login      │ • SearchClient   │ • Python package    │
│ • Auth panels    │ • llm switch     │ • Runtime access │ • Node.js package   │
│ • Chat tester    │ • llm status     │ • Direct API     │ • REST API          │
│ • Status widget  │ • llm logout     │ • Fallback logic │ • WebSocket         │
└──────────────────┴──────────────────┴──────────────────┴─────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                       API LAYER (FastAPI)                                     │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ SessionManager                                                            │ │
│  │ • GET  /llm/session → Current active LLM                               │ │
│  │ • POST /llm/switch → Change LLM (no restart)                           │ │
│  │ • POST /llm/validate-credentials → Test auth                           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ AuthenticationManager                                                     │ │
│  │ • POST /llm/auth/subscription/{provider} → OAuth initiate              │ │
│  │ • GET  /llm/auth/callback → OAuth callback handler                     │ │
│  │ • POST /llm/logout → Clear credentials                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ ProviderRegistry                                                          │ │
│  │ • Instantiate cloud providers                                            │ │
│  │ • Load local LLM routers                                                │ │
│  │ • Fallback logic                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
                ↓                              ↓                    ↓
        ┌──────────────┐           ┌──────────────────┐   ┌──────────────┐
        │ Local LLMs   │           │ Cloud Providers  │   │ Auth Storage │
        │              │           │                  │   │              │
        │ • Port 8081  │           │ • Gemini         │   │ • Encrypted  │
        │ • Port 8085  │           │ • ChatGPT        │   │ • Env vars   │
        │ • Port 8086  │           │ • Claude         │   │ • File-based │
        │ • Port 8087  │           │                  │   │              │
        │ • Port 8092  │           │                  │   │              │
        └──────────────┘           └──────────────────┘   └──────────────┘
```

---

## 2. Session Switching Flow (Zero Restart)

```
                         Current Session
                      [Local: phi3:8081]
                              |
                              v
           User clicks "Switch to Cloud LLM"
                              |
                    ┌─────────┴─────────┐
                    |                   |
            SELECT PROVIDER          ENTER AUTH
            (Gemini, ChatGPT,        (API Key /
             Claude)                  Subscription /
                    |                   CLI)
                    └─────────┬─────────┘
                              |
                              v
                ╔═════════════════════════════╗
                ║  SessionManager.switch_llm()║
                ║                              ║
                ║  1. Validate credentials    ║
                ║  2. Test connectivity       ║
                ║  3. Check rate limits       ║
                ║  4. Get model list          ║
                ║  5. Update session object   ║
                ║  6. Return success          ║
                ╚═════════════════════════════╝
                              |
                    ┌─────────┴─────────┐
                    |                   |
                  SUCCESS           FAILURE
                    |                   |
                    v                   v
        ┌─────────────────────┐   ┌──────────────┐
        │ Active Session:     │   │ Return Error │
        │ [Cloud: Gemini Pro] │   │ • Invalid key│
        │                     │   │ • No network │
        │ Chat tester ready   │   │ • Rate limit │
        │ for new queries     │   └──────────────┘
        │ (No restart needed) │
        └─────────────────────┘
```

---

## 3. Authentication Methods Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THREE AUTHENTICATION METHODS                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐  ┌──────────────────────────┐  ┌─────────────────┐
│    METHOD 1: API KEY     │  │  METHOD 2: SUBSCRIPTION  │  │ METHOD 3: CLI   │
├──────────────────────────┤  ├──────────────────────────┤  ├─────────────────┤
│                          │  │                          │  │                 │
│ Use Case:                │  │ Use Case:                │  │ Use Case:       │
│ • Personal developers    │  │ • Organizations          │  │ • Developer     │
│ • Quick testing          │  │ • Enterprise accounts    │  │   automation    │
│ • Single user projects   │  │ • Team accounts          │  │ • CI/CD         │
│                          │  │ • Managed credentials    │  │ • Scripting     │
│                          │  │                          │  │                 │
├──────────────────────────┤  ├──────────────────────────┤  ├─────────────────┤
│ Setup Flow:              │  │ Setup Flow:              │  │ Setup Flow:     │
│ 1. Get API key           │  │ 1. Click OAuth button    │  │ 1. Run CLI cmd  │
│ 2. Paste into Web UI     │  │ 2. Browser opens         │  │ 2. Browser      │
│ 3. Click "Switch"        │  │ 3. Login with account    │  │    opens auto   │
│ 4. Done (5 seconds)      │  │ 4. Grant permission      │  │ 3. Enter code   │
│                          │  │ 5. Redirects back        │  │ 4. Done         │
│                          │  │ 6. Done (1-2 minutes)    │  │                 │
├──────────────────────────┤  ├──────────────────────────┤  ├─────────────────┤
│ Security:                │  │ Security:                │  │ Security:       │
│ ✓ Simple                 │  │ ✓ Enterprise-grade       │  │ ✓ Device code   │
│ ✓ Quick setup            │  │ ✓ Managed tokens         │  │ ✓ No key paste  │
│ ✗ Manual key storage     │  │ ✓ Auto-refresh           │  │ ✓ Audit logs    │
│ ⚠ Key in plaintext risk  │  │ ✓ Better tracking        │  │ ✓ Time-limited  │
│                          │  │ ✗ Complex setup          │  │                 │
├──────────────────────────┤  ├──────────────────────────┤  ├─────────────────┤
│ Best For:                │  │ Best For:                │  │ Best For:       │
│ • Personal tinkering     │  │ • Production usage       │  │ • Automation    │
│ • Testing & demos        │  │ • Team collaboration     │  │ • Scripting     │
│ • Single-user apps       │  │ • Security compliance    │  │ • Headless env  │
│                          │  │ • Quota management       │  │ • CI/CD pipes   │
│                          │  │ • Billing integration    │  │                 │
└──────────────────────────┘  └──────────────────────────┘  └─────────────────┘
```

---

## 4. API Key Method - Sequence Diagram

```
User          Web UI          Backend       Credential    Cloud Provider
 |              |              |              Store         (Gemini)
 |              |              |              |              |
 1. Fill form   |              |              |              |
 2. Click switch|->            |              |              |
 |              |    POST /llm/switch        |              |
 |              |    {provider, creds}       |              |
 |              |    ->         |              |              |
 |              |              |  Validate format            |
 |              |              |->            |              |
 |              |              |  Save (encrypted)          |
 |              |              |     ->      |              |
 |              |              |    Test conn->             |
 |              |              |              | genai.list_models()
 |              |              |              |  ->         |
 |              |              |              |        {models}
 |              |              |    <-        |
 |              |              |  Success check             |
 |              |              |              |              |
 |              |<-            |              |              |
 |              | {success:true, session}    |              |
 |<-            |              |              |              |
 3. Ready to chat!             |              |              |
 |              |              |              |              |
 (No restart needed - instant functionality)
```

---

## 5. Subscription Method - OAuth Flow

```
User          Web UI          Backend      Auth Service    Cloud Provider
 |              |              |            (e.g., OpenAI)    |
 |              |              |              |              |
 1. Click login |              |              |              |
 2. -> button   |->            |              |              |
 |              |  POST /llm/auth/subscription/chatgpt
 |              |              |              |              |
 |              |    <-        |              |              |
 |              | {oauth_url}  |              |              |
 |              |              |              |              |
 3. Redirected  |              |              |              |
    to          |              |              |              |
    OpenAI      |  ────────────────────────────────────>    |
    login       |              |              | Browser       |
    page        |              |              | opens         |
                |              |              |              |
 4. Enter       |              |              |              |
    credentials |              |              |              |
 5. Click allow |              |              |              |
                |              |              |              |
    ←─────────────────── Auth Code ─────────────────        |
                |              |              |              |
 6. Redirected  |              | Exchange code for token    |
    back        |              | ->          |              |
                |              |    Token    |              |
                |              |    <-       |              |
                |              |  Save token (encrypted)    |
                |              |              |              |
 7. Ready to    |<-            |              |              |
    chat        | {success:true, session}    |              |
 |              |              |              |              |
```

---

## 6. CLI Method - Device Code Flow

```
Terminal       CLI Client       Backend       Auth Service   Cloud Provider
 |              |                |              |              |
 1. llm login   |                |              |              |
    chatgpt    |->              |              |              |
 |             | GET /auth/device-code         |              |
 |             |                |              |              |
 |             |    <-          |              |              |
 |             | {device_code, user_code,     |              |
 |             |  verification_uri}           |              |
 |             |                |              |              |
 2. "Your code: |                |              |              |
    ABC123"    |<-              |              |              |
 |             | "Visit: openai.com/device"   |              |
 |             |                |              |              |
 3. Browser    | ─────────────────────────────────────────> |
    opens auto |                |              |              |
 |             |                |              |              |
 4. User enters|                |              |              |
    code ABC123|                |              |              |
    and clicks |                |              |              |
    approve    |                |              |              |
                |                |              |              |
                | ─ POLLING EVERY 5 SEC ─────────────────→  |
                | GET /device/code/check?device_code=...     |
                |                |              |              |
    (User may be doing other    (Polling continues)           |
     things - doesn't block)     (until approval)             |
                |                |              |              |
 5. "Approved!"| <─ Token received ───────────────────────   |
    "Logged in"|                |              |              |
 |             |  Save token (encrypted)      |              |
 |             |  -> Save to ~/.myragdb/...   |              |
 |             |                |              |              |
 6. Ready to   |<-              |              |              |
    use        | {success:true} |              |              |
 |             |                |              |              |
```

---

## 7. Component Interaction: Session Manager

```
┌───────────────────────────────────────────────────────────────────┐
│                      SessionManager                                │
│                   (Central Orchestrator)                           │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Current Session State:                                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ {                                                            │ │
│  │   provider_type: "gemini",                                   │ │
│  │   model_id: "gemini-pro",                                    │ │
│  │   auth_method: "api_key",                                    │ │
│  │   status: "active",                                          │ │
│  │   created_at: "2026-01-07T10:30:00Z"                        │ │
│  │ }                                                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                          ↕ ↕ ↕                                     │
│     ┌────────────────┬────────────────┬────────────────┐          │
│     ↓                ↓                ↓                ↓          │
│  ┌────────┐    ┌──────────────┐  ┌──────────┐   ┌────────┐      │
│  │Provider│    │ Credential   │  │ Health   │   │ Model  │      │
│  │Manager │    │ Store        │  │ Checker  │   │ Router │      │
│  │        │    │              │  │          │   │        │      │
│  │select()│    │encrypt()     │  │validate()│   │fallback│      │
│  │lookup()│    │decrypt()     │  │refresh() │   │get()   │      │
│  └────────┘    │save()        │  │timeout() │   └────────┘      │
│                │load()        │  │retry()   │                    │
│                │delete()      │  │          │                    │
│                └──────────────┘  └──────────┘                    │
│                                                                    │
│  When user calls: switch_llm()                                   │
│  SessionManager coordinates:                                      │
│  1. Get credentials from CredentialStore                          │
│  2. Get provider from ProviderRegistry                            │
│  3. Call Provider.validate_credentials()                          │
│  4. Call HealthChecker.validate()                                 │
│  5. Update session state                                          │
│  6. Return result                                                 │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

---

## 8. Cloud Provider Abstraction Layer

```
                        CloudLLMProvider (Abstract)
                              ↑
                ┌─────────────┼─────────────┐
                ↑             ↑             ↑
         ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
         │GeminiProvider│ │ChatGPTProvider│ │ClaudeProvider│
         ├──────────────┤ ├──────────────┤ ├──────────────┤
         │ validate()   │ │ validate()   │ │ validate()   │
         │ list_models()│ │ list_models()│ │ list_models()│
         │ generate()   │ │ generate()   │ │ generate()   │
         │ stream()     │ │ stream()     │ │ stream()     │
         └──────────────┘ └──────────────┘ └──────────────┘
                │             │             │
                └──────┬──────┴─────┬──────┘
                       ↓            ↓
              [HTTP API Calls] [SDK Calls]
                       ↓            ↓
         API: genai.list_models()  openai.chat.completions.create()
         API: genai.generate_text() client.messages.create()
```

---

## 9. Web UI Layout: Before vs After

### Before (Current)
```
┌─────────────────────────────────────────────────┐
│ LLM Chat Tester                                 │
├─────────────────────────────────────────────────┤
│ [Select Local Model▼]  [Start] [Stop]           │
│                                                  │
│ Chat history...                                 │
│ (Can only select from running local LLMs)       │
│                                                  │
└─────────────────────────────────────────────────┘
```

### After (Proposed)
```
┌─────────────────────────────────────────────────┐
│ LLM Chat Tester                                 │
├─────────────────────────────────────────────────┤
│ Active: ◯ Local LLM  [Phi3]  [Switch LLM]       │
│         ◯ Cloud LLM  [Gemini Pro] [Logout]      │
│                                                  │
│ [LLM Type: Local ▼]                             │
│ [Model: Phi3 ▼]                                 │
│                                                  │
│ ┌─ Cloud LLM Options ─────────────────────────┐ │
│ │ Provider: [Gemini ▼] [ChatGPT ▼] [Claude ▼]│ │
│ │ Auth: [API Key ▼] [Subscription ▼] [CLI ▼] │ │
│ │                                              │ │
│ │ API Key Method:                              │ │
│ │ [Paste API Key ........................]      │ │
│ │                    [Switch to Cloud LLM]    │ │
│ │                                              │ │
│ │ Subscription Method:                         │ │
│ │ [Login with Account]                        │ │
│ │                                              │ │
│ │ CLI Method:                                  │ │
│ │ $ python -m myragdb.cli llm login gemini   │ │
│ │ [Show instructions]                         │ │
│ └────────────────────────────────────────────┘ │
│                                                  │
│ Current Session: Gemini Pro (API Key)            │
│ Status: ✓ Connected | Tokens: 1000 / 32000      │
│                                                  │
│ Chat history...                                 │
│ (Can switch anytime without restart)            │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 10. Data Flow: Chat Message Through System

```
User Types Prompt
    ↓
┌───────────────────────────────────────┐
│ Check Active Session                  │
│ (SessionManager.get_active_session()) │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ Is it Local or Cloud?                 │
└───────────────────────────────────────┘
    ├─ LOCAL                    CLOUD ─┤
    ↓                               ↓
┌─────────────────────┐     ┌──────────────────────┐
│Route to Local Port  │     │Get Cloud Provider    │
│(LLMRouter)          │     │Instance              │
│                     │     │                      │
│POST localhost:8081  │     │Get stored credentials│
│/completion          │     │Validate token       │
│  {prompt}           │     │Refresh if needed    │
│                     │     │                      │
│<- response          │     │Call API             │
└─────────────────────┘     │(e.g., genai.generate_text)
    ↓                       │  {prompt, model_id}
    └─────────┬─────────────┤
              ↓             │
         Return to Chat    │<- response
         Widget       └──────────────────────┘
              ↓
         Display              Display
         Response             Response
         (Local LLM)          (Cloud LLM)
```

---

## 11. Error Recovery Flow

```
User requests switch to Gemini with API key
    ↓
┌─────────────────────────────┐
│ Validate Credentials        │
└─────────────────────────────┘
    ↓
    ├─ Invalid Format? ──→ Return: "Format error"
    │                      User re-enters
    ↓
┌─────────────────────────────┐
│ Test Connectivity           │
│ (Call Gemini API)           │
└─────────────────────────────┘
    ↓
    ├─ Invalid Key? ──→ Return: "Invalid credentials"
    │                   User re-pastes key
    ├─ No Network? ──→ Return: "Network error"
    │                   Suggest: Switch to local
    ├─ Rate Limited? ──→ Return: "Rate limit (retry in 60s)"
    │                   Show: Countdown timer
    ├─ API Down? ──→ Return: "Service unavailable"
    │               Suggest: "Try again in 5 min"
    ↓
┌─────────────────────────────┐
│ Success!                    │
│ Update Session              │
│ Return: "Ready to chat"     │
└─────────────────────────────┘
    ↓
User can chat immediately
```

---

## 12. Configuration Hierarchy

```
┌─────────────────────────────────────────────────────┐
│ Environment Variables (Highest Priority)             │
│ GOOGLE_API_KEY=...                                   │
│ OPENAI_API_KEY=...                                   │
│ ANTHROPIC_API_KEY=...                                │
└─────────────────────────────────────────────────────┘
                    ↓ Falls back to ↓
┌─────────────────────────────────────────────────────┐
│ Encrypted Credentials File                           │
│ ~/.myragdb/credentials.json (encrypted)             │
│ {gemini: {...}, chatgpt: {...}, claude: {...}}      │
└─────────────────────────────────────────────────────┘
                    ↓ Falls back to ↓
┌─────────────────────────────────────────────────────┐
│ YAML Configuration File                              │
│ config/llm.yaml                                      │
│ [provider settings, model definitions]              │
└─────────────────────────────────────────────────────┘
                    ↓ Falls back to ↓
┌─────────────────────────────────────────────────────┐
│ Hardcoded Defaults                                   │
│ (In code: providers.py)                             │
└─────────────────────────────────────────────────────┘

Note: User input (API key pasted in UI) takes precedence
      and is securely encrypted before storage
```

---

## 13. Timeline: Implementation Schedule

```
Week 1: Foundation (Session Manager + Auth Config)
├─ Day 1: Create SessionManager, LLMSession classes
├─ Day 2: Create LLMAuthConfig, CredentialStore
├─ Day 3: Add new endpoints (/llm/session)
└─ Day 4: Unit tests + API docs

Week 2: Cloud Providers (Abstraction + Implementations)
├─ Day 1: CloudLLMProvider ABC
├─ Day 2: GeminiProvider, ChatGPTProvider, ClaudeProvider
├─ Day 3: ProviderRegistry
└─ Day 4: Integration tests

Week 3: API Key Method (Full end-to-end)
├─ Day 1: POST /llm/switch endpoint
├─ Day 2: Web UI cloud dropdown
├─ Day 3: Test with real APIs
└─ Day 4: Error handling

Week 4: Subscription Method (OAuth flows)
├─ Day 1: OAuth flow setup
├─ Day 2: /llm/auth/subscription/{provider}
├─ Day 3: /llm/auth/callback handling
└─ Day 4: Test with real subscriptions

Week 5: CLI Method (Device code + OAuth)
├─ Day 1: CLI commands skeleton
├─ Day 2: Device code flow
├─ Day 3: CLI OAuth flow
└─ Day 4: Test workflows

Week 6: Integration & Documentation
├─ Day 1-2: End-to-end testing
├─ Day 3: Documentation
└─ Day 4: Deployment + training

Parallel Activities:
- Security review (Week 2-3)
- Performance testing (Week 4-5)
- Dependency updates (Week 1 + 5)
```

---

## 14. Success Metrics

```
✓ Zero-downtime switching
  └─ Time to switch providers: < 5 seconds (API key method)

✓ Multiple auth methods working
  └─ All 3 methods (API key, subscription, CLI) functional

✓ Security compliance
  └─ No plaintext credentials, encryption enforced

✓ Error handling
  └─ 99%+ uptime with intelligent fallbacks

✓ User experience
  └─ Consistent UI across all auth methods
  └─ Clear error messages
  └─ No restart required

✓ Developer experience
  └─ CLI workflow for automation
  └─ Agent library integration seamless
  └─ API well-documented
```

---

**Questions:** libor@arionetworks.com
