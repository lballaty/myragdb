# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/clear_indexes.py
# Description: Clear all indexes and metadata database for clean re-indexing
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-06

"""
Clear Indexes Script

Business Purpose: Provides a safe way to clear all search indexes and metadata
database when major indexing changes are made (e.g., chunking strategy changes,
embedding changes). This ensures clean re-indexing without stale data.

Usage:
    # Clear everything (Meilisearch + ChromaDB + SQLite)
    python scripts/clear_indexes.py --all

    # Clear only vector index (ChromaDB + SQLite)
    python scripts/clear_indexes.py --vector

    # Clear only keyword index (Meilisearch)
    python scripts/clear_indexes.py --keyword

    # Clear only SQLite metadata
    python scripts/clear_indexes.py --metadata

Example:
    # After changing vector embedding logic, clear vector index
    python scripts/clear_indexes.py --vector
    # Then re-index
    python -m myragdb.cli index --all
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
from myragdb.indexers.vector_indexer import VectorIndexer
from myragdb.config import settings


def clear_meilisearch():
    """Clear Meilisearch keyword index."""
    print("[Clear] Clearing Meilisearch index...")
    try:
        indexer = MeilisearchIndexer()
        indexer.clear_index()
        indexer.wait_for_pending_tasks()
        print("[Clear] ✓ Meilisearch index cleared")
    except Exception as e:
        print(f"[Clear] ✗ Error clearing Meilisearch: {e}")


def clear_chromadb():
    """Clear ChromaDB vector index."""
    print("[Clear] Clearing ChromaDB vector index...")
    try:
        indexer = VectorIndexer()
        indexer.clear_index()
        print("[Clear] ✓ ChromaDB vector index cleared")
    except Exception as e:
        print(f"[Clear] ✗ Error clearing ChromaDB: {e}")


def clear_sqlite_metadata():
    """Clear SQLite metadata database."""
    print("[Clear] Clearing SQLite metadata database...")
    try:
        metadata_path = Path(settings.metadata_db)
        if metadata_path.exists():
            metadata_path.unlink()
            print(f"[Clear] ✓ SQLite metadata database deleted: {metadata_path}")
        else:
            print(f"[Clear] ⚠ SQLite metadata database does not exist: {metadata_path}")
    except Exception as e:
        print(f"[Clear] ✗ Error clearing SQLite metadata: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Clear MyRAGDB indexes and metadata for clean re-indexing"
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Clear all indexes (Meilisearch + ChromaDB + SQLite)'
    )

    parser.add_argument(
        '--keyword',
        action='store_true',
        help='Clear Meilisearch keyword index only'
    )

    parser.add_argument(
        '--vector',
        action='store_true',
        help='Clear ChromaDB vector index and SQLite metadata'
    )

    parser.add_argument(
        '--metadata',
        action='store_true',
        help='Clear SQLite metadata database only'
    )

    args = parser.parse_args()

    # If no arguments, show help
    if not any([args.all, args.keyword, args.vector, args.metadata]):
        parser.print_help()
        sys.exit(1)

    print("=" * 60)
    print("MyRAGDB Index Cleaner")
    print("=" * 60)

    if args.all:
        print("\n⚠️  Clearing ALL indexes and metadata...\n")
        clear_meilisearch()
        clear_chromadb()
        clear_sqlite_metadata()

    else:
        if args.keyword:
            clear_meilisearch()

        if args.vector:
            clear_chromadb()
            clear_sqlite_metadata()

        if args.metadata:
            clear_sqlite_metadata()

    print("\n" + "=" * 60)
    print("✓ Clear operations complete")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Re-index your repositories:")
    print("     python scripts/initial_index.py")
    print("\n  2. Verify index contents:")
    print("     python scripts/verify_indexed_content.py")
    print("\n  3. Test search:")
    print("     python -m myragdb.cli search 'your query'")


if __name__ == '__main__':
    main()
