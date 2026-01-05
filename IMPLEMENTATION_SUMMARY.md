# Whoosh → Meilisearch Migration: Implementation Summary

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/IMPLEMENTATION_SUMMARY.md
**Description:** Complete implementation guide with code snippets for remaining tasks
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04

---

## ✅ COMPLETED COMPONENTS

### 1. Base64 Document ID Generator
**Location:** `src/myragdb/utils/id_generator.py`

```python
from myragdb.utils.id_generator import generate_document_id

# Same file → same ID in both Meilisearch and ChromaDB
doc_id = generate_document_id("/path/to/file.py")
# Returns: "xK7JmH9vQpL2..." (deterministic, URL-safe Base64 SHA256)
```

### 2. Keyword Indexer (Meilisearch)
**Location:** `src/myragdb/indexers/meilisearch_indexer.py`

**Features:**
- ✅ Searchable attributes: `file_name`, `folder_name`, `content` (ranked priority)
- ✅ Filterable attributes: `file_path`, `extension`, `last_modified`, `size`, `repository`
- ✅ 50k batch indexing for 2M+ files
- ✅ Incremental indexing (mtime-based)
- ✅ Base64 hash primary keys
- ✅ Scoped searches (folder/extension filtering)

**Usage:**
```python
from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer

indexer = MeilisearchIndexer(
    host="http://localhost:7700",
    api_key="YOUR_KEY"
)

# Batch indexing (50k batches)
count = indexer.index_files_batch(files, batch_size=50000, incremental=True)

# Search with filters
results = indexer.search(
    "authentication",
    folder_filter="src/auth",
    extension_filter=".py",
    limit=10
)
```

### 3. Query Rewriter
**Location:** `src/myragdb/llm/query_rewriter.py`

**Features:**
- ✅ Uses phi3 on port 8081
- ✅ Transforms messy queries into keyword + semantic versions
- ✅ Removes noise words
- ✅ Fallback to original query if LLM unavailable
- ✅ ~1-2s response time

**Usage:**
```python
from myragdb.llm.query_rewriter import QueryRewriter

rewriter = QueryRewriter(port=8081)

# Transform messy query
original = "can you please find me the JWT authentication implementation?"
rewritten = await rewriter.rewrite(original)

# Clean versions
print(rewritten.keyword)   # "JWT authentication implementation"
print(rewritten.semantic)  # "code or documentation about JWT authentication logic"
```

---

## 📋 REMAINING IMPLEMENTATION

### 4. LLM Router (llama.cpp Multi-Port Suite)
**Location:** `src/myragdb/llm/llm_router.py` *(create this file)*

