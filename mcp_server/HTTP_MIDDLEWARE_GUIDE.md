# MyRAGDB HTTP Middleware Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/HTTP_MIDDLEWARE_GUIDE.md
**Description:** Guide for using MyRAGDB with local LLMs via HTTP middleware
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-05

---

## Overview

The HTTP middleware provides a **simple REST API** wrapper around MyRAGDB's search functionality, making it accessible to **any local LLM** that can make HTTP requests.

### Architecture

```
Local LLM (Ollama/LM Studio/etc)
    ↓ HTTP (port 8093)
HTTP Middleware
    ↓ HTTP (port 3003)
MyRAGDB API
    ↓
Meilisearch + ChromaDB
```

---

## Quick Start

### 1. Start MyRAGDB API Server

```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m myragdb.api.server
```

Server runs on: `http://localhost:3003`

### 2. Start HTTP Middleware

```bash
# In a new terminal
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m mcp_server.http_middleware
```

Middleware runs on: `http://localhost:8093`

### 3. Test the Middleware

```bash
# Health check
curl http://localhost:8093/health

# Search
curl -X POST http://localhost:8093/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "limit": 5}'
```

---

## API Endpoints

### Health & Info

#### `GET /`
Get API information and available endpoints.

#### `GET /health`
Check if middleware and MyRAGDB API are healthy.

**Response:**
```json
{
  "status": "healthy",
  "middleware": "ok",
  "myragdb_api": "healthy",
  "myragdb_url": "http://localhost:3003"
}
```

---

### Search

#### `POST /search`
Search across indexed codebases.

**Request:**
```json
{
  "query": "authentication flow JWT token",
  "search_type": "hybrid",
  "limit": 10,
  "min_score": 0.0,
  "repositories": ["xLLMArionComply"],
  "file_types": [".py", ".ts"],
  "folder_filter": "src/"
}
```

**Parameters:**
- `query` (required): Search query text
- `search_type` (optional): `"hybrid"` (default), `"semantic"`, or `"keyword"`
- `limit` (optional): Max results (1-100, default: 10)
- `min_score` (optional): Minimum relevance score (0.0-1.0)
- `repositories` (optional): Filter by repository names
- `file_types` (optional): Filter by file extensions
- `folder_filter` (optional): Filter by folder path

**Response:**
```json
{
  "query": "authentication flow JWT token",
  "search_type": "hybrid",
  "total_results": 5,
  "search_time_ms": 245.3,
  "results": [
    {
      "file_path": "/path/to/file.py",
      "repository": "xLLMArionComply",
      "relative_path": "src/auth/login.py",
      "score": 0.85,
      "snippet": "def authenticate_user(username, password)...",
      "file_type": "py",
      "keyword_score": 0.7,
      "vector_score": 0.9
    }
  ]
}
```

---

### Repository Management

#### `GET /repositories`
List all indexed repositories.

**Response:**
```json
[
  {
    "name": "xLLMArionComply",
    "path": "/path/to/repo",
    "enabled": true,
    "priority": "high"
  }
]
```

#### `POST /discover`
Discover new Git repositories.

**Request:**
```json
{
  "root_path": "/Users/username/projects",
  "max_depth": 2
}
```

#### `POST /repositories/add`
Add new repositories to index.

**Request:**
```json
["/path/to/repo1", "/path/to/repo2"]
```

---

### Indexing

#### `POST /reindex`
Trigger repository re-indexing.

**Request:**
```json
{
  "repositories": [],
  "full_reindex": false
}
```

**Parameters:**
- `repositories`: List of repo names (empty = all)
- `full_reindex`: `true` for full, `false` for incremental

#### `GET /stats`
Get indexing statistics.

**Response:**
```json
{
  "total_files": 1234,
  "total_repositories": 5,
  "repositories": {
    "xLLMArionComply": {
      "file_count": 567,
      "last_indexed": "2026-01-05T10:30:00"
    }
  }
}
```

---

## Interactive API Documentation

Visit: `http://localhost:8093/docs`

FastAPI provides automatic interactive documentation where you can:
- See all endpoints
- Try API calls directly in the browser
- View request/response schemas
- Test with example data

