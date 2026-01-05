# MyRAGDB Chat UI Testing Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/CHAT_UI_GUIDE.md
**Description:** Guide for testing LLMs with MyRAGDB search tool via chat interface
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-05

---

## Quick Start

### 1. Open the Chat UI

```bash
open /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/llm-chat-tester.html
```

Or double-click the file in Finder.

### 2. Select an LLM

The dropdown shows all your available LLMs:
- Phi-3 (port 8081)
- SmolLM3 (port 8082)
- Mistral 7B (port 8083)
- Qwen 2.5 32B (port 8084)
- Qwen Coder 7B (port 8085)
- Hermes 3 Llama 8B (port 8086)
- Llama 3.1 8B (port 8087)
- Llama 4 Scout 17B (port 8088)
- Mistral Small 24B (port 8089)
- DeepSeek R1 Qwen 32B (port 8092)

### 3. Test Connection

Click **"Test Connection"** to verify the LLM is running.

### 4. Try a Search Query

Example prompts that will trigger the search tool:

```
Search for authentication code in my repositories
```

```
Find examples of JWT token validation
```

```
Show me how API endpoints are defined
```

```
Look for error handling patterns
```

---

## How to Know When Tool is Being Used

### Visual Indicators in Chat UI

When the LLM uses the MyRAGDB search tool, you'll see:

1. **🔧 Tool Call** message showing:
   ```json
   {
     "query": "authentication",
     "search_type": "hybrid",
     "limit": 10
   }
   ```

2. **📊 Tool Result** message showing:
   ```json
   {
     "query": "authentication",
     "total_results": 5,
     "search_time_ms": 254.5,
     "results": [...]
   }
   ```

3. **Final LLM Response** using the search results

### Console Logs (Middleware)

The middleware running on port 8093 logs every search request:

```bash
# Watch middleware logs
tail -f <(ps aux | grep '[p]ython -m mcp_server.http_middleware')
```

You'll see output like:

```
============================================================
🔍 SEARCH REQUEST
============================================================
Query: authentication flow
Type: hybrid
Limit: 10
============================================================

✅ SEARCH COMPLETE
Total Results: 5
Search Time: 254.58ms
Top Result: /path/to/file.py
============================================================
```

### HTTP Access Logs

The uvicorn server logs show HTTP requests:

```
INFO:     127.0.0.1:54648 - "POST /search HTTP/1.1" 200 OK
```

---

## Example Conversation Flow

**You:** "Search for authentication code in my repositories"

**LLM thinks:** _I need to use the search_codebase tool_

**Tool Call (visible in UI):**
```json
{
  "query": "authentication code",
  "search_type": "hybrid",
  "limit": 10
}
```

**Tool Result (visible in UI):**
```json
{
  "total_results": 5,
  "results": [
    {
      "file_path": "/path/to/auth.py",
      "score": 0.85,
      "snippet": "def authenticate_user()..."
    }
  ]
}
```

**LLM Response:** "I found 5 files related to authentication in your repositories..."

---

## Monitoring Tool Usage

### Option 1: Watch Middleware Logs Live

```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb

# Method 1: Watch background process output
ps aux | grep '[p]ython -m mcp_server.http_middleware'

# Method 2: If you started middleware manually
tail -f /path/to/middleware.log
```

### Option 2: Check Middleware Console

If you started the middleware in a terminal, you'll see real-time logs:

```
============================================================
🔍 SEARCH REQUEST
============================================================
Query: your search query here
Type: hybrid
Limit: 10
============================================================
```

### Option 3: MyRAGDB API Logs

Check the main API server logs:

```bash
tail -f /tmp/myragdb_server.log
```

### Option 4: Use Browser Developer Tools

1. Open the chat UI
2. Press F12 (or Cmd+Option+I on Mac)
3. Go to **Console** tab
4. You'll see JavaScript logs showing tool calls and results

---

## Testing Different LLMs

### Test Which LLMs Support Function Calling

Not all LLMs support function calling equally well. Test each one:

1. Select LLM from dropdown
2. Send: "Search for authentication"
3. Check if tool is called

**Good signs:**
- 🔧 Tool Call appears
- 📊 Tool Result appears
- LLM uses the results in response

