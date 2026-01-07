# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/server.py
# Description: FastAPI server for MyRAGDB hybrid search service
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import os
import signal
import time
import asyncio
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from myragdb.api.models import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    DirectorySummary,
    SearchType,
    HealthResponse,
    StatsResponse,
    RepositoryInfo,
    RepositoryIndexingStats,
    ReindexRequest,
    ReindexResponse,
    StopIndexingRequest,
    StopIndexingResponse,
    DiscoverRequest,
    DiscoverResponse,
    DiscoveredRepositoryItem,
    AddRepositoriesRequest,
    AddRepositoriesResponse,
    LLMInfo,
    StartLLMRequest,
    StartLLMResponse,
    StopLLMRequest,
    StopLLMResponse,
    ObservabilityMetricsRequest,
    ObservabilityMetricsResponse,
    ObservabilityStatsResponse,
    ObservabilityCleanupRequest,
    ObservabilityCleanupResponse,
    SearchMetricItem,
    ErrorLogItem,
    SystemMetricItem,
    IndexingEventItem,
    WatcherStatusItem,
    WatcherStatusResponse,
    ToggleAutoReindexRequest,
    ToggleAutoReindexResponse,
    ReadmeRequest,
    ReadmeResponse
)
from myragdb.search.hybrid_search import HybridSearchEngine, HybridSearchResult
from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
from myragdb.indexers.vector_indexer import VectorIndexer
from myragdb.llm.query_rewriter import QueryRewriter
from myragdb.db.file_metadata import get_metadata_db
from myragdb.db.observability import ObservabilityDatabase
from myragdb.config import settings, load_repositories_config
from myragdb.utils.repo_discovery import RepositoryDiscovery, DiscoveredRepository
from myragdb.watcher.repository_watcher import RepositoryWatcherManager
from myragdb.api.routes.directories import router as directories_router
import structlog

# Configure structured logging
logger = structlog.get_logger()

# Initialize search engines and metadata store (singleton pattern)
meilisearch_indexer = None
vector_indexer = None
query_rewriter = None
hybrid_engine = None
metadata_store = None
observability_db = None
watcher_manager = None

# Indexing state - supports independent Keyword (Meilisearch) and Vector indexing
indexing_state = {
    "is_indexing": False,  # True if ANY indexing is happening
    "last_index_time": None,
    "stop_requested": False,  # Flag to request graceful stop
    "keyword": {
        "is_indexing": False,
        "stop_requested": False,
        "current_repository": None,
        "repositories_total": 0,
        "repositories_completed": 0,
        "files_processed": 0,
        "files_total": 0,
        "mode": None  # "incremental" or "full_rebuild"
    },
    "vector": {
        "is_indexing": False,
        "stop_requested": False,
        "current_repository": None,
        "repositories_total": 0,
        "repositories_completed": 0,
        "files_processed": 0,
        "files_total": 0,
        "mode": None  # "incremental" or "full_rebuild"
    },
    # Legacy fields for backward compatibility with UI
    "current_repository": None,
    "repositories_total": 0,
    "repositories_completed": 0,
    "index_types": [],
    "current_phase": None,  # "Keyword" or "Vector"
    "files_processed": 0,
    "files_total": 0,
    "mode": None
}


def get_search_engines():
    """
    Get or initialize search engines and metadata store.

    Business Purpose: Lazy initialization of search engines to avoid
    loading models at import time. Engines are created on first use.
    Also loads persistent metadata on first initialization.

    Returns:
        Tuple of (meilisearch_indexer, vector_indexer, hybrid_engine)
    """
    global meilisearch_indexer, vector_indexer, query_rewriter, hybrid_engine, metadata_store, observability_db

    if metadata_store is None:
        logger.info("Initializing metadata store")
        metadata_store = get_metadata_db()

        # Load last index time from persistent storage
        last_index_time = metadata_store.get_last_index_time()
        if last_index_time:
            indexing_state["last_index_time"] = last_index_time
            logger.info("Loaded last index time from metadata", last_index_time=last_index_time)

    if observability_db is None:
        logger.info("Initializing observability database")
        observability_db = ObservabilityDatabase()

    if meilisearch_indexer is None:
        logger.info("Initializing Meilisearch indexer", host=settings.meilisearch_host)
        meilisearch_indexer = MeilisearchIndexer(
            host=settings.meilisearch_host,
            api_key=settings.meilisearch_api_key
        )

    if vector_indexer is None:
        logger.info("Initializing ChromaDB vector indexer")
        vector_indexer = VectorIndexer()

    if query_rewriter is None:
        logger.info("Initializing query rewriter with phi3", port=8081)
        query_rewriter = QueryRewriter()

    if hybrid_engine is None:
        logger.info("Initializing hybrid search engine with RRF fusion")
        hybrid_engine = HybridSearchEngine(
            meilisearch_indexer=meilisearch_indexer,
            vector_indexer=vector_indexer,
            query_rewriter=query_rewriter
        )

    return meilisearch_indexer, vector_indexer, hybrid_engine


# Import version
from myragdb.version import __version__

