# MyRAGDB MCP Server

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/README.md
**Description:** Documentation for the MyRAGDB Model Context Protocol server
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-05

---

## Overview

The MyRAGDB MCP Server exposes MyRAGDB's search capabilities through the **Model Context Protocol (MCP)**, making it natively accessible to Claude, Claude Code, and other MCP-compatible LLMs.

## Business Purpose

Allows LLMs to discover and search across your indexed codebases directly, without manual API integration. The LLM can autonomously:
- Search for code patterns and implementations
- Find documentation and examples
- Understand how features work across projects
- Locate specific files, functions, or configurations

## Installation

### 1. Install MCP SDK

```bash
pip install mcp
```

### 2. Configure Claude Code

Add to `~/.config/claude-code/mcp_servers.json`:

```json
{
  "myragdb": {
    "command": "python",
    "args": [
      "-m",
      "mcp_server.server"
    ],
    "cwd": "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb",
    "env": {
      "PYTHONPATH": "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb"
    }
  }
}
```

### 3. Start MyRAGDB Server

The MCP server connects to your MyRAGDB API server, so make sure it's running:

```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m myragdb.api.server
```

### 4. Restart Claude Code

Restart Claude Code to load the MCP server configuration.

## Available Tools

The MCP server exposes these tools to Claude:

### 1. `search_codebase`
Hybrid keyword + semantic search across all codebases.

**Example Claude usage:**
```
"Find where JWT authentication is implemented"
"Show me how database migrations work"
"Where is the user registration flow?"
```

### 2. `search_semantic`
Semantic-only search for understanding concepts.

**Example Claude usage:**
```
"How do users authenticate in this codebase?"
"What patterns are used for error handling?"
```

### 3. `search_keyword`
Keyword-only search for exact matches.

**Example Claude usage:**
```
"Find the definition of 'authenticate_user' function"
"Where is 'class UserModel' defined?"
```

### 4. `get_index_stats`
Get statistics about indexed repositories.

**Example Claude usage:**
```
"What codebases are indexed?"
"How many files are in the index?"
```

### 5. `list_repositories`
List all available repositories.

**Example Claude usage:**
```
"What repositories can I search?"
"Show me all indexed projects"
```

## How It Works

1. **Claude** sends MCP tool call request
2. **MCP Server** receives request via stdio
3. **MCP Server** calls MyRAGDB HTTP API (`http://localhost:3003`)
4. **MyRAGDB** performs search (keyword + vector)
5. **MCP Server** formats results as markdown
6. **Claude** receives results and uses them to answer user

## Architecture

```
┌─────────┐         MCP Protocol        ┌─────────────┐
│ Claude  │◄────────(stdio)────────────►│ MCP Server  │
└─────────┘                              └─────────────┘
                                                │
                                                │ HTTP
                                                │
                                         ┌──────▼──────┐
                                         │  MyRAGDB    │
                                         │  API Server │
                                         └─────────────┘
                                                │
                                         ┌──────┴──────┐
                                         │             │
                                    ┌────▼────┐  ┌────▼────┐
                                    │Meili-   │  │ChromaDB │
                                    │search   │  │(Vectors)│
                                    └─────────┘  └─────────┘
```

## Testing

Test the MCP server manually:

```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m mcp_server.server
```

The server will wait for MCP protocol messages on stdin.

## Troubleshooting

### "Connection refused" or "HTTP error"

Make sure MyRAGDB API server is running:
```bash
python -m myragdb.api.server
```

### "MCP not found" error

Install the MCP SDK:
```bash
pip install mcp
```

### Claude doesn't see the tools

1. Check `~/.config/claude-code/mcp_servers.json` is correct
2. Restart Claude Code
3. Check Claude Code logs for MCP errors

### Search returns no results

1. Check if any repositories are indexed: `python -m myragdb.cli stats`
2. Re-index if needed: Use the web UI at `http://localhost:3003`

## Configuration

### Change MyRAGDB Server URL

Edit `mcp_server/server.py`:

```python
MYRAGDB_URL = "http://localhost:3003"  # Change to your URL
```

### Adjust Timeout

```python
TIMEOUT = 30.0  # Increase for large searches
```

## Example Conversations

**User:** "Find where authentication is implemented"

**Claude:** *Uses `search_codebase` tool with query "authentication implementation"*

**Result:** Claude shows relevant files with authentication code and explains the implementation.

---

**User:** "How do database migrations work in this project?"

**Claude:** *Uses `search_semantic` tool to understand the concept*

**Result:** Claude finds migration-related code and documentation, explains the migration process.

---

Questions: libor@arionetworks.com
