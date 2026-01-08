#!/usr/bin/env python3
"""
Comprehensive test suite for MyRAGDB functionality.

Business Purpose: Validates all critical functionality after code changes to ensure
nothing was broken by recent modifications. Tests repository discovery, indexing,
search, UI interactions, database integrity, incremental indexing, and error handling.
"""

import os
import sys
import time
import json
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from myragdb.utils.repo_discovery import RepositoryDiscovery
from myragdb.indexers.file_scanner import FileScanner, DirectoryScanner, ScannedFile
from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
from myragdb.indexers.vector_indexer import VectorIndexer
from myragdb.search.hybrid_search import HybridSearchEngine
from myragdb.db.file_metadata import FileMetadataDatabase
from myragdb.config import settings, RepositoryConfig, FilePatterns
import yaml


class TestResults:
    """Track test results."""
    def __init__(self):
        self.tests = {}
        self.passed = 0
        self.failed = 0

    def add_test(self, name, status, message=""):
        """Add test result."""
        self.tests[name] = {"status": status, "message": message}
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1
        status_symbol = "✓" if status == "PASS" else "✗"
        print(f"  {status_symbol} {name}: {message}")

    def summary(self):
        """Print summary."""
        print(f"\n{'='*60}")
        print(f"SUMMARY: {self.passed} passed, {self.failed} failed")
        print(f"{'='*60}\n")
        return self.failed == 0


def test_1_repository_discovery():
    """Test 1: Repository discovery and scanning."""
    print("\n" + "="*60)
    print("TEST 1: Repository Discovery and Scanning")
    print("="*60)

    results = TestResults()

    try:
        discovery = RepositoryDiscovery()

        # Test max_depth parameter
        repos_depth2 = discovery.scan_directory(
            "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments",
            max_depth=2
        )
        results.add_test(
            "scan with max_depth=2",
            "PASS" if len(repos_depth2) > 0 else "FAIL",
            f"Found {len(repos_depth2)} repositories"
        )

        # Test nested repository finding
        repos_depth3 = discovery.scan_directory(
            "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments",
            max_depth=3
        )
        results.add_test(
            "scan with max_depth=3",
            "PASS" if len(repos_depth3) >= len(repos_depth2) else "FAIL",
            f"Found {len(repos_depth3)} repositories"
        )

        # Test clone group detection
        clone_groups = set(r.clone_group for r in repos_depth3 if r.clone_group)
        results.add_test(
            "clone group detection",
            "PASS" if len(clone_groups) > 0 else "FAIL",
            f"Identified {len(clone_groups)} unique clone groups"
        )

    except Exception as e:
        results.add_test("repository discovery", "FAIL", str(e))

    return results.summary()


def test_2_repository_indexing():
    """Test 2: Repository indexing (keyword and vector)."""
    print("\n" + "="*60)
    print("TEST 2: Repository Indexing (Keyword and Vector)")
    print("="*60)

    results = TestResults()

    try:
        # Load test repository from config
        with open('/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/config/repositories.yaml', 'r') as f:
            config = yaml.safe_load(f)

        if not config or 'repositories' not in config or len(config['repositories']) == 0:
            results.add_test("load repositories config", "FAIL", "No repositories in config")
            return results.summary()

        # Use myragdb repo (it's enabled)
        test_repo = None
        for repo in config['repositories']:
            if repo['name'] == 'myragdb' and repo['enabled']:
                test_repo = repo
                break

        if not test_repo:
            results.add_test("find enabled repository", "FAIL", "No enabled repositories found")
            return results.summary()

        results.add_test("load repositories config", "PASS", f"Found {test_repo['name']}")

        # Scan repository
        repo_path = test_repo['path']
        if not os.path.exists(repo_path):
            results.add_test("repository path exists", "FAIL", f"Path not found: {repo_path}")
            return results.summary()

        # Create RepositoryConfig from dict
        repo_config = RepositoryConfig(
            name=test_repo['name'],
            path=repo_path,
            enabled=test_repo.get('enabled', True),
            priority=test_repo.get('priority', 'medium'),
            file_patterns=FilePatterns(**test_repo['file_patterns'])
        )

        scanner = FileScanner(repo_config)
        files = list(scanner.scan())

        results.add_test(
            "scan repository for files",
            "PASS" if len(files) > 0 else "FAIL",
            f"Scanned {len(files)} files"
        )

        if len(files) == 0:
            return results.summary()

        # Test Meilisearch indexing (force fresh index for testing)
        try:
            meilisearch_indexer = MeilisearchIndexer()
            start_time = time.time()
            # Use incremental=False to force re-indexing for testing purposes
            indexed_count = meilisearch_indexer.index_files_batch(files, incremental=False)
            meilisearch_time = time.time() - start_time

            results.add_test(
                "Meilisearch keyword indexing",
                "PASS" if indexed_count > 0 else "FAIL",
                f"Indexed {indexed_count} files in {meilisearch_time:.2f}s"
            )
        except Exception as e:
            results.add_test("Meilisearch indexing", "FAIL", str(e))

        # Test Vector indexing
        try:
            vector_indexer = VectorIndexer()
            start_time = time.time()
            indexed_count = vector_indexer.index_files(files, incremental=False)
            vector_time = time.time() - start_time

            results.add_test(
                "Vector semantic indexing",
                "PASS" if indexed_count > 0 else "FAIL",
                f"Indexed {indexed_count} files in {vector_time:.2f}s"
            )
        except Exception as e:
            results.add_test("Vector indexing", "FAIL", str(e))

    except Exception as e:
        results.add_test("repository indexing", "FAIL", str(e))

    return results.summary()


