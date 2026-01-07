# MyRAGDB Authentication Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/AUTHENTICATION_GUIDE.md
**Description:** Complete guide to MyRAGDB authentication methods and credential management
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

MyRAGDB provides three authentication methods for managing LLM provider credentials:

1. **API Key Flow** - Direct credential setup (production, CI/CD, automation)
2. **OAuth Flow** - Web-based provider authorization (user-friendly, secure)
3. **Device Code Flow** - CLI-friendly authentication (air-gapped systems, automation)

All credentials are stored securely in `~/.myragdb/` with encrypted storage and proper access controls.

---

## Supported Providers

| Provider | Auth Methods | Status |
|----------|--------------|--------|
| Claude (Anthropic) | All | ✅ Supported |
| ChatGPT (OpenAI) | All | ✅ Supported |
| Gemini (Google) | All | ✅ Supported |

---

## 1. API Key Authentication

### Overview

Direct API key setup for immediate access. Keys are stored encrypted in `~/.myragdb/keys/api_keys.json`.

**Best For:**
- Production environments
- CI/CD pipelines
- Automation scripts
- Server-to-server communication
- When you have API key available

### CLI Usage

#### Add API Key

```bash
# Interactive prompt for key
myragdb auth api-key add --provider claude --description "Production"

# Or provide key via stdin
echo "sk-ant-..." | myragdb auth api-key add --provider gpt

# With flags
myragdb auth api-key add \
  --provider gemini \
  --description "Development key" \
  --default  # Set as default for provider
```

#### List API Keys

```bash
# List all API keys
myragdb auth api-key list

# Filter by provider
myragdb auth api-key list --provider claude

# JSON output
myragdb auth api-key list --json
```

#### Remove API Key

```bash
myragdb auth api-key remove claude-abc12345
```

### Python Usage

```python
from myragdb.auth import AuthenticationManager

auth = AuthenticationManager()

# Add API key
credential = auth.authenticate_with_api_key(
    provider='claude',
    api_key='sk-ant-...',
    description='Production key',
    set_as_default=True
)

# List API keys
keys = auth.list_api_key_credentials()
for key in keys:
    print(f"{key.provider}: {key.credential_id}")

# Get default for provider
default_key = auth.get_credential('claude')
```

### API Usage

```bash
# Add API key via API
curl -X POST http://localhost:3003/api/v1/auth/credentials/api-key \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "claude",
    "api_key": "sk-ant-...",
    "description": "Production",
    "set_as_default": true
  }'

# List API keys
curl http://localhost:3003/api/v1/auth/credentials/api-key

# Filter by provider
curl "http://localhost:3003/api/v1/auth/credentials/api-key?provider=claude"
```

### Security Best Practices

1. **Never commit API keys** - Use environment variables in CI/CD
2. **Rotate regularly** - Refresh keys periodically
3. **Use separate keys per environment** - Dev, staging, production
4. **Revoke unused keys** - Clean up old credentials
5. **Avoid terminal history** - Use environment variables when possible

---

## 2. OAuth Authentication

### Overview

Web-based authorization flow. User visits provider authorization URL, consents, then credentials are stored securely.

**Best For:**
- Interactive user authentication
- Web applications
- When users need to grant consent
- Tokens with automatic refresh capability
- User-friendly authentication

### CLI Usage

#### Login with OAuth

```bash
# Start OAuth flow
myragdb auth oauth login --provider claude

# Visit URL in browser:
# https://auth.anthropic.com/authorize?client_id=...&redirect_uri=...&state=...

# Enter code when redirected
# Credentials automatically saved

# Don't open browser automatically
myragdb auth oauth login --provider gpt --no-browser
```

#### List OAuth Credentials

```bash
# List all OAuth credentials
myragdb auth oauth list

# Filter by provider
myragdb auth oauth list --provider claude

# JSON output
myragdb auth oauth list --json
```

### Python Usage

