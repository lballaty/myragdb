# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/version.py
# Description: CalVer version information for MyRAGDB (YYYY.MM.DD.MAJOR.MINOR.PATCH format)
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

from datetime import datetime

# CalVer: YYYY.MM.DD.MAJOR.MINOR.PATCH
# - YYYY: Release year
# - MM: Release month (zero-padded)
# - DD: Release day (zero-padded)
# - MAJOR: Major version (breaking changes)
# - MINOR: Minor version (new features, backward compatible)
# - PATCH: Patch version (bug fixes only)
# Example: 2026.01.05.1.0.0 = January 5, 2026, major version 1.0.0
_BUILD_DATE = datetime(2026, 1, 6)  # Update this when creating new releases
_MAJOR_VERSION = 2  # Increment for breaking changes
_MINOR_VERSION = 37  # Increment for new features (backward compatible)
_PATCH_VERSION = 10  # Increment for bug fixes only

__version__ = f"{_BUILD_DATE.year}.{_BUILD_DATE.month:02d}.{_BUILD_DATE.day:02d}.{_MAJOR_VERSION}.{_MINOR_VERSION}.{_PATCH_VERSION}"
__version_info__ = (_BUILD_DATE.year, _BUILD_DATE.month, _BUILD_DATE.day, _MAJOR_VERSION, _MINOR_VERSION, _PATCH_VERSION)
__build_date__ = _BUILD_DATE.strftime("%Y-%m-%d")

# Release notes for current version
RELEASE_NOTES = f"""
MyRAGDB v{__version__} - Port Registry Alignment ({__build_date__})

Changes in v2026.01.06.2.28.0:
- Aligned MCP middleware to use official port 8093 (per port-registry.json)
- Updated start.sh to check for port 8093 instead of 8080
- Port 8080 is reserved for Customer Compliance UI (production priority)
- MCP middleware properly accessible at http://localhost:8093

Previous changes (v2026.01.06.2.24.0):
- Integrated MCP HTTP middleware into start.sh (automatic startup)
- MCP middleware provides REST API for LLMs to access MyRAGDB search
- Allows local LLMs (llama.cpp, etc.) to use MyRAGDB as a tool
- Graceful handling: Won't restart if already running on port 8080
- Proper shutdown order in stop.sh (MCP → MyRAGDB → Meilisearch)
- Complete system now starts with single command: ./start.sh

Previous changes (v2026.01.06.2.22.0):
- Integrated Meilisearch startup into start.sh script
- Single command startup: ./start.sh now starts both Meilisearch and MyRAGDB
- Enhanced stop.sh to also stop Meilisearch
- Proper dependency ordering ensures Meilisearch is running before MyRAGDB
- Graceful handling: Won't restart Meilisearch if already running
- PID file tracking for both services (.meilisearch.pid and .server.pid)

Previous changes (v2026.01.05.2.13.2):
- Fixed lock/unlock button (logActivity → addActivityLog)
- Implemented remove repository endpoint (DELETE /repositories/:name)
- Remove button now actually removes repositories from config
- Both actions now log to activity monitor

Previous changes (v2026.01.05.2.13.1):
- Fixed keyword search 404 error (HTML dropdown value mismatch)
- Added cache busting to CSS/JS assets (prevents stale browser cache)
- HTML dropdown now correctly calls /search/keyword endpoint

Previous changes (v2026.01.05.1.0.2):
- Fixed Meilisearch get_document_count() error (IndexStats attribute access)
- Updated versioning format to YYYY.MM.DD.MAJOR.MINOR.PATCH for better granularity
- Replaced Whoosh with Meilisearch 1.31.0 for keyword search
- Fixed MeilisearchIndexer.index_files_batch method call in server.py
- Added HybridSearchEngine.get_stats() method for statistics endpoint
- Updated UI references from "BM25" to "Keyword (Meilisearch)"
- Base64 document ID parity between Meilisearch and ChromaDB
- M4 Max optimizations: 32GB memory, 10 threads for indexing

Features:
- Hybrid search combining Meilisearch keyword search and semantic vector search
- Independent parallel indexing for Keyword and Vector indexes
- Real-time indexing progress tracking with web UI
- Incremental and full rebuild indexing modes
- Typo-tolerant keyword search with file/folder name boosting
- Repository-based file scanning and indexing
- FastAPI backend with CORS support
- Modern web UI with search, activity monitoring, and statistics
- Non-blocking search during indexing operations

Technology Stack:
- Keyword: Meilisearch 1.31.0 (Rust-based, memory-mapped indexes)
- Vector: Sentence Transformers (all-MiniLM-L6-v2)
- ChromaDB for vector storage
- FastAPI for REST API
- Vanilla JavaScript frontend

Version Format: CalVer (YYYY.MM.PATCH)
- YYYY: Release year
- MM: Release month (zero-padded)
- PATCH: Bug fix increment within the month
"""
