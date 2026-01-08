-- File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/db/migrations/003_add_llm_provider_config.sql
-- Description: Add LLM provider configuration persistence across browsers and restarts
-- Author: Libor Ballaty <libor@arionetworks.com>
-- Created: 2026-01-08

-- LLM provider configuration storage
-- Purpose: Persist user's selected cloud LLM provider across browser sessions and server restarts
CREATE TABLE IF NOT EXISTS llm_provider_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,         -- Primary key
    provider_name TEXT NOT NULL UNIQUE,           -- Provider identifier (e.g., 'claude', 'chatgpt', 'gemini')
    display_name TEXT NOT NULL,                   -- User-friendly provider name (e.g., 'Claude (Anthropic)')
    enabled BOOLEAN DEFAULT 0,                    -- Whether this provider is currently active
    auth_method TEXT,                             -- Authentication method used ('api_key', 'oauth', 'device_code')
    configured_at INTEGER,                        -- Unix timestamp when provider was configured
    last_used_at INTEGER,                         -- Unix timestamp when provider was last used
    notes TEXT,                                   -- Optional notes about configuration
    created_at INTEGER NOT NULL,                  -- Unix timestamp when record created
    updated_at INTEGER NOT NULL                   -- Unix timestamp when record last updated
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_llm_provider_enabled ON llm_provider_config(enabled);
CREATE INDEX IF NOT EXISTS idx_llm_provider_name ON llm_provider_config(provider_name);

-- Global LLM session configuration
-- Purpose: Store which provider is currently selected globally across all browser instances
CREATE TABLE IF NOT EXISTS llm_session_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),       -- Single row constraint
    current_provider TEXT,                        -- Name of currently selected provider
    current_auth_method TEXT,                    -- Currently selected authentication method
    updated_at INTEGER NOT NULL                  -- Unix timestamp of last update
);

-- Initialize default LLM session config (single row)
INSERT OR IGNORE INTO llm_session_config (id, current_provider, updated_at)
VALUES (1, NULL, strftime('%s', 'now'));
