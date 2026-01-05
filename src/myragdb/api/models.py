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
    KEYWORD = "keyword"
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
        description="Type of search: hybrid, keyword, or semantic"
    )
    repositories: Optional[List[str]] = Field(
        default=None,
        description="Filter by specific repositories (None = all)"
    )
    repository_filter: Optional[str] = Field(
        default=None,
        description="Filter by single repository name"
    )
    folder_filter: Optional[str] = Field(
        default=None,
        description="Filter by folder path (e.g., 'src/components')"
    )
    extension_filter: Optional[str] = Field(
        default=None,
        description="Filter by file extension (e.g., '.py', '.ts')"
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
    keyword_score: Optional[float] = Field(None, description="Keyword component score")
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
                "keyword_score": 0.85,
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
    keyword_documents: int = Field(..., description="Number of documents in keyword index")
    vector_chunks: int = Field(..., description="Number of chunks in vector index")
    is_indexing: bool = Field(default=False, description="Whether indexing is currently in progress")
    last_index_time: Optional[str] = Field(None, description="ISO timestamp of last index completion")
    current_repository: Optional[str] = Field(None, description="Repository currently being indexed")
    repositories_total: int = Field(default=0, description="Total number of repositories to index")
    repositories_completed: int = Field(default=0, description="Number of repositories completed")
    index_types: List[str] = Field(default_factory=list, description="Index types being processed (Keyword, Vector)")
    current_phase: Optional[str] = Field(None, description="Current indexing phase (Keyword or Vector)")
    files_processed: int = Field(default=0, description="Number of files processed so far")
    files_total: int = Field(default=0, description="Total number of files to process")
    mode: Optional[str] = Field(None, description="Indexing mode (incremental or full_rebuild)")

    class Config:
        json_schema_extra = {
            "example": {
                "keyword_documents": 4521,
                "vector_chunks": 8932,
                "is_indexing": True,
                "last_index_time": "2026-01-04T19:00:00Z",
                "current_repository": "xLLMArionComply",
                "repositories_total": 1,
                "repositories_completed": 0,
                "index_types": ["Keyword", "Vector"],
                "current_phase": "Vector",
                "files_processed": 150,
                "files_total": 500,
                "mode": "incremental"
            }
        }


class RepositoryInfo(BaseModel):
    """
    Repository information.

    Business Purpose: Provides details about configured repositories.
    """
    name: str = Field(..., description="Repository name")
    path: str = Field(..., description="Repository path")
    enabled: bool = Field(..., description="Whether repository is enabled")
    priority: str = Field(..., description="Repository priority (high, medium, low)")
    excluded: bool = Field(False, description="Whether repository is excluded from indexing (locked)")
    file_count: Optional[int] = Field(None, description="Number of files that would be indexed (None if not yet scanned)")
    total_size_bytes: Optional[int] = Field(None, description="Total size of all files to be indexed in bytes (None if not yet scanned)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "xLLMArionComply",
                "path": "/Users/user/projects/xLLMArionComply",
                "enabled": True,
                "priority": "high"
            }
        }


class ReindexRequest(BaseModel):
    """
    Re-indexing request.

    Business Purpose: Allows selective re-indexing of specific repositories
    with control over which indexes to rebuild and how.
    """
    repositories: Optional[List[str]] = Field(
        default=None,
        description="List of repository names to re-index (None = all enabled)"
    )
    index_keyword: bool = Field(
        default=True,
        description="Whether to re-index keyword index"
    )
    index_vector: bool = Field(
        default=True,
        description="Whether to re-index Vector (semantic) index"
    )
    full_rebuild: bool = Field(
        default=False,
        description="If True, clears and rebuilds indexes from scratch. If False, incrementally updates existing indexes."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "repositories": ["xLLMArionComply"],
                "index_keyword": True,
                "index_vector": True,
                "full_rebuild": False
            }
        }


class ReindexResponse(BaseModel):
    """
    Re-indexing response.

    Business Purpose: Confirms re-indexing operation was triggered.
    """
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    started_at: str = Field(..., description="ISO timestamp when indexing started")
    repositories: List[str] = Field(..., description="List of repositories being indexed")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "started",
                "message": "Re-indexing started in background",
                "started_at": "2026-01-04T19:30:00Z",
                "repositories": ["xLLMArionComply"]
            }
        }


