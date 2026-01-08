# Cloud LLM Configuration Guide
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/CLOUD_LLM_CONFIGURATION.md
**Description:** Step-by-step instructions for configuring Claude, ChatGPT, and Gemini
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-08

---

## Overview

MyRAGDB supports three cloud LLM providers:
- **Claude** (Anthropic)
- **ChatGPT** (OpenAI)
- **Gemini** (Google)

Each provider has three authentication methods:
1. **API Key** (Simplest - recommended for getting started)
2. **OAuth** (Web-based - for production apps)
3. **Device Code / CLI** (Terminal-based - for developers)

---

## Method 1: API Key Setup (Easiest - Start Here!)

This is the simplest method and works immediately.

### Step 1: Get Your API Key

#### For Claude (Anthropic):
1. Go to https://console.anthropic.com
2. Sign in or create account
3. Click "API Keys" in left menu
4. Click "Create Key"
5. Copy the API key (starts with `sk-ant-`)
6. Keep this key secret!

#### For ChatGPT (OpenAI):
1. Go to https://platform.openai.com/api/keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the API key (starts with `sk-`)
5. Keep this key secret!

#### For Gemini (Google):
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the API key
5. Keep this key secret!

### Step 2: Configure in MyRAGDB UI

1. **Open MyRAGDB** at `http://localhost:3003`

2. **Click the "Cloud LLM Manager" tab**

3. **Select your provider**
   - Click the tab for "Claude", "ChatGPT", or "Gemini"
   - You'll see provider details appear below

4. **Select "API Key" authentication method**
   - Radio button should be selected
   - You'll see an "API Key Input" field appear

5. **Paste your API key**
   - Click in the API Key input field
   - Paste your key (Ctrl+V or Cmd+V)
   - Do NOT include any extra spaces or quotes

6. **Test the credentials**
   - Click the "✅ Validate Credentials" button
   - Wait for response (should show "✅ Credentials valid for [provider]")
   - If it fails, check:
     - API key is pasted correctly (no spaces at start/end)
     - Key hasn't expired
     - Your account is still active

7. **Activate the provider**
   - Click "Switch to [Provider]" button
   - You should see "✅ Successfully switched to [provider]!"
   - The session indicator at top should now show the active provider

### Done! Your cloud LLM is now configured.

---

## Method 2: OAuth Setup (Web-Based - For Production)

OAuth is more secure for production as you never paste API keys.

### Step 1: Get OAuth Credentials from Provider

#### For Claude (Anthropic):
1. OAuth support for Claude is in development
2. For now, use API Key method above
3. Note: Device code method coming soon

#### For ChatGPT (OpenAI):
1. Go to https://platform.openai.com/account/api-keys (alternative: use API key method first)
2. OAuth setup requires registering your app
3. For development: API Key method is simpler

#### For Gemini (Google):
1. Go to Google Cloud Console: https://console.cloud.google.com
2. Create a new project
3. Enable "Google Generative AI API"
4. Create OAuth 2.0 credentials
5. Add `http://localhost:3003/api/llm/oauth/callback` to Authorized redirect URIs

### Step 2: Configure OAuth in MyRAGDB

1. **Open MyRAGDB** at `http://localhost:3003`

2. **Click the "Cloud LLM Manager" tab**

3. **Select your provider** (e.g., "Gemini")

4. **Select "OAuth" authentication method**

5. **Click "Open OAuth Login"**
   - A new browser window will open with provider's login page
   - Sign in with your provider account
   - Click "Allow" or "Authorize" when prompted
   - You'll be redirected back to MyRAGDB

6. **Done!**
   - Session should show "✅ [Provider] configured"

---

## Method 3: CLI Device Code (Terminal-Based - For Developers)

This method is best for terminal/development workflows.

### Step 1: Start Device Code Flow

1. **Open MyRAGDB** at `http://localhost:3003`

2. **Click the "Cloud LLM Manager" tab**

3. **Select your provider**

