# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/TOOL_MONITORING_GUIDE.md
# Description: Comprehensive guide for monitoring tool usage in MyRAGDB
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

# How to Monitor Tool Usage in MyRAGDB

**Question:** "ok right now I have only one tool but in future how will I know that it is calling my tools?"

**Answer:** You have FOUR different monitoring methods available, each showing different aspects of tool calling.

---

## Method 1: HTTP Middleware Console Logs (RECOMMENDED)

**Where:** Terminal running the middleware (port 8093)

**What to Look For:**
```
============================================================
🔍 SEARCH REQUEST
============================================================
Query: authentication functions
Type: hybrid
Limit: 20
============================================================

✅ SEARCH COMPLETE
Total Results: 20
Search Time: 344.88ms
Top Result: /path/to/file.ts
============================================================
```

**How to Start Monitoring:**
```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m mcp_server.http_middleware
```

**Advantages:**
- Real-time visibility
- Shows all tool calls from all LLMs
- Most reliable indicator
- Shows search parameters and results

**When You'll See It:**
- Every time ANY LLM calls ANY tool through the middleware
- Even if the chat UI doesn't display it correctly

---

## Method 2: Chat UI Visual Indicators

**Where:** Browser at `web-ui/llm-chat-tester.html`

**What to Look For:**
```
🔧 Tool Call: search_codebase
{
  "query": "authentication functions",
  "search_type": "hybrid",
  "limit": 20
}

📊 Tool Result:
{
  "total_results": 20,
  "search_time_ms": 344.88,
  "results": [...]
}
```

**How to Enable:**
Already enabled - should display automatically when LLM makes a tool call.

**Current Issue:**
The LLM IS calling the tool (proven by middleware logs), but these visual indicators aren't showing up. This is likely because:

1. **The LLM might be calling the tool internally without exposing it in the response**
2. **The response format might not include `tool_calls` array**
3. **The LLM might be integrating the tool result directly into its answer**

**Why This Matters:**
Even if you don't see 🔧/📊 messages, if the middleware logs show activity, the tool IS working.

---

## Method 3: Browser Developer Console

**Where:** Browser → Right-click → Inspect → Console tab

**What to Look For:**
```javascript
// Outgoing request to LLM
POST http://localhost:8085/v1/chat/completions
{
  "tools": [{"function": {"name": "search_codebase", ...}}],
  "tool_choice": "auto"
}

// LLM response with tool call
{
  "choices": [{
    "message": {
      "tool_calls": [{
        "function": {
          "name": "search_codebase",
          "arguments": "{\"query\": \"...\"}"
        }
      }]
    }
  }]
}

// Tool execution
POST http://localhost:8093/search
{
  "query": "authentication functions",
  "search_type": "hybrid",
  "limit": 20
}
```

**How to Use:**
1. Open chat UI in browser
2. Right-click → Inspect → Console tab
3. Send a query that should trigger tool usage
4. Watch network requests in real-time

**Advantages:**
- See exact JSON payloads
- Verify tool definitions are sent to LLM
- Check if LLM is returning tool_calls in response
- Debug why visual indicators might not appear

---

## Method 4: MyRAGDB API Server Logs

**Where:** Terminal running MyRAGDB API (port 3003)

**What to Look For:**
```
INFO:     127.0.0.1:xxxxx - "POST /search/hybrid HTTP/1.1" 200 OK
```

**How to Start Monitoring:**
```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m myragdb.api.server
```

**Advantages:**
- Shows ultimate downstream impact
- Confirms search actually executed
- Less detailed than middleware logs

---

## Adding Future Tools: Monitoring Checklist

When you add more tools in the future, here's how to ensure they're monitorable:

### Step 1: Add Tool Definition to Middleware

**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/llm_tool_definitions.json`

```json
{
  "openai_format": {
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "search_codebase",
          "description": "...",
          "parameters": {...}
        }
      },
      {
        "type": "function",
        "function": {
          "name": "index_repository",  // ← NEW TOOL
          "description": "Index a new repository into MyRAGDB",
          "parameters": {
            "type": "object",
            "properties": {
              "repo_path": {
                "type": "string",
                "description": "Absolute path to repository"
              }
            },
            "required": ["repo_path"]
          }
        }
      }
    ]
  }
}
```

### Step 2: Add Endpoint to HTTP Middleware

**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/http_middleware.py`

```python
@app.post("/index")
async def index_repository(request: IndexRequest):
    """Index a new repository."""

    # Log incoming request
    print(f"\n{'='*60}")
    print(f"📚 INDEX REQUEST")
    print(f"{'='*60}")
    print(f"Repository: {request.repo_path}")
    print(f"{'='*60}\n")

    # Call MyRAGDB API
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{MYRAGDB_URL}/repositories/add",
            json={"repository_path": request.repo_path}
        )

        # Log result
        print(f"✅ INDEX COMPLETE")
        print(f"Repository: {request.repo_path}")
        print(f"{'='*60}\n")

        return response.json()
```

### Step 3: Update Chat UI Tool List

**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/llm-chat-tester.html`

Add the new tool to the `tools` array in `sendMessage()`:

```javascript
tools: [
    {
        type: 'function',
        function: {
            name: 'search_codebase',
            description: '...',
            parameters: {...}
        }
    },
    {
        type: 'function',
        function: {
            name: 'index_repository',  // ← NEW TOOL
            description: 'Index a new repository into MyRAGDB',
            parameters: {
                type: 'object',
                properties: {
                    repo_path: {
                        type: 'string',
                        description: 'Absolute path to repository'
                    }
                },
                required: ['repo_path']
            }
        }
    }
]
```

### Step 4: Add Tool Execution Handler

**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/llm-chat-tester.html`

