-- File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/migrations/001_add_directories_table.sql
-- Description: Database migration to add non-repository directory indexing support
-- Author: Libor Ballaty <libor@arionetworks.com>
-- Created: 2026-01-07

-- Migration Version: 2
-- Purpose: Add directories table and extend file_metadata to track both repositories and directories

-- Directories table: Track managed non-repository directories
-- Purpose: Persistent storage of user-added directories with metadata and indexing status
CREATE TABLE IF NOT EXISTS directories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,                 -- Absolute directory path (must be unique)
    name TEXT NOT NULL,                        -- User-friendly name for the directory
    enabled BOOLEAN NOT NULL DEFAULT 1,        -- Include in search? (0=disabled, 1=enabled)
    priority INTEGER NOT NULL DEFAULT 0,       -- Sort order in UI (higher = appears first)
    created_at INTEGER NOT NULL,               -- Unix timestamp when directory was added
    updated_at INTEGER NOT NULL,               -- Unix timestamp when record was last updated
    last_indexed INTEGER,                      -- Unix timestamp of last index (nullable = never indexed)
    notes TEXT                                 -- Optional user notes about this directory
);

-- Create indexes for fast lookups
-- Index on path: Used when checking if directory exists
CREATE INDEX IF NOT EXISTS idx_directories_path ON directories(path);

-- Index on enabled: Used when querying only enabled directories for search
CREATE INDEX IF NOT EXISTS idx_directories_enabled ON directories(enabled);

-- Index on created_at: Used for sorting by creation date
CREATE INDEX IF NOT EXISTS idx_directories_created_at ON directories(created_at);

-- Directory statistics table: Track indexing performance and size metrics per directory
-- Purpose: Store stats about how many files indexed, total size, indexing time
CREATE TABLE IF NOT EXISTS directory_stats (
    directory_id INTEGER NOT NULL,             -- Foreign key to directories table
    index_type TEXT NOT NULL,                  -- Type of index: 'keyword' or 'vector'
    total_files_indexed INTEGER NOT NULL DEFAULT 0,
                                               -- Total number of files indexed in this directory
    total_size_bytes INTEGER NOT NULL DEFAULT 0,
                                               -- Total size of all indexed files (bytes)
    initial_index_time_seconds REAL,           -- How long initial full index took (seconds)
    initial_index_timestamp INTEGER,           -- Unix timestamp when initial index completed
    last_reindex_time_seconds REAL,            -- How long most recent reindex took (seconds)
    last_reindex_timestamp INTEGER,            -- Unix timestamp when last reindex completed
    PRIMARY KEY (directory_id, index_type),
    FOREIGN KEY (directory_id) REFERENCES directories(id) ON DELETE CASCADE
);

-- Create index for fast directory lookup in stats
CREATE INDEX IF NOT EXISTS idx_directory_stats_directory_id ON directory_stats(directory_id);

-- Extend existing file_metadata table to support both repositories and directories
-- Add column: source_type - distinguishes whether file comes from repository or directory
-- Add column: source_id - either repository name (string) or directory_id (as string)
-- Business Logic:
--   - For existing files: source_type='repository', source_id=repository name
--   - For new directory files: source_type='directory', source_id=directory_id (as text)

ALTER TABLE file_metadata ADD COLUMN source_type TEXT DEFAULT 'repository';
ALTER TABLE file_metadata ADD COLUMN source_id TEXT;

-- Create composite index for fast filtering by source
-- Used when searching: "only results from these directories" or "only results from these repos"
CREATE INDEX IF NOT EXISTS idx_file_source ON file_metadata(source_type, source_id);

-- Update system_metadata to track schema version
-- Note: schema_version table is handled separately, this is for reference
UPDATE system_metadata SET value = '2', updated_at = strftime('%s', 'now')
WHERE key = 'schema_version';

-- Insert initial schema version if not exists
INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (2, strftime('%s', 'now'));
