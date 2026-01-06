# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/observability.py
# Description: SQLite database for observability metrics, errors, and performance tracking
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-06

import sqlite3
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timedelta


class ObservabilityDatabase:
    """
    Persistent storage for observability metrics, errors, and performance data.

    Business Purpose: Enables system monitoring, error tracking, and performance
    analysis over time. Provides data for visualizations and alerts to help
    identify issues before they impact users.

    Example:
        db = ObservabilityDatabase('data/observability.db')

        # Record search operation
        db.record_search_metric(
            query='authentication flow',
            search_type='hybrid',
            response_time_ms=245.3,
            result_count=15,
            repository='myragdb'
        )

        # Record error
        db.record_error(
            error_type='VectorIndexError',
            message='Failed to generate embedding',
            severity='ERROR',
            component='vector_indexer'
        )
    """

    def __init__(self, db_path: str = 'data/observability.db'):
        """
        Initialize observability database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """
        Create database and tables if they don't exist.

        Business Purpose: Initializes database schema on first run.
        """
        # Ensure data directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Read schema SQL
        schema_path = Path(__file__).parent / 'observability_schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute schema
        with self._get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Business Purpose: Ensures connections are properly closed and
        handles transaction management.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
        finally:
            conn.close()

    # ====================
    # Search Metrics
    # ====================

    def record_search_metric(
        self,
        query: str,
        search_type: str,
        response_time_ms: float,
        result_count: int,
        repository: Optional[str] = None,
        user_agent: Optional[str] = None,
        source: str = 'web_ui'
    ) -> None:
        """
        Record a search operation with its performance metrics.

        Business Purpose: Tracks search performance over time to identify
        slow queries, popular search terms, and usage patterns.

        Args:
            query: The search query text
            search_type: 'keyword', 'semantic', or 'hybrid'
            response_time_ms: Search duration in milliseconds
            result_count: Number of results returned
            repository: Optional repository filter used
            user_agent: Optional user agent string
            source: 'web_ui', 'mcp_server', or 'cli'

        Example:
            db.record_search_metric(
                query='authentication flow',
                search_type='hybrid',
                response_time_ms=245.3,
                result_count=15,
                repository='myragdb'
            )
        """
        now = int(time.time())

        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO search_metrics (
                    timestamp, query, search_type, response_time_ms,
                    result_count, repository, user_agent, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now, query, search_type, response_time_ms,
                result_count, repository, user_agent, source
            ))
            conn.commit()

    def get_search_metrics(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        search_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get search metrics within a time range.

        Args:
            start_time: Unix timestamp for start of range (optional)
            end_time: Unix timestamp for end of range (optional)
            search_type: Filter by search type (optional)
            limit: Maximum number of records to return

        Returns:
            List of search metric dictionaries

        Example:
            # Get last 24 hours of hybrid searches
            yesterday = int(time.time()) - 86400
            metrics = db.get_search_metrics(
                start_time=yesterday,
                search_type='hybrid'
            )
        """
        with self._get_connection() as conn:
            query = 'SELECT * FROM search_metrics WHERE 1=1'
            params = []

            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)

            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)

            if search_type is not None:
                query += ' AND search_type = ?'
                params.append(search_type)

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_search_statistics(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated search statistics.

        Business Purpose: Provides high-level metrics for dashboards showing
        search volume, average response time, and performance trends.

        Args:
            start_time: Unix timestamp for start of range (optional)
            end_time: Unix timestamp for end of range (optional)

        Returns:
            Dictionary with aggregated statistics

        Example:
            stats = db.get_search_statistics()
            print(f"Total searches: {stats['total_searches']}")
            print(f"Avg response time: {stats['avg_response_time_ms']:.2f}ms")
        """
        with self._get_connection() as conn:
            query = '''
                SELECT
                    COUNT(*) as total_searches,
                    AVG(response_time_ms) as avg_response_time_ms,
                    MIN(response_time_ms) as min_response_time_ms,
                    MAX(response_time_ms) as max_response_time_ms,
                    SUM(result_count) as total_results,
                    AVG(result_count) as avg_results_per_search
                FROM search_metrics
                WHERE 1=1
            '''
            params = []

            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)

            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)

            cursor = conn.execute(query, params)
            row = cursor.fetchone()

            if row:
                return dict(row)
            else:
                return {
                    'total_searches': 0,
                    'avg_response_time_ms': 0,
                    'min_response_time_ms': 0,
                    'max_response_time_ms': 0,
                    'total_results': 0,
                    'avg_results_per_search': 0
                }

    # ====================
    # Error Logging
    # ====================

    def record_error(
        self,
        error_type: str,
        message: str,
        severity: str,
        component: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an error or exception.

        Business Purpose: Centralized error tracking enables rapid identification
        of recurring issues and their root causes, improving system reliability.

        Args:
            error_type: Error class name or type
            message: Error message
            severity: 'ERROR', 'WARNING', or 'CRITICAL'
            component: Component where error occurred (e.g., 'vector_indexer', 'search_engine')
            stack_trace: Optional full stack trace
            context: Optional additional context as dict

        Example:
            db.record_error(
                error_type='VectorIndexError',
                message='Failed to generate embedding for file: /path/to/file.py',
                severity='ERROR',
                component='vector_indexer',
                context={'file_path': '/path/to/file.py', 'repository': 'myragdb'}
            )
        """
        now = int(time.time())
        context_json = json.dumps(context) if context else None

        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO error_log (
                    timestamp, error_type, message, severity,
                    component, stack_trace, context, resolved
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                now, error_type, message, severity,
                component, stack_trace, context_json
            ))
            conn.commit()

    def get_errors(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        severity: Optional[str] = None,
        component: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get errors within a time range.

        Args:
            start_time: Unix timestamp for start of range (optional)
            end_time: Unix timestamp for end of range (optional)
            severity: Filter by severity level (optional)
            component: Filter by component (optional)
            resolved: Filter by resolved status (optional)
            limit: Maximum number of records to return

        Returns:
            List of error dictionaries

        Example:
            # Get unresolved errors from last hour
            hour_ago = int(time.time()) - 3600
            errors = db.get_errors(
                start_time=hour_ago,
                resolved=False
            )
        """
        with self._get_connection() as conn:
            query = 'SELECT * FROM error_log WHERE 1=1'
            params = []

            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)

            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)

            if severity is not None:
                query += ' AND severity = ?'
                params.append(severity)

            if component is not None:
                query += ' AND component = ?'
                params.append(component)

            if resolved is not None:
                query += ' AND resolved = ?'
                params.append(1 if resolved else 0)

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor = conn.execute(query, params)
            results = []
            for row in cursor.fetchall():
                error_dict = dict(row)
                # Parse context JSON if present
                if error_dict.get('context'):
                    try:
                        error_dict['context'] = json.loads(error_dict['context'])
                    except json.JSONDecodeError:
                        pass
                results.append(error_dict)

            return results

    def mark_error_resolved(self, error_id: int) -> None:
        """
        Mark an error as resolved.

        Args:
            error_id: The error's database ID
        """
        with self._get_connection() as conn:
            conn.execute(
                'UPDATE error_log SET resolved = 1 WHERE id = ?',
                (error_id,)
            )
            conn.commit()

    def get_error_statistics(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated error statistics.

        Business Purpose: Provides high-level error metrics for dashboards,
        showing error rates by severity and component.

        Returns:
            Dictionary with error counts by severity and component

        Example:
            stats = db.get_error_statistics()
            print(f"Total errors: {stats['total_errors']}")
            print(f"By severity: {stats['by_severity']}")
        """
        with self._get_connection() as conn:
            # Total errors
            query = 'SELECT COUNT(*) as count FROM error_log WHERE 1=1'
            params = []

            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)

            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)

            cursor = conn.execute(query, params)
            total_errors = cursor.fetchone()['count']

            # By severity
            query = 'SELECT severity, COUNT(*) as count FROM error_log WHERE 1=1'
            params_copy = []

            if start_time is not None:
                query += ' AND timestamp >= ?'
                params_copy.append(start_time)

            if end_time is not None:
                query += ' AND timestamp <= ?'
                params_copy.append(end_time)

            query += ' GROUP BY severity'
            cursor = conn.execute(query, params_copy)
            by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}

            # By component
            query = 'SELECT component, COUNT(*) as count FROM error_log WHERE 1=1'
            params_copy = []

            if start_time is not None:
                query += ' AND timestamp >= ?'
                params_copy.append(start_time)

            if end_time is not None:
                query += ' AND timestamp <= ?'
                params_copy.append(end_time)

            query += ' GROUP BY component'
            cursor = conn.execute(query, params_copy)
            by_component = {row['component']: row['count'] for row in cursor.fetchall()}

            return {
                'total_errors': total_errors,
                'by_severity': by_severity,
                'by_component': by_component
            }

    # ====================
    # System Metrics
    # ====================

    def record_system_metric(
        self,
        metric_name: str,
        metric_value: float,
        unit: str,
        category: str = 'general'
    ) -> None:
        """
        Record a system-level metric.

        Business Purpose: Tracks system health metrics like memory usage,
        disk space, and index sizes over time.

        Args:
            metric_name: Name of the metric (e.g., 'memory_usage_mb', 'disk_space_gb')
            metric_value: Numeric value of the metric
            unit: Unit of measurement (e.g., 'MB', 'GB', 'count')
            category: Metric category (e.g., 'memory', 'disk', 'index')

        Example:
            db.record_system_metric(
                metric_name='memory_usage_mb',
                metric_value=2048.5,
                unit='MB',
                category='memory'
            )
        """
        now = int(time.time())

        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO system_metrics (
                    timestamp, metric_name, metric_value, unit, category
                )
                VALUES (?, ?, ?, ?, ?)
            ''', (now, metric_name, metric_value, unit, category))
            conn.commit()

    def get_system_metrics(
        self,
        metric_name: Optional[str] = None,
        category: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get system metrics within a time range.

        Args:
            metric_name: Filter by metric name (optional)
            category: Filter by category (optional)
            start_time: Unix timestamp for start of range (optional)
            end_time: Unix timestamp for end of range (optional)
            limit: Maximum number of records to return

        Returns:
            List of metric dictionaries

        Example:
            # Get memory usage for last hour
            hour_ago = int(time.time()) - 3600
            metrics = db.get_system_metrics(
                metric_name='memory_usage_mb',
                start_time=hour_ago
            )
        """
        with self._get_connection() as conn:
            query = 'SELECT * FROM system_metrics WHERE 1=1'
            params = []

            if metric_name is not None:
                query += ' AND metric_name = ?'
                params.append(metric_name)

            if category is not None:
                query += ' AND category = ?'
                params.append(category)

            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)

            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ====================
    # Indexing Events
    # ====================

    def record_indexing_event(
        self,
        repository: str,
        event_type: str,
        status: str,
        files_processed: int = 0,
        duration_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an indexing event.

        Business Purpose: Tracks indexing operations to monitor performance,
        identify failures, and provide audit trail.

        Args:
            repository: Repository name
            event_type: 'start', 'complete', 'error', 'cancelled'
            status: 'success', 'failed', 'in_progress'
            files_processed: Number of files processed
            duration_seconds: Operation duration (optional)
            error_message: Error message if failed (optional)
            metadata: Additional context as dict (optional)

        Example:
            db.record_indexing_event(
                repository='myragdb',
                event_type='complete',
                status='success',
                files_processed=91,
                duration_seconds=2.45,
                metadata={'index_type': 'keyword', 'mode': 'incremental'}
            )
        """
        now = int(time.time())
        metadata_json = json.dumps(metadata) if metadata else None

        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO indexing_events (
                    timestamp, repository, event_type, status,
                    files_processed, duration_seconds, error_message, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now, repository, event_type, status,
                files_processed, duration_seconds, error_message, metadata_json
            ))
            conn.commit()

    def get_indexing_events(
        self,
        repository: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get indexing events within a time range.

        Args:
            repository: Filter by repository (optional)
            event_type: Filter by event type (optional)
            status: Filter by status (optional)
            start_time: Unix timestamp for start of range (optional)
            end_time: Unix timestamp for end of range (optional)
            limit: Maximum number of records to return

        Returns:
            List of event dictionaries

        Example:
            # Get failed indexing events
            events = db.get_indexing_events(
                status='failed',
                limit=50
            )
        """
        with self._get_connection() as conn:
            query = 'SELECT * FROM indexing_events WHERE 1=1'
            params = []

            if repository is not None:
                query += ' AND repository = ?'
                params.append(repository)

            if event_type is not None:
                query += ' AND event_type = ?'
                params.append(event_type)

            if status is not None:
                query += ' AND status = ?'
                params.append(status)

            if start_time is not None:
                query += ' AND timestamp >= ?'
                params.append(start_time)

            if end_time is not None:
                query += ' AND timestamp <= ?'
                params.append(end_time)

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor = conn.execute(query, params)
            results = []
            for row in cursor.fetchall():
                event_dict = dict(row)
                # Parse metadata JSON if present
                if event_dict.get('metadata'):
                    try:
                        event_dict['metadata'] = json.loads(event_dict['metadata'])
                    except json.JSONDecodeError:
                        pass
                results.append(event_dict)

            return results

    # ====================
    # Data Retention
    # ====================

    def cleanup_old_data(self, retention_days: int = 30) -> Dict[str, int]:
        """
        Remove data older than specified retention period.

        Business Purpose: Prevents database from growing unbounded by
        removing old metrics while preserving recent data for analysis.

        Args:
            retention_days: Number of days to retain data

        Returns:
            Dictionary with counts of deleted records per table

        Example:
            # Keep only last 30 days of data
            deleted = db.cleanup_old_data(retention_days=30)
            print(f"Deleted {deleted['search_metrics']} old search metrics")
        """
        cutoff_time = int(time.time()) - (retention_days * 86400)

        with self._get_connection() as conn:
            # Clean up search metrics
            cursor = conn.execute(
                'DELETE FROM search_metrics WHERE timestamp < ?',
                (cutoff_time,)
            )
            search_deleted = cursor.rowcount

            # Clean up resolved errors (keep unresolved indefinitely)
            cursor = conn.execute(
                'DELETE FROM error_log WHERE timestamp < ? AND resolved = 1',
                (cutoff_time,)
            )
            errors_deleted = cursor.rowcount

            # Clean up system metrics
            cursor = conn.execute(
                'DELETE FROM system_metrics WHERE timestamp < ?',
                (cutoff_time,)
            )
            metrics_deleted = cursor.rowcount

            # Clean up indexing events
            cursor = conn.execute(
                'DELETE FROM indexing_events WHERE timestamp < ?',
                (cutoff_time,)
            )
            events_deleted = cursor.rowcount

            conn.commit()

            return {
                'search_metrics': search_deleted,
                'error_log': errors_deleted,
                'system_metrics': metrics_deleted,
                'indexing_events': events_deleted
            }

    def get_database_size(self) -> Dict[str, Any]:
        """
        Get database file size and row counts.

        Business Purpose: Monitors database growth to ensure cleanup
        policies are working and storage is not becoming a problem.

        Returns:
            Dictionary with file size and row counts

        Example:
            info = db.get_database_size()
            print(f"Database size: {info['size_mb']:.2f} MB")
            print(f"Total rows: {info['total_rows']}")
        """
        # Get file size
        db_path = Path(self.db_path)
        size_bytes = db_path.stat().st_size if db_path.exists() else 0
        size_mb = size_bytes / (1024 * 1024)

        # Get row counts
        with self._get_connection() as conn:
            tables = ['search_metrics', 'error_log', 'system_metrics', 'indexing_events']
            row_counts = {}
            total_rows = 0

            for table in tables:
                cursor = conn.execute(f'SELECT COUNT(*) as count FROM {table}')
                count = cursor.fetchone()['count']
                row_counts[table] = count
                total_rows += count

            return {
                'size_bytes': size_bytes,
                'size_mb': size_mb,
                'total_rows': total_rows,
                'row_counts': row_counts
            }
