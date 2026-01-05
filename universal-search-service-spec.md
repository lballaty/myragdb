# Universal Search Service - System Specification

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/universal-search-service-spec.md
**Description:** System-wide hybrid search infrastructure enabling semantic code/documentation discovery across all projects
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04  

---

## Executive Summary

Build a laptop-wide search service combining keyword search with vector embeddings to enable AI agents to intelligently discover, cross-reference, and learn from code and documentation across all development projects.

**Key Innovation:** Agents can query conceptually ("find authentication patterns") and get semantically relevant results across all repositories, enabling cross-project learning and pattern reuse.

---

## Problem Statement

### Current State
- Agents operate with limited context (single repo, manual file paths)
- No cross-project knowledge discovery
- Keyword search (grep/ripgrep) lacks semantic understanding
- Each project reinvents solutions to solved problems
- Agents cannot learn from past implementations

### Desired State
- Agents query semantically across all projects
- Automatic discovery of reusable patterns
- Cross-project learning and knowledge transfer
- Unified search API for all agent operations
- Self-improving development workflow

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  MacBook Pro M4 (128GB RAM)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔍 Universal Search Service (localhost:3002)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │  FastAPI REST Service                                 │  │
│  │  ├─ POST /search/hybrid    (Keyword + Vector)        │  │
│  │  ├─ POST /search/keyword   (Keyword only)            │  │
│  │  ├─ POST /search/semantic  (Vector only)             │  │
│  │  ├─ POST /index/repository (Add/update repo)         │  │
│  │  └─ GET  /stats           (Index statistics)         │  │
│  │                                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  📊 Search Engines                                          │
│  ┌──────────────────────┐  ┌──────────────────────────┐   │
│  │  Keyword Index       │  │  Vector Index            │   │
│  │  (Meilisearch)       │  │  (ChromaDB)              │   │
│  │                       │  │                           │   │
│  │  • Term frequency    │  │  • SmolLM2-1.7B          │   │
│  │  • Inverted index    │  │  • Semantic embeddings   │   │
│  │  • Fast lookup       │  │  • Cosine similarity     │   │
│  │  • 10-50ms queries   │  │  • 100-200ms queries     │   │
│  └──────────────────────┘  └──────────────────────────┘   │
│                                                              │
│  📁 Indexed Repositories                                    │
│  ├─ ~/LocalProjects/GitHubProjectsDocuments/               │
│  │  ├─ xLLMArionComply/                                    │
│  │  ├─ RepoDot/                                            │
│  │  └─ ArionNetworks/                                      │
│  ├─ ~/other-projects/                                      │
│  └─ Auto-discovered via config                             │
│                                                              │
│  🤖 Consumers                                               │
│  ├─ Documentation Sync Agent                               │
│  ├─ Cleanup Agent                                          │
│  ├─ Consolidation Agent                                    │
│  ├─ Claude CLI                                             │
│  └─ Future agents via unified API                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Stack

### Core Components

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **API Framework** | FastAPI | Async, OpenAPI docs, Python ecosystem |
| **Keyword Search** | Meilisearch | Fast, production-grade keyword search engine |
| **Vector Store** | ChromaDB | Already familiar, works well with local embeddings |
| **Embedding Model** | SmolLM2-1.7B-Instruct | CPU-optimized, runs on M4, 1.7B params |
| **File Watching** | Watchdog | Auto-reindex on changes |
| **Process Manager** | launchd | macOS native, auto-start on boot |

### Technology Justification

**Why FastAPI?**
- Native async/await for concurrent searches
- Automatic OpenAPI documentation
- Type hints for agent integration
- Python ecosystem (ML/NLP libraries)

**Why Meilisearch?**
- Production-grade search engine
- Fast keyword search performance
- Powerful filtering and faceting
- Handles 1M+ documents easily

**Why ChromaDB?**
- Already using for ArionComply
- Built for embeddings
- Local-first (no cloud dependency)
- Good Python API

**Why SmolLM2-1.7B?**
- Small enough for CPU inference on M4
- Quality embeddings for code/docs
- Fast enough (100-200ms per query)
- Lower memory than larger models

---

## Directory Structure