```python
# File: src/myragdb/llm/llm_router.py
# Description: LLM router with health checks and intelligent fallback
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import httpx
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskType(str, Enum):
    """LLM task types for routing."""
    QUERY_REWRITE = "query_rewrite"  # Port 8081: phi3
    CODE = "code"                     # Port 8085: qwen-coder-7b
    SUMMARY = "summary"               # Port 8081: phi3
    REASONING = "reasoning"           # Port 8092: deepseek-r1-qwen-32b (or 8089: mistral-small-24b)
    FALLBACK = "fallback"             # Port 8087: llama-3.1-8b


class LLMRouter:
    """
    Routes LLM requests to appropriate llama.cpp ports with health checks.

    Business Purpose: Intelligently routes requests to the best available model
    based on task type, with health checking to avoid cold starts and automatic
    fallback to lighter models if heavy models unavailable.

    Port Mapping:
    - 8081: phi3 (query rewriting, summaries)
    - 8082: smollm3 (fast tasks)
    - 8085: qwen-coder-7b (code questions)
    - 8087: llama-3.1-8b (fallback)
    - 8089: mistral-small-24b (heavy reasoning)
    - 8092: deepseek-r1-qwen-32b (complex RAG, 32B model)

    Configuration: All models use n_ctx=32768, use_mmap=True, Metal acceleration
    """

    PORT_MAP = {
        TaskType.QUERY_REWRITE: [8081],  # phi3
        TaskType.CODE: [8085, 8087],     # qwen-coder-7b → fallback
        TaskType.SUMMARY: [8081, 8087],  # phi3 → fallback
        TaskType.REASONING: [8092, 8089, 8087],  # deepseek → mistral → fallback
        TaskType.FALLBACK: [8087]        # llama-3.1-8b
    }

    def __init__(self, host: str = "http://localhost"):
        self.host = host
        self._health_cache: Dict[int, bool] = {}  # Cache health status

    async def check_port_health(self, port: int, use_cache: bool = True) -> bool:
        """
        Check if model is loaded and responsive on port.

        Args:
            port: llama.cpp server port
            use_cache: Use cached health status (faster, may be stale)

        Returns:
            True if healthy, False otherwise
        """
        if use_cache and port in self._health_cache:
            return self._health_cache[port]

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                # Try simple completion to verify model loaded
                response = await client.post(
                    f"{self.host}:{port}/v1/completions",
                    json={"prompt": "test", "max_tokens": 1}
                )
                is_healthy = response.status_code == 200
                self._health_cache[port] = is_healthy
                return is_healthy
        except:
            self._health_cache[port] = False
            return False

    async def get_healthy_port(self, task_type: TaskType) -> int:
        """
        Get first healthy port for task type with fallback logic.

        Business Purpose: Finds the best available model for the task, with
        automatic fallback to lighter models if heavy models unavailable.
        Prevents cold start delays by checking health first.

        Args:
            task_type: Type of task to route

        Returns:
            Port number of healthy model
        """
        candidate_ports = self.PORT_MAP.get(task_type, [8087])

        for port in candidate_ports:
            if await self.check_port_health(port):
                print(f"[LLMRouter] Routing {task_type} to port {port}")
                return port

        # Ultimate fallback
        print(f"[LLMRouter] WARNING: All ports for {task_type} unhealthy, using fallback 8087")
        return 8087

    async def generate(
        self,
        prompt: str,
        task_type: TaskType = TaskType.FALLBACK,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using appropriate LLM model.

        Args:
            prompt: User prompt
            task_type: Task type for routing
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        port = await self.get_healthy_port(task_type)

        # Build prompt with system message if provided
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        payload = {
            "prompt": full_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": ["\n\n", "User:", "Assistant:"],
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.host}:{port}/v1/completions",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data.get("choices", [{}])[0].get("text", "")

        except Exception as e:
            print(f"[LLMRouter] Error generating from port {port}: {e}")
            return ""

    async def generate_rag_response(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        task_type: TaskType = TaskType.REASONING
    ) -> str:
        """
        Generate RAG response using top-ranked documents.

        Business Purpose: Passes top 5-10 RRF-ranked results into LLM with
        context-grounded system prompt for accurate, citation-backed answers.

        Args:
            query: User question
            context_docs: Top search results (limit to 5-10 for 32k context)
            task_type: REASONING for deep analysis, CODE for code questions

        Returns:
            LLM-generated answer grounded in provided context
        """
        # Build context from top documents
        context = "\n\n---\n\n".join([
            f"FILE: {doc['file_path']}\nCONTENT:\n{doc['content'][:2000]}"
            for doc in context_docs[:5]  # Top 5 documents
        ])

        system_prompt = """You are a helpful code assistant with access to a codebase.

Answer the user's question based ONLY on the provided context files.
If the answer is not in the context, say "I don't have enough information."
Always cite which files you're referencing in your answer.

Context:
{context}
"""

        full_prompt = f"{system_prompt.format(context=context)}\n\nUser Question: {query}\n\nAnswer:"

        return await self.generate(
            full_prompt,
            task_type=task_type,
            max_tokens=2048,
            temperature=0.3
        )
```

---

### 5. Complete Hybrid Search with RRF
**Location:** `src/myragdb/search/hybrid_search.py` *(create this file)*