Update `executeToolCall()` function:

```javascript
async function executeToolCall(toolName, args) {
    if (toolName === 'search_codebase') {
        const response = await fetch(`${CONFIG.myragdb}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(args)
        });
        return await response.json();
    }
    else if (toolName === 'index_repository') {  // ← NEW TOOL
        const response = await fetch(`${CONFIG.myragdb}/index`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(args)
        });
        return await response.json();
    }
    else {
        throw new Error(`Unknown tool: ${toolName}`);
    }
}
```

---

## Monitoring Best Practices

### 1. Always Check Middleware Logs First

**Why:** The middleware logs are the SINGLE SOURCE OF TRUTH for tool usage.

**Example:**
```
User: "The chat UI isn't showing tool calls!"
You: Check middleware logs → 🔍 SEARCH REQUEST visible → Tool IS working
Conclusion: UI display issue, not tool issue
```

### 2. Use Unique Emoji Indicators for Each Tool

**Current Tools:**
- 🔍 `search_codebase` - Search request
- ✅ Generic completion marker

**Future Tools (Suggested):**
- 📚 `index_repository` - Indexing request
- 🗑️ `delete_repository` - Deletion request
- 📊 `get_stats` - Statistics request
- 🔄 `reindex_repository` - Reindexing request

**Implementation:**
```python
# In http_middleware.py
TOOL_EMOJIS = {
    'search': '🔍',
    'index': '📚',
    'delete': '🗑️',
    'stats': '📊',
    'reindex': '🔄'
}

@app.post("/index")
async def index_repository(request: IndexRequest):
    print(f"\n{'='*60}")
    print(f"{TOOL_EMOJIS['index']} INDEX REQUEST")  # ← Use emoji map
    print(f"{'='*60}")
```

### 3. Add Timestamps to Logs

**Enhancement:**
```python
from datetime import datetime

@app.post("/search")
async def search(request: SearchRequest):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*60}")
    print(f"🔍 SEARCH REQUEST [{timestamp}]")  # ← Add timestamp
    print(f"{'='*60}")
```

### 4. Create a Tool Usage Dashboard

**Future Enhancement Idea:**

Create a simple dashboard that shows:
- Total tool calls today
- Most frequently called tools
- Average response times
- Error rates per tool

**Implementation:**
Store metrics in SQLite database and expose via `/metrics` endpoint.

---

## Troubleshooting Tool Monitoring

### Issue: No logs appear in middleware console

**Check:**
1. Is middleware running? `lsof -i :8093`
2. Is LLM configured with function calling? Check for `--jinja` flag
3. Is chat UI using correct middleware URL? Should be `http://localhost:8093`

**Fix:**
```bash
# Restart middleware
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m mcp_server.http_middleware
```

### Issue: Chat UI doesn't show 🔧 Tool Call messages

**Possible Causes:**
1. **LLM is calling tool but not exposing in response** (this is what happened with Qwen Coder)
2. **Response format doesn't include `tool_calls` array**
3. **JavaScript code isn't parsing response correctly**

**How to Debug:**
1. Open browser console (F12 → Console tab)
2. Send a test query
3. Look for LLM response JSON
4. Check if `choices[0].message.tool_calls` exists
5. If it does: JS parsing bug
6. If it doesn't: LLM is calling tool internally without exposing it

**Current Behavior with Qwen Coder:**
- Middleware logs: ✅ Show tool call (proof it works)
- Chat UI: ❌ No 🔧 message (display issue)
- LLM response: Contains search results (tool was used)
- Conclusion: Tool works, LLM just integrates result silently

### Issue: Middleware shows request but no result

**Check:**
1. Did MyRAGDB API respond? Check MyRAGDB logs
2. Is search index populated? Run `python -m myragdb.cli search "test"`
3. Is request timing out? Check for timeout errors

**Fix:**
Increase timeout in middleware:
```python
# In http_middleware.py
TIMEOUT = 60.0  # Increase from 30.0 to 60.0
```

---

## Quick Reference: Where to Look

| Question | Where to Look |
|----------|---------------|
| "Is the tool being called?" | Middleware console logs (🔍 markers) |
| "What parameters were sent?" | Middleware console logs (detailed output) |
| "How fast was the response?" | Middleware logs (search_time_ms) |
| "Why isn't UI showing tool calls?" | Browser dev console → Network tab |
| "What tools are available?" | `llm_tool_definitions.json` |
| "How do I add a new tool?" | This guide → "Adding Future Tools" section |
| "Is MyRAGDB API working?" | MyRAGDB API logs (port 3003) |

---

## Summary: The Four Monitoring Layers

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Chat UI Visual Indicators (🔧/📊)         │
│ - User-facing display                               │
│ - May not always show (depends on LLM response)     │
│ - Nice to have, not critical                        │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Layer 2: Browser Dev Console                       │
│ - Shows raw JSON requests/responses                │
│ - Debug tool for developers                         │
│ - Reveals why Layer 1 might not work               │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Layer 3: HTTP Middleware Logs (MOST RELIABLE) ✅   │
│ - SINGLE SOURCE OF TRUTH                           │
│ - Shows 🔍 markers and detailed parameters         │
│ - ALWAYS check here first                          │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Layer 4: MyRAGDB API Logs                          │
│ - Final destination                                 │
│ - Confirms search actually executed                 │
│ - Less detailed than Layer 3                        │
└─────────────────────────────────────────────────────┘
```

**Golden Rule:** If Layer 3 (middleware logs) shows tool activity, the integration is working correctly, regardless of what any other layer shows.

---

Questions: libor@arionetworks.com