---

## Using with Local LLMs

### Ollama with Function Calling

Configure Ollama to use MyRAGDB as a tool:

```json
{
  "name": "search_codebase",
  "description": "Search across indexed codebases for code, documentation, and files",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "limit": {
        "type": "integer",
        "description": "Maximum results",
        "default": 10
      }
    },
    "required": ["query"]
  },
  "endpoint": "http://localhost:8093/search",
  "method": "POST"
}
```

### LM Studio

1. Start LM Studio with API server enabled
2. Configure function calling with the tool definition above
3. Make HTTP calls to `http://localhost:8093/search`

### OpenAI-Compatible APIs

Any tool that supports OpenAI's function calling format can use:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "search_codebase",
        "description": "Search indexed codebases",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    }
}]
```

Then implement the function to call `http://localhost:8093/search`.

---

## Example: Python Client

```python
import requests

def search_codebases(query: str, limit: int = 10):
    """Search codebases using MyRAGDB middleware."""
    response = requests.post(
        "http://localhost:8093/search",
        json={
            "query": query,
            "search_type": "hybrid",
            "limit": limit
        }
    )
    return response.json()

# Use it
results = search_codebases("authentication flow", limit=5)
for result in results["results"]:
    print(f"{result['file_path']} (score: {result['score']})")
    print(f"  {result['snippet'][:100]}...")
```

---

## Example: Curl Commands

```bash
# Search for authentication code
curl -X POST http://localhost:8093/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication JWT token",
    "search_type": "hybrid",
    "limit": 5
  }'

# List repositories
curl http://localhost:8093/repositories

# Get statistics
curl http://localhost:8093/stats

# Discover new repositories
curl -X POST http://localhost:8093/discover \
  -H "Content-Type: application/json" \
  -d '{
    "root_path": "/Users/username/projects",
    "max_depth": 2
  }'

# Trigger reindex
curl -X POST http://localhost:8093/reindex \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": [],
    "full_reindex": false
  }'
```

---

## Security Considerations

### Local Only

The middleware is designed for **local use only**:
- Binds to `0.0.0.0` by default (accessible on local network)
- No authentication required
- **Do NOT expose to the internet**

### Production Use

For production:
1. Add API key authentication
2. Use HTTPS/TLS
3. Bind to `127.0.0.1` only
4. Add rate limiting
5. Implement request logging

---

## Performance

- **Search latency**: ~200-300ms (hybrid search)
- **Throughput**: ~50-100 requests/second
- **Concurrent requests**: Handled by FastAPI async

---

## Troubleshooting

### Middleware won't start

**Error:** `Address already in use`

**Solution:** Port 8093 is in use. Start on different port:
```bash
python -m mcp_server.http_middleware --port 8081
```

### "MyRAGDB API unavailable"

**Cause:** MyRAGDB API not running

**Solution:**
```bash
# Start MyRAGDB API first
python -m myragdb.api.server
```

### CORS errors in browser

**Solution:** CORS is already enabled. Check browser console for specific error.

---

## Comparison: MCP vs HTTP Middleware

| Feature | MCP Server | HTTP Middleware |
|---------|-----------|-----------------|
| **Protocol** | stdio (JSON-RPC) | HTTP REST |
| **Port** | None | 8093 |
| **Clients** | MCP-compatible LLMs | Any HTTP client |
| **Best For** | Claude Code, Claude | Ollama, LM Studio, custom |
| **Ease of Use** | Automatic for MCP clients | Requires HTTP calls |
| **Performance** | Lower overhead | Slightly higher latency |

---

## Advanced: Custom Port and Host

```python
# Start on custom port
python -c "from mcp_server.http_middleware import start_server; start_server(port=9000)"

# Localhost only (more secure)
python -c "from mcp_server.http_middleware import start_server; start_server(host='127.0.0.1', port=8093)"
```

---

## Next Steps

1. **Start both servers** (MyRAGDB API + HTTP middleware)
2. **Test with curl** to verify it works
3. **Configure your LLM** with the tool definitions
4. **Try a search query** through your LLM

---

Questions: libor@arionetworks.com
