# MyRAGDB

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/README.md
**Description:** Hybrid search system for semantic code and documentation discovery
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04
**Last Updated:** 2026-01-08
**Last Updated By:** Libor Ballaty <libor@arionetworks.com>

## What's New in This Session (2026-01-08)

### Phase 1-2 Complete: Cloud LLM API Integration

**Authentication & Credential Management:**
- 🔐 **Secure Credential Storage**: Encrypted at `~/.myragdb/credentials.json` using Fernet symmetric encryption
- 🔑 **API Key Authentication**: Support for Google Gemini, OpenAI ChatGPT, and Anthropic Claude
- 🌐 **OAuth Flow**: Browser-based authentication for cloud LLM providers
- 💻 **Device Code Flow**: CLI-based authentication with polling for headless environments
- ✅ **Credential Validation**: Test API keys before switching providers

**REST API Endpoints (6 new endpoints):**
- `GET /llm/session` - Get current active LLM provider and session info
- `GET /llm/providers` - List all available providers and their models
- `POST /llm/validate-credentials` - Validate credentials before storing
- `POST /llm/switch` - Switch active provider with credential validation
- `GET /llm/authenticated` - List all authenticated providers for quick access
- `POST /llm/logout/{provider}` - Revoke provider credentials
- `GET /llm/health` - Detailed LLM-specific health check

**Enhanced Health Checking:**
- Enhanced `/health` endpoint now includes LLM component status
- New `/llm/health` endpoint provides detailed LLM configuration and availability
- Health status includes authenticated providers and current session info

**Web UI Implementation (Phase 3.1-3.2):**
- 🎨 **Cloud LLM Manager Tab**: Comprehensive provider management UI
- 📋 **Provider Selection**: Three provider tabs (Gemini, ChatGPT, Claude) with capabilities display
- 🔑 **Multiple Auth Methods**: API Key, OAuth, and Device Code authentication flows
- 📊 **Available Models Display**: Shows model specs (context window, vision capability)
- ⚡ **Quick Switch**: Buttons for rapidly switching between authenticated providers
- 🏥 **Health Monitoring**: Real-time LLM health status with component breakdown
- 📱 **Responsive Design**: Mobile-optimized Cloud LLM UI

**Documentation Updates:**
- Updated User Manual with complete API reference for all new LLM endpoints
- Added curl examples for all six new endpoints
- Documented all auth methods and response formats
- Updated README with cloud LLM feature overview

---

## Previous Session (2026-01-07)

Comprehensive enhancement session adding advanced filtering, monitoring, and observability features:

- **Date Range Filtering**: Filter results by modification date with ISO 8601 format (from_date, to_date, between_dates)
- **Min-Score Filtering**: Set relevance thresholds (0.0 to 1.0) to find only highly relevant results
- **Enhanced Activity Monitor**: Real-time activity logging with type/severity/time filtering, export, and persistent storage
- **Enhanced Observability Dashboard**: Interactive charts, alert thresholds, system health metrics, error tracking
- **QueryBuilder Enhancements**: New date range methods (from_date, to_date, between_dates) for fluent query construction
- **Web UI Advanced Filters**: New HTML5 date pickers and score input in search interface
- **Comprehensive API Documentation**: Complete SEARCH_API_REFERENCE.md with all endpoints, examples, and usage patterns
- **Port Alignment**: Verified all ports against port-registry.json (port 3003 for main API)
- **Updated User Manual**: Extensive new sections documenting all enhancements

---

## Overview

MyRAGDB is a **laptop-wide hybrid search service** that combines Meilisearch keyword search with vector embeddings to enable AI agents and developers to intelligently discover, cross-reference, and learn from code and documentation across all development projects.