```
universal-search-service/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── .gitignore
│
├── config/
│   ├── repositories.yaml          # Which repos to index
│   ├── file_filters.yaml          # Include/exclude patterns
│   └── service_config.yaml        # Service settings
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py              # FastAPI app
│   │   ├── routes/
│   │   │   ├── search.py          # Search endpoints
│   │   │   ├── index.py           # Indexing endpoints
│   │   │   └── stats.py           # Statistics endpoints
│   │   └── models/
│   │       ├── requests.py        # Pydantic request models
│   │       └── responses.py       # Pydantic response models
│   │
│   ├── indexers/
│   │   ├── __init__.py
│   │   ├── meilisearch_indexer.py # Meilisearch indexing
│   │   ├── vector_indexer.py      # ChromaDB + embeddings
│   │   ├── file_scanner.py        # Repository file discovery
│   │   └── file_watcher.py        # Auto-reindex on changes
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   ├── keyword_search.py      # Keyword search
│   │   ├── vector_search.py       # Semantic search
│   │   ├── hybrid_search.py       # Combined search
│   │   └── result_merger.py       # Merge + rank results
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── model_manager.py       # Load/manage SmolLM2
│   │   ├── text_chunker.py        # Split large files
│   │   └── embedding_cache.py     # Cache embeddings
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_processor.py      # Extract text from files
│       ├── logger.py              # Logging setup
│       └── metrics.py             # Performance metrics
│
├── data/                          # Gitignored
│   ├── indexes/
│   │   ├── keyword/               # Meilisearch indexes
│   │   └── vectors/               # ChromaDB storage
│   ├── embeddings_cache/          # Cached embeddings
│   └── metadata/                  # File metadata, timestamps
│
├── scripts/
│   ├── install_service.sh         # launchd setup
│   ├── initial_index.py           # First-time indexing
│   ├── reindex.py                 # Full reindex
│   └── benchmark.py               # Performance testing
│
├── tests/
│   ├── test_keyword.py
│   ├── test_vector.py
│   ├── test_hybrid.py
│   └── test_api.py
│
└── agent-library/                 # Helper library for agents
    ├── __init__.py
    ├── search_client.py           # Python client for agents
    ├── query_builder.py           # Query construction helpers
    └── examples/
        ├── documentation_sync.py  # Example: doc sync agent
        └── pattern_finder.py      # Example: find reusable patterns
```

---

## Data Model

### Repository Configuration (`config/repositories.yaml`)

```yaml
repositories:
  - name: xLLMArionComply
    path: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/xLLMArionComply
    enabled: true
    file_patterns:
      include:
        - "**/*.md"
        - "**/*.py"
        - "**/*.ts"
        - "**/*.dart"
      exclude:
        - "**/node_modules/**"
        - "**/.git/**"
        - "**/archive-*/**"
        - "**/*.lock"
    priority: high  # For result ranking
    
  - name: RepoDot
    path: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/RepoDot
    enabled: true
    file_patterns:
      include:
        - "**/*.md"
        - "**/*.py"
      exclude:
        - "**/venv/**"
        - "**/.git/**"
    priority: high
    
  - name: ArionNetworks
    path: /Users/liborballaty/LocalProjects/ArionNetworks
    enabled: true
    file_patterns:
      include:
        - "**/*.md"
        - "**/*.ts"
        - "**/*.tsx"
      exclude:
        - "**/dist/**"
        - "**/build/**"
    priority: medium
```

### Search Request Model

```python
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class SearchType(str, Enum):
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"

class SearchRequest(BaseModel):
    query: str
    search_type: SearchType = SearchType.HYBRID
    repositories: Optional[List[str]] = None  # None = all
    file_types: Optional[List[str]] = None    # [".md", ".py"]
    limit: int = 10
    min_score: float = 0.0
    include_snippets: bool = True
    snippet_length: int = 200
```

### Search Result Model

```python
class SearchResult(BaseModel):
    file_path: str
    repository: str
    score: float
    keyword_score: Optional[float] = None
    vector_score: Optional[float] = None
    snippet: Optional[str] = None
    line_number: Optional[int] = None
    file_type: str
    last_modified: str
    metadata: dict = {}

class SearchResponse(BaseModel):
    query: str
    total_results: int
    search_time_ms: float
    results: List[SearchResult]
```

