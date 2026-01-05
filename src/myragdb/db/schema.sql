-- File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/schema.sql
-- Description: SQLite schema for persistent file metadata tracking across server restarts
-- Author: Libor Ballaty <libor@arionetworks.com>
-- Created: 2026-01-05

-- File metadata tracking table
-- Purpose: Track which files have been indexed and when, to enable incremental indexing across restarts
CREATE TABLE IF NOT EXISTS file_metadata (
    file_path TEXT PRIMARY KEY,           -- Absolute path to file (unique identifier)
    repository TEXT NOT NULL,             -- Repository name this file belongs to
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

-- Index for fast lookup by last_indexed time (useful for cleanup/maintenance)
CREATE INDEX IF NOT EXISTS idx_last_indexed ON file_metadata(last_indexed);

-- Index for fast lookup by index_type
CREATE INDEX IF NOT EXISTS idx_index_type ON file_metadata(index_type);

-- Metadata version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL
);

-- Insert initial schema version
INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (1, strftime('%s', 'now'));
