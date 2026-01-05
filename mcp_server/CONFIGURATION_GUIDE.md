# MyRAGDB MCP Server Configuration Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/CONFIGURATION_GUIDE.md
**Description:** Configuration guide for different LLM CLI tools
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-05

---

## Quick Setup

MCP server configuration files have been created for:
- ✅ **Claude Code**: `~/.config/claude-code/mcp_servers.json`
- ✅ **ChatGPT CLI**: `~/.config/chatgpt-cli/mcp_servers.json`
- ✅ **Gemini CLI**: `~/.config/gemini-cli/mcp_servers.json`

---

## Configuration by CLI Tool

### Claude Code (Anthropic)

**Config Location:** `~/.config/claude-code/mcp_servers.json`

**Status:** ✅ Configured

**Restart Command:**
```bash
# Quit and restart Claude Code application
```

**Test:**
After restart, try asking Claude Code:
```
"Search for authentication in my codebases"
```

Claude should automatically use the `search_codebase` tool.

---

### ChatGPT CLI (OpenAI)

**Config Location:** `~/.config/chatgpt-cli/mcp_servers.json`

**Status:** ✅ Configured (verify CLI tool location)

**Note:** ChatGPT CLI MCP support varies by version. If your CLI tool uses a different config location, check:
- `~/.chatgpt-cli/config.json`
- `~/.config/openai/mcp_servers.json`
- Tool's documentation for MCP configuration

**Restart Command:**
```bash
# Restart your ChatGPT CLI session
chatgpt-cli --reset-session
```

---

### Gemini CLI (Google)

**Config Location:** `~/.config/gemini-cli/mcp_servers.json`

**Status:** ✅ Configured (verify CLI tool location)

**Note:** Gemini CLI MCP support varies by version. Alternative locations:
- `~/.gemini-cli/config.json`
- `~/.config/google/gemini-cli/mcp_servers.json`
- Check tool's documentation for MCP configuration

**Restart Command:**
```bash
# Restart your Gemini CLI session
gemini-cli --new-session
```

---

## Universal Configuration Template

For any MCP-compatible CLI tool, use this configuration:

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

---

## Prerequisites

### 1. MCP SDK Installed
```bash
pip install mcp
```

### 2. MyRAGDB Server Running
```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m myragdb.api.server
```

The server should be accessible at: `http://localhost:3003`

### 3. Python Path
Ensure Python is in your PATH:
```bash
which python
# Should show: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/venv/bin/python
# Or your system Python with mcp installed
```

---

## Available MCP Tools

Once configured, LLMs can use these tools:

### Search Tools
- `search_codebase` - Hybrid keyword + semantic search
- `search_semantic` - Semantic-only search (understanding concepts)
- `search_keyword` - Keyword-only search (exact matches)

### Repository Management
- `list_repositories` - List all indexed repositories
- `add_repositories` - Add new repositories to index
- `enable_repository` - Enable a disabled repository
- `disable_repository` - Disable a repository
- `remove_repository` - Remove repository from index

### Indexing Operations
- `trigger_reindex` - Reindex repositories (incremental or full)
- `discover_repositories` - Scan filesystem for new repos

### Information
- `get_index_stats` - Get statistics about indexed data

---

## Testing the Configuration

### Test 1: Manual MCP Server Start

```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m mcp_server.server
```

The server will wait for MCP protocol messages on stdin. If no errors appear, the server is working.

Press `Ctrl+C` to exit.

### Test 2: Check CLI Tool Logs

Most MCP-compatible CLI tools have logs showing MCP server connections:

**Claude Code:**
```bash
# Check logs (location varies by version)
tail -f ~/Library/Logs/Claude/mcp.log
```

**ChatGPT/Gemini CLI:**
Check the CLI tool's log location in its documentation.

### Test 3: Ask the LLM

After restarting your CLI tool, try:
```
"What repositories are available in MyRAGDB?"
```

The LLM should use the `list_repositories` tool.

---

## Troubleshooting

### "MCP server myragdb failed to start"

**Cause:** Python or mcp_server.server not found

**Fix:**
1. Check Python path: `which python`
2. Verify MCP SDK: `pip show mcp`
3. Test manual start: `python -m mcp_server.server`

---

### "Connection refused to localhost:3003"

**Cause:** MyRAGDB API server not running

**Fix:**
```bash
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate
python -m myragdb.api.server
```

Keep this running in a separate terminal.

---

### "Module 'mcp_server' has no attribute 'server'"

**Cause:** PYTHONPATH not set correctly

**Fix:**
Edit your config file to ensure:
```json
"env": {
  "PYTHONPATH": "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb"
}
```

---

### LLM doesn't use the tools

**Causes:**
1. CLI tool doesn't support MCP
2. Configuration not loaded
3. Server failed to start silently

**Fix:**
1. Check if your CLI tool version supports MCP
2. Restart the CLI tool
3. Check CLI tool logs for errors
4. Try manual server start to test

---

## Custom Configuration Locations

If your CLI tool uses a different config location:

1. Find your tool's config directory:
```bash
# Common locations:
ls ~/.config/
ls ~/Library/Application Support/
```

2. Look for MCP configuration file:
```bash
find ~ -name "*mcp*config*" 2>/dev/null
```

3. Create or update the MCP configuration in the correct location

4. Use the universal template above

---

## Environment Variables

You can also configure via environment variables:

```bash
export MYRAGDB_URL="http://localhost:3003"
export MYRAGDB_TIMEOUT="30"
```

Then update `mcp_server/server.py` to read from env vars.

---

## Advanced: Running MCP Server Standalone

For debugging or alternative setups:

```bash
# Start as standalone process
python -m mcp_server.server &

# The server waits for stdin (MCP protocol)
# CLI tools will connect via stdio
```

---

## Security Notes

- The MCP server runs locally and connects to local MyRAGDB API
- No external network access required
- All data stays on your machine
- MCP uses stdio (stdin/stdout), not network sockets

---

## Getting Help

If you encounter issues:

1. Check MyRAGDB logs: `tail -f logs/myragdb.log`
2. Check CLI tool's MCP documentation
3. Test MCP server manually: `python -m mcp_server.server`
4. Verify MyRAGDB API is accessible: `curl http://localhost:3003/health`

---

Questions: libor@arionetworks.com