### Index Metadata

```python
class FileMetadata(BaseModel):
    file_path: str
    repository: str
    file_type: str
    size_bytes: int
    last_modified: str
    last_indexed: str
    content_hash: str  # Detect changes
    chunk_count: int   # For large files
```

---

## API Specification

### Search Endpoints

#### `POST /search/hybrid`
Combines Meilisearch keyword and vector search for best results.

**Request:**
```json
{
  "query": "authentication flow with JWT tokens",
  "repositories": ["xLLMArionComply", "RepoDot"],
  "file_types": [".md", ".py"],
  "limit": 10,
  "include_snippets": true
}
```

**Response:**
```json
{
  "query": "authentication flow with JWT tokens",
  "total_results": 7,
  "search_time_ms": 245.3,
  "results": [
    {
      "file_path": "xLLMArionComply/docs/auth-flow.md",
      "repository": "xLLMArionComply",
      "score": 0.95,
      "bm25_score": 0.92,
      "vector_score": 0.98,
      "snippet": "...JWT tokens are validated using Supabase authentication...",
      "line_number": 45,
      "file_type": ".md",
      "last_modified": "2026-01-02T10:30:00Z"
    }
  ]
}
```

#### `POST /search/keyword`
Keyword-only search (faster, exact matching).

#### `POST /search/semantic`
Vector-only search (semantic understanding, slower).

### Index Management Endpoints

#### `POST /index/repository`
Add or reindex a repository.

**Request:**
```json
{
  "repository_name": "xLLMArionComply",
  "full_reindex": false  # Incremental by default
}
```

#### `GET /stats`
Get index statistics.

**Response:**
```json
{
  "total_files_indexed": 8432,
  "total_repositories": 3,
  "index_size_mb": 2847,
  "last_full_index": "2026-01-04T05:00:00Z",
  "repositories": [
    {
      "name": "xLLMArionComply",
      "files_indexed": 4521,
      "last_updated": "2026-01-04T12:30:00Z"
    }
  ]
}
```

---

## Search Algorithm

### Hybrid Search Ranking

**Step 1: Execute both searches in parallel**
```python
async def hybrid_search(query: str):
    # Run keyword and vector search concurrently
    keyword_results, vector_results = await asyncio.gather(
        keyword_search(query),
        vector_search(query)
    )
```

**Step 2: Normalize scores**
```python
# Normalize keyword scores (0-1)
keyword_normalized = normalize_scores(keyword_results)

# Vector scores already normalized (cosine similarity 0-1)
vector_normalized = vector_results
```

**Step 3: Combine with weights**
```python
# Default weights (tunable)
KEYWORD_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6

combined_score = (
    KEYWORD_WEIGHT * keyword_score +
    VECTOR_WEIGHT * vector_score
)
```

**Step 4: Merge and deduplicate**
```python
# Same file might appear in both result sets
merged = merge_by_file_path(bm25_results, vector_results)
sorted_results = sort_by_combined_score(merged)
```

**Step 5: Apply filters and limits**
```python
filtered = apply_repository_filter(sorted_results)
final = apply_file_type_filter(filtered)
return final[:limit]
```

### Semantic Chunking Strategy

Large files are split into semantic chunks:

```python
def chunk_file(content: str, max_chunk_size: int = 1000):
    """
    Split file into chunks at natural boundaries:
    - Function/class definitions
    - Section headers (markdown)
    - Paragraph breaks
    """
    chunks = []
    
    # For code files: split by functions/classes
    if is_code_file(content):
        chunks = split_by_code_blocks(content)
    
    # For markdown: split by headers
    elif is_markdown(content):
        chunks = split_by_headers(content)
    
    # Generic: split by paragraphs
    else:
        chunks = split_by_paragraphs(content)
    
    # Each chunk gets embedded separately
    # Maintains context while keeping chunk size reasonable
    return chunks
```

---

## Performance Targets

### Search Performance

| Operation | Target | Acceptable | Notes |
|-----------|--------|-----------|-------|
| Keyword search | <50ms | <100ms | Keyword lookup |
| Vector search | <200ms | <500ms | Embedding similarity |
| Hybrid search | <300ms | <600ms | Combined |
| Index update (per file) | <100ms | <500ms | Incremental |