```python
from myragdb.auth import AuthenticationManager

auth = AuthenticationManager()

# Start OAuth flow
auth_url = auth.initiate_oauth('claude')
print(f"Visit: {auth_url}")

# After user consents and receives code:
auth_code = input("Enter authorization code: ")

credential = auth.complete_oauth(
    provider='claude',
    auth_code=auth_code,
    set_as_default=True
)

# List OAuth credentials
oauth_creds = auth.list_oauth_credentials()
for cred in oauth_creds:
    print(f"{cred.provider}: {cred.identifier}")
```

### API Usage

```bash
# Initiate OAuth
curl -X POST "http://localhost:3003/api/v1/auth/oauth/initiate?provider=claude"

# Response:
# {
#   "provider": "claude",
#   "authorization_url": "https://auth.anthropic.com/authorize?...",
#   "description": "Visit this URL in your browser to authorize"
# }

# Complete OAuth with code
curl -X POST http://localhost:3003/api/v1/auth/oauth/complete \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "claude",
    "auth_code": "code_from_redirect",
    "set_as_default": true
  }'

# List OAuth credentials
curl http://localhost:3003/api/v1/auth/oauth/credentials
```

### OAuth Flow Diagram

```
User starts OAuth:
  myragdb auth oauth login --provider claude
        ↓
Gets authorization URL:
  https://auth.anthropic.com/authorize?...
        ↓
User visits URL in browser:
  https://auth.anthropic.com/authorize?client_id=...&state=xyz
        ↓
User authorizes MyRAGDB:
  [Allow button]
        ↓
Redirected with authorization code:
  http://localhost:8000/callback?code=abc123&state=xyz
        ↓
User enters code in CLI:
  Enter authorization code: abc123
        ↓
MyRAGDB exchanges code for token:
  POST https://auth.anthropic.com/token
  with: code=abc123, client_id=..., client_secret=...
        ↓
Token stored securely:
  ~/.myragdb/oauth/tokens.json (encrypted)
        ↓
Success! Ready to use OAuth credential
```

---

## 3. Device Code Authentication

### Overview

Device code flow for CLI-friendly authentication. User visits verification URL with short code, no key exposure in terminal. Perfect for CI/CD and automation.

**Best For:**
- CLI-only environments
- CI/CD pipelines
- Air-gapped systems
- Automation without terminal history
- When direct key input not desired

### CLI Usage

#### Device Code Login

```bash
# Start device code flow
myragdb auth device login --provider claude

# Output:
# ╭───────────────────────────────────────╮
# │ Device Code Authentication            │
# │                                       │
# │ Visit: https://device.auth.myragdb... │
# │ Enter code: ABCD-EFGH                 │
# │                                       │
# │ Expires in: 900s                      │
# ╰───────────────────────────────────────╯
#
# Polling for approval (will wait up to 900s)...
# ✓ Device code login successful

# User must:
# 1. Visit verification URL in ANOTHER terminal/browser
# 2. Enter device code: ABCD-EFGH
# 3. Approve access
# 4. CLI automatically detects approval and completes
```

#### List Device Code Credentials

```bash
# List all device code credentials
myragdb auth device list

# Filter by provider
myragdb auth device list --provider claude

# JSON output
myragdb auth device list --json
```

### Python Usage

```python
from myragdb.auth import AuthenticationManager
import asyncio

auth = AuthenticationManager()

# Initiate device code flow
device_code = auth.initiate_device_code('claude')

print(f"Visit: {device_code.verification_url}")
print(f"Enter code: {device_code.user_code}")
print(f"Waiting {device_code.expires_in}s for approval...")

# Poll for approval (blocks until approved, denied, or timeout)
credential = auth.complete_device_code(device_code.device_code)

if credential:
    print(f"✓ Approved! Credential: {credential.credential_id}")
else:
    print("✗ Not approved or timed out")
```

### API Usage

```bash
# Initiate device code
curl -X POST "http://localhost:3003/api/v1/auth/device-code/initiate?provider=claude"

# Response:
# {
#   "device_code": "abc123...",
#   "user_code": "ABCD-EFGH",
#   "provider": "claude",
#   "verification_url": "https://device.auth.myragdb...",
#   "expires_in": 900,
#   "interval": 5,
#   "instructions": "Visit the verification URL and enter the user code"
# }

# Complete device code (after user approves)
curl -X POST http://localhost:3003/api/v1/auth/device-code/complete \
  -H "Content-Type: application/json" \
  -d '{
    "device_code": "abc123...",
    "set_as_default": true
  }'
```