```python
# File: src/myragdb/search/hybrid_search.py
# Description: Hybrid search with Reciprocal Rank Fusion using keyword + vector search
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer, MeilisearchResult
from myragdb.indexers.vector_indexer import VectorIndexer
from myragdb.llm.query_rewriter import QueryRewriter


@dataclass
class HybridSearchResult:
    """Unified result from hybrid search (Meilisearch + ChromaDB)."""
    id: str
    file_path: str
    repository: str
    rrf_score: float
    keyword_score: Optional[float]
    semantic_score: Optional[float]
    snippet: str
    file_type: str
    relative_path: str
    rank: int


def reciprocal_rank_fusion(
    keyword_results: List[MeilisearchResult],
    vector_results: List[Dict[str, Any]],
    k: int = 60
) -> List[Tuple[str, float]]:
    """
    Merge keyword (Meilisearch) and vector (ChromaDB) results using RRF.

    Formula: Score(d) = Σ(r ∈ {Keyword, Vector}) 1 / (k + rank_r(d))
    """
    scores: Dict[str, float] = {}

    # Keyword search ranks
    for rank, hit in enumerate(keyword_results, start=1):
        scores[hit.id] = scores.get(hit.id, 0.0) + 1.0 / (k + rank)

    # Vector search ranks
    for rank, hit in enumerate(vector_results, start=1):
        doc_id = hit.get('id', '')
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class HybridSearchEngine:
    """
    Hybrid search with query rewriting + RRF fusion.

    Architecture:
    1. Query Rewriter (phi3) → keyword + semantic queries
    2. Parallel execution: Keyword search (Meilisearch) + Vector search (ChromaDB)
    3. RRF fusion → unified ranked results
    """

    def __init__(
        self,
        keyword_indexer: MeilisearchIndexer,
        vector_indexer: VectorIndexer,
        query_rewriter: Optional[QueryRewriter] = None
    ):
        self.keyword = keyword_indexer
        self.vector = vector_indexer
        self.rewriter = query_rewriter or QueryRewriter(port=8081)

    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        use_rewriter: bool = True,
        folder_filter: Optional[str] = None,
        extension_filter: Optional[str] = None,
        repository_filter: Optional[str] = None,
        rrf_k: int = 60
    ) -> List[HybridSearchResult]:
        """
        Execute hybrid search with query rewriting and RRF fusion.

        Args:
            query: User query
            limit: Max results
            use_rewriter: Use phi3 to rewrite query (default: True)
            folder_filter: Filter to folder (Meilisearch only)
            extension_filter: Filter by extension (Meilisearch only)
            repository_filter: Filter by repository (both)
            rrf_k: RRF smoothing constant (default: 60)

        Returns:
            Hybrid search results sorted by RRF score
        """
        # Step 1: Rewrite query (optional but recommended)
        if use_rewriter:
            rewritten = await self.rewriter.rewrite(query)
            keyword_query = rewritten.keyword
            semantic_query = rewritten.semantic
            print(f"[Hybrid] Rewritten - Keyword: '{keyword_query}', Semantic: '{semantic_query}'")
        else:
            keyword_query = semantic_query = query

        # Step 2: Parallel search execution
        fetch_limit = limit * 3  # Fetch more for RRF

        keyword_task = asyncio.to_thread(
            self.keyword.search,
            keyword_query,
            limit=fetch_limit,
            folder_filter=folder_filter,
            extension_filter=extension_filter,
            repository_filter=repository_filter
        )

        vector_task = asyncio.to_thread(
            self.vector.search_similar,
            semantic_query,
            k=fetch_limit,
            repository_filter=repository_filter
        )

        keyword_results, vector_results = await asyncio.gather(keyword_task, vector_task)

        # Step 3: RRF fusion
        merged_scores = reciprocal_rank_fusion(keyword_results, vector_results, k=rrf_k)

        # Step 4: Build final results
        keyword_map = {r.id: r for r in keyword_results}
        vector_map = {r.get('id', ''): r for r in vector_results}

        final_results: List[HybridSearchResult] = []

        for rank, (doc_id, rrf_score) in enumerate(merged_scores[:limit], start=1):
            keyword_hit = keyword_map.get(doc_id)
            vector_hit = vector_map.get(doc_id)

            if not keyword_hit and not vector_hit:
                continue

            # Prefer Meilisearch metadata (more complete)
            if keyword_hit:
                result = HybridSearchResult(
                    id=doc_id,
                    file_path=keyword_hit.file_path,
                    repository=keyword_hit.repository,
                    rrf_score=rrf_score,
                    keyword_score=keyword_hit.score if keyword_hit else None,
                    semantic_score=vector_hit.get('score') if vector_hit else None,
                    snippet=keyword_hit.snippet,
                    file_type=keyword_hit.file_type,
                    relative_path=keyword_hit.relative_path,
                    rank=rank
                )
            else:
                result = HybridSearchResult(
                    id=doc_id,
                    file_path=vector_hit.get('file_path', ''),
                    repository=vector_hit.get('repository', ''),
                    rrf_score=rrf_score,
                    keyword_score=None,
                    semantic_score=vector_hit.get('score'),
                    snippet=vector_hit.get('content', '')[:200],
                    file_type=vector_hit.get('file_type', ''),
                    relative_path=vector_hit.get('relative_path', ''),
                    rank=rank
                )

            final_results.append(result)

        return final_results
```

---

### 6. Update server.py

**Key Changes:**

1. **Replace BM25Indexer with MeilisearchIndexer (keyword search)**
2. **Add HybridSearchEngine**
3. **Add LLMRouter**
4. **Add RAG endpoint**

