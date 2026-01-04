# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/initial_index.py
# Description: Initial indexing script to populate search indexes
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

"""
Initial indexing script for MyRAGDB.

Business Purpose: Indexes all configured repositories for the first time,
populating both BM25 and vector indexes to enable search.

Usage:
    python scripts/initial_index.py
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from myragdb.config import load_repositories_config
from myragdb.indexers.file_scanner import FileScanner
from myragdb.indexers.bm25_indexer import BM25Indexer
from myragdb.indexers.vector_indexer import VectorIndexer


def main():
    """
    Index all configured repositories.

    Business Purpose: Builds initial search indexes from all enabled
    repositories, making them searchable.
    """
    print("=" * 70)
    print("MyRAGDB Initial Indexing")
    print("=" * 70)
    print()

    # Load configuration
    print("Loading repository configuration...")
    try:
        repos_config = load_repositories_config()
        enabled_repos = repos_config.get_enabled_repositories()

        if not enabled_repos:
            print("Error: No enabled repositories found in config/repositories.yaml")
            return

        print(f"Found {len(enabled_repos)} enabled repositories:")
        for repo in enabled_repos:
            print(f"  - {repo.name}: {repo.path}")
        print()

    except Exception as e:
        print(f"Error loading configuration: {e}")
        return

    # Initialize indexers
    print("Initializing indexers...")
    try:
        bm25_indexer = BM25Indexer()
        vector_indexer = VectorIndexer()
        print("✓ BM25 indexer ready")
        print("✓ Vector indexer ready (model loaded)")
        print()

    except Exception as e:
        print(f"Error initializing indexers: {e}")
        return

    # Index each repository
    total_files = 0
    start_time = time.time()

    for repo in enabled_repos:
        print(f"Processing repository: {repo.name}")
        print("-" * 70)

        try:
            # Scan files
            print(f"Scanning files in {repo.path}...")
            scanner = FileScanner(repo)
            files = list(scanner.scan())

            if not files:
                print(f"  No files found matching patterns")
                print()
                continue

            print(f"  Found {len(files)} files")
            total_files += len(files)

            # Index with BM25
            print(f"  Indexing with BM25...")
            bm25_start = time.time()
            bm25_count = bm25_indexer.index_files(files, batch_size=100)
            bm25_time = time.time() - bm25_start
            print(f"  ✓ BM25 indexed {bm25_count} files in {bm25_time:.1f}s")

            # Index with vectors
            print(f"  Generating embeddings and indexing...")
            vector_start = time.time()
            vector_count = vector_indexer.index_files(files)
            vector_time = time.time() - vector_start
            print(f"  ✓ Vector indexed {vector_count} files in {vector_time:.1f}s")

            print()

        except Exception as e:
            print(f"  Error indexing repository: {e}")
            print()
            continue

    # Summary
    total_time = time.time() - start_time
    print("=" * 70)
    print("Indexing Complete!")
    print("=" * 70)
    print(f"Total files processed: {total_files}")
    print(f"Total time: {total_time:.1f}s")
    print()

    # Show statistics
    print("Index Statistics:")
    print(f"  BM25 documents: {bm25_indexer.get_document_count()}")
    print(f"  Vector chunks: {vector_indexer.get_document_count()}")
    print()

    print("Next steps:")
    print("  1. Start the server: python -m myragdb.api.server")
    print("  2. Try a search: python -m myragdb.cli search 'your query'")
    print("  3. Or use the Python client in your agent code")
    print()


if __name__ == "__main__":
    main()