class StopIndexingRequest(BaseModel):
    """
    Stop indexing request.

    Business Purpose: Allows graceful stopping of running indexing operations
    to free up resources or make corrections.
    """
    stop_keyword: bool = Field(
        default=True,
        description="Whether to stop keyword indexing if running"
    )
    stop_vector: bool = Field(
        default=True,
        description="Whether to stop Vector indexing if running"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stop_keyword": True,
                "stop_vector": True
            }
        }


class StopIndexingResponse(BaseModel):
    """
    Stop indexing response.

    Business Purpose: Confirms stop request was registered and indicates
    which indexing operations were requested to stop.
    """
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    stopped: List[str] = Field(..., description="List of index types that were requested to stop")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "stopping",
                "message": "Stop request registered, indexing will halt at next safe checkpoint",
                "stopped": ["Keyword", "Vector"]
            }
        }


class DiscoverRequest(BaseModel):
    """
    Repository discovery request.

    Business Purpose: Allows scanning directories for git repositories
    that can be added to the indexing configuration.
    """
    root_path: str = Field(..., description="Root directory to scan for repositories")
    max_depth: int = Field(default=3, ge=1, le=10, description="Maximum directory depth to scan")

    class Config:
        json_schema_extra = {
            "example": {
                "root_path": "/Users/user/projects",
                "max_depth": 2
            }
        }


class DiscoveredRepositoryItem(BaseModel):
    """
    Individual discovered repository.

    Business Purpose: Represents a git repository found during directory scanning.
    Includes clone detection to identify multiple copies of the same repository.
    """
    name: str = Field(..., description="Repository name (directory name)")
    path: str = Field(..., description="Absolute path to repository")
    is_already_indexed: bool = Field(..., description="Whether repository is already in configuration")
    created_date: Optional[str] = Field(None, description="ISO timestamp when repository was created")
    modified_date: Optional[str] = Field(None, description="ISO timestamp when repository was last modified")
    git_remote_url: Optional[str] = Field(None, description="Git remote origin URL")
    clone_group: Optional[str] = Field(None, description="Normalized clone identifier (e.g., 'github.com/user/repo')")
    excluded: bool = Field(False, description="Whether repository is excluded from indexing (locked)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "MyProject",
                "path": "/Users/user/projects/MyProject",
                "is_already_indexed": False,
                "created_date": "2024-01-15T10:30:00",
                "modified_date": "2026-01-05T12:00:00"
            }
        }


class DiscoverResponse(BaseModel):
    """
    Repository discovery response.

    Business Purpose: Returns list of discovered repositories with status information.
    """
    total_found: int = Field(..., description="Total number of repositories found")
    new_repositories: int = Field(..., description="Number of repositories not yet indexed")
    already_indexed: int = Field(..., description="Number of repositories already in configuration")
    repositories: List[DiscoveredRepositoryItem] = Field(..., description="List of discovered repositories")

    class Config:
        json_schema_extra = {
            "example": {
                "total_found": 15,
                "new_repositories": 10,
                "already_indexed": 5,
                "repositories": []
            }
        }


class AddRepositoriesRequest(BaseModel):
    """
    Request to add multiple repositories to configuration.

    Business Purpose: Allows bulk addition of discovered repositories
    to the indexing configuration.
    """
    repositories: List[str] = Field(..., description="List of repository paths to add")
    priority: str = Field(default="medium", description="Priority for added repositories (high, medium, low)")
    enabled: bool = Field(default=True, description="Whether to enable repositories immediately")

    class Config:
        json_schema_extra = {
            "example": {
                "repositories": [
                    "/Users/user/projects/Project1",
                    "/Users/user/projects/Project2"
                ],
                "priority": "high",
                "enabled": True
            }
        }


class AddRepositoriesResponse(BaseModel):
    """
    Response for adding repositories.

    Business Purpose: Confirms how many repositories were added to configuration.
    """
    status: str = Field(..., description="Operation status")
    added_count: int = Field(..., description="Number of repositories added")
    skipped_count: int = Field(..., description="Number of repositories skipped (already exist)")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "added_count": 8,
                "skipped_count": 2,
                "message": "Added 8 repositories to configuration"
            }
        }