### Accuracy Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Precision@10 | >85% | Top 10 results relevant |
| Recall@50 | >90% | Finds 90% of relevant docs in top 50 |
| Semantic accuracy | >90% | Conceptual queries find right docs |

### Scalability Targets

| Metric | Initial | Target | Max |
|--------|---------|--------|-----|
| Total files | 10,000 | 50,000 | 100,000 |
| Repositories | 3 | 10 | 20 |
| Index size | 3GB | 10GB | 20GB |
| Memory usage | 3GB | 8GB | 12GB |

---

## Implementation Phases

### Phase 1: Core Service (Est. 4 hours)

**Deliverables:**
1. FastAPI server with basic endpoints
2. Keyword indexer (Meilisearch)
3. Vector indexer (ChromaDB + SmolLM2)
4. Basic search implementation
5. Configuration system

**Success Criteria:**
- Service starts and responds to health checks
- Can index a single repository
- Keyword search returns results
- Vector search returns results
- Hybrid search combines both

**Files to create:**
- `src/api/server.py`
- `src/indexers/meilisearch_indexer.py`
- `src/indexers/vector_indexer.py`
- `src/search/hybrid_search.py`
- `config/repositories.yaml`

### Phase 2: Repository Integration (Est. 2 hours)

**Deliverables:**
1. Index xLLMArionComply repository
2. Index RepoDot repository
3. File filtering working (include/exclude patterns)
4. Metadata storage and retrieval
5. Basic performance metrics

**Success Criteria:**
- All configured repos indexed successfully
- Search works across multiple repositories
- File filters correctly exclude unwanted files
- Can query by repository name
- Performance meets initial targets

**Files to create:**
- `src/indexers/file_scanner.py`
- `src/utils/file_processor.py`
- `scripts/initial_index.py`

### Phase 3: Agent Integration (Est. 2 hours)

**Deliverables:**
1. Python client library for agents
2. Query builder utilities
3. Example: Documentation sync agent integration
4. Example: Pattern discovery agent
5. Agent authentication (optional API keys)

**Success Criteria:**
- Documentation sync agent can query service
- Agents receive structured, parseable results
- Query construction helpers work
- Example agents demonstrate value

**Files to create:**
- `agent-library/search_client.py`
- `agent-library/query_builder.py`
- `agent-library/examples/documentation_sync.py`

### Phase 4: Auto-Indexing & Operations (Est. 2 hours)

**Deliverables:**
1. File watcher for auto-reindexing
2. Incremental indexing (only changed files)
3. launchd service configuration
4. Logging and monitoring
5. Performance benchmarks

**Success Criteria:**
- Service auto-starts on boot
- File changes trigger reindexing within 5 seconds
- Incremental updates work correctly
- Logs capture important events
- Benchmarks validate performance targets

**Files to create:**
- `src/indexers/file_watcher.py`
- `scripts/install_service.sh`
- `scripts/benchmark.py`
- `com.arionetworks.universalsearch.plist` (launchd)

---

## Installation & Setup

### Prerequisites

```bash
# Python 3.11+ required
python --version  # Should be 3.11 or higher

# Install system dependencies (macOS)
brew install llvm  # For Tantivy (optional, faster than Whoosh)
```

### Initial Setup

```bash
# 1. Clone/create repository
mkdir -p ~/universal-search-service
cd ~/universal-search-service

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure repositories
cp config/repositories.yaml.example config/repositories.yaml
# Edit config/repositories.yaml with your repo paths

# 5. Download SmolLM2 model
python scripts/download_model.py

# 6. Run initial indexing
python scripts/initial_index.py

# 7. Start service
python -m src.api.server

# Service now running at http://localhost:3002
```

### Install as System Service (launchd)

```bash
# Make service start automatically on boot
./scripts/install_service.sh

# Service commands
launchctl load ~/Library/LaunchAgents/com.arionetworks.universalsearch.plist
launchctl start com.arionetworks.universalsearch
launchctl stop com.arionetworks.universalsearch
```

---

## Configuration

### Service Configuration (`config/service_config.yaml`)