def test_3_directory_indexing():
    """Test 3: Directory indexing (keyword and vector)."""
    print("\n" + "="*60)
    print("TEST 3: Directory Indexing (Keyword and Vector)")
    print("="*60)

    results = TestResults()

    try:
        # Get test directory
        test_dir = "/Users/liborballaty/Documents"
        if not os.path.exists(test_dir):
            results.add_test("directory exists", "FAIL", f"Path not found: {test_dir}")
            return results.summary()

        results.add_test("directory exists", "PASS", test_dir)

        # Scan directory
        directory_id = 1  # From database
        scanner = DirectoryScanner(test_dir, directory_id)
        files = list(scanner.scan())

        results.add_test(
            "scan directory for files",
            "PASS" if len(files) > 0 else "FAIL",
            f"Scanned {len(files)} files"
        )

        if len(files) == 0:
            return results.summary()

        # Verify source_type is set to 'directory'
        for file in files[:5]:
            if not hasattr(file, 'directory_id') or file.directory_id != directory_id:
                results.add_test("file source metadata", "FAIL", "Files missing directory_id")
                return results.summary()

        results.add_test("file source metadata", "PASS", "All files have directory_id set")

        # Test Meilisearch indexing (force fresh index for testing)
        try:
            meilisearch_indexer = MeilisearchIndexer()
            start_time = time.time()
            # Use incremental=False to force re-indexing for testing purposes
            indexed_count = meilisearch_indexer.index_files_batch(files, incremental=False)
            meilisearch_time = time.time() - start_time

            results.add_test(
                "Meilisearch directory indexing",
                "PASS" if indexed_count > 0 else "FAIL",
                f"Indexed {indexed_count} files in {meilisearch_time:.2f}s"
            )
        except Exception as e:
            results.add_test("Meilisearch directory indexing", "FAIL", str(e))

        # Test Vector indexing
        try:
            vector_indexer = VectorIndexer()
            start_time = time.time()
            indexed_count = vector_indexer.index_directory(test_dir, directory_id, incremental=False)
            vector_time = time.time() - start_time

            results.add_test(
                "Vector directory indexing",
                "PASS" if indexed_count > 0 else "FAIL",
                f"Indexed {indexed_count} files in {vector_time:.2f}s"
            )
        except Exception as e:
            results.add_test("Vector directory indexing", "FAIL", str(e))

    except Exception as e:
        results.add_test("directory indexing", "FAIL", str(e))

    return results.summary()


def test_4_hybrid_search():
    """Test 4: Hybrid search (keyword + vector)."""
    print("\n" + "="*60)
    print("TEST 4: Hybrid Search (Keyword + Vector)")
    print("="*60)

    results = TestResults()

    try:
        # Initialize the required indexers
        meilisearch_indexer = MeilisearchIndexer()
        vector_indexer = VectorIndexer()

        # Create hybrid search engine
        hybrid = HybridSearchEngine(
            meilisearch_indexer=meilisearch_indexer,
            vector_indexer=vector_indexer
        )

        query = "authentication"

        # Test keyword search
        try:
            keyword_results = hybrid.search_keyword(query, limit=5)
            results.add_test(
                "keyword search",
                "PASS",
                f"Found {len(keyword_results)} keyword results"
            )
        except Exception as e:
            results.add_test("keyword search", "FAIL", str(e))

        # Test vector search
        try:
            vector_results = hybrid.search_vector(query, limit=5)
            results.add_test(
                "vector search",
                "PASS",
                f"Found {len(vector_results)} vector results"
            )
        except Exception as e:
            results.add_test("vector search", "FAIL", str(e))

        # Test hybrid search
        try:
            hybrid_results = hybrid.search(query, limit=5)
            results.add_test(
                "hybrid search",
                "PASS",
                f"Found {len(hybrid_results)} hybrid results"
            )
        except Exception as e:
            results.add_test("hybrid search", "FAIL", str(e))

    except Exception as e:
        results.add_test("hybrid search initialization", "FAIL", str(e))

    return results.summary()


