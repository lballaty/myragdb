# MyRAGDB User Manual

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/USER_MANUAL.md
**Description:** Complete user manual for MyRAGDB hybrid search system
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07
**Last Updated:** 2026-01-07
**Last Updated By:** Libor Ballaty <libor@arionetworks.com>

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Web UI Guide](#web-ui-guide)
4. [Search Features](#search-features)
5. [Repository Management](#repository-management)
6. [Indexing & Reindexing](#indexing--reindexing)
7. [LLM Integration](#llm-integration)
8. [API Reference](#api-reference)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Introduction

### What is MyRAGDB?

MyRAGDB is a **hybrid search system** that combines keyword search (via Meilisearch) with semantic vector search (via ChromaDB) to provide intelligent code and documentation discovery across multiple git repositories.

### Key Features

- **Hybrid Search**: Combines keyword matching with semantic understanding
- **Multi-Repository Support**: Index and search across unlimited repositories
- **Incremental Indexing**: Only reindex changed files for fast updates
- **LLM Integration**: Built-in support for local LLMs with function calling
- **Repository Discovery**: Automatically find git repositories in directories
- **Real-time Updates**: File watcher monitors changes (optional)
- **Web UI**: Modern, responsive interface with dark mode
- **REST API**: Full programmatic access for automation
- **Clone Detection**: Identifies duplicate repositories automatically

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI                                │
│              (HTML/CSS/JavaScript)                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                            │
│                  (Python REST API)                           │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │Meilisearch│    │ ChromaDB │    │  SQLite  │
    │ Keyword   │    │  Vector  │    │ Metadata │
    │  Search   │    │  Search  │    │ Tracking │
    └──────────┘    └──────────┘    └──────────┘
```

---

## Getting Started

### Prerequisites

- **Python 3.8+** installed
- **Git** installed
- **macOS, Linux, or Windows** with WSL

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd myragdb
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Install Meilisearch:**

   **macOS:**
   ```bash
   brew install meilisearch
   ```

   **Linux:**
   ```bash
   curl -L https://install.meilisearch.com | sh
   ```

   **Windows:**
   Download from https://github.com/meilisearch/meilisearch/releases

### Quick Start

1. **Configure repositories:**

   Edit `config/repositories.yaml`:
   ```yaml
   repositories:
     - name: myproject
       path: /path/to/your/project
       enabled: true
       priority: high
   ```

2. **Start the server:**
   ```bash
   python -m myragdb.api.server
   ```

   Server starts at: http://localhost:3002

3. **Open Web UI:**

   Navigate to http://localhost:3002 in your browser

4. **Index repositories:**

   Click "🔄 Reindex" in the Repositories section

---

## Web UI Guide

### Dashboard Overview

The main dashboard consists of four sections:

1. **Search Panel** (top)
2. **Repositories Panel** (left)
3. **Activity Log** (right)
4. **LLM Manager** (bottom)

### Search Panel

**Quick Search:**
- Type your query in the search box
- Press Enter or click 🔍 Search
- Results appear instantly below

**Search Modes:**
- **Hybrid** (default): Combines keyword + semantic search
- **Keyword**: Fast exact/fuzzy text matching
- **Vector**: Semantic similarity search

**Filters:**
- **Repositories**: Filter by one or more repositories
- **File Types**: Filter by file extension (.py, .md, .ts, etc.)
- **Result Limit**: Control number of results (1-100)

**Search Tips:**
- Use quotes for exact phrases: `"user authentication"`
- Include file extensions: `login .py`
- Use technical terms: `JWT token validation`
- Ask questions: `how does caching work?`

### Repositories Panel

**Repository Cards** show:
- 📁 **Available**: Files found on disk
- ✓ **Indexed**: Files in search index (percentage)
- 🔴/🟡/🟢 **Priority**: Search result ranking
- ✅/❌ **Enabled**: Active for indexing
- 🔒/🔓 **Lock Status**: Protected from reindexing

**Actions:**
- **🔓/🔒**: Lock/unlock repository
- **🗑️ Remove**: Remove from configuration
- **⚙️ Configure**: Open settings modal
- **📄 README**: View repository README

### Activity Log

Real-time stream of all system operations:
- ✅ **Success**: Operations completed successfully
- ⚠️ **Warning**: Non-critical issues
- ❌ **Error**: Failed operations
- ℹ️ **Info**: General information

**Features:**
- Auto-scroll (toggleable)
- Severity filter
- Export to file
- Clear log

### LLM Manager

Manage local LLMs for function calling:

**Columns:**
- Model name and path
- File size
- Status (Running/Stopped)
- Actions (Start/Stop/Restart)

**Modes:**
- **Basic**: Standard chat (no function calling)
- **Tools**: Function calling with --jinja
- **Performance**: Parallel processing enabled
- **Extended**: 32k context window

---

## Search Features

### Hybrid Search (Recommended)

Combines keyword and vector search using **Reciprocal Rank Fusion (RRF)**.

**How it works:**
1. Runs keyword search (BM25 algorithm)
2. Runs vector search (cosine similarity)
3. Merges results using rank-based scoring
4. Returns top results sorted by combined score

**Best for:**
- General queries
- Mixed technical/natural language
- When you're not sure which search type to use

**Example:**
```
Query: "database connection pool settings"
```

### Keyword Search

Fast exact and fuzzy text matching using Meilisearch.

**Features:**
- Typo tolerance
- Prefix matching
- Stop word removal
- Custom ranking

**Best for:**
- Exact file/function names
- Specific error messages
- Code snippets
- Technical identifiers

**Example:**
```
Query: "DatabaseConnectionPool.getConnection()"
```

### Vector Search

Semantic similarity using sentence embeddings (all-MiniLM-L6-v2).

**Features:**
- Understands meaning, not just keywords
- Finds conceptually similar content
- Language-agnostic
- Context-aware

**Best for:**
- Concept exploration
- "How does X work?" questions
- Finding similar implementations
- Cross-language patterns

**Example:**
```
Query: "how is user authentication handled?"
```

### Search Result Details

Each result shows:
- **File path** (clickable)
- **Repository** name
- **Content preview** with highlighted matches
- **Match score** (relevance percentage)
- **File type** indicator

**Actions:**
- Click path to copy
- Hover for full context
- Filter by repository

---

## Repository Management

### Adding Repositories

**Method 1: Manual Configuration**

Edit `config/repositories.yaml`:

```yaml
repositories:
  - name: myproject
    path: /Users/username/projects/myproject
    enabled: true
    priority: medium
    excluded: false
    auto_reindex: true
    file_patterns:
      include:
        - "**/*.md"
        - "**/*.py"
      exclude:
        - "**/node_modules/**"
        - "**/.git/**"
```

**Method 2: Repository Discovery (Web UI)**

1. Click "🔍 Scan for Repositories"
2. Enter base directory path
3. Configure scan options:
   - **Max Depth**: How deep to search (1-5 levels)
   - **Exclude Patterns**: Directories to skip
4. Click "Scan Now"
5. Review discovered repositories
6. Select repositories to add
7. Click "Add Selected Repositories"

**Method 3: API**

```bash
curl -X POST "http://localhost:3002/repositories/add" \
  -H "Content-Type: application/json" \
  -d '{
    "directories": ["/path/to/scan"],
    "max_depth": 3,
    "auto_add": false
  }'
```

### Repository Configuration

Click **⚙️ Configure** on any repository card to edit:

**Status:**
- **✅ Enabled**: Repository is active for indexing/searching
- **❌ Disabled**: Repository is ignored

**Priority:**
- **🔴 High**: Results ranked first
- **🟡 Medium**: Standard ranking
- **🟢 Low**: Results ranked last

**Protection:**
- **🔓 Unlocked**: Can be reindexed
- **🔒 Locked**: Protected from reindexing

**Exclude Patterns:**

Glob patterns for files to skip during indexing:

```
**/node_modules/**
**/.git/**
**/venv/**
**/__pycache__/**
**/*.log
**/temp/**
```

**Pattern Syntax:**
- `**` matches any number of directories
- `*` matches any characters in a filename
- One pattern per line

### Removing Repositories

**Option 1: Web UI**

1. Click **🗑️ Remove from Config** on repository card
2. Confirm removal
3. Repository is removed from configuration
4. **Note**: Files on disk are NOT deleted

**Option 2: Manual**

Edit `config/repositories.yaml` and remove the repository entry.

**Option 3: API**

```bash
curl -X DELETE "http://localhost:3002/repositories/myproject"
```

---

## Indexing & Reindexing

### Initial Indexing

When you add a new repository:

1. Server scans directory for matching files
2. Files are indexed in both Meilisearch and ChromaDB
3. Metadata is stored in SQLite database
4. Progress shown in Activity Log

**Time estimates:**
- 1,000 files: ~2-5 minutes
- 10,000 files: ~20-50 minutes
- 50,000 files: ~2-4 hours

### Incremental Reindexing

Reindexing is **incremental** - only changed files are processed.

**Triggers:**
- Manual: Click "🔄 Reindex" button
- Automatic: File watcher detects changes (if enabled)
- API: POST to `/reindex` endpoint

**How it works:**
1. Compares file modification times with database
2. Only indexes files that changed since last index
3. Deletes entries for removed files
4. Updates metadata for modified files

**Example:**
```
Repository: 10,000 total files
Changed: 50 files
Time: ~30 seconds (vs 30 minutes full reindex)
```

### Reindex Options (Web UI)

1. Click "🔄 Reindex" button
2. Modal shows repository selection
3. Check repositories to reindex
4. **Locked repositories** are unchecked by default
5. Click "Proceed" to start

**Smart Features:**
- Shows estimated file counts
- Warns if large number of files
- Prevents accidental reindex of locked repos
- Runs incrementally by default

### File Watcher (Auto-Reindex)

Enable in repository configuration:

```yaml
repositories:
  - name: myproject
    auto_reindex: true  # Enable file watcher
```

**Behavior:**
- Watches for file changes in real-time
- Triggers reindex after 2 seconds of inactivity
- Only indexes changed files
- Works in background

**Performance:**
- Low CPU usage (~0.1%)
- Instant search result updates
- No manual reindexing needed

---

## LLM Integration

### Overview

MyRAGDB integrates local LLMs to provide AI-powered search assistance.

**Capabilities:**
- Function calling to search repositories
- Multi-step reasoning
- Code generation from search results
- Natural language queries

### Supported Models

Any GGUF model compatible with llama.cpp:

**Recommended:**
- **DeepSeek R1 Distill Qwen 32B**: Best reasoning
- **Mistral Small 3.2 24B**: Fast and accurate
- **Llama 3.1 8B**: Good balance
- **Qwen 2.5 Coder 7B**: Code-focused

### Installing Models

**Option 1: Hugging Face CLI**

```bash
huggingface-cli download \
  TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q8_0.gguf \
  --local-dir /Users/username/llms/
```

**Option 2: Manual Download**

1. Visit https://huggingface.co/models
2. Search for GGUF models
3. Download .gguf file
4. Place in `/Users/username/llms/` directory

### Adding Models to UI

Models are auto-detected from these directories:
- `/Users/liborballaty/llms/`
- Custom paths in configuration

**To add custom directory:**

Edit server code or configuration to include your path.

### Starting an LLM

1. Go to **LLM Manager** section
2. Find your model in the list
3. Select **Mode**:
   - **Basic**: No function calling
   - **Tools**: Function calling enabled (recommended)
   - **Performance**: Parallel processing
   - **Extended**: 32k context
4. Click **▶️ Start**
5. Wait for status to show "Running"

### Using LLM with Function Calling

**Example conversation:**

```
User: Search for authentication code in the user service

LLM: [Calls search_repositories function]
     Found 15 results about authentication in user_service.py

     The authentication is handled in authenticate_user() function
     which validates JWT tokens and checks user permissions...
```

**Function Available:**
- `search_repositories(query, repositories, limit)`

**LLM can:**
- Decide when to search
- Refine queries based on results
- Combine multiple searches
- Explain code found

### Performance Tuning

**GPU Acceleration:**

Edit startup script to add GPU layers:
```bash
llama-server --model model.gguf --n-gpu-layers 35
```

**Context Window:**
- Basic: 2048 tokens
- Extended: 32768 tokens

**Batch Size:**
- Default: 512
- High performance: 2048

---

## API Reference

### Base URL

```
http://localhost:3002
```

### Authentication

Currently no authentication required (local use only).

### Endpoints

#### Search

**POST /search**

Perform hybrid search across repositories.

```bash
curl -X POST "http://localhost:3002/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication",
    "mode": "hybrid",
    "repositories": ["myproject"],
    "file_types": [".py"],
    "limit": 10
  }'
```

**Response:**
```json
{
  "results": [
    {
      "file_path": "/path/to/file.py",
      "repository": "myproject",
      "content": "def authenticate_user(username, password)...",
      "score": 0.95,
      "match_type": "hybrid"
    }
  ],
  "total_results": 15,
  "search_time_ms": 234
}
```

#### Repositories

**GET /repositories**

List all configured repositories.

```bash
curl "http://localhost:3002/repositories"
```

**POST /repositories/add**

Add repositories via discovery.

```bash
curl -X POST "http://localhost:3002/repositories/add" \
  -H "Content-Type: application/json" \
  -d '{
    "directories": ["/Users/username/projects"],
    "max_depth": 3,
    "exclude_patterns": ["archive-*", "old-*"]
  }'
```

**PATCH /repositories/{repo_name}**

Update repository configuration.

```bash
curl -X PATCH "http://localhost:3002/repositories/myproject?enabled=true&priority=high" \
  -H "Content-Type: application/json"
```

**DELETE /repositories/{repo_name}**

Remove repository from configuration.

```bash
curl -X DELETE "http://localhost:3002/repositories/myproject"
```

#### Indexing

**POST /reindex**

Trigger incremental reindexing.

```bash
curl -X POST "http://localhost:3002/reindex" \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": ["myproject"],
    "force": false
  }'
```

**GET /index/status**

Get indexing status and statistics.

```bash
curl "http://localhost:3002/index/status"
```

### Python Client

```python
from myragdb import SearchClient

# Initialize client
client = SearchClient(base_url="http://localhost:3002")

# Search
results = client.search(
    query="user authentication",
    mode="hybrid",
    repositories=["myproject"],
    limit=10
)

# Print results
for result in results:
    print(f"{result['file_path']}: {result['score']}")
```

---

## Configuration

### Repository Configuration

**File:** `config/repositories.yaml`

```yaml
repositories:
  - name: myproject              # Unique identifier
    path: /path/to/repo          # Absolute path to repository
    enabled: true                # Enable/disable indexing
    priority: high               # Search result ranking (high/medium/low)
    excluded: false              # Lock from reindexing
    auto_reindex: true           # Enable file watcher
    file_patterns:
      include:                   # Glob patterns to include
        - "**/*.md"
        - "**/*.py"
        - "**/*.ts"
        - "**/*.tsx"
      exclude:                   # Glob patterns to exclude
        - "**/node_modules/**"
        - "**/.git/**"
        - "**/venv/**"
        - "**/__pycache__/**"
        - "**/*.pyc"
```

### Search Configuration

**Keyword Search Weights:** 0.4
**Vector Search Weights:** 0.6

**Reciprocal Rank Fusion (RRF):**
```python
RRF_K = 60  # Constant for rank fusion algorithm
```

**Embedding Model:**
```
sentence-transformers/all-MiniLM-L6-v2
Dimensions: 384
```

### Server Configuration

**Port:** 3002
**Host:** 0.0.0.0
**CORS:** Enabled for all origins (local dev)

**Database Paths:**
- Metadata: `data/file_metadata.db`
- Meilisearch: `data/meilisearch/`
- ChromaDB: `data/chromadb/`

---

## Troubleshooting

### Common Issues

#### Search returns no results

**Possible causes:**
1. Repositories not indexed yet
2. Query too specific
3. File type filter excluding results

**Solutions:**
1. Click "🔄 Reindex" to index repositories
2. Try broader search terms
3. Remove file type filters
4. Switch to "Hybrid" search mode

#### Indexing is slow

**Possible causes:**
1. Large number of files
2. Slow disk I/O
3. Resource constraints

**Solutions:**
1. Add exclude patterns for large directories
2. Close other applications
3. Use incremental reindexing
4. Increase system resources

#### LLM won't start

**Possible causes:**
1. Insufficient RAM
2. Model file corrupted
3. Port already in use

**Solutions:**
1. Use smaller quantized model (Q4_K_M instead of Q8_0)
2. Re-download model file
3. Stop other llama-server instances:
   ```bash
   pkill llama-server
   ```

#### Server won't start

**Possible causes:**
1. Port 3002 already in use
2. Meilisearch not running
3. Missing dependencies

**Solutions:**
1. Check for conflicting processes:
   ```bash
   lsof -i :3002
   ```
2. Start Meilisearch manually:
   ```bash
   meilisearch --http-addr 127.0.0.1:7700
   ```
3. Reinstall dependencies:
   ```bash
   pip install -e .
   ```

### Error Messages

#### "Repository path does not exist"

**Solution:** Update path in `config/repositories.yaml` with correct absolute path.

#### "Failed to connect to Meilisearch"

**Solution:** Start Meilisearch:
```bash
meilisearch --http-addr 127.0.0.1:7700
```

#### "Database is locked"

**Solution:** Close other instances accessing the database:
```bash
pkill python
```

Then restart server.

### Logs

**Server logs:** Check terminal output
**Activity log:** View in Web UI
**Debug mode:** Set environment variable:

```bash
export DEBUG=1
python -m myragdb.api.server
```

---

## Best Practices

### Repository Organization

**Do:**
- Group related projects in same directory
- Use descriptive repository names
- Set appropriate priorities
- Lock production repositories

**Don't:**
- Index system directories (/, /usr/, etc.)
- Mix unrelated projects
- Enable auto-reindex on large repos
- Index temporary directories

### Search Optimization

**For best results:**
1. Start with hybrid search
2. Use specific technical terms
3. Include file extensions when known
4. Filter by repository for focused results
5. Use vector search for concepts
6. Use keyword search for exact matches

**Query tips:**
```
Good: "JWT token validation middleware"
Better: "JWT token validation .js"
Best: "JWT token validation middleware authentication.js"
```

### Indexing Strategy

**Initial setup:**
1. Add all repositories disabled
2. Enable and index one at a time
3. Verify results before adding more
4. Set priorities based on usage
5. Lock stable repositories

**Maintenance:**
1. Reindex monthly for stable repos
2. Enable auto-reindex for active development
3. Remove archived/old repositories
4. Update exclude patterns as needed

### Performance Optimization

**For large codebases (50k+ files):**
1. Aggressive exclude patterns
2. Disable auto-reindex
3. Schedule reindexing during off-hours
4. Use keyword search when possible
5. Filter by repository/file type

**For fast searches:**
1. Enable result caching
2. Use specific queries
3. Limit result count
4. Filter by known repositories

### Security

**Important notes:**
- MyRAGDB is designed for **local use only**
- No authentication/authorization by default
- All repositories are searchable by anyone with access
- Do not expose port 3002 to internet
- Keep sensitive repos excluded or disabled

**For production use:**
1. Add authentication middleware
2. Implement repository-level permissions
3. Use HTTPS/TLS
4. Add rate limiting
5. Audit search logs

---

## Appendix

### Keyboard Shortcuts

**Web UI:**
- `Ctrl/Cmd + K`: Focus search box
- `Enter`: Execute search
- `Esc`: Close modals

### File Type Extensions

**Supported by default:**
- Code: .py, .js, .ts, .tsx, .jsx, .java, .go, .rs, .c, .cpp, .h
- Docs: .md, .txt, .rst, .adoc
- Config: .json, .yaml, .yml, .toml, .xml
- Web: .html, .css, .scss, .vue
- Mobile: .dart, .swift, .kt

### Glossary

- **BM25**: Best Match 25, ranking function for keyword search
- **ChromaDB**: Vector database for embeddings
- **GGUF**: File format for quantized LLM models
- **Incremental Indexing**: Only index changed files
- **Meilisearch**: Fast, typo-tolerant search engine
- **RRF**: Reciprocal Rank Fusion, algorithm for combining search results
- **Vector Embedding**: Numerical representation of text meaning

### Additional Resources

- **Architecture Documentation**: `docs/myragdb-SYSTEM_ARCHITECTURE.md`
- **API Specification**: `docs/universal-search-service-spec.md`
- **Web UI Specification**: `docs/WEB-UI-SPEC.md`
- **GitHub Issues**: https://github.com/your-org/myragdb/issues

---

## Support

For questions or issues:
- **Email**: libor@arionetworks.com
- **Documentation**: `docs/` directory
- **Logs**: Check Activity Log in Web UI

---

*Last updated: 2026-01-07*