**Key Features:**
- 🔍 **Hybrid Search** - Combines keyword (Meilisearch) and semantic (vector) search with configurable weights
- 🚀 **Fast** - Sub-300ms hybrid search across thousands of files
- 🤖 **Agent-First** - Built-in MCP (Model Context Protocol) server for Claude and other LLMs
- 🏠 **Local-First** - All data stays on your machine, no cloud dependencies
- 📚 **Multi-Repository** - Search across all your projects simultaneously
- 🎯 **Smart Indexing** - Incremental updates, auto-reindex on file changes, scheduled indexing
- 📊 **Observability** - Real-time metrics, performance tracking, error monitoring
- 🌐 **Modern Web UI** - Repository discovery, indexing controls, search interface, LLM manager
- 🔄 **LLM Integration** - Built-in LLM query rewriting with local models (Phi-3, Llama, etc.)

---

## Quick Start

### macOS App Bundle (Easiest)

**Just double-click MyRAGDB.app!**

The app bundle provides the easiest way to start MyRAGDB on macOS:

1. **First time**: Double-click `MyRAGDB.app` in the project folder (or add to Applications/Dock)
2. App starts all services and opens browser automatically
3. App stays in Dock while services are running
4. **To stop**: Right-click app in Dock → Quit (or use `./stop.sh`)
5. **To reopen UI**: Double-click app again (services stay running, just opens browser)

**Troubleshooting**: If the app doesn't work, check logs with:
```bash
./view-app-logs.sh
# Or view live:
tail -f /tmp/myragdb_app_bundle.log
```

### One-Command Startup (Terminal)

```bash
./start.sh
```

This automatically:
1. ✅ Starts Meilisearch (if not running)
2. ✅ Starts MyRAGDB API server (port 3003)
3. ✅ Starts MCP middleware (port 3004)
4. ✅ Opens web browser to http://localhost:3003

### One-Command Shutdown

```bash
./stop.sh
```

This cleanly stops all services in reverse order.

---

## Installation

### Prerequisites

- **Python 3.9+** (recommended: Python 3.11)
- **Meilisearch** - Auto-installed by start.sh or install manually:
  ```bash
  # macOS (Homebrew)
  brew install meilisearch

  # Linux
  curl -L https://install.meilisearch.com | sh

  # Windows
  # Download from https://github.com/meilisearch/meilisearch/releases
  ```

### Setup Steps

```bash
# 1. Clone repository
git clone https://github.com/lballaty/myragdb.git
cd myragdb

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Configure repositories (optional - can use Web UI discovery)
cp config/repositories.yaml.example config/repositories.yaml
# Edit config/repositories.yaml with your repo paths

# 5. Start the system
./start.sh

# 6. (Optional) Add app to Dock for easy access
# Drag MyRAGDB.app to your Dock or Applications folder
```

The web UI will open automatically at http://localhost:3003

### Adding to Applications/Dock (macOS)

For easy access from anywhere:

**Option 1: Add to Dock**
- Drag `MyRAGDB.app` from the project folder to your Dock
- Click the icon to start/open MyRAGDB anytime

**Option 2: Add to Applications**
```bash
# Create symlink in Applications folder
ln -s "$(pwd)/MyRAGDB.app" ~/Applications/MyRAGDB.app
# Or copy it:
cp -R MyRAGDB.app ~/Applications/
```

**Option 3: Spotlight Search**
- Just type "MyRAGDB" in Spotlight (Cmd+Space)
- Press Enter to launch

---

## Usage Guide

### 1. Web UI (Recommended for New Users)

The web UI provides a complete interface for all features:

#### **Search Tab**
- Hybrid, keyword-only, or semantic-only search
- Repository filtering
- Result count customization
- **Advanced Filters**:
  - 📅 **Date Range**: Filter results by modification date (ISO 8601 format: YYYY-MM-DD)
    - `From Date`: Include results from this date (inclusive)
    - `To Date`: Include results up to this date (inclusive)
    - Leave blank for no date constraint
  - 📊 **Min Score**: Minimum relevance threshold (0.0 to 1.0)
    - 0.0-0.3: Weak match (consider removing)
    - 0.3-0.6: Moderate match (may have false positives)
    - 0.6-0.8: Good match (likely relevant)
    - 0.8-1.0: Excellent match (highly relevant)
  - 📁 **Folder Filter**: Scope search to specific folder path (e.g., `src/components`)
  - 📄 **File Extension**: Filter by single file type (e.g., `.py`)
