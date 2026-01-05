# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/version.py
# Description: CalVer version information for MyRAGDB (YYYY.MM.PATCH format)
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

from datetime import datetime

# CalVer: YYYY.MM.PATCH (Year.Month.Patch)
# Example: 2026.01.0 = January 2026, patch 0
_BUILD_DATE = datetime(2026, 1, 5)  # Update this when creating new releases
_PATCH_VERSION = 1  # Increment for bug fixes within the same month

__version__ = f"{_BUILD_DATE.year}.{_BUILD_DATE.month:02d}.{_PATCH_VERSION}"
__version_info__ = (_BUILD_DATE.year, _BUILD_DATE.month, _PATCH_VERSION)
__build_date__ = _BUILD_DATE.strftime("%Y-%m-%d")

# Release notes for current version
RELEASE_NOTES = f"""
MyRAGDB v{__version__} - Meilisearch Migration ({__build_date__})

Changes in v2026.01.1:
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
