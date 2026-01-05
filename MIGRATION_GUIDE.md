# Whoosh → Meilisearch Migration Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/MIGRATION_GUIDE.md
**Description:** Complete migration guide from Whoosh to Meilisearch with llama.cpp RAG integration
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04

---

## Migration Status

### ✅ Completed
1. Removed Whoosh dependency from `requirements.txt`
2. Installed Meilisearch Python SDK (v0.31.0)
3. Created `id_generator.py` - Base64 hash IDs for Meilisearch/ChromaDB parity
4. Created `meilisearch_indexer.py` - Full featured indexer with:
   - Searchable attributes: `["file_name", "folder_name", "content"]`
   - Filterable attributes: `["file_path", "extension", "last_modified", "size", "repository"]`
   - Ranking rules: `["words", "typo", "proximity", "attribute", "exactness"]`
   - 50k batch indexing
   - Incremental indexing (mtime-based)
   - Base64 hash primary keys

### ⏳ In Progress
5. Hybrid search with RRF (draft created, needs directory)
6. LLM router for llama.cpp ports
7. Update `server.py` to use Meilisearch
8. Update `vector_indexer.py` to use Base64 IDs

---

## Installation Steps

### 1. Install Meilisearch Service

```bash
# macOS (Homebrew)
brew install meilisearch

# Or download binary
curl -L https://install.meilisearch.com | sh
```

### 2. Start Meilisearch with 32GB Memory

```bash
# Create data directory
mkdir -p /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/data/meilisearch

# Start with 32GB max indexing memory (128GB RAM system)
meilisearch \
  --db-path /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/data/meilisearch \
  --master-key "YOUR_MASTER_KEY_HERE" \
  --max-indexing-memory 34359738368 \
  --http-addr 127.0.0.1:7700
```

### 3. Update Configuration

Add to `.env`:
```bash
MEILISEARCH_HOST=http://localhost:7700
MEILISEARCH_API_KEY=YOUR_MASTER_KEY_HERE
MEILISEARCH_INDEX=files
```

---

## Architecture Changes

### Before (Whoosh)
```
FastAPI Server
├── Whoosh (Keyword) - Pure Python, in-process
├── ChromaDB (Vector) - Separate service
└── Manual result merging
```

### After (Meilisearch)
```
FastAPI Server
├── Meilisearch (Keyword) - Rust-based, separate service, memory-mapped
├── ChromaDB (Vector) - Unchanged
├── RRF Hybrid Search - Reciprocal Rank Fusion
└── LLM Router - llama.cpp multi-port suite
```

---

## Key Features

### 1. Document ID Parity

**File:** `src/myragdb/utils/id_generator.py`

```python
from myragdb.utils.id_generator import generate_document_id

# Same file → same ID in both Meilisearch and ChromaDB
doc_id = generate_document_id("/path/to/file.py")
# Returns: "xK7JmH9vQpL2..." (Base64 URL-safe SHA256)
```

### 2. Meilisearch Indexer

**File:** `src/myragdb/indexers/meilisearch_indexer.py`

```python
from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer

indexer = MeilisearchIndexer(
    host="http://localhost:7700",
    api_key="YOUR_KEY"
)

# Batch indexing (50k batches for 2M+ files)
count = indexer.index_files_batch(
    scanned_files,
    batch_size=50000,
    incremental=True  # Only changed files
)

# Search with filters
results = indexer.search(
    "authentication flow",
    folder_filter="src/auth",
    extension_filter=".py",
    limit=10
)
```

### 3. Hybrid Search with RRF

**Formula:**
```
Score(d) = Σ(r ∈ {Meili, Chroma}) 1 / (k + rank_r(d))

Where k = 60 (smoothing constant)
```