- Real-time search as you type

#### **Activity Monitor Tab**
- **Real-time Activity Logging**:
  - UI activity log (local events - searches, filters, reindex)
  - Server log streaming (backend API events)
  - Auto-refresh every 5 seconds (toggleable)
  - Persistent local storage (500 most recent items)

- **Advanced Filtering**:
  - Filter by activity type (search, index, config, api, system)
  - Filter by severity level (error, warning, info, debug)
  - Filter by time range (1 hour, 24 hours, 7 days, 30 days, custom)
  - Text search across log messages

- **Export & Management**:
  - Export logs as JSON file for analysis
  - Configurable line display limits (10-100 lines)
  - Automatic data cleanup based on retention policy
  - Single-click severity filtering with color coding

#### **Repositories Tab**
- **Repository Discovery**: Scan filesystem for Git repositories
  - Configurable depth (1-5 levels)
  - Smart filtering (name, status, priority, dates)
  - Bulk selection and configuration
  - README viewer for each repository
  - Pagination for large result sets

- **Indexing Controls**:
  - Select repositories to index
  - Choose index types (keyword, vector, or both)
  - Incremental or full rebuild modes
  - Real-time progress tracking
  - Repository configuration (enable/disable, priority, lock status)

- **System Statistics**:
  - Keyword document count
  - Vector chunk count
  - Total searches performed
  - Average response time
  - Last indexing timestamp

#### **Observability Tab**
- **Real-time System Metrics**:
  - Total searches and average response time
  - Error tracking with severity levels (critical, error, warning, info)
  - Database statistics (Meilisearch size, ChromaDB collections, metadata records)
  - Performance indicators (fastest/slowest searches, indexing stats)
  - Configurable alert thresholds:
    - Response time: Warning at 1000ms, Error at 2000ms
    - Error rate: Warning at 5%, Error at 10%
    - System resources: CPU warning at 80%, Memory warning at 85%

- **Interactive Charts & Visualizations** (Chart.js):
  - 📈 **Line Chart**: Search response time trends over time
  - 🥧 **Doughnut Chart**: Search volume by type (hybrid/keyword/semantic)
  - 📊 **Bar Chart**: Error distribution by severity
  - 🎯 **Radar Chart**: System health with multiple metrics
  - 📉 **Error Rate Trends**: Error percentage over selected time range

- **Data Tables & Filtering**:
  - **Recent Errors**: Severity, component, type, message with sorting
  - **Indexing Events**: Status, repository, duration, file count
  - **Time Range Selection**: 1h, 24h, 7d, 30d, or custom date range
  - **Data Cleanup**: Manual purge or automatic retention policies
  - **Alert Notifications**: Real-time alerts when thresholds exceeded
  - **JSON Export**: Export all metrics and events for analysis

#### **Cloud LLM Manager Tab**
- Switch between cloud LLM providers (Google Gemini, OpenAI ChatGPT, Anthropic Claude)
- Multiple authentication methods:
  - **API Key**: Enter your provider API key (encrypted storage)
  - **OAuth**: Browser-based login for provider accounts
  - **Device Code**: CLI-based authentication for headless environments
- View provider capabilities:
  - Available models with context window sizes
  - Vision capability indicators
  - Model performance characteristics
- Quick-switch between authenticated providers
- Real-time health monitoring of LLM configuration
- Secure credential management with automatic encryption/decryption

### 2. CLI Search

```bash
# Activate virtual environment first
source venv/bin/activate

# Basic search
python -m myragdb.cli search "authentication flow"

# With repository filter
python -m myragdb.cli search "JWT tokens" --repos xLLMArionComply

# Limit results
python -m myragdb.cli search "rate limiting" --limit 5

# Semantic search only
python -m myragdb.cli search "how to secure API endpoints" --type semantic
```