```python
# In server.py, replace imports:
from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
from myragdb.search.hybrid_search import HybridSearchEngine
from myragdb.llm.query_rewriter import QueryRewriter
from myragdb.llm.llm_router import LLMRouter, TaskType

# Initialize keyword search indexer:
keyword_indexer = MeilisearchIndexer(
    host=settings.meilisearch_host or "http://localhost:7700",
    api_key=settings.meilisearch_api_key
)

# Add hybrid search engine:
hybrid_engine = HybridSearchEngine(
    keyword_indexer=keyword_indexer,
    vector_indexer=vector_indexer,
    query_rewriter=QueryRewriter(port=8081)
)

# Add LLM router:
llm_router = LLMRouter()

# Update search endpoint:
@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    start_time = time.time()

    if request.search_type == SearchType.HYBRID:
        results = await hybrid_engine.hybrid_search(
            query=request.query,
            limit=request.limit,
            use_rewriter=True,
            folder_filter=request.folder_filter if hasattr(request, 'folder_filter') else None,
            repository_filter=request.repositories[0] if request.repositories else None
        )
        # Convert to SearchResponse format...
    # ... rest of implementation

# Add RAG endpoint:
@app.post("/rag", response_model=Dict[str, Any])
async def rag_query(request: Dict[str, Any]):
    """RAG endpoint with LLM generation."""
    query = request.get("query", "")
    task_type_str = request.get("task_type", "reasoning")
    limit = request.get("limit", 5)

    # Search for context
    results = await hybrid_engine.hybrid_search(query, limit=limit)

    # Prepare context docs
    context_docs = [
        {
            "file_path": r.file_path,
            "content": r.snippet,  # In production, read full file
            "score": r.rrf_score
        }
        for r in results
    ]

    # Generate RAG response
    task_type = TaskType.CODE if "code" in task_type_str else TaskType.REASONING
    answer = await llm_router.generate_rag_response(
        query, context_docs, task_type=task_type
    )

    return {
        "query": query,
        "answer": answer,
        "sources": [{"file": r.file_path, "score": r.rrf_score} for r in results]
    }
```

---

### 7. Update vector_indexer.py

**Add Base64 ID support:**

```python
from myragdb.utils.id_generator import generate_document_id

# In index_chunk method, replace auto-ID with Base64 hash:
def index_chunk(self, file_path: str, chunk_text: str, ...):
    doc_id = generate_document_id(file_path)  # Same as Meilisearch!

    self.collection.add(
        ids=[doc_id],
        documents=[chunk_text],
        metadatas=[{
            "file_path": file_path,
            "repository": repository,
            ...
        }]
    )
```

---

## 🚀 DEPLOYMENT CHECKLIST

1. ✅ Install Meilisearch
2. ✅ Install Meilisearch Python SDK
3. ✅ Start Meilisearch with 32GB memory
4. ⏳ Start llama.cpp models on ports 8081, 8085, 8087, 8089, 8092
5. ⏳ Create hybrid_search.py
6. ⏳ Create llm_router.py
7. ⏳ Update server.py
8. ⏳ Update vector_indexer.py
9. ⏳ Re-index all files (2M files, ~2-3 hours)
10. ⏳ Test hybrid search
11. ⏳ Test RAG endpoint
12. ⏳ Benchmark performance
13. ⏳ Git commit

---

## 📊 EXPECTED PERFORMANCE (2M Files, 128GB RAM, M4 Max)

| Operation | Time | Notes |
|-----------|------|-------|
| Initial indexing | 2-3 hours | 50k batches, os.scandir |
| Incremental update | 5-10 min | Only changed files |
| Keyword search (Meilisearch) | <50ms | Memory-mapped indexes |
| Vector search (ChromaDB) | ~150ms | Semantic similarity |
| Hybrid search (RRF) | ~200ms | Parallel execution |
| With folder filter | <10ms | Scoped search |
| Query rewrite (phi3) | ~1-2s | Port 8081 |
| RAG (code, 8085) | ~2-3s | qwen-coder-7b |
| RAG (reasoning, 8092) | ~5-10s | deepseek-r1-qwen-32b |

---

## ✅ COMPLETED FILES

1. ✅ `requirements.txt` - Meilisearch added, Whoosh removed
2. ✅ `src/myragdb/utils/id_generator.py` - Base64 hash IDs
3. ✅ `src/myragdb/indexers/meilisearch_indexer.py` - Full indexer
4. ✅ `src/myragdb/llm/query_rewriter.py` - Query rewriter
5. ✅ `MIGRATION_GUIDE.md` - Complete migration documentation
6. ✅ `IMPLEMENTATION_SUMMARY.md` - This file

## 📝 NEXT: Create Remaining Files

Use the code snippets above to create:
1. `src/myragdb/llm/llm_router.py`
2. `src/myragdb/search/hybrid_search.py`
3. `src/myragdb/search/__init__.py` (empty)
4. Update `src/myragdb/indexers/vector_indexer.py`
5. Update `src/myragdb/api/server.py`

Then test the complete system!