### Device Code Flow Diagram

```
Terminal 1:
  myragdb auth device login --provider claude
        ↓
  Device code: ABCD-EFGH
  Verification URL: https://device.auth.myragdb...
  [Polling for approval...]

Terminal 2 (or Browser):
  Visit: https://device.auth.myragdb
  Enter code: ABCD-EFGH
  Approve access
        ↓
Terminal 1 detects approval:
  ✓ Device code login successful
  ID: device-code-xyz...
  Provider: claude
```

---

## Credential Management

### List All Credentials

```bash
# List all credentials across all auth methods
myragdb auth list

# Filter by provider
myragdb auth list --provider claude

# JSON output
myragdb auth list --json

# Output:
# All Credentials
# ┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
# ┃ ID              ┃ Provider ┃ Method  ┃ Default ┃
# ┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
# │ claude-abc...   │ claude   │ api_key │ ✓       │
# │ gpt-xyz...      │ gpt      │ oauth   │         │
# │ device-123...   │ gemini   │ device_ │         │
# └─────────────────┴─────────┴─────────┴─────────┘
#
# Total: 3 credentials
```

### Get Default Credential for Provider

```bash
# Get default credential for Claude
myragdb auth default-credential claude

# Python
from myragdb.auth import AuthenticationManager

auth = AuthenticationManager()
default_cred = auth.get_credential('claude')
if default_cred:
    print(f"Default: {default_cred.credential_id}")
```

### Set Default Credential

```bash
# Set API key as default for Claude
myragdb auth default claude-abc12345

# Python
auth.set_default_credential('claude-abc12345')
```

### Revoke Credential

```bash
# Revoke (deactivate) a credential
myragdb auth revoke claude-abc12345

# Python
auth.revoke_credential('claude-abc12345')
```

### Delete Credential

```bash
# Delete a credential completely
myragdb auth remove gpt-xyz789

# Python
auth.delete_credential('gpt-xyz789')
```

---

## Credential Storage

### Directory Structure

```
~/.myragdb/
├── credentials.json          # Credential metadata (all types)
├── keys/
│   └── api_keys.json         # API key credentials (encrypted at rest)
├── oauth/
│   ├── tokens.json           # OAuth tokens (encrypted at rest)
│   └── states.json           # OAuth state parameters for CSRF protection
└── device/
    └── device_codes.json     # Device code tracking
```

### File Permissions

All credential files are created with restrictive permissions:
- API keys: `0o600` (rw-------)
- OAuth tokens: `0o600` (rw-------)
- Device codes: `0o600` (rw-------)

### Encryption

Credentials are stored with encryption where possible:
- Fernet symmetric encryption for sensitive data
- Encryption key stored in `~/.myragdb/.key`
- All files have strict file permissions

---

## Environment Variables

You can also provide credentials via environment variables:

```bash
# Set API key via environment
export MYRAGDB_CLAUDE_API_KEY="sk-ant-..."
export MYRAGDB_GPT_API_KEY="sk-..."
export MYRAGDB_GEMINI_API_KEY="..."

# CLI will automatically detect and use these
myragdb agent execute code_search --param query="authentication"

# Python client will also detect
from myragdb.auth import AuthenticationManager
auth = AuthenticationManager()
# Will prefer env var > stored credentials > error
```

---

## Authentication in Code

### Using Credentials in Python

```python
from myragdb.auth import AuthenticationManager
from myragdb.agent.orchestration import AgentOrchestrator

# Get default credential for provider
auth = AuthenticationManager()
credential = auth.get_credential('claude')

if credential:
    # Credential is available, orchestrator can use it
    orchestrator = AgentOrchestrator()
    result = orchestrator.execute_template(
        'code_search',
        parameters={'query': 'authentication'},
        llm_provider='claude'
    )
else:
    print("No Claude credential available")
```

### Using Credentials in API

```bash
# API automatically uses default credential for provider
curl -X POST http://localhost:3003/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "code_search",
    "parameters": {
      "query": "authentication"
    }
  }'

# API will use default Claude credential
```

---