### 3. Python Client (For Agent Integration)

```python
from myragdb import SearchClient
from myragdb.agent_library import QueryBuilder

# Initialize client
client = SearchClient(base_url="http://localhost:3003")

# Hybrid search (default)
results = client.search("how to implement rate limiting")

# Keyword-only search
results = client.search("JWT tokens", search_type="keyword")

# Semantic-only search
results = client.search("authentication best practices", search_type="semantic")

# With filters
results = client.search(
    query="API security",
    repositories=["xLLMArionComply", "myragdb"],
    limit=10
)

# Process results
for result in results:
    print(f"File: {result.file_path}")
    print(f"Score: {result.score}")
    print(f"Snippet: {result.snippet}")
    print(f"Repository: {result.repository}")
    print("---")
```

#### **QueryBuilder - Fluent Query Construction**

Use `QueryBuilder` for programmatic query construction with a fluent API:

```python
from myragdb.agent_library import QueryBuilder

# Simple search
query = QueryBuilder().search("authentication").build()
results = client.search(**query)

# Complex filtered search with date range and score filtering
query = (QueryBuilder()
    .search("database migration")
    .in_repositories(["xLLMArionComply"])
    .only_python()
    .between_dates("2025-01-01", "2026-01-07")
    .with_min_score(0.6)
    .limit_to(20)
    .build())
results = client.search(**query)

# Search with date range
query = (QueryBuilder()
    .search("performance optimization")
    .from_date("2025-12-01")  # Results from this date onwards
    .semantic()
    .limit_to(10)
    .build())
results = client.search(**query)

# Search with score threshold
query = (QueryBuilder()
    .search("error handling")
    .with_min_score(0.8)  # Only highly relevant results
    .limit_to(5)
    .build())
results = client.search(**query)

# Convenience factory functions
from myragdb.agent_library.query_builder import (
    find_in_code,
    find_in_docs,
    find_pattern,
    understand_concept
)

# Find in code files
results = client.search(**find_in_code("JWT validation").build())

# Find in documentation
results = client.search(**find_in_docs("API usage").build())

# Find exact pattern
results = client.search(**find_pattern("def authenticate").build())

# Understand concept semantically
results = client.search(**understand_concept("how users log in").build())
```

**QueryBuilder Methods:**

| Method | Purpose | Example |
|--------|---------|---------|
| `.search(query)` | Set search query (required) | `.search("authentication")` |
| `.hybrid()` / `.keyword()` / `.semantic()` | Search type | `.hybrid()` (default) |
| `.in_repositories(list)` | Filter to repos | `.in_repositories(["MyApp"])` |
| `.only_file_types(list)` | Filter by extensions | `.only_file_types([".py", ".md"])` |
| `.only_python()` | Shortcut for `.py` files | `.only_python()` |
| `.with_extension(ext)` | Single extension filter | `.with_extension(".py")` |
| `.in_folder(path)` | Filter by folder | `.in_folder("src/components")` |
| `.from_date(date)` | Results from date (ISO 8601) | `.from_date("2025-01-01")` |
| `.to_date(date)` | Results up to date (ISO 8601) | `.to_date("2026-01-07")` |
| `.between_dates(from, to)` | Date range (inclusive) | `.between_dates("2025-06-01", "2025-06-30")` |
| `.with_min_score(score)` | Minimum relevance (0.0-1.0) | `.with_min_score(0.6)` |
| `.limit_to(n)` | Max results (1-100) | `.limit_to(20)` |
| `.build()` | Build final query dict | Required before `.search(**query)` |
| `.to_string()` | Human-readable representation | `print(query.to_string())` |

### 4. MCP Integration (Claude & AI Agents)

MyRAGDB provides a Model Context Protocol (MCP) server for native integration with Claude Code, Claude Desktop, and other MCP-compatible tools.

#### **Setup for Claude Code**

Add to `~/.config/claude-code/mcp_servers.json`:

```json
{
  "mcpServers": {
    "myragdb": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/myragdb",
      "env": {
        "PYTHONPATH": "/path/to/myragdb"
      }
    }
  }
}
```

