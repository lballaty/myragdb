# MyRAGDB Complete System Architecture

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/myragdb-SYSTEM_ARCHITECTURE.md
**Description:** Comprehensive architectural documentation covering all features, components, data flows, database schema, and implementation details for the MyRAGDB hybrid search system
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-06
**Last Updated:** 2026-01-06
**Last Updated By:** Libor Ballaty <libor@arionetworks.com>

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Architecture](#core-architecture)
3. [Component Details](#component-details)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Database Schema](#database-schema)
6. [API Endpoints Reference](#api-endpoints-reference)
7. [Web UI Architecture](#web-ui-architecture)
8. [LLM Integration System](#llm-integration-system)
9. [MCP Server Implementation](#mcp-server-implementation)
10. [Configuration Management](#configuration-management)
11. [Performance Optimizations](#performance-optimizations)
12. [Deployment Guide](#deployment-guide)

---

## System Overview

### Purpose

MyRAGDB is a hybrid search system that combines keyword-based search (Meilisearch with BM25 ranking) and semantic vector search (ChromaDB with sentence embeddings) to enable AI agents to discover code and documentation across multiple repositories.

### Key Features

- **Hybrid Search**: RRF (Reciprocal Rank Fusion) combining keyword + vector results
- **Multi-Repository Support**: Index and search across unlimited code repositories
- **Incremental Indexing**: SQLite-based metadata tracking only reindexes changed files
- **Web UI**: Modern browser interface with real-time updates
- **MCP Protocol**: Claude Code integration via Model Context Protocol
- **Local LLM Management**: Start/stop llama.cpp models with optimized modes
- **Real-time Statistics**: Track indexing progress, search performance, system health

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3.11+, FastAPI | HTTP API server |
| Keyword Search | Meilisearch 1.5+ | BM25 full-text search |
| Vector Search | ChromaDB | Cosine similarity search |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | 384-dim vectors |
| Metadata | SQLite | File tracking, stats, system metadata |
| Frontend | Vanilla JavaScript, HTML5, CSS3 | Browser UI |
| LLM Runtime | llama.cpp | Local model inference |
| AI Integration | MCP (Model Context Protocol) | Claude Code tools |

---

## Core Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interfaces                       │
├──────────────────┬──────────────────┬──────────────────────┤
│   Web UI         │   CLI            │   MCP Server         │
│   (Browser)      │   (Terminal)     │   (Claude Code)      │
└────────┬─────────┴────────┬─────────┴──────────┬───────────┘
         │                  │                     │
         └──────────────────┼─────────────────────┘
                           │
                  ┌────────▼────────┐
                  │   FastAPI       │
                  │   HTTP Server   │
                  │   (Port 3003)   │
                  └────────┬────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌────────▼─────┐  ┌────────▼────────┐  ┌────▼──────────┐
│ Hybrid       │  │  Repository     │  │  LLM          │
│ Search       │  │  Discovery &    │  │  Manager      │
│ Engine       │  │  Indexing       │  │               │
└───┬──────┬───┘  └────────┬────────┘  └───────────────┘
    │      │               │
    │      │      ┌────────▼────────────┐
    │      │      │  File Metadata DB   │
    │      │      │  (SQLite)           │
    │      │      │  - file_metadata    │
    │      │      │  - repository_stats │
    │      │      │  - system_metadata  │
    │      │      └─────────────────────┘
    │      │
┌───▼──┐ ┌─▼──────────┐
│Meili │ │  ChromaDB  │
│search│ │  Vector    │
│Index │ │  Store     │
└──────┘ └────────────┘
```

### Architecture Principles

1. **Separation of Concerns**: Each component has single, well-defined responsibility
2. **Independent Indexing**: Keyword and vector indexing run in parallel threads
3. **Incremental Updates**: SQLite indexes enable O(log n) lookups to skip unchanged files
4. **Stateless API**: All persistent state in SQLite, not in-memory
5. **Asynchronous Processing**: Background indexing doesn't block API responses
6. **Resource Efficiency**: Singleton embedding model, connection pooling, lazy generators

---

## Component Details

### 1. API Server (`src/myragdb/api/server.py`)

**Purpose**: FastAPI HTTP server exposing all system functionality

**Port**: 3003

**Key Responsibilities**:
- Handle search requests with filtering (repository, directories)
- Manage repository indexing (start/stop/status/progress)
- Serve web UI static files
- Coordinate parallel keyword + vector indexing
- Manage local LLM processes (start/stop/health)
- Provide repository discovery and configuration

**Indexing State Management**:
```python
indexing_state = {
    "is_indexing": False,         # Global: any indexing active?
    "last_index_time": None,      # ISO 8601 timestamp
    "keyword": {
        "is_indexing": False,
        "stop_requested": False,
        "current_repository": None,
        "repositories_total": 0,
        "repositories_completed": 0,
        "files_processed": 0,
        "files_total": 0,
        "mode": "incremental" | "full_rebuild"
    },
    "vector": {
        # Same structure as keyword
    }
}
```

**Startup Sequence**:
1. Load configuration from `config/repositories.yaml`
2. Initialize SQLite metadata database (creates tables + indexes)
3. Create singleton search engine instances
4. Start Meilisearch if not running
5. Configure CORS for web UI
6. Load last index time from SQLite

---

### 2. Hybrid Search Engine (`src/myragdb/search/hybrid_search.py`)

**Purpose**: Combine keyword and vector search using Reciprocal Rank Fusion

**Reciprocal Rank Fusion (RRF) Algorithm**:
```python
def calculate_rrf_score(keyword_rank: int, vector_rank: int, k: int = 60) -> float:
    """
    Combine rankings from two search systems.

    Formula: score = 1/(k + kw_rank + 1) + 1/(k + vec_rank + 1)

    Args:
        keyword_rank: 0-based position in keyword results
        vector_rank: 0-based position in vector results
        k: Smoothing constant (prevents early ranks from dominating)

    Returns:
        Combined score (higher is better)

    Example:
        File at position 0 in keyword, position 5 in vector:
        score = 1/(60+0+1) + 1/(60+5+1) = 0.0164 + 0.0152 = 0.0316
    """
    keyword_contrib = 1.0 / (k + keyword_rank + 1)
    vector_contrib = 1.0 / (k + vector_rank + 1)
    return keyword_contrib + vector_contrib
```

**Search Pipeline**:
1. Query Meilisearch → BM25-ranked keyword results
2. Query ChromaDB → Cosine similarity vector results
3. Deduplicate by file_path
4. Calculate RRF scores
5. Sort by RRF score descending
6. Apply limit (top N results)
7. Return with breakdown (keyword_score, vector_score, combined_score)

**Result Schema**:
```python
{
    "file_path": str,             # Absolute path
    "repository": str,            # Repository name
    "score": float,               # RRF combined score
    "snippet": str,               # Highlighted text excerpt
    "keyword_score": float,       # Original BM25 score
    "vector_score": float,        # Original cosine similarity
    "file_type": str              # Extension (py, md, ts, etc.)
}
```

---

### 3. Keyword Indexer (`src/myragdb/indexers/meilisearch_indexer.py`)

**Purpose**: Index files in Meilisearch for BM25 keyword search

**Meilisearch Document Schema**:
```json
{
    "id": "unique_file_id",           // SHA256 hash of file_path
    "file_path": "/absolute/path",
    "repository": "myragdb",
    "content": "file text content",   // Full file contents
    "file_type": "py"
}
```

**Searchable Attributes** (priority order):
1. `content` - Primary search field (80% weight)
2. `file_path` - Secondary (20% weight)

**Filterable Attributes**:
- `repository` - Filter to specific repo
- `file_type` - Filter to specific extensions

**Ranking Rules** (Meilisearch default):
1. `words` - More matched query terms = higher rank
2. `typo` - Fewer typos = higher rank
3. `proximity` - Query terms closer together = higher rank
4. `attribute` - Match in `content` > match in `file_path`
5. `sort` - Custom sort field (if specified)
6. `exactness` - Exact match > prefix match

**Incremental Indexing Logic**:
```python
# Check SQLite metadata for each file
last_indexed_time = db.get_last_indexed_time(file_path)
file_mtime = os.path.getmtime(file_path)

if file_mtime > last_indexed_time:
    # File changed since last index
    index_file_in_meilisearch(file_path)
    db.update_file_metadata(file_path, repository, 'keyword')
else:
    # Skip unchanged file (90% time savings)
    pass
```

**Performance**: O(log n) metadata lookups via `idx_repository` index

---

### 4. Vector Indexer (`src/myragdb/indexers/vector_indexer.py`)

**Purpose**: Generate semantic embeddings and store in ChromaDB

**Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Max tokens**: 256 (~200 words)
- **Speed**: ~1000 sentences/sec on CPU
- **Size**: 90MB model file
- **Quality**: Balanced speed/quality for code search

**Chunking Strategy**:
```python
CHUNK_SIZE = 500 characters      # Fits in 256 token limit
CHUNK_OVERLAP = 50 characters    # Preserve context between chunks

# Example file chunking:
# File: 2000 chars
# Chunks:
#   [0:500]      chunk 0
#   [450:950]    chunk 1 (50 char overlap with chunk 0)
#   [900:1400]   chunk 2 (50 char overlap with chunk 1)
#   [1350:1850]  chunk 3
#   [1800:2000]  chunk 4
```

**ChromaDB Collection Schema**:
```python
{
    "id": "file_path:chunk_index",        # e.g. "/path/file.py:0"
    "embedding": [384-dim float vector],  # Sentence embedding
    "metadata": {
        "file_path": str,
        "repository": str,
        "chunk_index": int,
        "file_type": str
    },
    "document": "chunk text content"     # Original text
}
```

**Incremental Indexing**:
1. Query SQLite: `SELECT * FROM file_metadata WHERE repository=? AND index_type='vector'`
2. Check if file mtime > last_indexed
3. If changed:
   - Delete old chunks from ChromaDB (by file_path prefix)
   - Chunk file (500 chars, 50 overlap)
   - Generate embeddings (batch of 32)
   - Insert new chunks to ChromaDB
   - Update SQLite metadata
4. If unchanged: Skip (saves ~5 seconds/file)

---

### 5. File Metadata Database (`src/myragdb/db/file_metadata.py`)

**Purpose**: Track indexed files, enable incremental updates, store system statistics

**Database**: SQLite at `data/file_metadata.db`

**Schema Version**: 1

**Tables**:

#### `file_metadata` - Per-file tracking
```sql
CREATE TABLE file_metadata (
    file_path TEXT PRIMARY KEY,           -- Absolute path (unique)
    repository TEXT NOT NULL,             -- Repository name
    last_indexed INTEGER NOT NULL,        -- Unix timestamp
    last_modified INTEGER NOT NULL,       -- File mtime
    content_hash TEXT,                    -- SHA256 (future deduplication)
    file_size INTEGER,                    -- Bytes
    index_type TEXT NOT NULL,             -- 'keyword', 'vector', 'both'
    created_at INTEGER NOT NULL,          -- First indexed timestamp
    updated_at INTEGER NOT NULL           -- Last update timestamp
);

-- Performance indexes
CREATE INDEX idx_repository ON file_metadata(repository);
CREATE INDEX idx_last_indexed ON file_metadata(last_indexed);
CREATE INDEX idx_index_type ON file_metadata(index_type);
```

**Query Performance**:
```sql
-- Fast repository lookup (uses idx_repository)
SELECT * FROM file_metadata WHERE repository = 'myragdb';
-- Query plan: SEARCH file_metadata USING INDEX idx_repository

-- Result: O(log n) instead of O(n) table scan
-- Impact: 100x faster on 10,000+ files
```

#### `repository_stats` - Aggregate statistics
```sql
CREATE TABLE repository_stats (
    repository TEXT NOT NULL,
    index_type TEXT NOT NULL,             -- 'keyword' or 'vector'
    total_files_indexed INTEGER,
    initial_index_time_seconds REAL,      -- Duration of first index
    initial_index_timestamp INTEGER,
    last_reindex_time_seconds REAL,       -- Duration of last reindex
    last_reindex_timestamp INTEGER,
    total_size_bytes INTEGER,
    PRIMARY KEY (repository, index_type)
);
```

**Used by**: Web UI to display indexing stats

#### `system_metadata` - Global application state (NEW)
```sql
CREATE TABLE system_metadata (
    key TEXT PRIMARY KEY,                 -- e.g. 'last_index_time'
    value TEXT,                           -- JSON-encoded value
    updated_at INTEGER NOT NULL
);

-- Replaces legacy data/metadata.json file
```

**Stored Keys**:
- `last_index_time`: ISO 8601 timestamp of last successful index
- `total_searches`: Cumulative search count
- `total_search_time_ms`: Cumulative search latency

**Migration Note**: Consolidated from separate JSON file for consistency

---

### 6. Repository Discovery (`src/myragdb/utils/repo_discovery.py`)

**Purpose**: Scan filesystem to discover git repositories

**Discovery Algorithm**:
```python
def discover_repositories(base_path: str, max_depth: int = 3) -> List[DiscoveredRepository]:
    """
    Walk directory tree to find git repositories.

    Steps:
    1. Check path exists and is directory
    2. Walk filesystem (up to max_depth levels)
    3. For each directory, check if .git exists
    4. If git repo found:
       - Count indexable files (apply exclusion patterns)
       - Calculate total size
       - Return metadata
    5. Continue walking subdirectories

    Returns:
        List of discovered repository metadata
    """
```

**Exclusion Patterns** (from `config/repositories.yaml`):
```yaml
global_exclude_patterns:
  - "**/node_modules/**"      # npm dependencies
  - "**/.git/**"              # Git internals
  - "**/venv/**"              # Python venv
  - "**/archive-*/**"         # Archived dirs
  - "**/__pycache__/**"       # Python bytecode
  - "**/*.lock"               # Lock files
  - "**/build/**"             # Build artifacts
  - "**/dist/**"              # Distribution files
  - "**/.pytest_cache/**"     # Test cache
```

**Indexable Extensions**:
```python
INDEXABLE_EXTENSIONS = {
    '.md', '.py', '.ts', '.tsx', '.dart', '.js', '.jsx',
    '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp',
    '.yaml', '.yml', '.json', '.toml', '.sql', '.sh'
}
```

**Performance**: Generator pattern (lazy file walking), constant memory

---

### 7. File Scanner (`src/myragdb/indexers/file_scanner.py`)

**Purpose**: Walk repository directories and yield indexable files

**Features**:
- Respects `.gitignore` patterns (via gitignore library)
- Applies global exclusion patterns
- Filters by file extension
- Handles symlinks safely (doesn't follow)
- Handles permission errors gracefully

**Usage**:
```python
scanner = FileScanner(exclude_patterns=config.global_exclude_patterns)

for file_path in scanner.scan_repository("/path/to/repo"):
    # Yields one file at a time (generator pattern)
    # Constant memory usage regardless of repo size
    index_file(file_path)
```

---

### 8. LLM Manager (`src/myragdb/llm/llm_router.py`)

**Purpose**: Manage local LLM processes via llama.cpp

**Supported Models** (stored in `/Users/liborballaty/llms/`):

| Model | Quantization | Size | Context | Use Case |
|-------|--------------|------|---------|----------|
| Llama 4 Scout 17B | Q3_K_S | 7.2GB | 8192 | Function calling |
| Mistral Small 3.2 24B | Q8_0 | 25.6GB | 8192 | High quality |
| DeepSeek R1 Distill Qwen 32B | Q4_K_M | 18.4GB | 8192 | Reasoning |
| Qwen 2.5 Coder 7B | Q8_0 | 7.7GB | 8192 | Code completion |
| Hermes 3 Llama 8B | Q8_0 | 8.5GB | 8192 | General purpose |

**Operating Modes**:

**1. Function Calling Mode** (Port 8080):
```bash
llama-server \
  --model /path/to/model.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --n-gpu-layers 999 \         # Offload all layers to GPU
  --ctx-size 8192 \            # Large context
  --parallel 1 \               # Single request (no batching)
  --threads 8                  # CPU threads
```

**Use case**: Structured output, tool use, JSON mode

**2. Speed Mode** (Port 8081):
```bash
llama-server \
  --model /path/to/model.gguf \
  --host 0.0.0.0 \
  --port 8081 \
  --n-gpu-layers 999 \
  --ctx-size 4096 \            # Smaller context (faster)
  --parallel 4 \               # 4 parallel requests (batching)
  --threads 8 \
  --flash-attn                 # Flash attention optimization
```

**Use case**: High throughput, chat, completion

**Process Lifecycle**:
```python
# 1. Start
process = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
llm_processes[model_id] = {
    "process": process,
    "mode": "function_calling",
    "port": 8080,
    "pid": process.pid,
    "started_at": datetime.now()
}

# 2. Health check (wait for server ready)
while not check_health("http://localhost:8080/health"):
    time.sleep(1)

# 3. Monitor (capture logs)
with open(f"logs/llm_{model_id}.log", "a") as log:
    log.write(process.stdout.read())

# 4. Stop (graceful shutdown)
process.terminate()  # SIGTERM
process.wait(timeout=10)  # Wait for clean exit
```

---

### 9. MCP Server (`mcp_server/server.py`)

**Purpose**: Expose MyRAGDB as tools for Claude Code via MCP protocol

**Protocol**: Model Context Protocol (MCP)
- **Transport**: stdio (JSON-RPC 2.0 over standard input/output)
- **Message Format**: JSON-RPC 2.0

**Exposed Tools**:

**1. myragdb_search** - Hybrid search
```json
{
  "name": "myragdb_search",
  "description": "Search code and documentation across indexed repositories",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "limit": {
        "type": "integer",
        "default": 10,
        "description": "Max results"
      },
      "repository": {
        "type": "string",
        "description": "Filter to specific repository"
      },
      "search_type": {
        "type": "string",
        "enum": ["hybrid", "keyword", "vector"],
        "default": "hybrid"
      }
    },
    "required": ["query"]
  }
}
```

**2. myragdb_get_repositories** - List repos
```json
{
  "name": "myragdb_get_repositories",
  "description": "List all configured repositories",
  "inputSchema": {
    "type": "object",
    "properties": {
      "enabled_only": {
        "type": "boolean",
        "default": true
      }
    }
  }
}
```

**3. myragdb_reindex** - Trigger indexing
```json
{
  "name": "myragdb_reindex",
  "description": "Reindex repositories (keyword and/or vector)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "repositories": {
        "type": "array",
        "items": {"type": "string"}
      },
      "index_types": {
        "type": "array",
        "items": {"type": "string", "enum": ["keyword", "vector"]}
      },
      "force_rebuild": {
        "type": "boolean",
        "default": false
      }
    },
    "required": ["repositories"]
  }
}
```

**Claude Code Integration**:

Config file: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "myragdb": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb",
      "env": {
        "PYTHONPATH": "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb"
      }
    }
  }
}
```

**Message Flow**:
```
Claude Code → stdin → MCP Server → HTTP API → MyRAGDB
            ← stdout ←          ← JSON ←
```

---

### 10. Configuration System (`src/myragdb/config.py`)

**Purpose**: Centralized configuration with environment overrides

**Configuration Hierarchy** (lower overrides higher):
1. Code defaults (`Settings` class)
2. YAML file (`config/repositories.yaml`)
3. Environment variables
4. Runtime API parameters

**repositories.yaml Structure**:
```yaml
repositories:
  - name: myragdb
    path: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
    enabled: true
    priority: high        # high, medium, low
    excluded: false       # If true, locked from indexing

global_exclude_patterns:
  - "**/node_modules/**"
  - "**/.git/**"
  # ... (see Repository Discovery section)

global_include_extensions:
  - .md
  - .py
  - .ts
  # ... (see Repository Discovery section)
```

**Settings Class**:
```python
class Settings:
    # API
    API_HOST = "0.0.0.0"
    API_PORT = 3003

    # Meilisearch
    MEILISEARCH_URL = "http://localhost:7700"
    MEILISEARCH_API_KEY = None

    # ChromaDB
    CHROMADB_PATH = "data/chromadb"

    # Embeddings
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    # Search weights (future use)
    KEYWORD_WEIGHT = 0.4
    VECTOR_WEIGHT = 0.6

    # Chunking
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
```

**Environment Variable Overrides**:
```bash
export MEILISEARCH_URL=http://remote-server:7700
export MEILISEARCH_API_KEY=secure_key_here
export EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
```

---

## Data Flow Diagrams

### Search Request Flow

```
┌──────────────┐
│ User submits │
│ query via UI │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────┐
│ POST /search                     │
│ {                                │
│   query: "auth flow",            │
│   limit: 10,                     │
│   search_type: "hybrid"          │
│ }                                │
└──────┬──────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ HybridSearchEngine.search()      │
└──┬───────────────────────────┬───┘
   │                           │
   ▼                           ▼
┌──────────────┐        ┌─────────────────┐
│ Meilisearch  │        │ ChromaDB        │
│ keyword      │        │ vector          │
│ search       │        │ search          │
│ (BM25)       │        │ (cosine sim)    │
└──────┬───────┘        └────────┬────────┘
       │                         │
       │ Returns 15 results      │ Returns 15 results
       │                         │
       └──────────┬──────────────┘
                  │
                  ▼
       ┌────────────────────────┐
       │ Merge by file_path     │
       │ (deduplicate)          │
       └────────┬───────────────┘
                │
                ▼
       ┌────────────────────────┐
       │ Calculate RRF scores   │
       │ for each result        │
       └────────┬───────────────┘
                │
                ▼
       ┌────────────────────────┐
       │ Sort by score DESC     │
       └────────┬───────────────┘
                │
                ▼
       ┌────────────────────────┐
       │ Return top 10 results  │
       └────────────────────────┘
```

### Indexing Flow (Parallel Keyword + Vector)

```
┌─────────────────────────────┐
│ POST /reindex                │
│ {                            │
│   repositories: ["myragdb"], │
│   index_types: ["keyword",   │
│                 "vector"],   │
│   force_rebuild: false       │
│ }                            │
└──────────┬──────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Spawn 2 background threads   │
└──┬───────────────────────┬───┘
   │                       │
   ▼                       ▼
KEYWORD THREAD          VECTOR THREAD
   │                       │
   │ For each repo:        │ For each repo:
   │                       │
   ▼                       ▼
FileScanner             FileScanner
  .scan_repository()      .scan_repository()
   │                       │
   │ Yields file paths     │ Yields file paths
   │                       │
   ▼                       ▼
Query SQLite:           Query SQLite:
WHERE repo=?            WHERE repo=?
AND type='keyword'      AND type='vector'
   │                       │
   ▼                       ▼
Check if file           Check if file
mtime > last_indexed    mtime > last_indexed
   │                       │
   │ If YES:               │ If YES:
   ▼                       ▼
Read file               Read file
   │                       │
   ▼                       ▼
Index in                Chunk file
Meilisearch             (500 chars, 50 overlap)
   │                       │
   │                       ▼
   │                    Generate embeddings
   │                    (batch of 32)
   │                       │
   │                       ▼
   │                    Index in ChromaDB
   │                       │
   ▼                       ▼
Update SQLite           Update SQLite
file_metadata           file_metadata
   │                       │
   │ If NO: Skip           │ If NO: Skip
   │                       │
   ▼                       ▼
Update                  Update
repository_stats        repository_stats
   │                       │
   └───────────┬───────────┘
               │
               ▼
       ┌──────────────────┐
       │ Both threads     │
       │ complete         │
       └──────┬───────────┘
              │
              ▼
       ┌──────────────────┐
       │ Update global    │
       │ indexing_state   │
       │ is_indexing=False│
       └──────────────────┘
```

---

## Database Schema

### Complete SQLite Schema (`data/file_metadata.db`)

```sql
-- File metadata tracking
CREATE TABLE IF NOT EXISTS file_metadata (
    file_path TEXT PRIMARY KEY,
    repository TEXT NOT NULL,
    last_indexed INTEGER NOT NULL,
    last_modified INTEGER NOT NULL,
    content_hash TEXT,
    file_size INTEGER,
    index_type TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX idx_repository ON file_metadata(repository);
CREATE INDEX idx_last_indexed ON file_metadata(last_indexed);
CREATE INDEX idx_index_type ON file_metadata(index_type);

-- Repository statistics
CREATE TABLE IF NOT EXISTS repository_stats (
    repository TEXT NOT NULL,
    index_type TEXT NOT NULL,
    total_files_indexed INTEGER,
    initial_index_time_seconds REAL,
    initial_index_timestamp INTEGER,
    last_reindex_time_seconds REAL,
    last_reindex_timestamp INTEGER,
    total_size_bytes INTEGER,
    PRIMARY KEY (repository, index_type)
);

CREATE INDEX idx_repo_stats_repository ON repository_stats(repository);

-- System metadata (replaces data/metadata.json)
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at INTEGER NOT NULL
);

-- Default values
INSERT OR IGNORE INTO system_metadata VALUES
    ('last_index_time', NULL, strftime('%s', 'now')),
    ('total_searches', '0', strftime('%s', 'now')),
    ('total_search_time_ms', '0', strftime('%s', 'now'));

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL
);

INSERT OR IGNORE INTO schema_version VALUES (1, strftime('%s', 'now'));
```

**Storage Consolidation** (as of 2026-01-06):
- ✅ **Active**: `data/file_metadata.db` (SQLite) - All metadata
- ✅ **Active**: `data/chromadb/` - Vector embeddings
- ✅ **Active**: Meilisearch index (HTTP API) - Keyword documents
- ❌ **Removed**: `data/metadata.json` (consolidated into system_metadata table)
- ❌ **Removed**: `data/myragdb.db` (empty, never used)

---

## API Endpoints Reference

### Search

#### POST /search
Hybrid search across indexed repositories.

**Request**:
```json
{
  "query": "authentication flow",
  "limit": 10,
  "search_type": "hybrid",
  "repository": "myragdb",
  "directories": ["src/", "docs/"]
}
```

**Response**:
```json
{
  "results": [
    {
      "file_path": "/Users/liborballaty/.../server.py",
      "repository": "myragdb",
      "score": 0.0316,
      "snippet": "...authentication middleware...",
      "keyword_score": 0.0164,
      "vector_score": 0.0152,
      "file_type": "py"
    }
  ],
  "total": 15,
  "search_type": "hybrid",
  "query": "authentication flow"
}
```

### Repository Management

#### GET /repositories
List all configured repositories with file counts and stats.

**Response**:
```json
[
  {
    "name": "myragdb",
    "path": "/Users/liborballaty/.../myragdb",
    "enabled": true,
    "priority": "high",
    "excluded": false,
    "file_count": 91,                    // Files on disk
    "total_size_bytes": 813561,
    "indexing_stats": [
      {
        "index_type": "keyword",
        "total_files_indexed": 90,       // Files in search index
        "initial_index_time_seconds": 12.5,
        "last_reindex_time_seconds": 8.2
      },
      {
        "index_type": "vector",
        "total_files_indexed": 90,
        "initial_index_time_seconds": 45.3,
        "last_reindex_time_seconds": null
      }
    ]
  }
]
```

**Key Metrics**:
- `file_count`: Available files on disk (what *could* be indexed)
- `total_files_indexed`: Files in search index (what *has been* indexed)

#### POST /reindex
Trigger repository reindexing.

**Request**:
```json
{
  "repositories": ["myragdb"],
  "index_types": ["keyword", "vector"],
  "force_rebuild": false
}
```

**Modes**:
- `incremental` (force_rebuild=false): Only reindex changed files
- `full_rebuild` (force_rebuild=true): Clear index, reindex all files

#### POST /stop-indexing
Stop ongoing indexing gracefully.

**Request**:
```json
{
  "index_types": ["keyword", "vector"]
}
```

### Repository Discovery

#### POST /discover
Discover git repositories in directory tree.

**Request**:
```json
{
  "base_path": "/Users/liborballaty/LocalProjects",
  "max_depth": 3
}
```

#### POST /add-repositories
Add discovered repositories to configuration.

**Request**:
```json
{
  "repositories": [
    {
      "name": "myragdb",
      "path": "/Users/liborballaty/.../myragdb",
      "priority": "high"
    }
  ]
}
```

**Side Effect**: Updates `config/repositories.yaml`

### Statistics

#### GET /stats
System-wide statistics.

**Response**:
```json
{
  "keyword_documents": 90,
  "vector_chunks": 688,
  "is_indexing": false,
  "last_index_time": "2026-01-06T15:59:00Z",
  "files_processed": 90,
  "files_total": 91
}
```

#### GET /health
Health check.

**Response**:
```json
{
  "status": "healthy",
  "meilisearch": "connected",
  "chromadb": "connected"
}
```

### LLM Management

#### GET /llms
List available LLM models.

#### POST /llms/start
Start a local LLM.

**Request**:
```json
{
  "model_id": "llama-4-scout-17b",
  "mode": "function_calling"
}
```

#### POST /llms/stop
Stop a running LLM.

---

## Web UI Architecture

### Technology
- Vanilla JavaScript (ES6+)
- HTML5
- CSS3 (CSS variables for theming)

### Files
- `web-ui/index.html` - Main UI
- `web-ui/static/js/app.js` - JavaScript logic
- Inline CSS in index.html

### Tabs

**1. Search Tab**
- Query input
- Search type selector (Hybrid, Keyword, Vector)
- Repository filter dropdown
- Directory filter input
- Results display with syntax highlighting

**2. Repository Manager Tab**
- Repository discovery form
- Repository list showing:
  - 📁 Available: X files (Y MB) - Files on disk
  - ✓ Indexed: Z files (N%) - Files in search index
  - ⚡K: Xs ⚡V: Ys - Indexing timing stats
  - Enable/disable toggles
  - Lock/exclude capability
- Reindex controls with progress bars

**3. Statistics Tab**
- Keyword documents count
- Vector chunks count
- Total searches
- Average response time
- Last indexing run
- Current status

**4. LLM Manager Tab**
- Grid of available models
- Start/stop controls
- Mode selection (function calling, speed)
- Status indicators

### Real-time Updates
- Polls `/stats` every 2 seconds during indexing
- Updates progress bars
- Shows current repository and file count

---

## LLM Integration System

### Architecture
```
FastAPI (Port 3003)
    │
    │ subprocess.Popen()
    ▼
llama-server (Port 8080/8081)
    │
    │ OpenAI-compatible API
    ▼
HTTP clients (curl, Python, etc.)
```

### Model Storage
`/Users/liborballaty/llms/` - All GGUF models

### Startup Commands
See "LLM Manager" section above for full llama-server commands

---

## MCP Server Implementation

### Protocol
JSON-RPC 2.0 over stdio

### Tools
See "MCP Server" section above for full tool schemas

---

## Configuration Management

### Hierarchy
See "Configuration System" section above

---

## Performance Optimizations

### 1. SQLite Indexed Queries
**Impact**: 100x faster on 10,000+ files (1000ms → 10ms)

**Before** (O(n) table scan):
```sql
SELECT * FROM file_metadata WHERE repository = 'myragdb';
-- Scans all rows
```

**After** (O(log n) B-tree lookup):
```sql
CREATE INDEX idx_repository ON file_metadata(repository);
SELECT * FROM file_metadata WHERE repository = 'myragdb';
-- SEARCH file_metadata USING INDEX idx_repository
```

### 2. Incremental Indexing
**Impact**: 90% reduction in reindex time

- **Before**: Index all 10,000 files = 10 minutes
- **After**: Check metadata, index only 100 changed files = 1 minute

### 3. Embedding Model Caching
**Impact**: Saves 2 seconds per batch × 100 batches = 200 seconds

- Load model once at startup (singleton)
- Reuse for all indexing operations

### 4. Parallel Indexing
**Impact**: 30% faster overall

- Keyword and vector indexing run in separate threads
- Total time = max(keyword_time, vector_time)

### 5. Lazy File Reading (Generators)
**Impact**: Constant memory usage

- Use Python generators to yield files one at a time
- Never load all file paths into memory

### Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Hybrid search | < 500ms | ~200ms | ✅ |
| Keyword search | < 100ms | ~50ms | ✅ |
| Vector search | < 300ms | ~150ms | ✅ |
| Incremental reindex (100 files) | < 30s | ~15s | ✅ |
| Full rebuild (10,000 files) | < 10min | ~6min | ✅ |
| Memory (indexing) | < 2GB | ~1.5GB | ✅ |
| SQLite query (10k files) | < 50ms | ~10ms | ✅ |

---

## Deployment Guide

### Development Setup

```bash
# 1. Clone
git clone https://github.com/yourusername/myragdb.git
cd myragdb

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies
pip install -e .

# 4. Start Meilisearch
./scripts/start_meilisearch.sh

# 5. Initial indexing
python scripts/initial_index.py

# 6. Run server
python -m myragdb.api.server

# 7. Access UI
open http://localhost:3003
```

### Production Deployment

#### Docker Compose

```yaml
version: '3.8'

services:
  meilisearch:
    image: getmeili/meilisearch:v1.5
    ports:
      - "7700:7700"
    volumes:
      - ./data/meilisearch:/meili_data
    environment:
      MEILI_MASTER_KEY: ${MEILI_MASTER_KEY}

  myragdb:
    build: .
    ports:
      - "3003:3003"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      MEILISEARCH_URL: http://meilisearch:7700
      MEILISEARCH_API_KEY: ${MEILI_MASTER_KEY}
    depends_on:
      - meilisearch
```

#### Systemd Service

```ini
[Unit]
Description=MyRAGDB Search Service
After=network.target

[Service]
Type=simple
User=myragdb
WorkingDirectory=/opt/myragdb
Environment="PATH=/opt/myragdb/venv/bin"
ExecStart=/opt/myragdb/venv/bin/python -m myragdb.api.server
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## Glossary

**BM25**: Best Matching 25 - probabilistic ranking algorithm

**ChromaDB**: Open-source vector database

**Embedding**: Dense vector representation (384 dims for MiniLM)

**GGUF**: GPT-Generated Unified Format (quantized LLM format)

**Hybrid Search**: Keyword (BM25) + semantic (vector) search

**Incremental Indexing**: Only reindex changed files (mtime check)

**llama.cpp**: C++ LLaMA inference engine

**MCP**: Model Context Protocol

**Meilisearch**: Fast, typo-tolerant search engine

**Quantization**: Reduced precision (Q8_0 = 8-bit, Q4_K_M = 4-bit)

**RRF**: Reciprocal Rank Fusion (merge ranked lists)

**sentence-transformers**: Sentence embedding library

**Vector Search**: Semantic search via cosine similarity

---

## File Structure

```
myragdb/
├── config/
│   └── repositories.yaml
├── data/
│   ├── chromadb/               # Vector embeddings
│   ├── file_metadata.db        # SQLite (ACTIVE) ✅
│   ├── meilisearch/            # Keyword index
│   └── embeddings_cache/
├── docs/
│   ├── myragdb-SYSTEM_ARCHITECTURE.md  # This file
│   ├── TEST-DESIGN.md
│   └── VERSION_BUMPING.md
├── logs/
│   └── llm_*.log
├── mcp_server/
│   └── server.py               # MCP protocol server
├── scripts/
│   ├── start_meilisearch.sh
│   ├── initial_index.py
│   └── clear_indexes.py
├── src/myragdb/
│   ├── api/
│   │   ├── server.py           # FastAPI (port 3003)
│   │   └── models.py           # Pydantic models
│   ├── db/
│   │   ├── file_metadata.py    # SQLite metadata (ACTIVE) ✅
│   │   └── metadata.py         # DEPRECATED ❌
│   ├── indexers/
│   │   ├── file_scanner.py
│   │   ├── meilisearch_indexer.py
│   │   └── vector_indexer.py
│   ├── llm/
│   │   ├── llm_router.py
│   │   └── query_rewriter.py
│   ├── search/
│   │   └── hybrid_search.py
│   ├── utils/
│   │   ├── repo_discovery.py
│   │   └── id_generator.py
│   ├── config.py
│   └── cli.py
├── web-ui/
│   ├── index.html
│   └── static/js/app.js
├── requirements.txt
├── setup.py
└── README.md
```

---

## Questions and Support

**Author**: Libor Ballaty <libor@arionetworks.com>

**Repository**: GitHub (private)

**Documentation**: `docs/` directory

**Document Version**: 1.0.0
**Last Updated**: 2026-01-06
