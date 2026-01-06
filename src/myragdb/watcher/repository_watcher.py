# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/watcher/repository_watcher.py
# Description: File system monitoring for automatic change detection and incremental reindexing
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-06

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
from pathlib import Path
from typing import Set, Callable, List
import structlog

logger = structlog.get_logger()


class RepositoryEventHandler(FileSystemEventHandler):
    """
    Handles file system events for a single repository.

    Business Purpose: Automatically detect file changes to keep
    search indexes up-to-date without manual intervention.

    Example:
        handler = RepositoryEventHandler(
            repository_name="myragdb",
            repository_path="/path/to/myragdb",
            file_extensions={'.py', '.md'},
            reindex_callback=trigger_reindex,
            debounce_seconds=5
        )
    """

    def __init__(
        self,
        repository_name: str,
        repository_path: str,
        file_extensions: Set[str],
        reindex_callback: Callable[[str, List[str]], None],
        debounce_seconds: int = 5
    ):
        """
        Initialize event handler for a repository.

        Args:
            repository_name: Name of the repository
            repository_path: Absolute path to repository root
            file_extensions: Set of file extensions to watch (e.g., {'.py', '.md'})
            reindex_callback: Function to call when reindexing needed
            debounce_seconds: Wait time after last change before triggering reindex
        """
        self.repository_name = repository_name
        self.repository_path = Path(repository_path)
        self.file_extensions = file_extensions
        self.reindex_callback = reindex_callback
        self.debounce_seconds = debounce_seconds

        # Track pending changes
        self.pending_changes: Set[tuple] = set()  # Set of (file_path, event_type)
        self.debounce_timer = None
        self.lock = threading.Lock()

    def _should_process_file(self, file_path: str) -> bool:
        """
        Check if file should trigger reindexing.

        Business Purpose: Filter out irrelevant files to avoid unnecessary
        reindexing operations for build artifacts and temporary files.

        Args:
            file_path: Absolute path to file

        Returns:
            True if file should trigger reindexing, False otherwise
        """
        path = Path(file_path)

        # Check extension
        if path.suffix not in self.file_extensions:
            return False

        # Exclude patterns (same as indexing exclusions)
        exclude_patterns = [
            '**/node_modules/**',
            '**/.git/**',
            '**/venv/**',
            '**/archive-*/**',
            '**/*.lock',
            '**/__pycache__/**',
            '**/data/**',
            '**/.meilisearch/**',
            '**/.chroma/**',
            '**/dist/**',
            '**/build/**',
            '**/target/**',
            '**/.next/**',
            '**/.nuxt/**',
            '**/.dart_tool/**',
            '**/android/.gradle/**',
            '**/.gradle/**',
            '**/vendor/**',
            '**/ios/Pods/**',
            '**/.pytest_cache/**',
            '**/.mypy_cache/**',
            '**/coverage/**'
        ]

        for pattern in exclude_patterns:
            if path.match(pattern):
                return False

        return True

    def on_created(self, event):
        """Handle file creation event."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change(event.src_path, 'created')

    def on_modified(self, event):
        """Handle file modification event."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change(event.src_path, 'modified')

    def on_deleted(self, event):
        """Handle file deletion event."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change(event.src_path, 'deleted')

    def on_moved(self, event):
        """Handle file move/rename event."""
        if not event.is_directory:
            # Treat move as delete + create
            if self._should_process_file(event.src_path):
                self._queue_change(event.src_path, 'deleted')
            if self._should_process_file(event.dest_path):
                self._queue_change(event.dest_path, 'created')

    def _queue_change(self, file_path: str, event_type: str):
        """
        Queue a file change for reindexing with debouncing.

        Business Purpose: Batch multiple rapid changes into a single
        reindex operation to avoid excessive indexing during active editing.

        Args:
            file_path: Path to changed file
            event_type: Type of event ('created', 'modified', 'deleted')
        """
        with self.lock:
            self.pending_changes.add((file_path, event_type))

            # Cancel existing timer
            if self.debounce_timer:
                self.debounce_timer.cancel()

            # Start new timer
            self.debounce_timer = threading.Timer(
                self.debounce_seconds,
                self._trigger_reindex
            )
            self.debounce_timer.start()

    def _trigger_reindex(self):
        """
        Trigger incremental reindexing for pending changes.

        Business Purpose: Execute reindexing after debounce period to
        ensure search results reflect latest file changes.
        """
        with self.lock:
            if not self.pending_changes:
                return

            # Get unique file paths (ignore event type for now)
            changed_files = list({path for path, _ in self.pending_changes})

            logger.info(
                "Auto-reindex triggered",
                repository=self.repository_name,
                file_count=len(changed_files),
                files_preview=changed_files[:10]  # Log first 10
            )

            # Clear pending changes
            self.pending_changes.clear()

        # Trigger reindexing via callback
        try:
            self.reindex_callback(self.repository_name, changed_files)
        except Exception as e:
            logger.error(
                "Auto-reindex failed",
                repository=self.repository_name,
                error=str(e),
                exc_info=True
            )


class RepositoryWatcherManager:
    """
    Manages file system watchers for multiple repositories.

    Business Purpose: Coordinates automatic change detection across
    all indexed repositories with centralized lifecycle management.

    Example:
        manager = RepositoryWatcherManager(reindex_callback=trigger_reindex)
        manager.start_watching(
            repository_name="myragdb",
            repository_path="/path/to/myragdb",
            file_extensions=['.py', '.md']
        )
        manager.stop_all()
    """

    def __init__(self, reindex_callback: Callable[[str, List[str]], None]):
        """
        Initialize watcher manager.

        Args:
            reindex_callback: Function to call when reindexing needed.
                             Signature: (repository_name: str, changed_files: List[str]) -> None
        """
        self.reindex_callback = reindex_callback
        self.observers = {}  # repo_name -> Observer
        self.handlers = {}   # repo_name -> RepositoryEventHandler
        self.lock = threading.Lock()

    def start_watching(
        self,
        repository_name: str,
        repository_path: str,
        file_extensions: List[str],
        debounce_seconds: int = 5
    ):
        """
        Start watching a repository for changes.

        Business Purpose: Enable automatic reindexing for a repository
        to keep search results up-to-date as files change.

        Args:
            repository_name: Name of the repository
            repository_path: Absolute path to repository root
            file_extensions: List of file extensions to watch (e.g., ['.py', '.md'])
            debounce_seconds: Wait time after last change before triggering reindex

        Example:
            manager.start_watching(
                "myragdb",
                "/path/to/myragdb",
                ['.py', '.md', '.ts']
            )
        """
        with self.lock:
            if repository_name in self.observers:
                logger.warning(f"Already watching repository: {repository_name}")
                return

            # Create event handler
            handler = RepositoryEventHandler(
                repository_name=repository_name,
                repository_path=repository_path,
                file_extensions=set(file_extensions),
                reindex_callback=self.reindex_callback,
                debounce_seconds=debounce_seconds
            )

            # Create observer
            observer = Observer()
            observer.schedule(handler, repository_path, recursive=True)
            observer.start()

            self.observers[repository_name] = observer
            self.handlers[repository_name] = handler

            logger.info(
                "Started watching repository",
                repository=repository_name,
                path=repository_path,
                extensions=file_extensions
            )

    def stop_watching(self, repository_name: str):
        """
        Stop watching a repository.

        Business Purpose: Disable automatic reindexing for a repository
        to conserve resources or prevent unwanted updates.

        Args:
            repository_name: Name of the repository to stop watching
        """
        with self.lock:
            if repository_name not in self.observers:
                logger.warning(f"Not watching repository: {repository_name}")
                return

            observer = self.observers[repository_name]
            observer.stop()
            observer.join(timeout=5)

            del self.observers[repository_name]
            del self.handlers[repository_name]

            logger.info("Stopped watching repository", repository=repository_name)

    def stop_all(self):
        """
        Stop all watchers.

        Business Purpose: Cleanly shutdown all file monitoring when
        application shuts down to avoid orphaned threads.

        Example:
            # At application shutdown
            manager.stop_all()
        """
        with self.lock:
            repo_names = list(self.observers.keys())

        for repo_name in repo_names:
            self.stop_watching(repo_name)

        logger.info("All repository watchers stopped")

    def get_watcher_status(self) -> List[dict]:
        """
        Get status of all active watchers.

        Business Purpose: Provide visibility into which repositories are
        being monitored for automatic reindexing.

        Returns:
            List of dictionaries with watcher status information

        Example:
            status = manager.get_watcher_status()
            # Returns: [
            #     {
            #         "repository": "myragdb",
            #         "status": "active",
            #         "pending_changes": 0,
            #         "watching_since": 1704567890
            #     }
            # ]
        """
        with self.lock:
            status = []
            for repo_name, observer in self.observers.items():
                handler = self.handlers[repo_name]
                with handler.lock:
                    pending_count = len(handler.pending_changes)

                status.append({
                    "repository": repo_name,
                    "status": "active" if observer.is_alive() else "stopped",
                    "pending_changes": pending_count,
                    "path": str(handler.repository_path),
                    "debounce_seconds": handler.debounce_seconds
                })

            return status