**Bad signs:**
- LLM tries to answer without calling tool
- LLM says "I don't have access to your repositories"
- No tool call messages appear

### Best LLMs for Function Calling

Based on your available models:

1. **Qwen Coder 7B** - Specifically trained for code-related tasks
2. **Llama 3.1 8B** - Good function calling support
3. **Hermes 3 Llama 8B** - Trained for tool use
4. **Mistral 7B** - Decent function calling

**Note:** Some LLMs require the `--jinja` flag when started to support function calling. If you get an error like "tools param requires --jinja flag", the LLM needs to be restarted with a compatible chat template that supports tool calling.

---

## Troubleshooting

### Tool Not Being Called

**Problem:** LLM responds without calling the search tool

**Solutions:**
1. Make your request more explicit: "Use the search_codebase tool to find authentication code"
2. Try a different LLM (some are better at function calling)
3. Check that the LLM's context includes tool definitions (reload page)

### Connection Errors

**Problem:** "Failed to connect to LLM"

**Solutions:**
1. Check LLM is running: `launchctl list | grep llms`
2. Test directly: `curl http://localhost:8081/v1/models`
3. Start LLM if needed: Check LLM controller docs

### MyRAGDB Not Available

**Problem:** "MyRAGDB middleware not available"

**Solutions:**
1. Check middleware is running: `lsof -ti:8093`
2. Start middleware: `cd myragdb && source venv/bin/activate && python -m mcp_server.http_middleware`
3. Check logs: `tail -f /tmp/myragdb_server.log`

### No Search Results

**Problem:** Tool is called but returns empty results

**Solutions:**
1. Check repositories are indexed: `curl http://localhost:3003/stats`
2. Reindex if needed: `python scripts/initial_index.py`
3. Try different search query
4. Check Meilisearch is running: `./scripts/start_meilisearch.sh`

---

## Advanced Usage

### Custom Search Parameters

You can ask the LLM to use specific search parameters:

```
Search for authentication code, but only in Python files
```
→ LLM should add `file_types: [".py"]`

```
Search for error handling in the xLLMArionComply repository
```
→ LLM should add `repositories: ["xLLMArionComply"]`

```
Find JWT validation code, limit to 5 results
```
→ LLM should add `limit: 5`

### Compare LLM Responses

1. Ask same question to multiple LLMs
2. See which one:
   - Calls the tool most reliably
   - Interprets results best
   - Provides most useful response

### Test Edge Cases

```
Search for something that doesn't exist
```
→ Should return empty results, LLM should say "I found no results"

```
Search for a very common term like "function"
```
→ Should return many results, LLM should summarize

```
Ask a question that doesn't need search
```
→ LLM should NOT call the tool (e.g., "What's 2+2?")

---

## Architecture Recap

```
Browser (Chat UI)
    ↓ HTTP POST /v1/chat/completions with tool definitions
Local LLM (port 8081-8092)
    ↓ Decides to use search_codebase tool
    ↓ HTTP POST to http://localhost:8093/search
HTTP Middleware (port 8093)
    ↓ Logs request 🔍
    ↓ HTTP POST to http://localhost:3003/search/hybrid
MyRAGDB API (port 3003)
    ↓ Queries Meilisearch (keyword) + ChromaDB (vector)
    ↓ Returns results
HTTP Middleware (port 8093)
    ↓ Logs results ✅
    ↓ Returns to LLM
Local LLM
    ↓ Formulates response using search results
    ↓ Returns to browser
Browser (Chat UI)
    ↓ Shows: Tool Call → Tool Result → LLM Response
```

---

## Quick Commands Reference

```bash
# Start MyRAGDB API
cd myragdb && ./start.sh

# Start HTTP Middleware
cd myragdb && source venv/bin/activate && python -m mcp_server.http_middleware

# Open Chat UI
open web-ui/llm-chat-tester.html

# Watch Middleware Logs
tail -f <middleware-log-location>

# Check Services
curl http://localhost:3003/health    # MyRAGDB API
curl http://localhost:8093/health    # HTTP Middleware
curl http://localhost:8081/v1/models # LLM (change port for different LLMs)

# Stop Services
./stop.sh  # Stops both API and middleware
```

---

Questions: libor@arionetworks.com
