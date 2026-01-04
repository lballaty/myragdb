# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/server.py
# Description: FastAPI server for MyRAGDB hybrid search service
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import time
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from myragdb.api.models import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchType,
    HealthResponse,
    StatsResponse
)
from myragdb.search.hybrid_search import HybridSearchEngine, HybridSearchResult
from myragdb.indexers.bm25_indexer import BM25Indexer
from myragdb.indexers.vector_indexer import VectorIndexer
from myragdb.config import settings


# Initialize search engines (singleton pattern)
bm25_indexer = None
vector_indexer = None
hybrid_engine = None


def get_search_engines():
    """
    Get or initialize search engines.

    Business Purpose: Lazy initialization of search engines to avoid
    loading models at import time. Engines are created on first use.

    Returns:
        Tuple of (bm25_indexer, vector_indexer, hybrid_engine)
    """
    global bm25_indexer, vector_indexer, hybrid_engine

    if bm25_indexer is None:
        print("Initializing BM25 indexer...")
        bm25_indexer = BM25Indexer()

    if vector_indexer is None:
        print("Initializing vector indexer...")
        vector_indexer = VectorIndexer()

    if hybrid_engine is None:
        print("Initializing hybrid search engine...")
        hybrid_engine = HybridSearchEngine(
            bm25_indexer=bm25_indexer,
            vector_indexer=vector_indexer
        )

    return bm25_indexer, vector_indexer, hybrid_engine


# Create FastAPI app
app = FastAPI(
    title="MyRAGDB",
    description="Hybrid search service combining BM25 and vector embeddings",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
web_ui_path = Path(__file__).parent.parent.parent.parent / "web-ui"
if web_ui_path.exists():
    app.mount("/static", StaticFiles(directory=str(web_ui_path / "static")), name="static")


@app.get("/")
async def root():
    """
    Serve the web UI.

    Business Purpose: Provides web interface for searching and monitoring.
    """
    index_path = web_ui_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HealthResponse(
        status="healthy",
        message="MyRAGDB service is running (Web UI not found)"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Business Purpose: Allows monitoring systems to verify service health.
    """
    return HealthResponse(
        status="healthy",
        message="MyRAGDB service is healthy"
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get index statistics.

    Business Purpose: Provides visibility into index size and contents
    for monitoring and debugging.
    """
    try:
        _, _, engine = get_search_engines()
        stats = engine.get_stats()

        return StatsResponse(
            bm25_documents=stats["bm25_documents"],
            vector_chunks=stats["vector_chunks"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.post("/search/hybrid", response_model=SearchResponse)
async def search_hybrid(request: SearchRequest):
    """
    Hybrid search combining BM25 and vector search.

    Business Purpose: Primary search endpoint providing best-of-both-worlds
    search using keyword matching and semantic understanding.

    Args:
        request: Search request parameters

    Returns:
        SearchResponse with results and metadata

    Example:
        POST /search/hybrid
        {
            "query": "JWT authentication",
            "limit": 10
        }
    """
    start_time = time.time()

    try:
        _, _, engine = get_search_engines()

        # Execute search
        # Note: Repository filter will be handled in Phase 2
        results = engine.search(
            query=request.query,
            limit=request.limit,
            repository=request.repositories[0] if request.repositories else None,
            min_score=request.min_score
        )

        # Convert to API response format
        result_items = [
            SearchResultItem(
                file_path=r.file_path,
                repository=r.repository,
                relative_path=r.relative_path,
                score=r.combined_score,
                bm25_score=r.bm25_score,
                vector_score=r.vector_score,
                snippet=r.snippet,
                file_type=r.file_type
            )
            for r in results
        ]

        search_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            total_results=len(result_items),
            search_time_ms=search_time_ms,
            results=result_items
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.post("/search/bm25", response_model=SearchResponse)
async def search_bm25(request: SearchRequest):
    """
    BM25 keyword-only search.

    Business Purpose: Provides fast keyword matching for queries where
    exact term matching is preferred.

    Args:
        request: Search request parameters

    Returns:
        SearchResponse with BM25 results
    """
    start_time = time.time()

    try:
        bm25, _, _ = get_search_engines()

        # Execute BM25 search
        results = bm25.search(
            query=request.query,
            limit=request.limit,
            repository=request.repositories[0] if request.repositories else None
        )

        # Convert to API response format
        result_items = [
            SearchResultItem(
                file_path=r.file_path,
                repository=r.repository,
                relative_path=r.relative_path,
                score=r.score,
                bm25_score=r.score,
                vector_score=None,
                snippet=r.snippet,
                file_type=r.file_type
            )
            for r in results
        ]

        search_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            total_results=len(result_items),
            search_time_ms=search_time_ms,
            results=result_items
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BM25 search error: {str(e)}")


@app.post("/search/semantic", response_model=SearchResponse)
async def search_semantic(request: SearchRequest):
    """
    Vector semantic-only search.

    Business Purpose: Provides semantic search for queries where understanding
    meaning and context is more important than exact keywords.

    Args:
        request: Search request parameters

    Returns:
        SearchResponse with vector search results
    """
    start_time = time.time()

    try:
        _, vector, _ = get_search_engines()

        # Execute vector search
        results = vector.search(
            query=request.query,
            limit=request.limit,
            repository=request.repositories[0] if request.repositories else None
        )

        # Convert to API response format
        result_items = [
            SearchResultItem(
                file_path=r.file_path,
                repository=r.repository,
                relative_path=r.relative_path,
                score=r.score,
                bm25_score=None,
                vector_score=r.score,
                snippet=r.snippet,
                file_type=r.file_type
            )
            for r in results
        ]

        search_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            total_results=len(result_items),
            search_time_ms=search_time_ms,
            results=result_items
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")


def main():
    """
    Run the FastAPI server.

    Business Purpose: Entry point for starting the service.

    Example:
        python -m myragdb.api.server
    """
    print(f"Starting MyRAGDB server on {settings.host}:{settings.port}")
    uvicorn.run(
        "myragdb.api.server:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # Set to True for development
        log_level="info"
    )


if __name__ == "__main__":
    main()