```yaml
service:
  host: localhost
  port: 3002
  workers: 4  # CPU cores for parallel processing
  
indexing:
  chunk_size: 1000  # Characters per chunk for large files
  batch_size: 100   # Files to index before committing
  watch_enabled: true  # Auto-reindex on file changes
  watch_debounce_ms: 1000  # Wait before reindexing
  
search:
  default_limit: 10
  max_limit: 100
  bm25_weight: 0.4
  vector_weight: 0.6
  snippet_length: 200
  
embeddings:
  model: "SmolLM2-1.7B-Instruct"
  model_path: "./models/smollm2-1.7b"
  device: "cpu"  # M4 CPU is fast enough
  batch_size: 32
  cache_enabled: true
  
performance:
  max_memory_gb: 8
  index_cache_size: 1000  # Documents to keep in memory
  embedding_cache_size: 10000  # Cached embeddings
```

### File Filters (`config/file_filters.yaml`)

```yaml
global_exclude:
  # Version control
  - "**/.git/**"
  - "**/.svn/**"
  
  # Dependencies
  - "**/node_modules/**"
  - "**/venv/**"
  - "**/env/**"
  - "**/.env/**"
  
  # Build artifacts
  - "**/dist/**"
  - "**/build/**"
  - "**/*.pyc"
  - "**/__pycache__/**"
  
  # Archives
  - "**/archive-*/**"
  - "**/archived/**"
  - "**/*.zip"
  - "**/*.tar.gz"
  
  # Locks and logs
  - "**/*.lock"
  - "**/*.log"
  - "**/logs/**"

file_type_configs:
  markdown:
    extensions: [".md", ".markdown"]
    chunking: semantic_headers
    priority: high
    
  python:
    extensions: [".py"]
    chunking: code_blocks
    priority: high
    
  typescript:
    extensions: [".ts", ".tsx"]
    chunking: code_blocks
    priority: high
    
  dart:
    extensions: [".dart"]
    chunking: code_blocks
    priority: medium
    
  config:
    extensions: [".json", ".yaml", ".yml", ".toml"]
    chunking: whole_file
    priority: low
```

---

## Agent Integration Examples

### Example 1: Documentation Sync Agent

```python
from agent_library import SearchClient, QueryBuilder

class DocumentationSyncAgent:
    def __init__(self):
        self.search = SearchClient(base_url="http://localhost:3002")
    
    def find_related_todos(self, domain_name: str):
        """Find TODO items related to a domain"""
        
        query = QueryBuilder() \
            .semantic(f"TODO items and tasks for {domain_name} domain") \
            .in_repositories(["xLLMArionComply"]) \
            .file_types([".md"]) \
            .limit(20) \
            .build()
        
        results = self.search.hybrid_search(query)
        
        # Filter for TODO files
        todo_files = [
            r for r in results 
            if "TODO" in r.file_path.upper()
        ]
        
        return todo_files
    
    def find_documentation_gaps(self, domain_name: str):
        """Find features documented but not in TODO"""
        
        # Find documented features
        docs_query = QueryBuilder() \
            .semantic(f"features and functionality for {domain_name}") \
            .in_repositories(["xLLMArionComply"]) \
            .file_types([".md"]) \
            .exclude_patterns(["*TODO*"]) \
            .limit(50) \
            .build()
        
        documented = self.search.semantic_search(docs_query)
        
        # Find TODO items
        todos = self.find_related_todos(domain_name)
        
        # Compare (simplified - would need NLP for real comparison)
        gaps = self.identify_gaps(documented, todos)
        
        return gaps
```

### Example 2: Cross-Project Pattern Finder

```python
from agent_library import SearchClient

class PatternFinderAgent:
    def __init__(self):
        self.search = SearchClient(base_url="http://localhost:3002")
    
    def find_similar_implementations(self, description: str):
        """Find how other projects solved similar problems"""
        
        results = self.search.semantic_search({
            "query": description,
            "repositories": None,  # Search ALL repos
            "file_types": [".py", ".ts", ".dart"],
            "limit": 20
        })
        
        # Group by repository
        by_repo = {}
        for result in results:
            repo = result.repository
            if repo not in by_repo:
                by_repo[repo] = []
            by_repo[repo].append(result)
        
        return by_repo
    
    def suggest_implementation(self, feature_description: str):
        """Suggest implementation based on past solutions"""
        
        similar = self.find_similar_implementations(feature_description)
        
        # Analyze patterns
        suggestions = []
        for repo, files in similar.items():
            # Extract common patterns
            pattern = self.extract_pattern(files)
            suggestions.append({
                "source_repo": repo,
                "pattern": pattern,
                "confidence": files[0].score,
                "example_files": [f.file_path for f in files[:3]]
            })
        
        return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)
```

