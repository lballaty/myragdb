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
    directories: Optional[List[int]] = Field(
        default=None,
        description="Filter by specific directory IDs (None = all)"
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
                "directories": [1, 2],
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


class DirectorySummary(BaseModel):
    """
    Summary of a directory containing search results.

    Business Purpose: Helps LLMs understand which directories contain
    relevant files without parsing file paths.
    """
    directory_path: str = Field(..., description="Full directory path")
    relative_directory: str = Field(..., description="Relative directory path from repository root")
    repository: str = Field(..., description="Repository name")
    file_count: int = Field(..., description="Number of files in this directory matching the search")


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
            results=[...],
            directories=[...],
            repositories_searched=["xLLMArionComply", "RepoDot"]
        )
    """
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Number of results returned")
    search_time_ms: float = Field(..., description="Search duration in milliseconds")
    results: List[SearchResultItem] = Field(..., description="Search results")
    directories: Optional[List[DirectorySummary]] = Field(None, description="Summary of directories containing results (if applicable)")
    repositories_searched: Optional[List[str]] = Field(None, description="List of repository names that were searched")

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


class RepositoryIndexingStats(BaseModel):
    """
    Indexing performance statistics for a repository.

    Business Purpose: Tracks how long indexing takes for correlation
    with file count and size, enabling future time estimates.
    """
    index_type: str = Field(..., description="Index type: 'keyword' or 'vector'")
    initial_index_time_seconds: Optional[float] = Field(None, description="Time taken for initial full index (seconds)")
    initial_index_timestamp: Optional[int] = Field(None, description="Unix timestamp when initial index completed")
    last_reindex_time_seconds: Optional[float] = Field(None, description="Time taken for most recent reindex (seconds)")
    last_reindex_timestamp: Optional[int] = Field(None, description="Unix timestamp when last reindex completed")
    total_files_indexed: Optional[int] = Field(None, description="Number of files indexed")
    total_size_bytes: Optional[int] = Field(None, description="Total size of indexed files (bytes)")

    class Config:
        json_schema_extra = {
            "example": {
                "index_type": "keyword",
                "initial_index_time_seconds": 45.2,
                "initial_index_timestamp": 1735948800,
                "last_reindex_time_seconds": 12.3,
                "last_reindex_timestamp": 1736035200,
                "total_files_indexed": 1234,
                "total_size_bytes": 5242880
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
    indexing_stats: Optional[List[RepositoryIndexingStats]] = Field(None, description="Indexing performance statistics (keyword and vector)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "xLLMArionComply",
                "path": "/Users/user/projects/xLLMArionComply",
                "enabled": True,
                "priority": "high",
                "file_count": 1234,
                "total_size_bytes": 5242880,
                "indexing_stats": [
                    {
                        "index_type": "keyword",
                        "initial_index_time_seconds": 45.2,
                        "last_reindex_time_seconds": 12.3,
                        "total_files_indexed": 1234,
                        "total_size_bytes": 5242880
                    }
                ]
            }
        }


class DirectoryStatsInfo(BaseModel):
    """
    Indexing statistics for a directory.

    Business Purpose: Tracks performance metrics for directory indexing
    operations, enabling time estimates and health monitoring.

    Example:
        stats = DirectoryStatsInfo(
            total_files_indexed=245,
            total_size_bytes=2048576,
            index_type="keyword",
            initial_index_time_seconds=12.5,
            last_reindex_time_seconds=3.2,
            last_reindex_timestamp=1735948800
        )
    """
    index_type: str = Field(..., description="Index type: 'keyword' or 'vector'")
    total_files_indexed: int = Field(..., description="Total number of files indexed in this directory")
    total_size_bytes: int = Field(..., description="Total size of all indexed files (bytes)")
    initial_index_time_seconds: Optional[float] = Field(None, description="Time taken for initial full index (seconds)")
    initial_index_timestamp: Optional[int] = Field(None, description="Unix timestamp when initial index completed")
    last_reindex_time_seconds: Optional[float] = Field(None, description="Time taken for most recent reindex (seconds)")
    last_reindex_timestamp: Optional[int] = Field(None, description="Unix timestamp when last reindex completed")

    class Config:
        json_schema_extra = {
            "example": {
                "index_type": "keyword",
                "total_files_indexed": 245,
                "total_size_bytes": 2048576,
                "initial_index_time_seconds": 12.5,
                "initial_index_timestamp": 1735948800,
                "last_reindex_time_seconds": 3.2,
                "last_reindex_timestamp": 1735962400
            }
        }


class DirectoryInfo(BaseModel):
    """
    Directory information and metadata.

    Business Purpose: Provides complete details about a managed directory
    including status, configuration, and indexing statistics for UI display
    and API consumers.

    Example:
        directory = DirectoryInfo(
            id=1,
            path="/Users/user/documents/research",
            name="Research Papers",
            enabled=True,
            priority=1,
            created_at=1735948800,
            updated_at=1735948800,
            last_indexed=1735949000,
            notes="PDF research papers for analysis",
            stats=[...]
        )
    """
    id: int = Field(..., description="Directory ID (unique)")
    path: str = Field(..., description="Absolute directory path")
    name: str = Field(..., description="User-friendly name for the directory")
    enabled: bool = Field(..., description="Whether directory is included in search")
    priority: int = Field(..., description="Sort priority in UI (higher = appears first)")
    created_at: int = Field(..., description="Unix timestamp when directory was added")
    updated_at: int = Field(..., description="Unix timestamp when record was last updated")
    last_indexed: Optional[int] = Field(None, description="Unix timestamp of last indexing (None = never indexed)")
    notes: Optional[str] = Field(None, description="Optional user notes about this directory")
    stats: Optional[List[DirectoryStatsInfo]] = Field(None, description="Indexing statistics for keyword and vector indexes")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "path": "/Users/user/documents/research",
                "name": "Research Papers",
                "enabled": True,
                "priority": 1,
                "created_at": 1735948800,
                "updated_at": 1735948800,
                "last_indexed": 1735949000,
                "notes": "PDF research papers for analysis",
                "stats": [
                    {
                        "index_type": "keyword",
                        "total_files_indexed": 245,
                        "total_size_bytes": 2048576,
                        "initial_index_time_seconds": 12.5,
                        "last_reindex_time_seconds": 3.2
                    }
                ]
            }
        }


class DirectoryRequest(BaseModel):
    """
    Request to add or update a directory.

    Business Purpose: Defines input validation for directory creation
    and modification operations via API.

    Example:
        request = DirectoryRequest(
            path="/Users/user/documents",
            name="Documents",
            enabled=True,
            notes="Project documentation"
        )
    """
    path: str = Field(..., min_length=1, description="Absolute directory path")
    name: str = Field(..., min_length=1, description="User-friendly name for the directory")
    enabled: bool = Field(default=True, description="Whether to include directory in search")
    priority: int = Field(default=0, description="Sort priority (higher = appears first)")
    notes: Optional[str] = Field(None, description="Optional user notes about this directory")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "/Users/user/documents/research",
                "name": "Research Papers",
                "enabled": True,
                "priority": 1,
                "notes": "PDF research papers for analysis"
            }
        }


class DirectoryDiscoveryInfo(BaseModel):
    """
    Directory discovery information for tree picker UI.

    Business Purpose: Represents a directory in a hierarchical tree structure
    for UI components allowing users to browse and select directories.

    Example:
        item = DirectoryDiscoveryInfo(
            path="/Users/user/documents",
            name="documents",
            is_directory=True,
            children=[...]
        )
    """
    path: str = Field(..., description="Absolute directory path")
    name: str = Field(..., description="Directory name (basename)")
    is_directory: bool = Field(..., description="Whether this is a directory (True) or file (False)")
    children: Optional[List["DirectoryDiscoveryInfo"]] = Field(None, description="Child directories/files in tree structure")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "/Users/user",
                "name": "user",
                "is_directory": True,
                "children": [
                    {
                        "path": "/Users/user/documents",
                        "name": "documents",
                        "is_directory": True,
                        "children": [
                            {
                                "path": "/Users/user/documents/research",
                                "name": "research",
                                "is_directory": True,
                                "children": None
                            }
                        ]
                    }
                ]
            }
        }


# Enable forward references for DirectoryDiscoveryInfo
DirectoryDiscoveryInfo.update_forward_refs()


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


class LLMInfo(BaseModel):
    """
    LLM model information.

    Business Purpose: Provides details about available local LLMs.
    """
    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Display name")
    port: int = Field(..., description="Port number")
    status: str = Field(..., description="Status: running or stopped")
    category: str = Field(..., description="Category: best or limited")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "qwen-coder-7b",
                "name": "Qwen Coder 7B",
                "port": 8085,
                "status": "running",
                "category": "best"
            }
        }


class StartLLMRequest(BaseModel):
    """
    Request to start an LLM.

    Business Purpose: Starts a local LLM with specified mode.
    """
    model_id: str = Field(..., description="Model ID to start")
    mode: str = Field(..., description="Mode: basic, tools, performance, extended")

    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "qwen-coder-7b",
                "mode": "tools"
            }
        }


class StartLLMResponse(BaseModel):
    """
    Response from starting an LLM.

    Business Purpose: Confirms LLM start status.
    """
    status: str = Field(..., description="Status: success or error")
    message: str = Field(..., description="Status message")
    model_id: str = Field(..., description="Model ID that was started")
    pid: Optional[int] = Field(None, description="Process ID if started successfully")
    log_file: Optional[str] = Field(None, description="Path to log file")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Qwen Coder 7B started successfully in tools mode",
                "model_id": "qwen-coder-7b",
                "pid": 12345,
                "log_file": "/Users/liborballaty/llms/logs/qwen-coder-7b-tools.log"
            }
        }


class StopLLMRequest(BaseModel):
    """
    Request to stop an LLM.

    Business Purpose: Stops a running local LLM gracefully.
    """
    model_id: str = Field(..., description="Model ID to stop")

    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "qwen-coder-7b"
            }
        }


class StopLLMResponse(BaseModel):
    """
    Response from stopping an LLM.

    Business Purpose: Confirms LLM stop status.
    """
    status: str = Field(..., description="Status: success or error")
    message: str = Field(..., description="Status message")
    model_id: str = Field(..., description="Model ID that was stopped")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Qwen Coder 7B stopped successfully",
                "model_id": "qwen-coder-7b"
            }
        }


# ====================
# Observability Models
# ====================

class ObservabilityMetricsRequest(BaseModel):
    """
    Request model for retrieving observability metrics.

    Business Purpose: Allows filtering metrics by time range and type
    for dashboard visualizations and analysis.

    Example:
        request = ObservabilityMetricsRequest(
            start_time=1704067200,
            end_time=1704153600,
            metric_type="search"
        )
    """
    start_time: Optional[int] = Field(
        default=None,
        description="Unix timestamp for start of time range"
    )
    end_time: Optional[int] = Field(
        default=None,
        description="Unix timestamp for end of time range"
    )
    metric_type: Optional[str] = Field(
        default=None,
        description="Type of metrics: 'search', 'error', 'system', 'indexing'"
    )
    limit: int = Field(
        default=1000,
        description="Maximum number of records to return"
    )


class SearchMetricItem(BaseModel):
    """Individual search metric record."""
    id: int
    timestamp: int
    query: str
    search_type: str
    response_time_ms: float
    result_count: int
    repository: Optional[str] = None
    source: str


class ErrorLogItem(BaseModel):
    """Individual error log record."""
    id: int
    timestamp: int
    error_type: str
    message: str
    severity: str
    component: str
    stack_trace: Optional[str] = None
    context: Optional[dict] = None
    resolved: bool


class SystemMetricItem(BaseModel):
    """Individual system metric record."""
    id: int
    timestamp: int
    metric_name: str
    metric_value: float
    unit: str
    category: str


class IndexingEventItem(BaseModel):
    """Individual indexing event record."""
    id: int
    timestamp: int
    repository: str
    event_type: str
    status: str
    files_processed: int
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None


class ObservabilityMetricsResponse(BaseModel):
    """
    Response model for observability metrics.

    Business Purpose: Returns metrics data for visualization and analysis.
    """
    metric_type: str
    total_count: int
    time_range_start: Optional[int] = None
    time_range_end: Optional[int] = None
    search_metrics: Optional[List[SearchMetricItem]] = None
    error_logs: Optional[List[ErrorLogItem]] = None
    system_metrics: Optional[List[SystemMetricItem]] = None
    indexing_events: Optional[List[IndexingEventItem]] = None


class ObservabilityStatsResponse(BaseModel):
    """
    Response model for aggregated observability statistics.

    Business Purpose: Provides high-level summary metrics for dashboards.
    """
    search_stats: dict = Field(description="Aggregated search statistics")
    error_stats: dict = Field(description="Aggregated error statistics")
    database_info: dict = Field(description="Database size and row counts")


class ObservabilityCleanupRequest(BaseModel):
    """Request model for data cleanup operations."""
    retention_days: int = Field(
        default=30,
        description="Number of days to retain data"
    )


class ObservabilityCleanupResponse(BaseModel):
    """Response model for cleanup operations."""
    status: str
    records_deleted: dict
    message: str


# Auto-reindexing / File Watching Models

class WatcherStatusItem(BaseModel):
    """
    Status information for a single repository watcher.

    Business Purpose: Provides visibility into which repositories are
    being monitored for automatic reindexing.

    Example:
        {
            "repository": "myragdb",
            "status": "active",
            "pending_changes": 0,
            "path": "/path/to/myragdb",
            "debounce_seconds": 5
        }
    """
    repository: str
    status: str  # "active" or "stopped"
    pending_changes: int
    path: str
    debounce_seconds: int


class WatcherStatusResponse(BaseModel):
    """
    Response model for watcher status endpoint.

    Business Purpose: Shows all active file system watchers and their state.

    Example:
        response = WatcherStatusResponse(
            watchers=[...],
            total_watchers=3,
            total_pending_changes=0
        )
    """
    watchers: List[WatcherStatusItem]
    total_watchers: int
    total_pending_changes: int


class ToggleAutoReindexRequest(BaseModel):
    """
    Request model for enabling/disabling auto-reindex for a repository.

    Business Purpose: Allows users to control whether a repository
    should automatically reindex when files change.

    Example:
        request = ToggleAutoReindexRequest(enabled=True)
    """
    enabled: bool = Field(..., description="True to enable auto-reindex, False to disable")


class ToggleAutoReindexResponse(BaseModel):
    """
    Response model for auto-reindex toggle.

    Business Purpose: Confirms the auto-reindex setting was updated
    and returns the new watcher status.

    Example:
        {
            "status": "success",
            "repository": "myragdb",
            "auto_reindex_enabled": true,
            "watcher_status": "active",
            "message": "Auto-reindex enabled for repository myragdb"
        }
    """
    status: str
    repository: str
    auto_reindex_enabled: bool
    watcher_status: str  # "active", "stopped", or "not_found"
    message: str


# README Viewer Models

class ReadmeRequest(BaseModel):
    """
    Request model for fetching repository README.

    Business Purpose: Allows UI to fetch and display README content
    for repositories to help users understand what each repository contains.

    Example:
        request = ReadmeRequest(repository="myragdb")
    """
    repository: str = Field(..., description="Repository name")


class ReadmeResponse(BaseModel):
    """
    Response model for README content.

    Business Purpose: Returns README file content with metadata for
    display in modal viewer.

    Example:
        {
            "repository": "myragdb",
            "readme_found": true,
            "readme_path": "/path/to/myragdb/README.md",
            "content": "# MyRAGDB\\n\\nHybrid search system...",
            "file_name": "README.md"
        }
    """
    repository: str
    readme_found: bool
    readme_path: Optional[str] = None
    content: Optional[str] = None
    file_name: Optional[str] = None
    error: Optional[str] = None
