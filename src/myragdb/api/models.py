# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/models.py
# Description: Pydantic models for API requests and responses
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class SearchType(str, Enum):
    """Type of search to perform."""
    HYBRID = "hybrid"
    BM25 = "bm25"
    SEMANTIC = "semantic"


class SearchRequest(BaseModel):
    """
    Request model for search endpoints.

    Business Purpose: Defines the structure of search requests,
    enabling type-safe API calls with validation.

    Example:
        request = SearchRequest(
            query="JWT authentication",
            search_type=SearchType.HYBRID,
            limit=10
        )
    """
    query: str = Field(..., min_length=1, description="Search query string")
    search_type: SearchType = Field(
        default=SearchType.HYBRID,
        description="Type of search: hybrid, bm25, or semantic"
    )
    repositories: Optional[List[str]] = Field(
        default=None,
        description="Filter by specific repositories (None = all)"
    )
    file_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by file types (e.g., ['.md', '.py'])"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum score threshold"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "how to implement authentication",
                "search_type": "hybrid",
                "repositories": ["xLLMArionComply"],
                "file_types": [".md", ".py"],
                "limit": 10,
                "min_score": 0.0
            }
        }


class SearchResultItem(BaseModel):
    """
    Individual search result.

    Business Purpose: Represents a single search result with all
    information needed for display.

    Example:
        result = SearchResultItem(
            file_path="/path/to/file.py",
            repository="MyProject",
            score=0.89,
            snippet="def authenticate...",
            file_type=".py"
        )
    """
    file_path: str = Field(..., description="Absolute path to file")
    repository: str = Field(..., description="Repository name")
    relative_path: str = Field(..., description="Path relative to repository")
    score: float = Field(..., description="Relevance score (0-1)")
    bm25_score: Optional[float] = Field(None, description="BM25 component score")
    vector_score: Optional[float] = Field(None, description="Vector component score")
    snippet: str = Field(..., description="Content preview/snippet")
    file_type: str = Field(..., description="File extension")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/Users/user/project/auth.py",
                "repository": "MyProject",
                "relative_path": "src/auth.py",
                "score": 0.89,
                "bm25_score": 0.85,
                "vector_score": 0.92,
                "snippet": "def authenticate_user(token: str)...",
                "file_type": ".py"
            }
        }


class SearchResponse(BaseModel):
    """
    Response model for search endpoints.

    Business Purpose: Standardizes search response format with
    results and metadata.

    Example:
        response = SearchResponse(
            query="authentication",
            total_results=7,
            search_time_ms=234.5,
            results=[...]
        )
    """
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Number of results returned")
    search_time_ms: float = Field(..., description="Search duration in milliseconds")
    results: List[SearchResultItem] = Field(..., description="Search results")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "authentication flow",
                "total_results": 7,
                "search_time_ms": 234.5,
                "results": []
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response.

    Business Purpose: Confirms service is running and responsive.
    """
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Health check message")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "MyRAGDB service is running"
            }
        }


class StatsResponse(BaseModel):
    """
    Statistics response.

    Business Purpose: Provides visibility into index size and health.
    """
    bm25_documents: int = Field(..., description="Number of documents in BM25 index")
    vector_chunks: int = Field(..., description="Number of chunks in vector index")

    class Config:
        json_schema_extra = {
            "example": {
                "bm25_documents": 4521,
                "vector_chunks": 8932
            }
        }
