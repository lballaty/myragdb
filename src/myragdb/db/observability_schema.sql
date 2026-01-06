-- File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/observability_schema.sql
-- Description: SQLite schema for observability metrics, errors, and performance tracking
-- Author: Libor Ballaty <libor@arionetworks.com>
-- Created: 2026-01-06

-- Search metrics tracking table
-- Purpose: Track all search operations with performance metrics for analysis
CREATE TABLE IF NOT EXISTS search_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,           -- Unix timestamp when search occurred
    query TEXT NOT NULL,                  -- The search query text
    search_type TEXT NOT NULL,            -- 'keyword', 'semantic', or 'hybrid'
    response_time_ms REAL NOT NULL,       -- Search duration in milliseconds
    result_count INTEGER NOT NULL,        -- Number of results returned
    repository TEXT,                      -- Optional repository filter applied
    user_agent TEXT,                      -- Optional user agent string
    source TEXT NOT NULL DEFAULT 'web_ui' -- 'web_ui', 'mcp_server', or 'cli'
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_search_timestamp ON search_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_search_type ON search_metrics(search_type);
CREATE INDEX IF NOT EXISTS idx_search_repository ON search_metrics(repository);

-- Error logging table
-- Purpose: Centralized error tracking for all components
CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,           -- Unix timestamp when error occurred
    error_type TEXT NOT NULL,             -- Error class name or type
    message TEXT NOT NULL,                -- Error message
    severity TEXT NOT NULL,               -- 'ERROR', 'WARNING', or 'CRITICAL'
    component TEXT NOT NULL,              -- Component where error occurred
    stack_trace TEXT,                     -- Optional full stack trace
    context TEXT,                         -- Optional JSON context (file paths, params, etc.)
    resolved INTEGER NOT NULL DEFAULT 0   -- 0 = unresolved, 1 = resolved
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_severity ON error_log(severity);
CREATE INDEX IF NOT EXISTS idx_error_component ON error_log(component);
CREATE INDEX IF NOT EXISTS idx_error_resolved ON error_log(resolved);

-- System metrics table
-- Purpose: Track system-level metrics like memory, disk, index sizes
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,           -- Unix timestamp when metric recorded
    metric_name TEXT NOT NULL,            -- Name of metric (e.g., 'memory_usage_mb')
    metric_value REAL NOT NULL,           -- Numeric value
    unit TEXT NOT NULL,                   -- Unit of measurement (e.g., 'MB', 'GB', 'count')
    category TEXT NOT NULL DEFAULT 'general' -- Metric category (e.g., 'memory', 'disk', 'index')
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metric_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_category ON system_metrics(category);

-- Indexing events table
-- Purpose: Audit trail of all indexing operations
CREATE TABLE IF NOT EXISTS indexing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,           -- Unix timestamp when event occurred
    repository TEXT NOT NULL,             -- Repository name
    event_type TEXT NOT NULL,             -- 'start', 'complete', 'error', 'cancelled'
    status TEXT NOT NULL,                 -- 'success', 'failed', 'in_progress'
    files_processed INTEGER DEFAULT 0,    -- Number of files processed
    duration_seconds REAL,                -- Operation duration (null for start events)
    error_message TEXT,                   -- Error message if failed
    metadata TEXT                         -- Optional JSON metadata (index_type, mode, etc.)
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_indexing_timestamp ON indexing_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_indexing_repository ON indexing_events(repository);
CREATE INDEX IF NOT EXISTS idx_indexing_status ON indexing_events(status);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS observability_schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL
);

-- Insert initial schema version
INSERT OR IGNORE INTO observability_schema_version (version, applied_at) VALUES (1, strftime('%s', 'now'));
