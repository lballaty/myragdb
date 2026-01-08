-- Migration: Make repository column nullable to support directory-sourced files
-- File: src/myragdb/db/migrations/002_make_repository_nullable.sql
-- Description: Allow NULL values in repository column for directory-sourced files
-- Author: Libor Ballaty <libor@arionetworks.com>
-- Created: 2026-01-08

-- SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table
-- This is a safe operation that preserves all existing data

-- Step 1: Create new table with correct schema (repository nullable)
CREATE TABLE file_metadata_new (
    file_path TEXT PRIMARY KEY,
    repository TEXT,  -- Now nullable for directory-sourced files
    source_type TEXT DEFAULT 'repository',
    source_id TEXT,
    last_indexed INTEGER NOT NULL,
    last_modified INTEGER NOT NULL,
    content_hash TEXT,
    file_size INTEGER,
    index_type TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Step 2: Copy all data from old table to new table
INSERT INTO file_metadata_new
SELECT * FROM file_metadata;

-- Step 3: Drop old table
DROP TABLE file_metadata;

-- Step 4: Rename new table to original name
ALTER TABLE file_metadata_new RENAME TO file_metadata;

-- Step 5: Recreate index (if it exists)
CREATE INDEX IF NOT EXISTS idx_file_metadata_repository ON file_metadata(repository);
CREATE INDEX IF NOT EXISTS idx_file_metadata_source_type ON file_metadata(source_type);
CREATE INDEX IF NOT EXISTS idx_file_metadata_source_id ON file_metadata(source_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_index_type ON file_metadata(index_type);