**Implementation:**
```python
def reciprocal_rank_fusion(meili_hits, chroma_hits, k=60):
    scores = {}
    # Process Meilisearch ranks
    for rank, hit in enumerate(meili_hits, start=1):
        doc_id = hit['id']
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)

    # Process ChromaDB ranks
    for rank, doc_id in enumerate(chroma_hits, start=1):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)

    # Sort by combined score
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### 4. LLM Router (llama.cpp Suite)

**Port Mapping:**
- **8081** - phi3 (Fast summaries/keywords)
- **8082** - smollm3 (Fast tasks)
- **8085** - qwen-coder-7b (Code questions)
- **8087** - llama-3.1-8b (Fallback)
- **8089** - mistral-small-24b (Heavy reasoning)
- **8092** - deepseek-r1-qwen-32b (Complex RAG)

**Configuration:**
```python
# All models: n_ctx=32768, use_mmap=True, metal_enabled=True
```

---

## Remaining Tasks

### 1. Complete `hybrid_search.py`

Location: `src/myragdb/search/hybrid_search.py`

```python
class HybridSearchEngine:
    async def hybrid_search(query, limit=10, keyword_weight=0.5):
        # Parallel execution
        meili_results = await meili.search(query, limit=limit*3)
        chroma_results = await vector.search(query, k=limit*3)

        # RRF merge
        merged = reciprocal_rank_fusion(meili_results, chroma_results, k=60)
        return merged[:limit]
```

### 2. Create `llm_router.py`

Location: `src/myragdb/llm/llm_router.py`

```python
class LLMRouter:
    PORTS = {
        "code": 8085,      # qwen-coder-7b
        "reasoning": 8092, # deepseek-r1-qwen-32b
        "summary": 8081,   # phi3
        "fallback": 8087   # llama-3.1-8b
    }

    async def route_query(self, query, context, task_type="reasoning"):
        port = self.PORTS.get(task_type, 8087)

        # Health check
        if not await self.check_port(port):
            port = self.PORTS["fallback"]

        # Send to llama.cpp
        response = await self.call_llm(port, query, context)
        return response

    async def check_port(self, port):
        """Verify llama.cpp model is loaded"""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"http://localhost:{port}/health")
                return r.status_code == 200
        except:
            return False
```

### 3. Update `vector_indexer.py`

**Change:** Use `generate_document_id()` instead of ChromaDB auto-IDs

```python
from myragdb.utils.id_generator import generate_document_id

def index_chunk(self, file_path, chunk_text):
    doc_id = generate_document_id(file_path)  # Same as Meilisearch
    self.collection.add(
        ids=[doc_id],
        documents=[chunk_text],
        metadatas=[{...}]
    )
```

### 4. Update `server.py`

**Replace:**
```python
from myragdb.indexers.bm25_indexer import MeilisearchIndexer
keyword_indexer = MeilisearchIndexer()
```

**With:**
```python
from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
from myragdb.search.hybrid_search import HybridSearchEngine

meili_indexer = MeilisearchIndexer(
    host=settings.meilisearch_host,
    api_key=settings.meilisearch_api_key
)

hybrid_engine = HybridSearchEngine(
    meilisearch_indexer=meili_indexer,
    vector_indexer=vector_indexer
)
```

**Update endpoints:**
```python
@app.post("/search")
async def search(request: SearchRequest):
    if request.search_type == SearchType.HYBRID:
        results = await hybrid_engine.hybrid_search(
            request.query,
            limit=request.limit,
            folder_filter=request.folder_filter
        )
    elif request.search_type == SearchType.KEYWORD:
        results = meili_indexer.search(request.query, limit=request.limit)
    # ...
```

### 5. Create Start Script

**File:** `scripts/start_meilisearch.sh`

```bash
#!/bin/bash
# Start Meilisearch with 32GB memory for 2M+ files

DATA_DIR="/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/data/meilisearch"
MASTER_KEY="YOUR_MASTER_KEY_HERE"
MAX_MEMORY=34359738368  # 32 GiB in bytes

mkdir -p "$DATA_DIR"

meilisearch \
  --db-path "$DATA_DIR" \
  --master-key "$MASTER_KEY" \
  --max-indexing-memory "$MAX_MEMORY" \
  --http-addr 127.0.0.1:7700 \
  --log-level info
```

---

## Testing Migration

### 1. Start Meilisearch

```bash
chmod +x scripts/start_meilisearch.sh
./scripts/start_meilisearch.sh
```

### 2. Test Indexing

```python
from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
from myragdb.indexers.file_scanner import FileScanner
from myragdb.config import RepositoryConfig

indexer = MeilisearchIndexer(
    host="http://localhost:7700",
    api_key="YOUR_KEY"
)

# Scan files
config = RepositoryConfig(...)
scanner = FileScanner(config)
files = list(scanner.scan())