## Common Workflows

### 1. Quick Start (Interactive)

```bash
# Add API key interactively
myragdb auth api-key add --provider claude

# Run template immediately
myragdb agent execute code_search --param query="authentication"
```

### 2. Production Setup (Automated)

```bash
# Use environment variable
export MYRAGDB_CLAUDE_API_KEY="sk-ant-..."

# No prompt needed, directly use
myragdb agent execute code_search --param query="authentication"

# Or add to credentials for reuse
myragdb auth api-key add --provider claude \
  --key "$MYRAGDB_CLAUDE_API_KEY" \
  --description "Production"
```

### 3. CI/CD Setup

```yaml
# GitHub Actions example
env:
  MYRAGDB_CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
  MYRAGDB_GPT_API_KEY: ${{ secrets.GPT_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: myragdb agent execute code_analysis --param code="..."
```

### 4. Web Application

```python
# Flask app with OAuth
@app.route('/auth/oauth/callback')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')

    auth = AuthenticationManager()
    credential = auth.complete_oauth(
        provider='claude',
        auth_code=code,
        state=state
    )

    if credential:
        session['credential_id'] = credential.credential_id
        return redirect('/dashboard')
    else:
        return 'OAuth failed', 400
```

---

## Troubleshooting

### "No default credential for provider"

```bash
# Check available credentials
myragdb auth list --provider claude

# Add credential if missing
myragdb auth api-key add --provider claude

# Set as default if multiple exist
myragdb auth default <credential-id>
```

### "Failed to authenticate"

```bash
# Check if credential is active
myragdb auth list

# Check if credential is valid
myragdb auth api-key list --provider claude

# Try different authentication method
myragdb auth oauth login --provider claude
```

### "Credential not found"

```bash
# List all credentials
myragdb auth list

# Verify credential ID
myragdb auth api-key list --json

# Use correct ID for operations
myragdb auth default <correct-id>
```

### "File permission denied"

```bash
# Check ~/.myragdb/ permissions
ls -la ~/.myragdb/

# Should see user ownership and 0o600 permissions
# Fix if needed:
chmod 600 ~/.myragdb/credentials.json
chmod 600 ~/.myragdb/keys/api_keys.json
chmod 600 ~/.myragdb/oauth/tokens.json
```

---

## API Reference

### Endpoints

#### API Key Endpoints
- `POST /api/v1/auth/credentials/api-key` - Create API key credential
- `GET /api/v1/auth/credentials/api-key` - List API key credentials
- `DELETE /api/v1/auth/credentials/{id}` - Delete credential

#### OAuth Endpoints
- `POST /api/v1/auth/oauth/initiate` - Start OAuth flow
- `POST /api/v1/auth/oauth/complete` - Complete OAuth flow
- `GET /api/v1/auth/oauth/credentials` - List OAuth credentials

#### Device Code Endpoints
- `POST /api/v1/auth/device-code/initiate` - Start device code flow
- `POST /api/v1/auth/device-code/complete` - Complete device code flow
- `GET /api/v1/auth/device-code/credentials` - List device code credentials

#### General Endpoints
- `GET /api/v1/auth/credentials` - List all credentials
- `GET /api/v1/auth/credentials/default/{provider}` - Get default credential
- `PATCH /api/v1/auth/credentials/{id}/default` - Set as default
- `POST /api/v1/auth/credentials/{id}/revoke` - Revoke credential

---

## Security Considerations

1. **Never hardcode API keys** - Use environment variables or credential manager
2. **Rotate credentials regularly** - Replace old credentials periodically
3. **Use OAuth for user applications** - More secure than API keys
4. **Use Device Code for automation** - Better than key exposure in terminal
5. **Restrict file permissions** - Credentials stored with 0o600 (user-only)
6. **Revoke unused credentials** - Delete old/test credentials
7. **Monitor credential usage** - Track which credentials are active
8. **Separate by environment** - Use different credentials for dev/prod

---

## Questions

For questions about authentication:
- Check examples in this guide
- Review API documentation at `/api/docs`
- See CLI help: `myragdb auth --help`
- Review implementation: `src/myragdb/auth/`

Questions: libor@arionetworks.com