#### **Setup for Claude Desktop**

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "myragdb": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/myragdb"
    }
  }
}
```

#### **Available MCP Tools**

Once configured, Claude can use these tools:

- `search_hybrid` - Hybrid keyword + semantic search
- `search_keyword` - Keyword-only search (fast)
- `search_semantic` - Semantic-only search (context-aware)

**Example Claude prompt:**
```
"Use the search_hybrid tool to find information about authentication flows in my codebase"
```

---

## Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Web UI (React/TypeScript)                  │
│  localhost:3003  (Search, Discovery, Indexing, Observability) │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│               FastAPI REST Service (Port 3003)                │
├──────────────────────────────────────────────────────────────┤
│  Search Endpoints:                                            │
│    POST /search/hybrid    - Keyword + Vector (weighted)       │
│    POST /search/keyword   - Meilisearch only                  │
│    POST /search/semantic  - Vector only                       │
│                                                               │
│  Indexing Endpoints:                                          │
│    POST /index/keyword    - Index documents to Meilisearch    │
│    POST /index/vector     - Generate and store embeddings     │
│                                                               │
│  Repository Endpoints:                                        │
│    GET  /repositories                - List all repositories  │
│    POST /repositories/discover       - Scan filesystem        │
│    POST /repositories/configure      - Update config          │
│    GET  /repositories/{repo}/readme  - Get README content     │
│                                                               │
│  Observability Endpoints:                                     │
│    GET  /observability/stats         - System metrics         │
│    GET  /observability/errors        - Error logs             │
│    GET  /observability/search_events - Search history         │
│    GET  /observability/indexing_events - Index history        │
│    POST /observability/cleanup       - Cleanup old data       │
│                                                               │
│  Other:                                                        │
│    GET  /stats           - System statistics                  │
│    GET  /health          - Health check                       │
│    GET  /                - Serve Web UI                       │
└─────────────┬──────────────────┬────────────────┬────────────┘
              │                  │                │
              ▼                  ▼                ▼
  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐
  │ Meilisearch      │  │  ChromaDB      │  │  SQLite DB   │
  │ (Keyword Index)  │  │ (Vector Store) │  │  (Metadata)  │
  │  Port: 7700      │  │  In-process    │  │  data/*.db   │
  └──────────────────┘  └────────────────┘  └──────────────┘
```

### MCP Integration Architecture

```
┌─────────────────────────────────────────┐
│  Claude / Claude Code / LLM Client      │
└────────────────┬────────────────────────┘
                 │ (MCP Protocol - stdio)
                 ▼
┌─────────────────────────────────────────┐
│  MCP Middleware Server (Port 3004)      │
│  - Translates MCP ↔ HTTP                │
│  - Handles tool discovery               │
│  - Manages async communication          │
└────────────────┬────────────────────────┘
                 │ (HTTP)
                 ▼
┌─────────────────────────────────────────┐
│  MyRAGDB API Server (Port 3003)         │
│  - Processes search requests            │
│  - Returns structured results           │
└─────────────────────────────────────────┘
```

### Smart Indexing Features

#### **1. Incremental Indexing**
- Only indexes changed files (compares modification time)
- Tracks metadata in SQLite database
- Significantly faster than full rebuilds

#### **2. Auto-Reindexing on File Changes**
- Uses `watchdog` library for filesystem monitoring
- Debouncing (5-second delay) to batch rapid changes
- Per-repository enable/disable via `auto_reindex` config
- Respects exclude patterns (node_modules, .git, etc.)
- Automatic startup/shutdown with server lifecycle

#### **3. Scheduled Indexing** (Coming Soon)
- Cron-based scheduled indexing
- Per-repository schedules (hourly, daily, weekly, custom)
- Next run time display in UI
- Manual trigger override

---

## Configuration

### Repository Configuration

Edit `config/repositories.yaml`:

```yaml
repositories:
  - name: MyProject
    path: /absolute/path/to/project
    enabled: true
    priority: high  # high, medium, low
    excluded: false  # true = locked (protected from reindexing)
    auto_reindex: true  # Enable automatic file-change detection
    file_patterns:
      include:
        - "**/*.md"
        - "**/*.py"
        - "**/*.ts"
        - "**/*.tsx"
        - "**/*.js"
        - "**/*.dart"
      exclude:
        - "**/node_modules/**"
        - "**/.git/**"
        - "**/venv/**"
        - "**/archive-*/**"
        - "**/*.lock"
        - "**/__pycache__/**"
        - "**/dist/**"
        - "**/build/**"
```

**Configuration Fields:**
- `name`: Repository identifier (must be unique)
- `path`: Absolute path to repository root
- `enabled`: Whether to include in searches and indexing
- `priority`: Affects search result ordering (high > medium > low)
- `excluded`: Lock status (locked repos can't be reindexed)
- `auto_reindex`: Enable automatic reindexing on file changes
- `file_patterns.include`: File glob patterns to index
- `file_patterns.exclude`: File glob patterns to ignore

### Environment Variables

Create `.env` file (use `.env.example` as template):

```bash
# Meilisearch Configuration
MEILI_MASTER_KEY=myragdb_dev_key_2026
MEILI_HOST=http://localhost:7700

# MyRAGDB Configuration
MYRAGDB_PORT=3003
MYRAGDB_LOG_LEVEL=INFO

# Vector Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Search Weights (must sum to 1.0)
KEYWORD_WEIGHT=0.4
VECTOR_WEIGHT=0.6

# LLM Configuration (optional)
LLM_QUERY_REWRITE_ENABLED=true
LLM_ENDPOINT=http://localhost:8081/v1
```

---

## Development

### Project Structure

```
myragdb/
├── src/myragdb/              # Main Python package
│   ├── api/                  # FastAPI server and endpoints
│   │   ├── server.py         # Main server with all routes
│   │   └── models.py         # Pydantic request/response models
│   ├── indexers/             # Indexing engines
│   │   ├── meilisearch_indexer.py  # Keyword indexing
│   │   └── vector_indexer.py       # Vector embedding indexing
│   ├── search/               # Search logic
│   │   ├── hybrid_search.py  # Combines keyword + vector
│   │   ├── keyword_search.py # Meilisearch queries
│   │   └── vector_search.py  # ChromaDB queries
│   ├── db/                   # Database layer
│   │   ├── file_metadata.py  # File tracking
│   │   └── schema.sql        # SQLite schema
│   ├── watcher/              # File system monitoring
│   │   └── repository_watcher.py  # Auto-reindex on changes
│   ├── config.py             # Configuration loading
│   ├── cli.py                # Command-line interface
│   └── version.py            # Version (auto-managed by pre-commit)
├── mcp_server/               # MCP server for Claude integration
│   └── server.py             # MCP protocol implementation
├── web-ui/                   # Frontend (vanilla JS)
│   ├── index.html            # Main UI
│   ├── llm-chat-tester.html  # LLM testing interface
│   └── static/
│       ├── css/styles.css    # Styling
│       └── js/app.js         # UI logic
├── agent_library/            # Python client for agents
│   └── examples/             # Usage examples
├── config/                   # Configuration files
│   └── repositories.yaml     # Repository definitions
├── scripts/                  # Utility scripts
│   ├── initial_index.py      # First-time indexing
│   └── verify_indexed_content.py  # Index verification
├── data/                     # Runtime data (gitignored)
│   ├── meilisearch/          # Meilisearch data
│   ├── chroma/               # Vector store
│   └── *.db                  # SQLite databases
├── docs/                     # Documentation
│   ├── OBSERVABILITY_AND_SCHEDULING_DESIGN.md
│   └── AUTO_REINDEX_TESTING.md
├── start.sh                  # Startup script
├── stop.sh                   # Shutdown script
├── setup.py                  # Package definition
└── requirements.txt          # Python dependencies
```

### Development Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run server with auto-reload
uvicorn myragdb.api.server:app --reload --port 3003

# Run tests (when available)
pytest tests/

# Check code style
black src/
flake8 src/
```

### Adding New Features

1. **Backend Changes**:
   - Add endpoints to `src/myragdb/api/server.py`
   - Add Pydantic models to `src/myragdb/api/models.py`
   - Add business logic to appropriate modules

2. **Frontend Changes**:
   - Update `web-ui/index.html` for structure
   - Update `web-ui/static/js/app.js` for behavior
   - Update `web-ui/static/css/styles.css` for styling

3. **Commit Standards**:
   - Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
   - Pre-commit hook auto-bumps version in `src/myragdb/version.py`
   - Never manually edit `version.py`

### API Documentation

**Comprehensive API Reference:** See [SEARCH_API_REFERENCE.md](SEARCH_API_REFERENCE.md) for complete documentation including:
- All three search endpoints (hybrid, keyword, semantic)
- Complete filter reference (date range, score, repository, file type)
- Request/response examples with full JSON structures
- Date filtering behavior and examples
- Score filtering with typical ranges
- Health check and statistics endpoints
- Error handling with HTTP status codes
- Python client library usage
- cURL examples for all scenarios

**Interactive API Documentation** (when server is running):
- **Swagger UI**: http://localhost:3003/docs
- **ReDoc**: http://localhost:3003/redoc

---

## Performance

### Benchmarks

Tested on MacBook Pro M1 (16GB RAM):

| Operation | Time | Notes |
|-----------|------|-------|
| Keyword Search | < 50ms | Meilisearch only |
| Vector Search | < 200ms | ChromaDB + embeddings |
| Hybrid Search | < 300ms | Combined |
| Index Update (incremental) | ~100ms/file | Changed files only |
| Full Repository Index | ~2-5 min | 5,000-10,000 files |

### Scalability

- **Tested**: 30,000+ files across 6 repositories
- **Target**: 50,000+ files
- **Memory Usage**: ~2-4GB (with embeddings loaded)
- **Disk Usage**: ~500MB-3GB (depends on file count)

### Optimization Tips

1. **Use Incremental Indexing**: Much faster than full rebuilds
2. **Enable Auto-Reindex**: Keeps index fresh without manual intervention
3. **Tune Search Weights**: Adjust keyword/vector weights based on use case
4. **Filter by Repository**: Narrow searches to specific projects
5. **Use Keyword Search**: When semantic understanding isn't needed

---

## Troubleshooting

### Common Issues

#### **Port Already in Use**

```bash
# Check what's using port 3003
lsof -i :3003

# Kill the process
kill -9 <PID>

# Or use stop.sh which handles this automatically
./stop.sh
```

#### **Meilisearch Not Starting**

```bash
# Check if Meilisearch is installed
which meilisearch

# Install if missing (macOS)
brew install meilisearch

# Manually start Meilisearch
meilisearch --master-key myragdb_dev_key_2026 --db-path ./data/meilisearch
```

#### **Import Errors**

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall package
pip install -e .
```

#### **macOS App Bundle Not Working**

If double-clicking MyRAGDB.app doesn't work:

1. **Check the logs**:
   ```bash
   ./view-app-logs.sh
   # Or view live:
   tail -f /tmp/myragdb_app_bundle.log
   ```

2. **Common causes**:
   - **PATH issues**: App can't find `meilisearch` or `python3`
     - Solution: App automatically adds Homebrew paths
     - Check log shows: "Meilisearch: /opt/homebrew/bin/meilisearch"

   - **Permission issues**: App can't execute
     ```bash
     chmod +x MyRAGDB.app/Contents/MacOS/MyRAGDB
     ```

   - **Gatekeeper blocking**: macOS security blocking unsigned app
     ```bash
     # Remove quarantine attribute
     xattr -dr com.apple.quarantine MyRAGDB.app
     # Or: Right-click app → Open → Click "Open" in dialog
     ```

3. **Fallback to terminal**:
   ```bash
   # Always works as fallback
   ./start.sh
   ```

#### **Browser Cache Issues**

If UI doesn't reflect latest changes:
- **Mac**: Cmd + Shift + R (hard refresh)
- **Windows/Linux**: Ctrl + Shift + R
- **Alternative**: Open DevTools (F12) → Right-click refresh → "Empty Cache and Hard Reload"

#### **No Search Results**

1. Check if repositories are indexed:
   - Go to Repositories tab
   - Check "Indexed Files" column
   - If 0, run indexing (select repos → "Re-index Selected Repositories")

2. Check if repositories are enabled:
   - Click ⚙️ Configure on repository card
   - Ensure "Status" is "Enabled"

3. Check logs:
   - Go to Activity Monitor tab
   - Switch to "Server Logs"
   - Look for errors

---

## Project Status

### Current Phase: Production-Ready ✅

**Completed Features:**
- ✅ Hybrid search (keyword + vector)
- ✅ Multi-repository support
- ✅ Web UI with full functionality
- ✅ CLI search interface
- ✅ Python client library with SearchClient
- ✅ **QueryBuilder fluent API** for programmatic query construction
- ✅ **Date range filtering** (from_date, to_date, between_dates)
- ✅ **Min-score filtering** for relevance thresholds
- ✅ **Advanced search filters** in UI (date range, score, folder, extension)
- ✅ MCP server for Claude integration
- ✅ Repository discovery and configuration
- ✅ Incremental indexing
- ✅ Auto-reindexing on file changes
- ✅ **Enhanced Activity Monitor** with type/severity/time filtering, export
- ✅ **Enhanced Observability Dashboard** with alerts, charts, metrics
- ✅ LLM query rewriting integration
- ✅ LLM manager UI
- ✅ Real-time indexing progress
- ✅ README viewer for repositories
- ✅ **Comprehensive API documentation** (SEARCH_API_REFERENCE.md)

**Upcoming Features:**
- 🔄 Scheduled indexing (cron-based)
- 🔄 Advanced search syntax (boolean operators)
- 🔄 Search result highlighting
- 🔄 Export search results
- 🔄 API rate limiting
- 🔄 Comprehensive test suite
- 🔄 Docker containerization

### Documentation

- [System Specification](universal-search-service-spec.md) - Backend architecture
- [Web UI Specification](WEB-UI-SPEC.md) - Frontend design
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Development roadmap
- [Observability & Scheduling Design](docs/OBSERVABILITY_AND_SCHEDULING_DESIGN.md)
- [Auto-Reindex Testing Guide](docs/AUTO_REINDEX_TESTING.md)
- [TODO](TODO.md) - Task tracking

---

## Port Reservations

MyRAGDB uses these ports:

- **3003**: MyRAGDB API server (FastAPI) and Web UI
- **3004**: MCP middleware server
- **7700**: Meilisearch
- **8081**: LLM endpoint (optional, when using query rewriting)

Check `../project-config/PORT-RESERVATIONS.json` before adding new ports.

---

## Contributing

This is currently a private project. For questions or contributions:

**Contact:** Libor Ballaty <libor@arionetworks.com>

### Development Guidelines

1. **Always use virtual environment**: `source venv/bin/activate`
2. **Never edit version.py manually**: Pre-commit hook handles it
3. **Follow naming standards**: Descriptive names, no abbreviations
4. **Add docstrings**: Every function needs business purpose + example
5. **Test before committing**: Verify functionality works
6. **Commit frequently**: Every logical unit of work (30-60 min max)
7. **Use conventional commits**: `feat:`, `fix:`, `refactor:`, etc.

---

## License

Private project - All rights reserved

---

## Version

**Current Version**: Auto-managed by pre-commit hook (see `src/myragdb/version.py`)

**Version Format**: CalVer (`YYYY.MM.DD.MAJOR.MINOR.PATCH`)

**Latest Changes**: See `git log` or check header version badge in Web UI

---

**Questions:** libor@arionetworks.com
