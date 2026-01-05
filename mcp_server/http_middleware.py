# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/http_middleware.py
# Description: HTTP middleware to expose MCP server functionality via REST API
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

"""
HTTP Middleware for MyRAGDB MCP Server.

Business Purpose: Allows any local LLM (Ollama, LM Studio, etc.) to access
MyRAGDB search capabilities through a simple REST API, without requiring
MCP protocol support.

Example Usage:
    # Start the middleware
    python -m mcp_server.http_middleware

    # Use from any LLM or client
    curl http://localhost:8080/search -d '{"query": "authentication"}'
"""

import asyncio
import httpx
from typing import Any, Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# MyRAGDB API configuration
MYRAGDB_URL = "http://localhost:3003"
TIMEOUT = 30.0

# Initialize FastAPI app
app = FastAPI(
    title="MyRAGDB MCP Middleware",
    description="HTTP API wrapper for MyRAGDB MCP server",
    version="1.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query text")
    search_type: str = Field(default="hybrid", description="Search type: hybrid, semantic, or keyword")
    repositories: Optional[List[str]] = Field(default=None, description="Filter by repository names")
    file_types: Optional[List[str]] = Field(default=None, description="Filter by file extensions")
    folder_filter: Optional[str] = Field(default=None, description="Filter by folder path")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score")


class SearchResult(BaseModel):
    """Search result model."""
    file_path: str
    repository: str
    relative_path: str
    score: float
    snippet: str
    file_type: str
    keyword_score: Optional[float] = None
    vector_score: Optional[float] = None


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    search_type: str
    total_results: int
    search_time_ms: float
    results: List[SearchResult]


class RepositoryInfo(BaseModel):
    """Repository information model."""
    name: str
    path: str
    enabled: bool
    priority: Optional[str] = None


class DiscoverRequest(BaseModel):
    """Repository discovery request."""
    root_path: str = Field(..., description="Base directory to scan")
    max_depth: int = Field(default=3, ge=1, le=10, description="Maximum scan depth")


class ReindexRequest(BaseModel):
    """Reindex request model."""
    repositories: List[str] = Field(default_factory=list, description="Repositories to reindex (empty = all)")
    full_reindex: bool = Field(default=False, description="Full reindex vs incremental")


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "MyRAGDB MCP HTTP Middleware",
        "version": "1.0.0",
        "description": "HTTP wrapper for MyRAGDB search functionality",
        "endpoints": {
            "search": "/search - Search codebases",
            "repositories": "/repositories - List repositories",
            "stats": "/stats - Get index statistics",
            "discover": "/discover - Discover new repositories",
            "reindex": "/reindex - Trigger reindexing"
        },
        "myragdb_api": MYRAGDB_URL,
        "docs": "/docs - Interactive API documentation"
    }


@app.get("/health")
async def health_check():
    """Check if middleware and MyRAGDB API are healthy."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MYRAGDB_URL}/health")
            api_health = response.json()

            return {
                "status": "healthy",
                "middleware": "ok",
                "myragdb_api": api_health.get("status", "unknown"),
                "myragdb_url": MYRAGDB_URL
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MyRAGDB API unavailable: {str(e)}")


# ============================================================================
# Search Endpoints
# ============================================================================

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search across indexed codebases.

    Supports hybrid (keyword + semantic), semantic-only, and keyword-only search.

    Example:
        POST /search
        {
            "query": "authentication flow",
            "search_type": "hybrid",
            "limit": 10
        }
    """
    try:
        # Determine endpoint based on search type
        endpoint_map = {
            "hybrid": "/search/hybrid",
            "semantic": "/search/semantic",
            "keyword": "/search/keyword"
        }

        endpoint = endpoint_map.get(request.search_type, "/search/hybrid")

        # Build request payload
        payload = {
            "query": request.query,
            "limit": request.limit,
            "min_score": request.min_score
        }

        # Add optional filters
        if request.repositories:
            payload["repositories"] = request.repositories
        if request.file_types:
            payload["file_types"] = request.file_types
        if request.folder_filter:
            payload["folder_filter"] = request.folder_filter

        # Call MyRAGDB API
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{MYRAGDB_URL}{endpoint}", json=payload)
            response.raise_for_status()
            data = response.json()

            # Return formatted response
            return SearchResponse(
                query=data["query"],
                search_type=request.search_type,
                total_results=data["total_results"],
                search_time_ms=data["search_time_ms"],
                results=[SearchResult(**r) for r in data["results"]]
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ============================================================================
# Repository Management Endpoints
# ============================================================================

@app.get("/repositories")
async def list_repositories():
    """
    List all indexed repositories.

    Returns information about all repositories including their status.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{MYRAGDB_URL}/repositories")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list repositories: {str(e)}")


@app.post("/discover")
async def discover_repositories(request: DiscoverRequest):
    """
    Discover new Git repositories in a directory tree.

    Example:
        POST /discover
        {
            "root_path": "/Users/username/projects",
            "max_depth": 2
        }
    """
    try:
        payload = {
            "root_path": request.root_path,
            "max_depth": request.max_depth
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{MYRAGDB_URL}/repositories/discover", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@app.post("/repositories/add")
async def add_repositories(repository_paths: List[str]):
    """
    Add new repositories to the search index.

    Example:
        POST /repositories/add
        ["/path/to/repo1", "/path/to/repo2"]
    """
    try:
        payload = {"repository_paths": repository_paths}

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{MYRAGDB_URL}/repositories/add-batch", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add repositories: {str(e)}")


# ============================================================================
# Indexing Endpoints
# ============================================================================

@app.post("/reindex")
async def trigger_reindex(request: ReindexRequest):
    """
    Trigger re-indexing of repositories.

    Example:
        POST /reindex
        {
            "repositories": [],
            "full_reindex": false
        }
    """
    try:
        payload = {
            "repositories": request.repositories,
            "full_reindex": request.full_reindex
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{MYRAGDB_URL}/reindex", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            raise HTTPException(status_code=409, detail="Indexing already in progress")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """
    Get indexing statistics.

    Returns counts of indexed files, repositories, and other metrics.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{MYRAGDB_URL}/stats")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# ============================================================================
# Server Startup
# ============================================================================

def start_server(host: str = "0.0.0.0", port: int = 8080):
    """
    Start the HTTP middleware server.

    Args:
        host: Host to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to listen on (default: 8080)
    """
    print("="*60)
    print("MyRAGDB MCP HTTP Middleware")
    print("="*60)
    print(f"\nStarting server on http://{host}:{port}")
    print(f"MyRAGDB API: {MYRAGDB_URL}")
    print("\nEndpoints:")
    print(f"  - Docs: http://localhost:{port}/docs")
    print(f"  - Health: http://localhost:{port}/health")
    print(f"  - Search: http://localhost:{port}/search")
    print(f"  - Repositories: http://localhost:{port}/repositories")
    print("\nUse Ctrl+C to stop\n")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