4. **Select "CLI Device Code" authentication method**

5. **Click "Generate Device Code"**
   - You'll see:
     - User Code (e.g., "ABC-123")
     - Verification URL (e.g., "https://provider.com/device")
     - Instructions

### Step 2: Authorize on Provider Website

1. **Visit the verification URL** shown in the UI
   - Opens in your browser

2. **Sign in** to your provider account

3. **Enter the device code** (the short code like "ABC-123")

4. **Click "Authorize"** or "Allow"

### Step 3: MyRAGDB Will Detect Authorization

- MyRAGDB automatically polls for approval
- Once you authorize, it will detect and save credentials
- Session will show provider as configured

---

## Troubleshooting

### "Invalid API Key" Error

**For Claude:**
- Key must start with `sk-ant-`
- Check at https://console.anthropic.com your key hasn't expired
- Key must have "Generate API key" permissions

**For ChatGPT:**
- Key must start with `sk-`
- Check at https://platform.openai.com/account/api-keys the key hasn't expired
- Ensure you selected "Secret key" not "Public key"

**For Gemini:**
- Key must be from https://makersuite.google.com/app/apikey
- API key must have "Generative Language API" access
- Check your billing account is active

### OAuth Window Doesn't Open

1. Check browser popup blockers
2. Try again with popup blocker disabled
3. Use API Key method instead as fallback

### Device Code Keeps Asking

1. Make sure you clicked "Authorize" on provider website
2. Check URL was entered correctly
3. Device code expires after 15 minutes - restart if expired

### "Credentials Already Stored"

You already have credentials for this provider. To switch:
1. Use "Switch" button to switch to different provider
2. Or delete old credentials first via credentials management (if available)

---

## Using Your Configured LLM

### In Search UI

Once configured, your cloud LLM becomes available in:
- **LLM Chat Tester** - Test the LLM's ability to search your codebase
- Use the `search_codebase` tool to perform intelligent searches
- LLM can understand context and make better search queries

### API Usage (For Developers)

Once configured, the API automatically uses your configured LLM:

```python
from myragdb import SearchClient

client = SearchClient("http://localhost:3003")

# This automatically uses your configured cloud LLM
response = client.search("authentication flow", use_ai=True)
```

---

## Switching Providers

To switch from one provider to another:

1. **Select new provider tab**
   - Click Claude, ChatGPT, or Gemini tab

2. **Select authentication method**
   - API Key (recommended)
   - OAuth
   - Device Code

3. **Enter credentials**
   - For API Key: paste your key
   - For OAuth: click login button
   - For Device Code: follow on-screen instructions

4. **Click "Switch to [Provider]"**
   - Your active LLM is now switched

The system automatically:
- Validates new credentials
- Stores them securely (encrypted)
- Updates active session
- Clears old input fields

---

## Security Notes

### API Keys
- API keys are encrypted before storing
- Stored in `~/.myragdb/credentials.json` with encryption
- Never pasted or logged
- Can be deleted anytime from "Delete Credential" button

### OAuth Tokens
- Access tokens obtained via OAuth are also encrypted
- Tokens refresh automatically
- Can be revoked from provider website anytime

### Device Codes
- Device codes expire after 15 minutes
- One-time use
- No credentials stored locally after approval

---

## Getting Help

If configuration fails:

1. **Check your internet connection** - APIs require connectivity
2. **Verify API key is correct** - Copy/paste carefully
3. **Check provider account** - Ensure account is active and not suspended
4. **Check MyRAGDB logs** - Look in terminal for error details

For API key validation errors:
- Claude: Check https://console.anthropic.com status
- ChatGPT: Check https://status.openai.com
- Gemini: Check Google Cloud Console for API status

---

## Next Steps

Once configured:
1. Go to "LLM Chat Tester" to test your LLM
2. Ask it to search your codebase using the `search_codebase` tool
3. See how it intelligently uses search filters to find relevant code

Questions: libor@arionetworks.com
