-- File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/schema.sql
-- Description: SQLite schema for persistent file metadata tracking across server restarts
-- Author: Libor Ballaty <libor@arionetworks.com>
-- Created: 2026-01-05

-- File metadata tracking table
-- Purpose: Track which files have been indexed and when, to enable incremental indexing across restarts
CREATE TABLE IF NOT EXISTS file_metadata (
    file_path TEXT PRIMARY KEY,           -- Absolute path to file (unique identifier)
    repository TEXT NOT NULL,             -- Repository name this file belongs to (for backward compat)
    source_type TEXT DEFAULT 'repository', -- 'repository' or 'directory'
    source_id TEXT,                       -- Repository name or directory ID string
    last_indexed INTEGER NOT NULL,        -- Unix timestamp when we last indexed this file
    last_modified INTEGER NOT NULL,       -- File's modification time (mtime) at index time
    content_hash TEXT,                    -- SHA256 hash of file content (optional, for deduplication)
    file_size INTEGER,                    -- File size in bytes
    index_type TEXT NOT NULL,             -- 'keyword', 'vector', or 'both'
    created_at INTEGER NOT NULL,          -- Unix timestamp when first indexed
    updated_at INTEGER NOT NULL           -- Unix timestamp when metadata last updated
);

-- Index for fast repository filtering
CREATE INDEX IF NOT EXISTS idx_repository ON file_metadata(repository);

-- Index for fast source filtering (directory or repository)
CREATE INDEX IF NOT EXISTS idx_source_id ON file_metadata(source_id);

-- Index for fast lookup by last_indexed time (useful for cleanup/maintenance)
CREATE INDEX IF NOT EXISTS idx_last_indexed ON file_metadata(last_indexed);

-- Index for fast lookup by index_type
CREATE INDEX IF NOT EXISTS idx_index_type ON file_metadata(index_type);

-- Repository indexing statistics tracking
-- Purpose: Track indexing performance and timing for each repository
CREATE TABLE IF NOT EXISTS repository_stats (
    repository TEXT NOT NULL,             -- Repository name
    index_type TEXT NOT NULL,             -- 'keyword' or 'vector'
    initial_index_time_seconds REAL,      -- How long the initial full index took (seconds)
    initial_index_timestamp INTEGER,      -- Unix timestamp when initial index completed
    last_reindex_time_seconds REAL,       -- How long the most recent reindex took (seconds)
    last_reindex_timestamp INTEGER,       -- Unix timestamp when last reindex completed
    total_files_indexed INTEGER,          -- Total number of files indexed
    total_size_bytes INTEGER,             -- Total size of all indexed files
    PRIMARY KEY (repository, index_type)
);

-- Index for fast repository lookup
CREATE INDEX IF NOT EXISTS idx_repo_stats_repository ON repository_stats(repository);

-- Global system metadata tracking
-- Purpose: Store system-wide statistics and state (replaces metadata.json)
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,                 -- Metadata key (e.g., 'last_index_time')
    value TEXT,                           -- Value (JSON-encoded for complex values)
    updated_at INTEGER NOT NULL           -- Unix timestamp of last update
);

-- Initialize default values
INSERT OR IGNORE INTO system_metadata (key, value, updated_at) VALUES ('last_index_time', NULL, strftime('%s', 'now'));
INSERT OR IGNORE INTO system_metadata (key, value, updated_at) VALUES ('total_searches', '0', strftime('%s', 'now'));
INSERT OR IGNORE INTO system_metadata (key, value, updated_at) VALUES ('total_search_time_ms', '0', strftime('%s', 'now'));

-- Metadata version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL
);

-- Insert initial schema version
INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (1, strftime('%s', 'now'));

-- ============================================================================
-- Directory Management Tables (NEW - Phase A)
-- ============================================================================

-- Non-repository directories for indexing
-- Purpose: Track arbitrary directories (outside git repos) that users want indexed
CREATE TABLE IF NOT EXISTS directories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,      -- Unique directory identifier
    path TEXT NOT NULL UNIQUE,                 -- Absolute directory path (must be unique)
    name TEXT NOT NULL,                        -- User-friendly name for the directory
    enabled BOOLEAN DEFAULT 1,                 -- Whether to include in search by default
    priority INTEGER DEFAULT 0,                -- Sort order in UI (higher = first)
    created_at INTEGER NOT NULL,               -- Unix timestamp when directory added
    updated_at INTEGER NOT NULL,               -- Unix timestamp when settings last updated
    last_indexed INTEGER,                      -- Unix timestamp when last indexed
    notes TEXT                                 -- Optional user notes about directory
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_directories_enabled ON directories(enabled);
CREATE INDEX IF NOT EXISTS idx_directories_priority ON directories(priority);

-- Directory indexing statistics tracking
-- Purpose: Track indexing performance for each directory (same format as repository_stats)
CREATE TABLE IF NOT EXISTS directory_stats (
    directory_id INTEGER NOT NULL,             -- Foreign key to directories.id
    index_type TEXT NOT NULL,                  -- 'keyword' or 'vector'
    initial_index_time_seconds REAL,           -- How long the initial full index took (seconds)
    initial_index_timestamp INTEGER,           -- Unix timestamp when initial index completed
    last_reindex_time_seconds REAL,            -- How long the most recent reindex took (seconds)
    last_reindex_timestamp INTEGER,            -- Unix timestamp when last reindex completed
    total_files_indexed INTEGER,               -- Total number of files indexed
    total_size_bytes INTEGER,                  -- Total size of all indexed files
    PRIMARY KEY (directory_id, index_type),
    FOREIGN KEY (directory_id) REFERENCES directories(id) ON DELETE CASCADE
);

-- Index for fast directory lookup
CREATE INDEX IF NOT EXISTS idx_directory_stats_directory_id ON directory_stats(directory_id);