# Create FastAPI app
app = FastAPI(
    title="MyRAGDB",
    description="Hybrid search service combining keyword (Meilisearch) and vector embeddings",
    version=__version__,
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

# Mount docs directory for user manual access
docs_path = Path(__file__).parent.parent.parent.parent / "docs"
if docs_path.exists():
    app.mount("/docs", StaticFiles(directory=str(docs_path)), name="docs")

# Register directory management routes
app.include_router(directories_router)


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """
    Initialize services on application startup.

    Business Purpose: Start file system watchers for automatic reindexing
    when files change in indexed repositories.
    """
    global watcher_manager

    # Create reindex callback function
    def trigger_auto_reindex(repository_name: str, changed_files: List[str]):
        """
        Callback for watcher to trigger incremental reindexing.

        Args:
            repository_name: Name of repository with changes
            changed_files: List of file paths that changed
        """
        logger.info(
            "Automatic reindex triggered by file changes",
            repository=repository_name,
            file_count=len(changed_files)
        )

        # Trigger incremental indexing (both keyword and vector)
        # Use threading to avoid blocking the watcher
        threading.Thread(
            target=run_keyword_index,
            args=([repository_name], False),  # incremental=True
            daemon=True,
            name=f"Auto-Reindex-Keyword-{repository_name}"
        ).start()

        threading.Thread(
            target=run_vector_index,
            args=([repository_name], False),  # incremental=True
            daemon=True,
            name=f"Auto-Reindex-Vector-{repository_name}"
        ).start()

    # Initialize watcher manager
    watcher_manager = RepositoryWatcherManager(reindex_callback=trigger_auto_reindex)

    # Start watching all enabled repositories with auto_reindex=True
    try:
        repo_config = load_repositories_config()
        for repo in repo_config.get_enabled_repositories():
            if repo.auto_reindex:
                # Extract file extensions from include patterns
                file_extensions = []
                for pattern in repo.file_patterns.include:
                    if pattern.startswith('**/') and pattern.count('.') == 1:
                        # Pattern like '**/*.py' -> extract '.py'
                        ext = pattern.split('.')[-1]
                        file_extensions.append(f'.{ext}')

                # Default extensions if none found
                if not file_extensions:
                    file_extensions = ['.py', '.md', '.ts', '.tsx', '.js', '.dart']

                watcher_manager.start_watching(
                    repository_name=repo.name,
                    repository_path=repo.path,
                    file_extensions=file_extensions,
                    debounce_seconds=5
                )

        logger.info("Repository watchers started successfully")
    except Exception as e:
        logger.error("Failed to start repository watchers", error=str(e), exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown.

    Business Purpose: Gracefully stop all file system watchers to
    avoid orphaned threads and ensure clean shutdown.
    """
    if watcher_manager:
        try:
            watcher_manager.stop_all()
            logger.info("Repository watchers stopped successfully")
        except Exception as e:
            logger.error("Error stopping repository watchers", error=str(e), exc_info=True)


@app.get("/")
async def root():
    """
    Serve the web UI.

    Business Purpose: Provides web interface for searching and monitoring.
    """
    index_path = web_ui_path / "index.html"
    if index_path.exists():
        # Add cache control headers to prevent browser caching of index.html
        # This ensures users always get the latest version with updated JS/CSS version strings
        return FileResponse(
            str(index_path),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return HealthResponse(
        status="healthy",
        message="MyRAGDB service is running (Web UI not found)"
    )


@app.get("/llm-chat-tester.html")
async def llm_chat_tester():
    """
    Serve the LLM chat tester UI.

    Business Purpose: Provides interface for testing local LLMs with function calling.
    """
    chat_tester_path = web_ui_path / "llm-chat-tester.html"
    if chat_tester_path.exists():
        return FileResponse(str(chat_tester_path))
    raise HTTPException(status_code=404, detail="LLM chat tester page not found")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint with dependency checks.

    Business Purpose: Allows monitoring systems to verify service health
    and detect if critical dependencies (Meilisearch, ChromaDB) are unavailable.
    """
    try:
        # Check if search engines can be initialized
        keyword_indexer, vector_indexer, hybrid_engine = get_search_engines()

        # Try to verify Meilisearch is responding
        try:
            keyword_indexer.get_document_count()
            meilisearch_ok = True
        except Exception:
            meilisearch_ok = False

        # Try to verify ChromaDB is responding
        try:
            vector_indexer.get_document_count()
            chromadb_ok = True
        except Exception:
            chromadb_ok = False

        # Determine overall health
        if meilisearch_ok and chromadb_ok:
            return HealthResponse(
                status="healthy",
                message="MyRAGDB service is healthy (Meilisearch + ChromaDB OK)"
            )
        elif meilisearch_ok or chromadb_ok:
            issues = []
            if not meilisearch_ok:
                issues.append("Meilisearch unavailable")
            if not chromadb_ok:
                issues.append("ChromaDB unavailable")
            return HealthResponse(
                status="degraded",
                message=f"MyRAGDB service degraded: {', '.join(issues)}"
            )
        else:
            return HealthResponse(
                status="unhealthy",
                message="MyRAGDB service unhealthy: Meilisearch and ChromaDB unavailable"
            )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            message=f"MyRAGDB service unhealthy: {str(e)}"
        )


@app.get("/version")
async def get_version():
    """
    Get application version information.

    Business Purpose: Provides version info for debugging and compatibility checking.

    Returns:
        Dictionary with version number and release notes

    Example:
        GET /version
        {"version": "0.1.0", "api_version": "v1"}
    """
    return {
        "version": __version__,
        "api_version": "v1"
    }


@app.post("/admin/restart")
async def restart_server(background_tasks: BackgroundTasks):
    """
    Restart the MyRAGDB server process.

    Business Purpose: Allows UI-triggered server restart for dependency issues
    (e.g., Meilisearch unavailable) without SSH access.

    NOTE: This triggers a graceful shutdown that requires start.sh or similar
    script to automatically restart the server.

    Returns:
        Confirmation message that restart is initiated

    Example:
        POST /admin/restart
        {"status": "restarting", "message": "Server restart initiated", "pid": 12345}
    """
    current_pid = os.getpid()
    logger.info(f"Server restart requested via API (PID: {current_pid})")

    def trigger_restart():
        """Schedule server shutdown in 1 second to allow response to be sent."""
        time.sleep(1)
        logger.info("Sending SIGTERM to trigger restart...")
        os.kill(current_pid, signal.SIGTERM)

    # Schedule restart in background so we can return response first
    background_tasks.add_task(trigger_restart)

    return {
        "status": "restarting",
        "message": "Server restart initiated. Server will shutdown in 1 second.",
        "pid": current_pid
    }


@app.get("/logs")
async def get_logs(lines: int = 100, level: Optional[str] = None):
    """
    Get recent server logs from /tmp/myragdb_server.log.

    Business Purpose: Allows UI to display server logs for troubleshooting
    without SSH access. Includes startup logs, errors, and runtime events.

    Query Parameters:
        lines: Number of recent lines to return (default: 100, max: 1000)
        level: Filter by log level (e.g., "ERROR", "WARNING", "INFO")

    Returns:
        JSON with log lines array and metadata

    Example:
        GET /logs?lines=50&level=ERROR
        {"logs": ["2026-01-05 10:30:15 ERROR: Connection failed", ...], "total": 50}
    """
    log_file = "/tmp/myragdb_server.log"
    max_lines = min(lines, 1000)  # Cap at 1000 lines

    try:
        if not os.path.exists(log_file):
            return {
                "logs": [],
                "total": 0,
                "message": "Log file not found. Server may not have started yet."
            }

        # Read last N lines efficiently using tail-like approach
        with open(log_file, 'r') as f:
            # Get file size and seek to approximate position
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()

            # Estimate bytes per line (rough guess: 150 bytes/line)
            estimated_bytes = max_lines * 150
            start_pos = max(0, file_size - estimated_bytes)

            f.seek(start_pos)
            if start_pos > 0:
                f.readline()  # Skip partial line

            all_lines = f.readlines()

        # Get last N lines
        recent_lines = all_lines[-max_lines:] if len(all_lines) > max_lines else all_lines

        # Filter by level if specified
        if level:
            level_upper = level.upper()
            filtered_lines = [line for line in recent_lines if level_upper in line]
            return {
                "logs": [line.rstrip('\n') for line in filtered_lines],
                "total": len(filtered_lines),
                "filtered_by": level_upper
            }

        return {
            "logs": [line.rstrip('\n') for line in recent_lines],
            "total": len(recent_lines)
        }

    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
        return {
            "logs": [],
            "total": 0,
            "error": f"Error reading logs: {str(e)}"
        }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get index statistics and indexing progress.

    Business Purpose: Provides visibility into index size and contents
    for monitoring and debugging, plus real-time indexing progress.
    """
    try:
        _, _, engine = get_search_engines()
        stats = engine.get_stats()

        return StatsResponse(
            keyword_documents=stats["keyword_documents"],
            vector_chunks=stats["vector_chunks"],
            is_indexing=indexing_state["is_indexing"],
            last_index_time=indexing_state["last_index_time"],
            current_repository=indexing_state.get("current_repository"),
            repositories_total=indexing_state.get("repositories_total", 0),
            repositories_completed=indexing_state.get("repositories_completed", 0),
            index_types=indexing_state.get("index_types", []),
            current_phase=indexing_state.get("current_phase"),
            files_processed=indexing_state.get("files_processed", 0),
            files_total=indexing_state.get("files_total", 0),
            mode=indexing_state.get("mode")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.get("/repositories", response_model=List[RepositoryInfo])
async def get_repositories():
    """
    Get list of configured repositories with file counts and indexing stats.

    Business Purpose: Allows UI to display available repositories
    for selective re-indexing, showing file counts and historical
    indexing performance to help users estimate indexing time.

    Returns:
        List of RepositoryInfo with details, file counts, and indexing stats
    """
    try:
        from myragdb.indexers.file_scanner import FileScanner
        from myragdb.db.file_metadata import FileMetadataDatabase

        repo_config = load_repositories_config()
        file_db = FileMetadataDatabase()
        repositories = []

        for repo in repo_config.repositories:
            # Count files and calculate total size
            try:
                scanner = FileScanner(repo)
                file_count = 0
                total_size = 0

                for scanned_file in scanner.scan():
                    file_count += 1
                    total_size += scanned_file.size_bytes

            except Exception as e:
                print(f"Error counting files for {repo.name}: {e}")
                file_count = None
                total_size = None

            # Get indexing statistics from database
            indexing_stats = []
            try:
                stats_data = file_db.get_repository_stats(repo.name)
                for stat in stats_data:
                    indexing_stats.append(RepositoryIndexingStats(
                        index_type=stat['index_type'],
                        initial_index_time_seconds=stat['initial_index_time_seconds'],
                        initial_index_timestamp=stat['initial_index_timestamp'],
                        last_reindex_time_seconds=stat['last_reindex_time_seconds'],
                        last_reindex_timestamp=stat['last_reindex_timestamp'],
                        total_files_indexed=stat['total_files_indexed'],
                        total_size_bytes=stat['total_size_bytes']
                    ))
            except Exception as e:
                print(f"Error loading indexing stats for {repo.name}: {e}")

            repositories.append(RepositoryInfo(
                name=repo.name,
                path=repo.path,
                enabled=repo.enabled,
                priority=repo.priority,
                excluded=getattr(repo, 'excluded', False),
                file_count=file_count,
                total_size_bytes=total_size,
                indexing_stats=indexing_stats if indexing_stats else None
            ))

        return repositories

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading repositories: {str(e)}")


@app.post("/repositories/discover", response_model=DiscoverResponse)
async def discover_repositories(request: DiscoverRequest):
    """
    Discover git repositories in a directory tree.

    Business Purpose: Allows automatic discovery of repositories that can be
    added to the indexing configuration, avoiding manual YAML editing.

    Args:
        request: DiscoverRequest with root_path and max_depth

    Returns:
        DiscoverResponse with list of discovered repositories and status

    Example:
        POST /repositories/discover
        {
            "root_path": "/Users/user/projects",
            "max_depth": 2
        }
    """
    try:
        # Scan for repositories
        discovery = RepositoryDiscovery()
        discovered_repos = discovery.scan_directory(
            request.root_path,
            max_depth=request.max_depth
        )

        # Load existing configuration to check for duplicates and get excluded status
        try:
            existing_config = load_repositories_config()
            existing_paths = {repo.path for repo in existing_config.repositories}
            existing_repos_map = {repo.path: repo for repo in existing_config.repositories}
        except Exception:
            existing_paths = set()
            existing_repos_map = {}

        # Build response
        repository_items = []
        new_count = 0

        for repo in discovered_repos:
            is_already_indexed = repo.path in existing_paths
            if not is_already_indexed:
                new_count += 1

            # Get excluded status from existing config if repo is already indexed
            excluded = False
            if is_already_indexed and repo.path in existing_repos_map:
                excluded = getattr(existing_repos_map[repo.path], 'excluded', False)

            repository_items.append(DiscoveredRepositoryItem(
                name=repo.name,
                path=repo.path,
                is_already_indexed=is_already_indexed,
                created_date=repo.created_date,
                modified_date=repo.modified_date,
                git_remote_url=repo.git_remote_url,
                clone_group=repo.clone_group,
                excluded=excluded
            ))

        return DiscoverResponse(
            total_found=len(discovered_repos),
            new_repositories=new_count,
            already_indexed=len(discovered_repos) - new_count,
            repositories=repository_items
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering repositories: {str(e)}")


@app.post("/repositories/add-batch", response_model=AddRepositoriesResponse)
async def add_repositories_batch(request: AddRepositoriesRequest):
    """
    Add multiple repositories to configuration.

    Business Purpose: Enables bulk addition of discovered repositories to the
    indexing configuration, streamlining setup for large numbers of repos.

    Args:
        request: AddRepositoriesRequest with repository paths, priority, and enabled status

    Returns:
        AddRepositoriesResponse with count of added/skipped repositories

    Example:
        POST /repositories/add-batch
        {
            "repositories": ["/path/to/repo1", "/path/to/repo2"],
            "priority": "high",
            "enabled": true
        }
    """
    try:
        # Convert paths to DiscoveredRepository objects
        discovered_repos = [
            DiscoveredRepository(
                name=Path(path).name,
                path=path,
                git_dir=str(Path(path) / ".git"),
                is_git_repo=True
            )
            for path in request.repositories
        ]

        # Add to configuration
        discovery = RepositoryDiscovery()
        added_count = discovery.add_repositories_to_config(
            discovered_repos,
            config_path="config/repositories.yaml",
            enabled=request.enabled,
            priority=request.priority
        )

        skipped_count = len(request.repositories) - added_count

        return AddRepositoriesResponse(
            status="success",
            added_count=added_count,
            skipped_count=skipped_count,
            message=f"Added {added_count} repositories to configuration"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding repositories: {str(e)}")


@app.patch("/repositories/bulk-update")
async def bulk_update_repositories(
    action: str
):
    """
    Bulk update all repositories with a single action.

    Business Purpose: Allows quickly enabling/disabling or locking/unlocking all repositories
    at once instead of updating each repository individually.

    Args:
        action: Bulk action to perform
            - "enable_all": Set all repositories to enabled=true
            - "disable_all": Set all repositories to enabled=false
            - "unlock_all": Set all repositories to excluded=false
            - "lock_all": Set all repositories to excluded=true

    Returns:
        Count of updated repositories and success status

    Example:
        PATCH /repositories/bulk-update?action=enable_all
        PATCH /repositories/bulk-update?action=unlock_all
    """
    try:
        import yaml
        config_path = "config/repositories.yaml"

        # Validate action parameter
        valid_actions = ["enable_all", "disable_all", "unlock_all", "lock_all"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
            )

        # Load current configuration
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        repositories = config_data.get('repositories', [])
        if not repositories:
            raise HTTPException(status_code=404, detail="No repositories found in configuration")

        # Apply bulk action to all repositories
        updated_count = 0
        for repo in repositories:
            if action == "enable_all":
                repo['enabled'] = True
                updated_count += 1
            elif action == "disable_all":
                repo['enabled'] = False
                updated_count += 1
            elif action == "unlock_all":
                repo['excluded'] = False
                updated_count += 1
            elif action == "lock_all":
                repo['excluded'] = True
                updated_count += 1

        # Save updated configuration
        with open(config_path, 'w') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)

        # Reload configuration
        repos_config = load_repositories_config(config_path)

        # Return success with count
        action_descriptions = {
            "enable_all": "enabled",
            "disable_all": "disabled",
            "unlock_all": "unlocked",
            "lock_all": "locked"
        }

        return {
            "status": "success",
            "message": f"Successfully {action_descriptions[action]} {updated_count} repositories",
            "updated_count": updated_count,
            "action": action
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing bulk update: {str(e)}")


@app.patch("/repositories/{repo_name}")
async def update_repository_settings(
    repo_name: str,
    excluded: Optional[bool] = None,
    priority: Optional[str] = None,
    enabled: Optional[bool] = None,
    exclude_patterns: Optional[str] = None
):
    """
    Update repository settings (excluded status, priority, enabled, exclude patterns).

    Business Purpose: Allows locking/excluding repositories from indexing and updating
    other repository settings without removing them from configuration.

    Args:
        repo_name: Name of the repository to update
        excluded: Whether to exclude repository from indexing (lock)
        priority: Repository priority (high, medium, low)
        enabled: Whether repository is enabled
        exclude_patterns: Comma-separated list of file exclude patterns

    Returns:
        Updated repository information

    Example:
        PATCH /repositories/myragdb?excluded=true&priority=high
        PATCH /repositories/myragdb?exclude_patterns=**/*.log,**/temp/**
    """
    try:
        import yaml
        config_path = "config/repositories.yaml"

        # Load current configuration
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Find and update repository
        repo_found = False
        for repo in config_data.get('repositories', []):
            if repo['name'] == repo_name:
                repo_found = True
                if excluded is not None:
                    repo['excluded'] = excluded
                if priority is not None:
                    repo['priority'] = priority
                if enabled is not None:
                    repo['enabled'] = enabled
                if exclude_patterns is not None:
                    # Parse comma-separated patterns into list, filtering out empty strings
                    patterns_list = [p.strip() for p in exclude_patterns.split(',') if p.strip()]
                    # Initialize file_patterns if not exists
                    if 'file_patterns' not in repo:
                        repo['file_patterns'] = {}
                    repo['file_patterns']['exclude'] = patterns_list
                break

        if not repo_found:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found")

        # Save updated configuration
        with open(config_path, 'w') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)

        # Reload configuration
        repos_config = load_repositories_config(config_path)

        # Return updated repository info
        updated_repo = repos_config.get_repository_by_name(repo_name)
        if updated_repo:
            return {
                "status": "success",
                "message": f"Repository '{repo_name}' updated successfully",
                "repository": {
                    "name": updated_repo.name,
                    "path": updated_repo.path,
                    "enabled": updated_repo.enabled,
                    "priority": updated_repo.priority,
                    "excluded": getattr(updated_repo, 'excluded', False),
                    "file_patterns": {
                        "exclude": updated_repo.file_patterns.exclude if updated_repo.file_patterns else []
                    }
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload updated configuration")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating repository: {str(e)}")


@app.delete("/repositories/{repo_name}")
async def delete_repository(repo_name: str):
    """
    Remove repository from configuration.

    Business Purpose: Allows removing repositories from indexing configuration.
    Does not delete any files on disk, only removes from config/repositories.yaml.

    Args:
        repo_name: Name of the repository to remove

    Returns:
        Confirmation of removal

    Example:
        DELETE /repositories/myragdb
    """
    try:
        import yaml
        config_path = "config/repositories.yaml"

        # Load current configuration
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Find and remove repository
        repos = config_data.get('repositories', [])
        original_count = len(repos)
        repos = [repo for repo in repos if repo['name'] != repo_name]

        if len(repos) == original_count:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found")

        # Update configuration
        config_data['repositories'] = repos

        # Save updated configuration
        with open(config_path, 'w') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)

        return {
            "status": "success",
            "message": f"Repository '{repo_name}' removed from configuration",
            "repository_name": repo_name
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing repository: {str(e)}")


def _extract_directories(query: str, results: List[HybridSearchResult]) -> Optional[List[DirectorySummary]]:
    """
    Extract unique directories from search results if query asks for directories.

    Business Purpose: Helps LLMs (especially local models) understand which
    directories contain relevant files without having to parse file paths.

    Args:
        query: User search query
        results: List of search results

    Returns:
        List of DirectorySummary objects if query asks for directories, None otherwise
    """
    # Detect directory-related queries
    query_lower = query.lower()
    is_directory_query = any(keyword in query_lower for keyword in [
        'director', 'folder', 'path', 'locate all', 'find all', 'list all', 'where is', 'where are'
    ])

    if not is_directory_query:
        return None

    # Group files by directory
    directories = {}
    for result in results:
        file_path = Path(result.file_path)
        dir_path = str(file_path.parent)
        rel_dir = str(Path(result.relative_path).parent)

        if dir_path not in directories:
            directories[dir_path] = {
                'repository': result.repository,
                'relative_directory': rel_dir,
                'files': []
            }
        directories[dir_path]['files'].append(result)

    # Convert to DirectorySummary objects (limit to top 20 directories)
    directory_summaries = [
        DirectorySummary(
            directory_path=dir_path,
            relative_directory=info['relative_directory'],
            repository=info['repository'],
            file_count=len(info['files'])
        )
        for dir_path, info in sorted(directories.items(), key=lambda x: len(x[1]['files']), reverse=True)[:20]
    ]

    return directory_summaries if directory_summaries else None


@app.post("/search/hybrid", response_model=SearchResponse)
async def search_hybrid(request: SearchRequest):
    """
    Hybrid search combining Meilisearch keyword and vector search.

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

        # Determine repository filter: use repositories list if provided, otherwise single repository_filter
        repo_filter = request.repository_filter
        multi_repo_filter = request.repositories

        # Execute hybrid search with larger limit if filtering by multiple repos
        fetch_limit = request.limit * 3 if multi_repo_filter else request.limit

        results = await engine.hybrid_search(
            query=request.query,
            limit=fetch_limit,
            repository_filter=repo_filter,
            folder_filter=request.folder_filter,
            extension_filter=request.extension_filter
        )

        # Filter by multiple repositories if specified
        if multi_repo_filter:
            results = [r for r in results if r.repository in multi_repo_filter]
            results = results[:request.limit]  # Trim to requested limit

        # Convert to API response format
        result_items = [
            SearchResultItem(
                file_path=r.file_path,
                repository=r.repository,
                relative_path=r.relative_path,
                score=r.rrf_score,
                keyword_score=r.keyword_score,
                vector_score=1.0 / (1.0 + r.semantic_distance) if r.semantic_distance is not None else None,
                snippet=r.snippet,
                file_type=r.file_name.split('.')[-1] if '.' in r.file_name else ''
            )
            for r in results
        ]

        search_time_ms = (time.time() - start_time) * 1000

        # Record search metrics for observability
        try:
            observability_db.record_search_metric(
                query=request.query,
                search_type='hybrid',
                response_time_ms=search_time_ms,
                result_count=len(result_items),
                repository=repo_filter,
                source='web_ui'
            )
        except Exception as e:
            logger.warning("Failed to record search metric", error=str(e))

        # Extract unique directories if query seems to be asking for directories
        directories = _extract_directories(request.query, results) if results else None

        # Determine which repositories were actually searched
        if multi_repo_filter:
            # Specific repositories requested
            repositories_searched = multi_repo_filter
        elif repo_filter:
            # Single repository filter
            repositories_searched = [repo_filter]
        else:
            # All enabled repositories
            config_path = "config/repositories.yaml"
            repos_config = load_repositories_config(config_path)
            enabled_repos = repos_config.get_enabled_repositories()
            repositories_searched = [repo.name for repo in enabled_repos]

        return SearchResponse(
            query=request.query,
            total_results=len(result_items),
            search_time_ms=search_time_ms,
            results=result_items,
            directories=directories,
            repositories_searched=repositories_searched
        )

    except Exception as e:
        # Record error for observability
        try:
            observability_db.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity='ERROR',
                component='search_hybrid',
                context={'query': request.query, 'repository_filter': repo_filter}
            )
        except Exception as log_err:
            logger.warning("Failed to record error", error=str(log_err))

        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.post("/search/keyword", response_model=SearchResponse)
async def search_keyword(request: SearchRequest):
    """
    Meilisearch keyword-only search.

    Business Purpose: Provides fast keyword matching using Meilisearch for queries
    where exact term matching is preferred.

    Args:
        request: Search request parameters

    Returns:
        SearchResponse with keyword search results
    """
    start_time = time.time()

    try:
        meili, _, _ = get_search_engines()

        logger.info("Executing keyword search", query=request.query, limit=request.limit)

        # Execute Meilisearch keyword search
        results = meili.search(
            query=request.query,
            limit=request.limit,
            repository_filter=request.repository_filter,
            folder_filter=request.folder_filter,
            extension_filter=request.extension_filter
        )

        # Convert to API response format
        result_items = [
            SearchResultItem(
                file_path=r.file_path,
                repository=r.repository,
                relative_path=r.relative_path,
                score=r.score,
                keyword_score=r.score,
                vector_score=None,
                snippet=r.snippet,
                file_type=r.file_type
            )
            for r in results
        ]

        search_time_ms = (time.time() - start_time) * 1000

        # Record search metrics for observability
        try:
            observability_db.record_search_metric(
                query=request.query,
                search_type='keyword',
                response_time_ms=search_time_ms,
                result_count=len(result_items),
                repository=request.repository_filter,
                source='web_ui'
            )
        except Exception as e:
            logger.warning("Failed to record search metric", error=str(e))

        logger.info("Keyword search completed",
                   query=request.query,
                   results_count=len(result_items),
                   search_time_ms=search_time_ms)

        # Extract unique directories if query seems to be asking for directories
        directories = _extract_directories(request.query, results) if results else None

        # Determine which repositories were actually searched
        if request.repositories:
            repositories_searched = request.repositories
        elif request.repository_filter:
            repositories_searched = [request.repository_filter]
        else:
            # All enabled repositories
            config_path = "config/repositories.yaml"
            repos_config = load_repositories_config(config_path)
            enabled_repos = repos_config.get_enabled_repositories()
            repositories_searched = [repo.name for repo in enabled_repos]

        return SearchResponse(
            query=request.query,
            total_results=len(result_items),
            search_time_ms=search_time_ms,
            results=result_items,
            directories=directories,
            repositories_searched=repositories_searched
        )

    except Exception as e:
        # Record error for observability
        try:
            observability_db.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity='ERROR',
                component='search_keyword',
                context={'query': request.query, 'repository_filter': request.repository_filter}
            )
        except Exception as log_err:
            logger.warning("Failed to record error", error=str(log_err))

        logger.error("Keyword search failed", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Keyword search error: {str(e)}")


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
            repository=request.repository_filter or (request.repositories[0] if request.repositories else None)
        )

        # Convert to API response format
        result_items = [
            SearchResultItem(
                file_path=r.file_path,
                repository=r.repository,
                relative_path=r.relative_path,
                score=r.score,
                keyword_score=None,
                vector_score=r.score,
                snippet=r.snippet,
                file_type=r.file_type
            )
            for r in results
        ]

        search_time_ms = (time.time() - start_time) * 1000

        # Record search metrics for observability
        try:
            observability_db.record_search_metric(
                query=request.query,
                search_type='semantic',
                response_time_ms=search_time_ms,
                result_count=len(result_items),
                repository=request.repository_filter,
                source='web_ui'
            )
        except Exception as e:
            logger.warning("Failed to record search metric", error=str(e))

        # Extract unique directories if query seems to be asking for directories
        directories = _extract_directories(request.query, results) if results else None

        # Determine which repositories were actually searched
        if request.repositories:
            repositories_searched = request.repositories
        elif request.repository_filter:
            repositories_searched = [request.repository_filter]
        else:
            # All enabled repositories
            config_path = "config/repositories.yaml"
            repos_config = load_repositories_config(config_path)
            enabled_repos = repos_config.get_enabled_repositories()
            repositories_searched = [repo.name for repo in enabled_repos]

        return SearchResponse(
            query=request.query,
            total_results=len(result_items),
            search_time_ms=search_time_ms,
            results=result_items,
            directories=directories,
            repositories_searched=repositories_searched
        )

    except Exception as e:
        # Record error for observability
        try:
            observability_db.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity='ERROR',
                component='search_semantic',
                context={'query': request.query, 'repository_filter': request.repository_filter}
            )
        except Exception as log_err:
            logger.warning("Failed to record error", error=str(log_err))

        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")


def run_keyword_index(
    repository_names: Optional[List[str]] = None,
    full_rebuild: bool = False
):
    """
    Run Meilisearch keyword indexing in background thread (independent of Vector indexing).

    Business Purpose: Indexes files using Meilisearch for fast keyword search.
    Runs independently so it can execute in parallel with Vector indexing.

    Args:
        repository_names: List of repository names to index (None = all enabled)
        full_rebuild: If True, clears and rebuilds from scratch. If False, incremental update.
    """
    global meilisearch_indexer, vector_indexer, hybrid_engine, indexing_state

    try:
        # Initialize Keyword indexing state
        indexing_state["keyword"]["is_indexing"] = True
        indexing_state["keyword"]["current_repository"] = None
        indexing_state["keyword"]["repositories_completed"] = 0
        indexing_state["keyword"]["files_processed"] = 0
        indexing_state["keyword"]["files_total"] = 0
        indexing_state["keyword"]["mode"] = "full_rebuild" if full_rebuild else "incremental"
        indexing_state["is_indexing"] = True

        # Update legacy fields for UI compatibility
        if not indexing_state["vector"]["is_indexing"]:
            indexing_state["current_phase"] = "Keyword"
            indexing_state["mode"] = indexing_state["keyword"]["mode"]
            indexing_state["files_total"] = 0  # Reset files_total for new indexing run

        # Add to active index types
        if "Keyword" not in indexing_state["index_types"]:
            indexing_state["index_types"].append("Keyword")

        print(f"[Keyword] Starting indexing for repositories: {repository_names or 'all enabled'}")

        # Record indexing start event for observability
        indexing_start_time = time.time()

        # Import indexing logic
        from myragdb.indexers.file_scanner import FileScanner

        # Load repository configuration
        repo_config = load_repositories_config()

        # Filter repositories
        if repository_names:
            repos_to_index = [
                repo for repo in repo_config.repositories
                if repo.name in repository_names
            ]
        else:
            repos_to_index = repo_config.get_enabled_repositories()

        if not repos_to_index:
            print("[Keyword] No repositories to index")
            indexing_state["keyword"]["is_indexing"] = False
            return

        # Set total repositories
        indexing_state["keyword"]["repositories_total"] = len(repos_to_index)
        indexing_state["repositories_total"] = max(
            indexing_state["keyword"]["repositories_total"],
            indexing_state["vector"]["repositories_total"]
        )

        # Handle full rebuild vs incremental
        if full_rebuild:
            print(f"[Keyword] FULL REBUILD mode - creating fresh index")
            target_meilisearch = MeilisearchIndexer(
                host=settings.meilisearch_host,
                api_key=settings.meilisearch_api_key
            )
        else:
            print(f"[Keyword] INCREMENTAL mode - updating existing index")
            existing_meilisearch, _, _ = get_search_engines()
            target_meilisearch = existing_meilisearch

        # Index each repository
        total_files = 0
        for repo in repos_to_index:
            # Check if stop was requested
            if indexing_state["keyword"]["stop_requested"]:
                print(f"[Keyword] Stop requested - halting indexing")
                print(f"[Keyword] State change: stop_requested=True detected, breaking indexing loop")
                break

            # Update progress: current repository
            indexing_state["keyword"]["current_repository"] = repo.name
            print(f"[Keyword] State change: current_repository={repo.name}, reason=starting repository processing")
            if not indexing_state["vector"]["is_indexing"]:
                indexing_state["current_repository"] = repo.name

            print(f"[Keyword] Processing repository: {repo.name}")

            # Start timing for this repository
            repo_start_time = time.time()

            scanner = FileScanner(repo)
            files = list(scanner.scan())
            total_files += len(files)
            indexing_state["keyword"]["files_total"] = total_files

            if not indexing_state["vector"]["is_indexing"]:
                indexing_state["files_total"] = total_files

            repo_file_count = len(files)
            repo_total_size = 0

            if files:
                mode_str = "full rebuild" if full_rebuild else "incremental"
                print(f"[Keyword]   Found {len(files)} files in {repo.name} ({mode_str})")

                # Calculate total size from ScannedFile objects
                for scanned_file in files:
                    repo_total_size += scanned_file.size_bytes

                target_meilisearch.index_files_batch(files, batch_size=100, incremental=not full_rebuild)
                indexing_state["keyword"]["files_processed"] += len(files)
            else:
                print(f"[Keyword]   No files found in {repo.name}")

            # Record timing for this repository
            repo_duration = time.time() - repo_start_time

            # Import database
            from myragdb.db.file_metadata import FileMetadataDatabase
            file_db = FileMetadataDatabase()

            # Record stats (is_initial=True for full_rebuild)
            file_db.record_repository_indexing(
                repository=repo.name,
                index_type='keyword',
                duration_seconds=repo_duration,
                total_files=repo_file_count,
                total_size_bytes=repo_total_size,
                is_initial=full_rebuild
            )

            # Record indexing event for observability
            try:
                observability_db.record_indexing_event(
                    repository=repo.name,
                    event_type='complete',
                    status='success',
                    files_processed=repo_file_count,
                    duration_seconds=repo_duration,
                    metadata={
                        'index_type': 'keyword',
                        'mode': 'full_rebuild' if full_rebuild else 'incremental',
                        'size_bytes': repo_total_size
                    }
                )
            except Exception as e:
                logger.warning("Failed to record indexing event", error=str(e))

            print(f"[Keyword]   Indexed {repo_file_count} files ({repo_total_size / 1024 / 1024:.1f} MB) in {repo_duration:.1f}s")

            # Mark repository as completed
            indexing_state["keyword"]["repositories_completed"] += 1
            if not indexing_state["vector"]["is_indexing"]:
                indexing_state["repositories_completed"] = indexing_state["keyword"]["repositories_completed"]

        # Reset search engines if full rebuild
        if full_rebuild:
            meilisearch_indexer = None
            hybrid_engine = None

        print(f"[Keyword] Completed indexing {total_files} files from {len(repos_to_index)} repositories")

        # Clear progress state and mark complete
        indexing_state["keyword"]["is_indexing"] = False
        indexing_state["keyword"]["stop_requested"] = False
        print(f"[Keyword] State change: is_indexing=False, stop_requested=False, reason=indexing completed normally")

        # Update global state
        if not indexing_state["vector"]["is_indexing"]:
            indexing_state["is_indexing"] = False
            indexing_state["stop_requested"] = False
            current_time = datetime.utcnow()
            indexing_state["last_index_time"] = current_time.isoformat() + "Z"
            indexing_state["current_repository"] = None
            indexing_state["current_phase"] = None
            indexing_state["index_types"] = []

            # Persist last index time to disk
            if metadata_store:
                metadata_store.set_last_index_time(current_time)

            print(f"[Keyword] State change: global is_indexing=False, stop_requested=False, reason=no active indexing")
        else:
            # Remove Keyword from active types
            if "Keyword" in indexing_state["index_types"]:
                indexing_state["index_types"].remove("Keyword")
            print(f"[Keyword] State change: removed Keyword from active index_types, reason=Vector still running")

        print("[Keyword] Indexing completed successfully")

    except Exception as e:
        # Record error for observability
        try:
            current_repo = indexing_state["keyword"].get("current_repository", "unknown")
            observability_db.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity='CRITICAL',
                component='keyword_indexer',
                context={
                    'repository': current_repo,
                    'mode': 'full_rebuild' if full_rebuild else 'incremental'
                }
            )
            observability_db.record_indexing_event(
                repository=current_repo,
                event_type='error',
                status='failed',
                files_processed=indexing_state["keyword"].get("files_processed", 0),
                error_message=str(e),
                metadata={'index_type': 'keyword', 'mode': 'full_rebuild' if full_rebuild else 'incremental'}
            )
        except Exception as log_err:
            logger.warning("Failed to record error", error=str(log_err))

        # Clear progress state on error
        indexing_state["keyword"]["is_indexing"] = False
        indexing_state["keyword"]["stop_requested"] = False
        print(f"[Keyword] State change: is_indexing=False, stop_requested=False, reason=indexing failed with error")
        if not indexing_state["vector"]["is_indexing"]:
            indexing_state["is_indexing"] = False
            indexing_state["stop_requested"] = False
            indexing_state["current_repository"] = None
            indexing_state["current_phase"] = None
            print(f"[Keyword] State change: global is_indexing=False, stop_requested=False, reason=error cleanup")
        print(f"[Keyword] Indexing failed: {str(e)}")
        raise


def run_vector_index(
    repository_names: Optional[List[str]] = None,
    full_rebuild: bool = False
):
    """
    Run Vector indexing in background thread (independent of Keyword indexing).

    Business Purpose: Indexes files using semantic vector embeddings.
    Runs independently so it can execute in parallel with Keyword indexing.

    Args:
        repository_names: List of repository names to index (None = all enabled)
        full_rebuild: If True, clears and rebuilds from scratch. If False, incremental update.
    """
    global meilisearch_indexer, vector_indexer, hybrid_engine, indexing_state

    try:
        # Initialize Vector indexing state
        indexing_state["vector"]["is_indexing"] = True
        indexing_state["vector"]["current_repository"] = None
        indexing_state["vector"]["repositories_completed"] = 0
        indexing_state["vector"]["files_processed"] = 0
        indexing_state["vector"]["files_total"] = 0
        indexing_state["vector"]["mode"] = "full_rebuild" if full_rebuild else "incremental"
        indexing_state["is_indexing"] = True

        # Update legacy fields for UI compatibility
        if not indexing_state["keyword"]["is_indexing"]:
            indexing_state["current_phase"] = "Vector"
            indexing_state["mode"] = indexing_state["vector"]["mode"]
            indexing_state["files_total"] = 0  # Reset files_total for new indexing run

        # Add to active index types
        if "Vector" not in indexing_state["index_types"]:
            indexing_state["index_types"].append("Vector")

        print(f"[Vector] Starting indexing for repositories: {repository_names or 'all enabled'}")

        # Import indexing logic
        from myragdb.indexers.file_scanner import FileScanner

        # Load repository configuration
        repo_config = load_repositories_config()

        # Filter repositories
        if repository_names:
            repos_to_index = [
                repo for repo in repo_config.repositories
                if repo.name in repository_names
            ]
        else:
            repos_to_index = repo_config.get_enabled_repositories()

        if not repos_to_index:
            print("[Vector] No repositories to index")
            indexing_state["vector"]["is_indexing"] = False
            return

        # Set total repositories
        indexing_state["vector"]["repositories_total"] = len(repos_to_index)
        indexing_state["repositories_total"] = max(
            indexing_state["keyword"]["repositories_total"],
            indexing_state["vector"]["repositories_total"]
        )

        # Handle full rebuild vs incremental
        if full_rebuild:
            print(f"[Vector] FULL REBUILD mode - creating fresh index")
            target_vector = VectorIndexer()
        else:
            print(f"[Vector] INCREMENTAL mode - updating existing index")
            _, existing_vector, _ = get_search_engines()
            target_vector = existing_vector

        # Index each repository
        total_files = 0
        for repo in repos_to_index:
            # Check if stop was requested
            if indexing_state["vector"]["stop_requested"]:
                print(f"[Vector] Stop requested - halting indexing")
                print(f"[Vector] State change: stop_requested=True detected, breaking indexing loop")
                break

            # Update progress: current repository
            indexing_state["vector"]["current_repository"] = repo.name
            if not indexing_state["keyword"]["is_indexing"]:
                indexing_state["current_repository"] = repo.name

            print(f"[Vector] Processing repository: {repo.name}")
            print(f"[Vector] State change: current_repository={repo.name}, reason=starting repository processing")

            # Start timing for this repository
            repo_start_time = time.time()

            scanner = FileScanner(repo)
            files = list(scanner.scan())
            total_files += len(files)
            indexing_state["vector"]["files_total"] = total_files

            if not indexing_state["keyword"]["is_indexing"]:
                indexing_state["files_total"] = total_files

            repo_file_count = len(files)
            repo_total_size = 0

            if files:
                mode_str = "full rebuild" if full_rebuild else "incremental"
                print(f"[Vector]   Found {len(files)} files in {repo.name} ({mode_str})")

                # Calculate total size from ScannedFile objects
                for scanned_file in files:
                    repo_total_size += scanned_file.size_bytes

                target_vector.index_files(files, incremental=not full_rebuild)
                indexing_state["vector"]["files_processed"] += len(files)
            else:
                print(f"[Vector]   No files found in {repo.name}")

            # Record timing for this repository
            repo_duration = time.time() - repo_start_time

            # Import database
            from myragdb.db.file_metadata import FileMetadataDatabase
            file_db = FileMetadataDatabase()

            # Record stats (is_initial=True for full_rebuild)
            file_db.record_repository_indexing(
                repository=repo.name,
                index_type='vector',
                duration_seconds=repo_duration,
                total_files=repo_file_count,
                total_size_bytes=repo_total_size,
                is_initial=full_rebuild
            )

            print(f"[Vector]   Indexed {repo_file_count} files ({repo_total_size / 1024 / 1024:.1f} MB) in {repo_duration:.1f}s")

            # Mark repository as completed
            indexing_state["vector"]["repositories_completed"] += 1
            if not indexing_state["keyword"]["is_indexing"]:
                indexing_state["repositories_completed"] = indexing_state["vector"]["repositories_completed"]

        # Reset search engines if full rebuild
        if full_rebuild:
            vector_indexer = None
            hybrid_engine = None

        print(f"[Vector] Completed indexing {total_files} files from {len(repos_to_index)} repositories")

        # Clear progress state and mark complete
        indexing_state["vector"]["is_indexing"] = False
        indexing_state["vector"]["stop_requested"] = False
        print(f"[Vector] State change: is_indexing=False, stop_requested=False, reason=indexing completed normally")

        # Update global state
        if not indexing_state["keyword"]["is_indexing"]:
            indexing_state["is_indexing"] = False
            indexing_state["stop_requested"] = False
            current_time = datetime.utcnow()
            indexing_state["last_index_time"] = current_time.isoformat() + "Z"
            indexing_state["current_repository"] = None
            indexing_state["current_phase"] = None
            indexing_state["index_types"] = []

            # Persist last index time to disk
            if metadata_store:
                metadata_store.set_last_index_time(current_time)

            print(f"[Vector] State change: global is_indexing=False, stop_requested=False, reason=no active indexing")
        else:
            # Remove Vector from active types
            if "Vector" in indexing_state["index_types"]:
                indexing_state["index_types"].remove("Vector")
            print(f"[Vector] State change: removed Vector from active index_types, reason=Keyword still running")

        print("[Vector] Indexing completed successfully")

    except Exception as e:
        # Clear progress state on error
        indexing_state["vector"]["is_indexing"] = False
        indexing_state["vector"]["stop_requested"] = False
        print(f"[Vector] State change: is_indexing=False, stop_requested=False, reason=indexing failed with error")
        if not indexing_state["keyword"]["is_indexing"]:
            indexing_state["is_indexing"] = False
            indexing_state["stop_requested"] = False
            indexing_state["current_repository"] = None
            indexing_state["current_phase"] = None
            print(f"[Vector] State change: global is_indexing=False, stop_requested=False, reason=error cleanup")
        print(f"[Vector] Indexing failed: {str(e)}")
        raise


@app.post("/reindex", response_model=ReindexResponse)
async def reindex(request: ReindexRequest):
    """
    Trigger re-indexing of selected or all repositories.

    Business Purpose: Allows users to manually refresh the index to pick up
    new or modified files without restarting the service. Can re-index
    specific repositories for faster updates. Supports parallel Keyword and
    Vector indexing - they can run independently and simultaneously.

    Args:
        request: ReindexRequest with optional list of repository names

    Returns:
        ReindexResponse with status and timestamp

    Example:
        POST /reindex
        {"repositories": ["xLLMArionComply"], "index_keyword": true, "index_vector": true}
    """
    # Check if requested index types are already indexing
    if request.index_keyword and indexing_state["keyword"]["is_indexing"]:
        raise HTTPException(
            status_code=409,
            detail="Keyword indexing already in progress"
        )

    if request.index_vector and indexing_state["vector"]["is_indexing"]:
        raise HTTPException(
            status_code=409,
            detail="Vector indexing already in progress"
        )

    # Validate at least one index type selected
    if not request.index_keyword and not request.index_vector:
        raise HTTPException(
            status_code=400,
            detail="At least one index type (Keyword or Vector) must be selected"
        )

    started_at = datetime.utcnow().isoformat() + "Z"

    # Determine which repositories to index
    repo_names = request.repositories or []
    if not repo_names:
        # Load config to get all enabled repos
        repo_config = load_repositories_config()
        repo_names = [repo.name for repo in repo_config.get_enabled_repositories()]

    # Launch independent threads for Keyword (Meilisearch) and Vector indexing (can run in parallel)
    if request.index_keyword:
        keyword_thread = threading.Thread(
            target=run_keyword_index,
            args=(request.repositories, request.full_rebuild),
            daemon=True,
            name="Keyword-Indexer"
        )
        keyword_thread.start()
        print(f"Started Keyword indexing thread")

    if request.index_vector:
        vector_thread = threading.Thread(
            target=run_vector_index,
            args=(request.repositories, request.full_rebuild),
            daemon=True,
            name="Vector-Indexer"
        )
        vector_thread.start()
        print(f"Started Vector indexing thread")

    # Build descriptive message
    index_types = []
    if request.index_keyword: index_types.append("Keyword")
    if request.index_vector: index_types.append("Vector")
    mode = "full rebuild" if request.full_rebuild else "incremental update"

    return ReindexResponse(
        status="started",
        message=f"Re-indexing {len(repo_names)} repositor{'y' if len(repo_names) == 1 else 'ies'} ({', '.join(index_types)} - {mode}).",
        started_at=started_at,
        repositories=repo_names
    )


@app.post("/stop-indexing", response_model=StopIndexingResponse)
async def stop_indexing(request: StopIndexingRequest):
    """
    Request graceful stop of running indexing operations.

    Business Purpose: Allows users to stop indexing operations to free up
    resources or make corrections. Indexing will halt at the next safe
    checkpoint (between repositories) to avoid corruption.

    Args:
        request: StopIndexingRequest specifying which index types to stop

    Returns:
        StopIndexingResponse confirming which stops were requested

    Example:
        POST /stop-indexing
        {"stop_keyword": true, "stop_vector": true}
    """
    stopped = []

    # Check what's actually running and set stop flags
    if request.stop_keyword:
        if indexing_state["keyword"]["is_indexing"]:
            indexing_state["keyword"]["stop_requested"] = True
            indexing_state["stop_requested"] = True
            stopped.append("Keyword")
            print(f"[API] State change: keyword.stop_requested=True, reason=user requested stop via API")
        else:
            print(f"[API] Keyword stop requested but Keyword indexing is not currently running")

    if request.stop_vector:
        if indexing_state["vector"]["is_indexing"]:
            indexing_state["vector"]["stop_requested"] = True
            indexing_state["stop_requested"] = True
            stopped.append("Vector")
            print(f"[API] State change: vector.stop_requested=True, reason=user requested stop via API")
        else:
            print(f"[API] Vector stop requested but Vector is not currently indexing")

    if not stopped:
        return StopIndexingResponse(
            status="idle",
            message="No indexing operations are currently running",
            stopped=[]
        )

    return StopIndexingResponse(
        status="stopping",
        message=f"Stop request registered for {', '.join(stopped)}. Indexing will halt at next safe checkpoint.",
        stopped=stopped
    )


# ============================================================================
# LLM Management Endpoints
# ============================================================================

LLM_MODELS = [
    {"id": "qwen-coder-7b", "name": "Qwen Coder 7B", "port": 8085, "category": "best"},
    {"id": "qwen2.5-32b", "name": "Qwen 2.5 32B", "port": 8084, "category": "best"},
    {"id": "deepseek-r1-qwen-32b", "name": "DeepSeek R1 Qwen 32B", "port": 8092, "category": "best"},
    {"id": "llama-3.1-8b", "name": "Llama 3.1 8B", "port": 8087, "category": "best"},
    {"id": "llama-4-scout-17b", "name": "Llama 4 Scout 17B", "port": 8088, "category": "best"},
    {"id": "hermes-3-llama-8b", "name": "Hermes 3 Llama 8B", "port": 8086, "category": "best"},
    {"id": "mistral-7b", "name": "Mistral 7B", "port": 8083, "category": "limited"},
    {"id": "mistral-small-24b", "name": "Mistral Small 24B", "port": 8089, "category": "limited"},
    {"id": "phi3", "name": "Phi-3", "port": 8081, "category": "limited"},
    {"id": "smollm3", "name": "SmolLM3", "port": 8082, "category": "limited"},
]


def check_llm_running(port: int) -> bool:
    """
    Check if an LLM is running on a specific port.

    Business Purpose: Determine LLM status for UI display.

    Args:
        port: Port number to check

    Returns:
        True if process is listening on the port, False otherwise

    Example:
        is_running = check_llm_running(8085)
    """
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception as e:
        logger.error(f"Error checking port {port}: {e}")
        return False


@app.get("/llm/models", response_model=List[LLMInfo])
async def get_llm_models():
    """
    Get list of all available LLM models with their current status.

    Business Purpose: Provides UI with model information for display
    and management.

    Returns:
        List of LLM model information including running status

    Example:
        GET /llm/models

        [
            {
                "id": "qwen-coder-7b",
                "name": "Qwen Coder 7B",
                "port": 8085,
                "status": "running",
                "category": "best"
            },
            ...
        ]
    """
    models = []
    for model in LLM_MODELS:
        is_running = check_llm_running(model["port"])
        models.append(
            LLMInfo(
                id=model["id"],
                name=model["name"],
                port=model["port"],
                status="running" if is_running else "stopped",
                category=model["category"]
            )
        )
    return models


@app.post("/llm/start", response_model=StartLLMResponse)
async def start_llm(request: StartLLMRequest):
    """
    Start an LLM with specified mode.

    Business Purpose: Allows users to start local LLMs from the web UI
    without using terminal commands.

    Args:
        request: StartLLMRequest with model_id and mode

    Returns:
        StartLLMResponse with status, message, PID, and log file path

    Example:
        POST /llm/start
        {
            "model_id": "qwen-coder-7b",
            "mode": "tools"
        }
    """
    script_path = "/Users/liborballaty/llms/restart-llm-interactive.sh"

    # Validate model_id
    valid_models = [m["id"] for m in LLM_MODELS]
    if request.model_id not in valid_models:
        return StartLLMResponse(
            status="error",
            message=f"Invalid model_id '{request.model_id}'. Valid models: {', '.join(valid_models)}",
            model_id=request.model_id,
            pid=None,
            log_file=None
        )

    # Validate mode
    valid_modes = ["basic", "tools", "performance", "extended"]
    if request.mode not in valid_modes:
        return StartLLMResponse(
            status="error",
            message=f"Invalid mode '{request.mode}'. Valid modes: {', '.join(valid_modes)}",
            model_id=request.model_id,
            pid=None,
            log_file=None
        )

    try:
        # Execute the restart script
        result = subprocess.run(
            [script_path, request.model_id, request.mode],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Extract PID from output
        pid = None
        for line in result.stdout.split('\n'):
            if "Started with PID:" in line:
                pid_str = line.split("Started with PID:")[1].strip()
                try:
                    pid = int(pid_str)
                except ValueError:
                    pass

        # Construct log file path
        log_file = f"/Users/liborballaty/llms/logs/{request.model_id}-{request.mode}.log"

        # Check if process is actually running
        model_info = next((m for m in LLM_MODELS if m["id"] == request.model_id), None)
        if model_info and check_llm_running(model_info["port"]):
            return StartLLMResponse(
                status="success",
                message=f"{model_info['name']} started successfully in {request.mode} mode",
                model_id=request.model_id,
                pid=pid,
                log_file=log_file
            )
        else:
            return StartLLMResponse(
                status="error",
                message=f"Failed to start {request.model_id}. Check logs: {log_file}",
                model_id=request.model_id,
                pid=pid,
                log_file=log_file
            )

    except subprocess.TimeoutExpired:
        return StartLLMResponse(
            status="error",
            message=f"Timeout starting {request.model_id}",
            model_id=request.model_id,
            pid=None,
            log_file=None
        )
    except Exception as e:
        logger.error(f"Error starting LLM {request.model_id}: {e}")
        return StartLLMResponse(
            status="error",
            message=f"Error starting {request.model_id}: {str(e)}",
            model_id=request.model_id,
            pid=None,
            log_file=None
        )


@app.post("/llm/stop", response_model=StopLLMResponse)
async def stop_llm(request: StopLLMRequest):
    """
    Stop a running LLM.

    Business Purpose: Allows users to stop local LLMs from the web UI
    to free up resources or switch models.

    Args:
        request: StopLLMRequest with model_id

    Returns:
        StopLLMResponse with status and message

    Example:
        POST /llm/stop
        {
            "model_id": "qwen-coder-7b"
        }
    """
    # Validate model_id
    valid_models = [m["id"] for m in LLM_MODELS]
    if request.model_id not in valid_models:
        return StopLLMResponse(
            status="error",
            message=f"Invalid model_id '{request.model_id}'. Valid models: {', '.join(valid_models)}",
            model_id=request.model_id
        )

    # Get model info to find port
    model_info = next((m for m in LLM_MODELS if m["id"] == request.model_id), None)
    if not model_info:
        return StopLLMResponse(
            status="error",
            message=f"Model '{request.model_id}' not found",
            model_id=request.model_id
        )

    port = model_info["port"]

    try:
        # Find process using the port (same method as restart-llm-interactive.sh)
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            pid = int(result.stdout.strip())

            # Kill the process
            subprocess.run(
                ["kill", str(pid)],
                timeout=5
            )

            # Wait a moment for process to stop
            import time
            time.sleep(1)

            # Verify it stopped
            if not check_llm_running(port):
                logger.info(f"Stopped LLM {request.model_id} (PID: {pid})")
                return StopLLMResponse(
                    status="success",
                    message=f"{model_info['name']} stopped successfully (PID: {pid})",
                    model_id=request.model_id
                )
            else:
                return StopLLMResponse(
                    status="error",
                    message=f"Failed to stop {model_info['name']}. Process may still be running.",
                    model_id=request.model_id
                )
        else:
            # No process found on port
            return StopLLMResponse(
                status="success",
                message=f"{model_info['name']} is not running (no process found on port {port})",
                model_id=request.model_id
            )

    except subprocess.TimeoutExpired:
        return StopLLMResponse(
            status="error",
            message=f"Timeout while trying to stop {request.model_id}",
            model_id=request.model_id
        )
    except Exception as e:
        logger.error(f"Error stopping LLM {request.model_id}: {e}")
        return StopLLMResponse(
            status="error",
            message=f"Error stopping {request.model_id}: {str(e)}",
            model_id=request.model_id
        )


# ====================
# Observability Endpoints
# ====================

@app.get("/observability/stats", response_model=ObservabilityStatsResponse)
async def get_observability_stats(
    start_time: Optional[int] = None,
    end_time: Optional[int] = None
):
    """
    Get aggregated observability statistics.

    Business Purpose: Provides high-level metrics for dashboard overview
    showing search performance, error rates, and system health.

    Args:
        start_time: Unix timestamp for start of range (optional)
        end_time: Unix timestamp for end of range (optional)

    Returns:
        ObservabilityStatsResponse with aggregated statistics

    Example:
        GET /observability/stats
        GET /observability/stats?start_time=1704067200&end_time=1704153600
    """
    try:
        get_search_engines()  # Ensures observability_db is initialized

        # Get search statistics
        search_stats = observability_db.get_search_statistics(
            start_time=start_time,
            end_time=end_time
        )

        # Get error statistics
        error_stats = observability_db.get_error_statistics(
            start_time=start_time,
            end_time=end_time
        )

        # Get database info
        database_info = observability_db.get_database_size()

        return ObservabilityStatsResponse(
            search_stats=search_stats,
            error_stats=error_stats,
            database_info=database_info
        )

    except Exception as e:
        logger.error("Failed to get observability stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving observability stats: {str(e)}")


@app.post("/observability/metrics", response_model=ObservabilityMetricsResponse)
async def get_observability_metrics(request: ObservabilityMetricsRequest):
    """
    Get detailed observability metrics.

    Business Purpose: Retrieves time-series metrics data for charts and
    detailed analysis of search performance, errors, and system metrics.

    Args:
        request: Metrics request with filters

    Returns:
        ObservabilityMetricsResponse with filtered metrics

    Example:
        POST /observability/metrics
        {
            "metric_type": "search",
            "start_time": 1704067200,
            "limit": 1000
        }
    """
    try:
        get_search_engines()  # Ensures observability_db is initialized

        metric_type = request.metric_type or "all"
        response_data = {
            "metric_type": metric_type,
            "total_count": 0,
            "time_range_start": request.start_time,
            "time_range_end": request.end_time
        }

        if metric_type in ("search", "all"):
            search_metrics = observability_db.get_search_metrics(
                start_time=request.start_time,
                end_time=request.end_time,
                limit=request.limit
            )
            response_data["search_metrics"] = [SearchMetricItem(**m) for m in search_metrics]
            response_data["total_count"] += len(search_metrics)

        if metric_type in ("error", "all"):
            error_logs = observability_db.get_errors(
                start_time=request.start_time,
                end_time=request.end_time,
                limit=request.limit
            )
            response_data["error_logs"] = [ErrorLogItem(**e) for e in error_logs]
            response_data["total_count"] += len(error_logs)

        if metric_type in ("system", "all"):
            system_metrics = observability_db.get_system_metrics(
                start_time=request.start_time,
                end_time=request.end_time,
                limit=request.limit
            )
            response_data["system_metrics"] = [SystemMetricItem(**m) for m in system_metrics]
            response_data["total_count"] += len(system_metrics)

        if metric_type in ("indexing", "all"):
            indexing_events = observability_db.get_indexing_events(
                start_time=request.start_time,
                end_time=request.end_time,
                limit=request.limit
            )
            response_data["indexing_events"] = [IndexingEventItem(**e) for e in indexing_events]
            response_data["total_count"] += len(indexing_events)

        return ObservabilityMetricsResponse(**response_data)

    except Exception as e:
        logger.error("Failed to get observability metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving observability metrics: {str(e)}")


@app.post("/observability/cleanup", response_model=ObservabilityCleanupResponse)
async def cleanup_observability_data(request: ObservabilityCleanupRequest):
    """
    Clean up old observability data.

    Business Purpose: Prevents database from growing unbounded by removing
    old metrics while preserving recent data for analysis.

    Args:
        request: Cleanup request with retention period

    Returns:
        ObservabilityCleanupResponse with deletion counts

    Example:
        POST /observability/cleanup
        {
            "retention_days": 30
        }
    """
    try:
        get_search_engines()  # Ensures observability_db is initialized

        records_deleted = observability_db.cleanup_old_data(
            retention_days=request.retention_days
        )

        total_deleted = sum(records_deleted.values())

        return ObservabilityCleanupResponse(
            status="success",
            records_deleted=records_deleted,
            message=f"Successfully deleted {total_deleted} old records (retention: {request.retention_days} days)"
        )

    except Exception as e:
        logger.error("Failed to cleanup observability data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error cleaning up observability data: {str(e)}")


# ============================================================================
# File Watching / Auto-Reindex Endpoints
# ============================================================================

@app.get("/watcher/status", response_model=WatcherStatusResponse)
async def get_watcher_status():
    """
    Get status of all active repository file system watchers.

    Business Purpose: Provides visibility into which repositories are
    being monitored for automatic reindexing when files change.

    Returns:
        WatcherStatusResponse with list of active watchers and their status

    Example:
        GET /watcher/status

        Response:
        {
            "watchers": [
                {
                    "repository": "myragdb",
                    "status": "active",
                    "pending_changes": 0,
                    "path": "/path/to/myragdb",
                    "debounce_seconds": 5
                }
            ],
            "total_watchers": 1,
            "total_pending_changes": 0
        }
    """
    if not watcher_manager:
        return WatcherStatusResponse(
            watchers=[],
            total_watchers=0,
            total_pending_changes=0
        )

    try:
        watcher_status = watcher_manager.get_watcher_status()
        total_pending = sum(w["pending_changes"] for w in watcher_status)

        watchers = [
            WatcherStatusItem(**w) for w in watcher_status
        ]

        return WatcherStatusResponse(
            watchers=watchers,
            total_watchers=len(watchers),
            total_pending_changes=total_pending
        )
    except Exception as e:
        logger.error("Failed to get watcher status", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get watcher status: {str(e)}")


@app.post("/repositories/{repository}/auto-reindex", response_model=ToggleAutoReindexResponse)
async def toggle_auto_reindex(repository: str, request: ToggleAutoReindexRequest):
    """
    Enable or disable automatic reindexing for a repository.

    Business Purpose: Allows users to control whether a repository should
    automatically reindex when files change, providing flexibility to
    disable watching for repositories that change frequently or don't
    need immediate updates.

    Args:
        repository: Repository name
        request: ToggleAutoReindexRequest with enabled flag

    Returns:
        ToggleAutoReindexResponse with updated status

    Example:
        POST /repositories/myragdb/auto-reindex
        {"enabled": false}

        Response:
        {
            "status": "success",
            "repository": "myragdb",
            "auto_reindex_enabled": false,
            "watcher_status": "stopped",
            "message": "Auto-reindex disabled for repository myragdb"
        }
    """
    if not watcher_manager:
        raise HTTPException(
            status_code=503,
            detail="Watcher manager not initialized"
        )

    try:
        # Load repository config
        repo_config = load_repositories_config()
        repo = repo_config.get_repository_by_name(repository)

        if not repo:
            raise HTTPException(
                status_code=404,
                detail=f"Repository not found: {repository}"
            )

        if not repo.enabled:
            raise HTTPException(
                status_code=400,
                detail=f"Repository is not enabled: {repository}"
            )

        # Toggle watcher
        if request.enabled:
            # Start watching
            # Extract file extensions from include patterns
            file_extensions = []
            for pattern in repo.file_patterns.include:
                if pattern.startswith('**/') and pattern.count('.') == 1:
                    ext = pattern.split('.')[-1]
                    file_extensions.append(f'.{ext}')

            if not file_extensions:
                file_extensions = ['.py', '.md', '.ts', '.tsx', '.js', '.dart']

            watcher_manager.start_watching(
                repository_name=repo.name,
                repository_path=repo.path,
                file_extensions=file_extensions,
                debounce_seconds=5
            )

            watcher_status = "active"
            message = f"Auto-reindex enabled for repository {repository}"
        else:
            # Stop watching
            watcher_manager.stop_watching(repository)
            watcher_status = "stopped"
            message = f"Auto-reindex disabled for repository {repository}"

        logger.info(message, repository=repository, enabled=request.enabled)

        return ToggleAutoReindexResponse(
            status="success",
            repository=repository,
            auto_reindex_enabled=request.enabled,
            watcher_status=watcher_status,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to toggle auto-reindex",
            repository=repository,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to toggle auto-reindex: {str(e)}"
        )


# ============================================================================
# README Viewer Endpoints
# ============================================================================

@app.get("/repositories/{repository}/readme", response_model=ReadmeResponse)
async def get_repository_readme(repository: str):
    """
    Fetch README content for a repository.

    Business Purpose: Allows users to view repository README files
    directly in the UI to understand what each repository contains
    without leaving the application.

    Args:
        repository: Repository name

    Returns:
        ReadmeResponse with README content if found

    Example:
        GET /repositories/myragdb/readme

        Response:
        {
            "repository": "myragdb",
            "readme_found": true,
            "readme_path": "/path/to/myragdb/README.md",
            "content": "# MyRAGDB\\n\\n...",
            "file_name": "README.md"
        }
    """
    try:
        # Load repository config
        repo_config = load_repositories_config()
        repo = repo_config.get_repository_by_name(repository)

        if not repo:
            return ReadmeResponse(
                repository=repository,
                readme_found=False,
                error=f"Repository not found: {repository}"
            )

        # Look for README files (case-insensitive)
        repo_path = Path(repo.path)
        readme_patterns = [
            "README.md",
            "readme.md",
            "Readme.md",
            "README.MD",
            "README.txt",
            "readme.txt",
            "README.rst",
            "readme.rst",
            "README",
            "readme"
        ]

        readme_file = None
        for pattern in readme_patterns:
            candidate = repo_path / pattern
            if candidate.exists() and candidate.is_file():
                readme_file = candidate
                break

        if not readme_file:
            return ReadmeResponse(
                repository=repository,
                readme_found=False,
                error="No README file found in repository"
            )

        # Read README content
        try:
            with open(readme_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Limit content size to prevent large responses
            max_size = 100000  # 100KB
            if len(content) > max_size:
                content = content[:max_size] + "\n\n... (content truncated)"

            return ReadmeResponse(
                repository=repository,
                readme_found=True,
                readme_path=str(readme_file),
                content=content,
                file_name=readme_file.name
            )

        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(readme_file, 'r', encoding='latin-1') as f:
                    content = f.read()

                return ReadmeResponse(
                    repository=repository,
                    readme_found=True,
                    readme_path=str(readme_file),
                    content=content,
                    file_name=readme_file.name
                )
            except Exception as e:
                return ReadmeResponse(
                    repository=repository,
                    readme_found=False,
                    error=f"Failed to read README file: {str(e)}"
                )

        except Exception as e:
            return ReadmeResponse(
                repository=repository,
                readme_found=False,
                error=f"Error reading README: {str(e)}"
            )

    except Exception as e:
        logger.error("Failed to fetch README", repository=repository, error=str(e), exc_info=True)
        return ReadmeResponse(
            repository=repository,
            readme_found=False,
            error=f"Internal error: {str(e)}"
        )


# ============================================================================
# Main Entry Point
# ============================================================================

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