### Example 3: Documentation Completeness Checker

```python
class CompletenessCheckerAgent:
    def __init__(self):
        self.search = SearchClient(base_url="http://localhost:3002")
    
    def check_code_vs_docs(self, repository: str):
        """Find code components without documentation"""
        
        # Find all code files
        code_results = self.search.bm25_search({
            "query": "class function async def",  # Common code patterns
            "repositories": [repository],
            "file_types": [".py", ".ts", ".dart"],
            "limit": 1000
        })
        
        # Find all documentation
        doc_results = self.search.bm25_search({
            "query": "*",  # All docs
            "repositories": [repository],
            "file_types": [".md"],
            "limit": 1000
        })
        
        # Extract component names from code
        components = self.extract_component_names(code_results)
        
        # Check if each component is documented
        undocumented = []
        for component in components:
            is_documented = self.is_component_documented(
                component, 
                doc_results
            )
            if not is_documented:
                undocumented.append(component)
        
        return undocumented
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_keyword.py
def test_keyword_exact_match():
    """Keyword search should find exact keyword matches"""
    indexer = MeilisearchIndexer()
    indexer.index_document("test.md", "supabase authentication flow")
    
    results = indexer.search("supabase authentication")
    assert len(results) == 1
    assert results[0].score > 0.8

# tests/test_vector.py
def test_vector_semantic_match():
    """Vector search should find semantically similar content"""
    indexer = VectorIndexer()
    indexer.index_document("test.md", "user login with JWT tokens")
    
    # Query uses different words but same concept
    results = indexer.search("authentication flow")
    assert len(results) == 1
    assert results[0].score > 0.7

# tests/test_hybrid.py
def test_hybrid_combines_results():
    """Hybrid search should merge keyword and vector results"""
    searcher = HybridSearcher()
    
    # Index documents
    searcher.index("doc1.md", "authentication with JWT")
    searcher.index("doc2.md", "user login security")
    
    results = searcher.search("authentication flow")
    
    # Should find both (one by keyword, one by semantics)
    assert len(results) == 2
    # JWT doc should rank higher (has exact keyword)
    assert "JWT" in results[0].content
```

### Integration Tests

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient

