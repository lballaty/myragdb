# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/metadata.py
# Description: Persistent metadata storage for indexing state and statistics
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()


class MetadataStore:
    """
    Persistent storage for MyRAGDB metadata.

    Business Purpose: Preserves indexing history, statistics, and state
    across server restarts, ensuring users don't lose track of when
    their repositories were last indexed.

    Storage Format: JSON file in data directory

    Example:
        store = MetadataStore()
        store.set_last_index_time(datetime.utcnow())
        last_time = store.get_last_index_time()
    """

    def __init__(self, metadata_path: Optional[Path] = None):
        """
        Initialize metadata store.

        Args:
            metadata_path: Path to metadata.json file. If None, uses default
                          location at data/metadata.json
        """
        if metadata_path is None:
            # Default location: data/metadata.json
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            metadata_path = data_dir / "metadata.json"

        self.metadata_path = Path(metadata_path)
        self._ensure_metadata_file()

        logger.info("Metadata store initialized", path=str(self.metadata_path))

    def _ensure_metadata_file(self):
        """Create metadata file with defaults if it doesn't exist."""
        if not self.metadata_path.exists():
            default_metadata = {
                "last_index_time": None,
                "total_searches": 0,
                "total_search_time_ms": 0,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "version": "1.0"
            }
            self._save_metadata(default_metadata)
            logger.info("Created new metadata file", path=str(self.metadata_path))

    def _load_metadata(self) -> Dict[str, Any]:
        """
        Load metadata from disk.

        Returns:
            Dictionary containing all metadata
        """
        try:
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning("Failed to load metadata, using defaults", error=str(e))
            return {
                "last_index_time": None,
                "total_searches": 0,
                "total_search_time_ms": 0,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "version": "1.0"
            }

    def _save_metadata(self, metadata: Dict[str, Any]):
        """
        Save metadata to disk.

        Args:
            metadata: Dictionary to save
        """
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error("Failed to save metadata", error=str(e))

    def get_last_index_time(self) -> Optional[str]:
        """
        Get timestamp of last successful indexing run.

        Returns:
            ISO 8601 timestamp string or None if never indexed

        Example:
            last_time = store.get_last_index_time()
            if last_time:
                print(f"Last indexed: {last_time}")
            else:
                print("Never indexed")
        """
        metadata = self._load_metadata()
        return metadata.get("last_index_time")

    def set_last_index_time(self, timestamp: Optional[datetime] = None):
        """
        Record timestamp of successful indexing completion.

        Args:
            timestamp: Datetime object or None to use current time

        Example:
            store.set_last_index_time()  # Uses current time
            store.set_last_index_time(datetime(2026, 1, 5, 12, 0, 0))
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        metadata = self._load_metadata()
        metadata["last_index_time"] = timestamp.isoformat() + "Z"
        self._save_metadata(metadata)

        logger.info("Updated last index time", timestamp=metadata["last_index_time"])

    def get_search_stats(self) -> Dict[str, int]:
        """
        Get cumulative search statistics.

        Returns:
            Dictionary with total_searches and total_search_time_ms

        Example:
            stats = store.get_search_stats()
            avg_ms = stats["total_search_time_ms"] / stats["total_searches"]
            print(f"Average search time: {avg_ms:.2f}ms")
        """
        metadata = self._load_metadata()
        return {
            "total_searches": metadata.get("total_searches", 0),
            "total_search_time_ms": metadata.get("total_search_time_ms", 0)
        }

    def record_search(self, search_time_ms: float):
        """
        Record a search operation and its duration.

        Business Purpose: Track search performance over time to identify
        degradation or improvements.

        Args:
            search_time_ms: Search duration in milliseconds

        Example:
            start = time.time()
            results = search_engine.search("query")
            duration_ms = (time.time() - start) * 1000
            store.record_search(duration_ms)
        """
        metadata = self._load_metadata()
        metadata["total_searches"] = metadata.get("total_searches", 0) + 1
        metadata["total_search_time_ms"] = metadata.get("total_search_time_ms", 0) + search_time_ms
        self._save_metadata(metadata)

    def get_all_metadata(self) -> Dict[str, Any]:
        """
        Get all metadata as dictionary.

        Returns:
            Complete metadata dictionary

        Example:
            metadata = store.get_all_metadata()
            print(json.dumps(metadata, indent=2))
        """
        return self._load_metadata()

    def clear(self):
        """
        Reset all metadata to defaults.

        Business Purpose: Allow users to reset statistics without
        deleting the entire data directory.

        Example:
            store.clear()  # Reset all stats
        """
        default_metadata = {
            "last_index_time": None,
            "total_searches": 0,
            "total_search_time_ms": 0,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0"
        }
        self._save_metadata(default_metadata)
        logger.info("Metadata cleared")
