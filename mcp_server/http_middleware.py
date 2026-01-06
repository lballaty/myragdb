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
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# MyRAGDB API configuration
MYRAGDB_URL = "http://localhost:3003"
TIMEOUT = 30.0

# LLM Port to Name mapping
LLM_PORT_MAP = {
    8081: "Phi-3",
    8082: "SmolLM3",
    8083: "Mistral 7B",
    8084: "Qwen 2.5 32B",
    8085: "Qwen Coder 7B",
    8086: "Hermes 3 Llama 8B",
    8087: "Llama 3.1 8B",
    8088: "Llama 4 Scout 17B",
    8089: "Mistral Small 24B",
    8092: "DeepSeek R1 Qwen 32B"
}


def detect_llm_source(request: Request) -> str:
    """
    Detect which LLM made the request based on headers and origin.

    Returns:
        LLM name or "Unknown LLM" if can't be determined
    """
    # Check Referer header (from browser UI)
    referer = request.headers.get("referer", "")

    # Check X-Request-Source custom header (if we add it to chat UI)
    source_header = request.headers.get("x-llm-source", "")
    if source_header:
        return source_header

    # Check User-Agent for clues
    user_agent = request.headers.get("user-agent", "")

    # Check client host/port (won't work for browser requests, but might for direct LLM calls)
    client_host = request.client.host if request.client else "unknown"

    # For now, return generic identifier with client info
    if referer:
        return f"Browser UI ({client_host})"
    elif "python" in user_agent.lower():
        return f"Python Client ({client_host})"
    else:
        return f"Unknown ({client_host})"

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


class DirectorySummary(BaseModel):
    """Directory summary model."""
    directory_path: str
    relative_directory: str
    repository: str
    file_count: int


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    search_type: str
    total_results: int
    search_time_ms: float
    results: List[SearchResult]
    directories: Optional[List[DirectorySummary]] = None


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
async def search(request_body: SearchRequest, request: Request):
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
    # Detect LLM source
    llm_source = detect_llm_source(request)

    # Log incoming search request
    print(f"\n{'='*60}")
    print(f"🔍 SEARCH REQUEST")
    print(f"{'='*60}")
    print(f"LLM Source: {llm_source}")
    print(f"Query: {request_body.query}")
    print(f"Type: {request_body.search_type}")
    print(f"Limit: {request_body.limit}")
    if request_body.repositories:
        print(f"Repositories: {', '.join(request_body.repositories)}")
    if request_body.file_types:
        print(f"File Types: {', '.join(request_body.file_types)}")
    print(f"{'='*60}\n")

    try:
        # Determine endpoint based on search type
        endpoint_map = {
            "hybrid": "/search/hybrid",
            "semantic": "/search/semantic",
            "keyword": "/search/keyword"
        }

        endpoint = endpoint_map.get(request_body.search_type, "/search/hybrid")

        # Build request payload
        payload = {
            "query": request_body.query,
            "limit": request_body.limit,
            "min_score": request_body.min_score
        }

        # Add optional filters
        if request_body.repositories:
            payload["repositories"] = request_body.repositories
        if request_body.file_types:
            payload["file_types"] = request_body.file_types
        if request_body.folder_filter:
            payload["folder_filter"] = request_body.folder_filter

        # Call MyRAGDB API
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{MYRAGDB_URL}{endpoint}", json=payload)
            response.raise_for_status()
            data = response.json()

            # Log results
            print(f"✅ SEARCH COMPLETE")
            print(f"Total Results: {data['total_results']}")
            print(f"Search Time: {data['search_time_ms']:.2f}ms")
            if data['results']:
                print(f"Top Result: {data['results'][0].get('file_path', 'N/A')}")
            print(f"{'='*60}\n")

            # Return formatted response
            return SearchResponse(
                query=data["query"],
                search_type=request_body.search_type,
                total_results=data["total_results"],
                search_time_ms=data["search_time_ms"],
                results=[SearchResult(**r) for r in data["results"]],
                directories=[DirectorySummary(**d) for d in data.get("directories", [])] if data.get("directories") else None
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

def start_server(host: str = "0.0.0.0", port: int = 8093):
    """
    Start the HTTP middleware server.

    Args:
        host: Host to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to listen on (default: 8093)
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