def test_search_endpoint():
    """Test /search/hybrid endpoint"""
    client = TestClient(app)
    
    response = client.post("/search/hybrid", json={
        "query": "authentication flow",
        "repositories": ["test_repo"],
        "limit": 10
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["total_results"] >= 0

def test_index_repository():
    """Test repository indexing"""
    client = TestClient(app)
    
    response = client.post("/index/repository", json={
        "repository_name": "test_repo",
        "full_reindex": True
    })
    
    assert response.status_code == 200
    assert "files_indexed" in response.json()
```

### Performance Tests

```python
# scripts/benchmark.py
import time
import statistics

def benchmark_search_performance():
    """Measure search performance"""
    
    queries = [
        "authentication flow",
        "database migration",
        "error handling",
        # ... 100 test queries
    ]
    
    times = []
    for query in queries:
        start = time.time()
        results = search_service.hybrid_search(query)
        elapsed = time.time() - start
        times.append(elapsed * 1000)  # Convert to ms
    
    print(f"Average search time: {statistics.mean(times):.2f}ms")
    print(f"95th percentile: {statistics.quantiles(times, n=20)[18]:.2f}ms")
    print(f"Max time: {max(times):.2f}ms")
```

---

## Monitoring & Observability

### Metrics to Track

```python
# Prometheus-style metrics
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
search_requests_total = Counter(
    'search_requests_total',
    'Total search requests',
    ['search_type', 'repository']
)

search_duration_seconds = Histogram(
    'search_duration_seconds',
    'Search duration in seconds',
    ['search_type']
)

# Index metrics
files_indexed_total = Gauge(
    'files_indexed_total',
    'Total files indexed',
    ['repository']
)

index_size_bytes = Gauge(
    'index_size_bytes',
    'Size of search indexes in bytes',
    ['index_type']
)

# Error metrics
search_errors_total = Counter(
    'search_errors_total',
    'Total search errors',
    ['error_type']
)
```

### Logging Structure

```python
import structlog

logger = structlog.get_logger()

# Search logging
logger.info(
    "search_completed",
    query=query,
    search_type="hybrid",
    total_results=len(results),
    duration_ms=elapsed_time,
    repositories=repositories
)

# Index logging
logger.info(
    "repository_indexed",
    repository=repo_name,
    files_added=added_count,
    files_updated=updated_count,
    duration_seconds=elapsed
)

# Error logging
logger.error(
    "search_failed",
    query=query,
    error=str(e),
    traceback=traceback.format_exc()
)
```

---

## Security Considerations

### Local-Only Service
- Service binds to `localhost` only (not accessible externally)
- No authentication required (trusted local environment)
- Optional: API key for production use

### Data Privacy
- All data stays local (no cloud uploads)
- Indexed content never leaves laptop
- Embeddings generated locally

### File Access
- Service runs as user (no elevated privileges)
- Can only access files user can access
- Respects file system permissions

---

## Future Enhancements

### Phase 5: Advanced Features (Future)

1. **Code-Aware Chunking**
   - Parse AST for better code chunking
   - Preserve function/class context
   - Language-specific optimizations

2. **Query Understanding**
   - Intent classification (code search vs doc search)
   - Query expansion (synonyms, related terms)
   - Auto-correction for typos

3. **Result Ranking Improvements**
   - Learn from click-through data
   - Repository priority weighting
   - File freshness boosting

4. **Multi-Modal Search**
   - Search in images (diagrams, screenshots)
   - Search in PDFs
   - Search in Jupyter notebooks

5. **Agent Collaboration**
   - Agents share successful queries
   - Query templates for common tasks
   - Collaborative filtering

6. **Incremental Learning**
   - Model fine-tuning on your codebase
   - Custom embeddings for domain terms
   - Personalized ranking

---

## Success Metrics

### Technical Metrics
- Search latency <300ms (p95)
- Index build time <30min (full reindex)
- Memory usage <8GB
- Accuracy (precision@10) >85%

### Agent Productivity Metrics
- Time to find relevant code: -50%
- Cross-project pattern reuse: +200%
- Documentation gaps discovered: +100%
- Agent autonomy: +75%

### System Health Metrics
- Service uptime: >99.9%
- Index freshness: <5min lag
- Error rate: <0.1%

---

## Dependencies

### Python Packages (`requirements.txt`)

```
# Core framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3

# Search engines
meilisearch==0.35.0  # Keyword search
chromadb==0.4.22  # Vector store

# ML/Embeddings
transformers==4.36.2
torch==2.1.2
sentence-transformers==2.3.1

# File processing
python-magic==0.4.27  # File type detection
chardet==5.2.0  # Encoding detection
watchdog==3.0.0  # File watching

# Utilities
pyyaml==6.0.1
python-dotenv==1.0.0
structlog==24.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0

# Monitoring
prometheus-client==0.19.0
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Clone repository to `~/universal-search-service`
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Configure `config/repositories.yaml`
- [ ] Download SmolLM2 model
- [ ] Run initial indexing
- [ ] Verify search works
- [ ] Run performance benchmarks

### Service Setup
- [ ] Install launchd service
- [ ] Verify service auto-starts
- [ ] Check logs for errors
- [ ] Monitor resource usage
- [ ] Test agent integration

### Validation
- [ ] Search latency meets targets
- [ ] All repositories indexed
- [ ] File watching works
- [ ] Agents can query successfully
- [ ] Cross-project search works

---

## Support & Maintenance

### Routine Maintenance

**Daily:**
- Automatic file watching handles updates
- No manual intervention needed

**Weekly:**
- Review logs for errors
- Check index size growth
- Verify service uptime

**Monthly:**
- Full reindex (refresh all data)
- Update dependencies
- Review performance metrics
- Tune weights if needed

### Troubleshooting

**Search returns no results:**
```bash
# Check if repository is indexed
curl http://localhost:3002/stats

# Verify files exist
ls /path/to/repository

# Check logs
tail -f data/logs/service.log
```

**Service won't start:**
```bash
# Check if port is available
lsof -i :3002

# Check logs
cat data/logs/service.log

# Restart service
launchctl stop com.arionetworks.universalsearch
launchctl start com.arionetworks.universalsearch
```

**Slow search performance:**
```bash
# Run benchmark
python scripts/benchmark.py

# Check index size
du -sh data/indexes/*

# Consider reindexing
python scripts/reindex.py
```

---

## Glossary

**Keyword Search:** Term-based search using Meilisearch for fast retrieval
**Vector Embedding:** Numerical representation of text capturing semantic meaning
**Hybrid Search:** Combining keyword and semantic (vector) search
**Chunking:** Splitting large documents into smaller pieces for indexing
**Cosine Similarity:** Measure of similarity between two vectors
**TF-IDF:** Term Frequency-Inverse Document Frequency, weighting scheme
**Incremental Indexing:** Updating index with only changed files
**launchd:** macOS system service manager  

---

## References

**Technical Papers:**
- Robertson & Zaragoza (2009): "The Probabilistic Relevance Framework: BM25 and Beyond"
- Reimers & Gurevych (2019): "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"

**Libraries & Tools:**
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Meilisearch Documentation: https://docs.meilisearch.com/
- ChromaDB Documentation: https://docs.trychroma.com/
- SmolLM2 Paper: https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct

**Related Projects:**
- Algolia: Commercial search service (inspiration)
- Meilisearch: Open-source search engine
- Vespa: Search and recommendation engine

---

## Appendix A: Sample Queries

### Agent Query Patterns

```python
# Pattern 1: Find implementation examples
{
    "query": "How to implement rate limiting in edge functions",
    "search_type": "semantic",
    "file_types": [".ts", ".py"]
}

# Pattern 2: Find related TODOs
{
    "query": "authentication authorization security tasks",
    "search_type": "hybrid",
    "file_types": [".md"],
    "file_patterns": ["*TODO*.md"]
}

# Pattern 3: Cross-project pattern discovery
{
    "query": "database migration scripts and patterns",
    "search_type": "semantic",
    "repositories": None,  # All repos
    "limit": 50
}

# Pattern 4: Documentation lookup
{
    "query": "Supabase Row Level Security configuration",
    "search_type": "keyword",  # Exact keywords
    "file_types": [".md"],
    "repositories": ["xLLMArionComply"]
}
```

---

## Appendix B: Performance Tuning Guide

### Keyword Search Parameters

```python
# Meilisearch ranking parameters
keyword_params = {
    "ranking_rules": [
        "words",        # Proximity of search terms
        "typo",         # Number of typos
        "proximity",    # Proximity between matched terms
        "attribute",    # Searchable attribute priority
        "sort",         # User-specified sort
        "exactness",    # Exact matches ranked higher
    ],
}

# Results ranked by number of matching terms and proximity
# Supports fuzzy matching and typo tolerance
```

### Vector Search Parameters

```python
# ChromaDB parameters
vector_params = {
    "n_results": 20,  # Retrieve more, then rerank
    "distance_metric": "cosine",  # Or "l2", "ip"
}

# Embedding model parameters
embedding_params = {
    "max_length": 512,  # Max tokens per chunk
    "batch_size": 32,  # Embedding batch size
    "normalize_embeddings": True,  # L2 normalize
}
```

### Hybrid Weights Tuning

```python
# Test different weight combinations
weight_configs = [
    (0.3, 0.7),  # More semantic
    (0.4, 0.6),  # Balanced (default)
    (0.5, 0.5),  # Equal
    (0.6, 0.4),  # More keyword
    (0.7, 0.3),  # Mostly keyword
]

# Run evaluation on test queries
for keyword_w, vec_w in weight_configs:
    precision = evaluate_precision(keyword_w, vec_w)
    print(f"Keyword:{keyword_w} Vector:{vec_w} -> P@10: {precision}")
```

---

**End of Specification**

---

**Next Steps:**
1. Create new repository: `~/universal-search-service`
2. Set up directory structure
3. Begin Phase 1 implementation
4. Iterate based on real-world usage

**Questions or modifications needed before starting implementation?**
