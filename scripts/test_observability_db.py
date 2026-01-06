#!/usr/bin/env python3
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/test_observability_db.py
# Description: Test script to verify observability database initialization and basic operations
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-06

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from myragdb.db.observability import ObservabilityDatabase


def test_database_creation():
    """Test database creation and schema initialization."""
    print("Testing observability database creation...")

    # Create database in test location
    test_db_path = 'data/test_observability.db'
    db = ObservabilityDatabase(test_db_path)

    print(f"✓ Database created at: {test_db_path}")
    return db


def test_search_metrics(db):
    """Test recording and retrieving search metrics."""
    print("\nTesting search metrics...")

    # Record some search operations
    db.record_search_metric(
        query='authentication flow',
        search_type='hybrid',
        response_time_ms=245.3,
        result_count=15,
        repository='myragdb',
        source='web_ui'
    )

    db.record_search_metric(
        query='vector indexing',
        search_type='semantic',
        response_time_ms=178.5,
        result_count=23,
        source='cli'
    )

    print("✓ Recorded 2 search metrics")

    # Retrieve metrics
    metrics = db.get_search_metrics(limit=10)
    print(f"✓ Retrieved {len(metrics)} search metrics")

    # Get statistics
    stats = db.get_search_statistics()
    print(f"✓ Search statistics:")
    print(f"  - Total searches: {stats['total_searches']}")
    print(f"  - Avg response time: {stats['avg_response_time_ms']:.2f}ms")


def test_error_logging(db):
    """Test recording and retrieving errors."""
    print("\nTesting error logging...")

    # Record some errors
    db.record_error(
        error_type='VectorIndexError',
        message='Failed to generate embedding for file',
        severity='ERROR',
        component='vector_indexer',
        context={'file_path': '/path/to/file.py', 'repository': 'myragdb'}
    )

    db.record_error(
        error_type='MeilisearchConnectionError',
        message='Connection timeout to Meilisearch server',
        severity='CRITICAL',
        component='keyword_indexer'
    )

    print("✓ Recorded 2 errors")

    # Retrieve errors
    errors = db.get_errors(limit=10)
    print(f"✓ Retrieved {len(errors)} errors")

    # Get statistics
    stats = db.get_error_statistics()
    print(f"✓ Error statistics:")
    print(f"  - Total errors: {stats['total_errors']}")
    print(f"  - By severity: {stats['by_severity']}")
    print(f"  - By component: {stats['by_component']}")


def test_system_metrics(db):
    """Test recording and retrieving system metrics."""
    print("\nTesting system metrics...")

    # Record some system metrics
    db.record_system_metric(
        metric_name='memory_usage_mb',
        metric_value=2048.5,
        unit='MB',
        category='memory'
    )

    db.record_system_metric(
        metric_name='keyword_index_size_mb',
        metric_value=156.3,
        unit='MB',
        category='index'
    )

    print("✓ Recorded 2 system metrics")

    # Retrieve metrics
    metrics = db.get_system_metrics(limit=10)
    print(f"✓ Retrieved {len(metrics)} system metrics")


def test_indexing_events(db):
    """Test recording and retrieving indexing events."""
    print("\nTesting indexing events...")

    # Record indexing events
    db.record_indexing_event(
        repository='myragdb',
        event_type='start',
        status='in_progress',
        metadata={'index_type': 'keyword', 'mode': 'incremental'}
    )

    time.sleep(0.1)  # Simulate indexing duration

    db.record_indexing_event(
        repository='myragdb',
        event_type='complete',
        status='success',
        files_processed=91,
        duration_seconds=2.45,
        metadata={'index_type': 'keyword', 'mode': 'incremental'}
    )

    print("✓ Recorded 2 indexing events")

    # Retrieve events
    events = db.get_indexing_events(repository='myragdb', limit=10)
    print(f"✓ Retrieved {len(events)} indexing events")


def test_database_info(db):
    """Test database size and cleanup operations."""
    print("\nTesting database info...")

    # Get database size
    info = db.get_database_size()
    print(f"✓ Database size: {info['size_mb']:.2f} MB")
    print(f"✓ Total rows: {info['total_rows']}")
    print(f"  Row counts: {info['row_counts']}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Observability Database Test Suite")
    print("=" * 60)

    try:
        # Test database creation
        db = test_database_creation()

        # Test all operations
        test_search_metrics(db)
        test_error_logging(db)
        test_system_metrics(db)
        test_indexing_events(db)
        test_database_info(db)

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