# Index in batches
count = indexer.index_files_batch(files, batch_size=50000)
print(f"Indexed {count} files")

# Wait for completion
indexer.wait_for_pending_tasks()

# Test search
results = indexer.search("authentication", limit=10)
for r in results:
    print(f"{r.score:.2f} - {r.file_path}")
```

### 3. Test Hybrid Search

```python
from myragdb.search.hybrid_search import HybridSearchEngine

engine = HybridSearchEngine(
    meilisearch_indexer=meili_indexer,
    vector_indexer=vector_indexer
)

results = await engine.hybrid_search(
    "JWT authentication flow",
    limit=10,
    keyword_weight=0.5
)

for r in results:
    print(f"Rank {r.rank}: RRF={r.rrf_score:.3f} (kw={r.keyword_score}, sem={r.semantic_score})")
    print(f"  {r.file_path}")
```

---

## Performance Expectations (2M Files)

### Indexing
- **Initial crawl:** ~2-3 hours (50k batches, os.scandir)
- **Incremental updates:** ~5-10 minutes (only changed files)
- **Memory usage:** ~10-15GB (Meilisearch memory-mapped)

### Search
- **Keyword search:** <50ms (even with 2M files)
- **Semantic search:** ~100-200ms (ChromaDB)
- **Hybrid search (RRF):** ~150-250ms (parallel execution)
- **With folder filter:** <10ms (scoped search)

### llama.cpp RAG
- **phi3/smollm3 (8B):** ~1-2s for summaries
- **qwen-coder-7b:** ~1-3s for code questions
- **deepseek-r1-qwen-32b:** ~5-10s for complex reasoning
- **Context window:** 32,768 tokens (enough for top 5-10 files)

---

## Troubleshooting

### Meilisearch Won't Start
```bash
# Check port
lsof -i:7700

# Check logs
tail -f /path/to/meilisearch/logs

# Reset index
curl -X DELETE 'http://localhost:7700/indexes/files' \
  -H 'Authorization: Bearer YOUR_KEY'
```

### Slow Indexing
```bash
# Increase batch size (more RAM usage)
count = indexer.index_files_batch(files, batch_size=100000)

# Check SSD vs HDD (MUST use SSD for 2M files)
df -h

# Monitor memory
top -pid $(pgrep meilisearch)
```

### Out of Memory
```bash
# Reduce max indexing memory
--max-indexing-memory 17179869184  # 16 GiB

# Or close other apps
# 128GB should handle 32GB for Meilisearch + models easily
```

---

## Next Steps

1. ✅ Meilisearch installed and running
2. ✅ Python SDK installed
3. ✅ Indexer created with Base64 IDs
4. ⏳ Complete hybrid_search.py
5. ⏳ Create llm_router.py
6. ⏳ Update vector_indexer.py (use Base64 IDs)
7. ⏳ Update server.py (replace Whoosh)
8. ⏳ Test with 100k files
9. ⏳ Full re-index of 2M files
10. ⏳ Benchmark search performance
11. ⏳ Integrate llama.cpp RAG
12. ⏳ Git commit migration

---

## Files Modified/Created

```
✅ requirements.txt                          (Whoosh → Meilisearch)
✅ src/myragdb/utils/id_generator.py        (NEW: Base64 hash IDs)
✅ src/myragdb/indexers/meilisearch_indexer.py  (NEW: Full indexer)
⏳ src/myragdb/search/hybrid_search.py      (NEW: RRF merge)
⏳ src/myragdb/llm/llm_router.py            (NEW: llama.cpp router)
⏳ src/myragdb/indexers/vector_indexer.py   (UPDATE: Base64 IDs)
⏳ src/myragdb/api/server.py                (UPDATE: Use Meilisearch)
⏳ src/myragdb/api/models.py                (UPDATE: Hybrid result models)
⏳ scripts/start_meilisearch.sh             (NEW: Service script)
```

---

## References

- [Meilisearch Docs](https://www.meilisearch.com/docs)
- [Python SDK](https://github.com/meilisearch/meilisearch-python)
- [Indexing Best Practices](https://www.meilisearch.com/docs/learn/indexing/indexing_best_practices)
- [Reciprocal Rank Fusion Paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