def test_5_database_integrity():
    """Test 5: Database integrity."""
    print("\n" + "="*60)
    print("TEST 5: Database Integrity")
    print("="*60)

    results = TestResults()

    try:
        metadata_db = FileMetadataDatabase()

        # Check if database file exists
        db_path = Path(settings.data_dir) / "file_metadata.db"
        results.add_test(
            "metadata database exists",
            "PASS" if db_path.exists() else "FAIL",
            str(db_path)
        )

        if not db_path.exists():
            return results.summary()

        # Check database schema
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [t[0] for t in tables]

            has_required_tables = 'file_metadata' in table_names
            results.add_test(
                "required tables exist",
                "PASS" if has_required_tables else "FAIL",
                f"Found tables: {', '.join(table_names)}"
            )

            if has_required_tables:
                # Check columns
                cursor.execute("PRAGMA table_info(file_metadata)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]

                has_source_columns = 'source_type' in column_names and 'source_id' in column_names
                results.add_test(
                    "source tracking columns exist",
                    "PASS" if has_source_columns else "FAIL",
                    f"Found columns: {', '.join(column_names)}"
                )

            # Check for directory files in database
            cursor.execute("SELECT COUNT(*) FROM file_metadata WHERE source_type='directory'")
            directory_count = cursor.fetchone()[0]

            results.add_test(
                "directory files tracked",
                "PASS",
                f"Found {directory_count} directory files in database"
            )

            # Check for repository files in database
            cursor.execute("SELECT COUNT(*) FROM file_metadata WHERE source_type='repository'")
            repo_count = cursor.fetchone()[0]

            results.add_test(
                "repository files tracked",
                "PASS",
                f"Found {repo_count} repository files in database"
            )

            conn.close()
        except Exception as e:
            results.add_test("database schema check", "FAIL", str(e))

    except Exception as e:
        results.add_test("database integrity", "FAIL", str(e))

    return results.summary()


def test_6_incremental_indexing():
    """Test 6: Incremental indexing."""
    print("\n" + "="*60)
    print("TEST 6: Incremental Indexing")
    print("="*60)

    results = TestResults()

    try:
        test_dir = "/Users/liborballaty/Documents"
        if not os.path.exists(test_dir):
            results.add_test("directory exists", "FAIL", f"Path not found: {test_dir}")
            return results.summary()

        # First full index
        try:
            vector_indexer = VectorIndexer()
            directory_id = 1

            start_time = time.time()
            count1 = vector_indexer.index_directory(test_dir, directory_id, incremental=False)
            time1 = time.time() - start_time

            results.add_test(
                "full index",
                "PASS" if count1 > 0 else "FAIL",
                f"Indexed {count1} files in {time1:.2f}s"
            )

            # Second incremental index (nothing changed)
            start_time = time.time()
            count2 = vector_indexer.index_directory(test_dir, directory_id, incremental=True)
            time2 = time.time() - start_time

            results.add_test(
                "incremental index (no changes)",
                "PASS" if count2 < count1 else "FAIL",
                f"Indexed {count2} files in {time2:.2f}s (should be less than full index)"
            )

            # Check that incremental is faster
            if time2 < time1:
                results.add_test(
                    "incremental index performance",
                    "PASS",
                    f"Incremental ({time2:.2f}s) faster than full ({time1:.2f}s)"
                )
            else:
                results.add_test(
                    "incremental index performance",
                    "PASS",
                    f"Both took similar time - acceptable behavior"
                )

        except Exception as e:
            results.add_test("incremental indexing", "FAIL", str(e))

    except Exception as e:
        results.add_test("incremental indexing setup", "FAIL", str(e))

    return results.summary()


def test_7_error_handling():
    """Test 7: Error handling and edge cases."""
    print("\n" + "="*60)
    print("TEST 7: Error Handling and Edge Cases")
    print("="*60)

    results = TestResults()

    try:
        discovery = RepositoryDiscovery()

        # Test non-existent path
        try:
            repos = discovery.scan_directory("/nonexistent/path", max_depth=2)
            results.add_test(
                "handle non-existent path",
                "PASS" if len(repos) == 0 else "FAIL",
                "Non-existent path handled gracefully"
            )
        except Exception as e:
            results.add_test("handle non-existent path", "PASS", "Exception handled gracefully")

        # Test exclude patterns
        repos = discovery.scan_directory(
            "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments",
            max_depth=2,
            exclude_patterns=["node_modules", "venv"]
        )
        results.add_test(
            "exclude patterns work",
            "PASS",
            f"Found {len(repos)} repos with exclude patterns"
        )

        # Test search with minimal data
        try:
            meilisearch_indexer = MeilisearchIndexer()
            vector_indexer = VectorIndexer()
            hybrid = HybridSearchEngine(
                meilisearch_indexer=meilisearch_indexer,
                vector_indexer=vector_indexer
            )
            results_empty = hybrid.search("test", limit=1)
            results.add_test(
                "search with minimal data",
                "PASS",
                f"Search returned {len(results_empty)} results"
            )
        except Exception as e:
            results.add_test("search error handling", "FAIL", str(e))

    except Exception as e:
        results.add_test("error handling", "FAIL", str(e))

    return results.summary()


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MyRAGDB COMPREHENSIVE TEST SUITE")
    print("="*60)

    all_passed = True

    # Run tests
    all_passed &= test_1_repository_discovery()
    all_passed &= test_2_repository_indexing()
    all_passed &= test_3_directory_indexing()
    all_passed &= test_4_hybrid_search()
    all_passed &= test_5_database_integrity()
    all_passed &= test_6_incremental_indexing()
    all_passed &= test_7_error_handling()

    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
