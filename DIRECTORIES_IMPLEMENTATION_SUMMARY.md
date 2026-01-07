# Non-Repository Directory Indexing - Implementation Summary

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/DIRECTORIES_IMPLEMENTATION_SUMMARY.md
**Description:** Quick reference guide for the directories feature implementation
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## What's Being Built

A new "Directories" tab in settings that mirrors "Repositories" functionality, enabling users to:
- **Add arbitrary directories** (not just git repos) for indexing
- **Manage them** (enable/disable, reindex, remove, see stats)
- **Search them** with the same filters as repositories
- **Filter by directory hierarchically** on the search page

---

## Quick Architecture Overview

### Database (3 new tables)
```
directories
├── id, path, name, enabled, priority
├── created_at, updated_at, last_indexed, notes

directory_stats
├── directory_id, index_type, total_files, size, timings

file_metadata (extended)
├── source_type: 'repository' | 'directory'
└── source_id: repo_name | directory_id
```

### API Endpoints (New)
```
GET /directories                    → List all managed directories
POST /directories                   → Add new directory
GET /directories/{id}               → Get directory details
PATCH /directories/{id}             → Update directory
DELETE /directories/{id}            → Remove directory
POST /directories/{id}/reindex      → Reindex specific directory
```

### Search Updates (Modified)
```
POST /search/hybrid|keyword|semantic
  New field: directories?: List[int]  # Directory IDs to include
```

### UI Changes
```
Settings Page
├── Directories Tab (NEW)
│   └── Directory List
│       ├── DirectoryCard (edit/reindex/remove)
│       ├── DirectoryForm (add new)
│       └── DirectoryBrowser (tree picker)

Search Page
├── Filters Panel (modified)
│   ├── Repositories (existing)
│   └── Directories (NEW) - hierarchical selector
```

---

## Implementation Phases at a Glance

| Phase | What | Hours | Backend/Frontend | Status |
|-------|------|-------|------------------|--------|
| **A** | Database schema & migration | 2-3 | Backend | Ready to start |
| **B** | API models (DirectoryInfo, etc) | 1 | Backend | Ready to start |
| **C** | Extend indexers (keyword & vector) | 3-4 | Backend | Ready to start |
| **D** | Add directory filtering to search | 2-3 | Backend | Ready to start |
| **E** | API endpoints (CRUD + reindex) | 2 | Backend | Ready to start |
| **F** | Directory management UI | 4-5 | Frontend | Ready to start |
| **G** | Search filter UI (directory selector) | 2-3 | Frontend | Ready to start |
| **H** | Testing & integration | 2-3 | Both | After phases A-G |
| | **TOTAL: 18-24 hours** | | | |

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| **Directory Storage** | Database table | Persistent, queryable, stats-trackable |
| **File Source Tracking** | Add source_type & source_id fields | Distinguish repo vs directory files |
| **Search Integration** | Optional directories parameter | Backward compatible, flexible |
| **UI Pattern** | Mirror repository management | Consistent UX, familiar to users |
| **API Style** | REST (same as repositories) | Consistent with existing API |
| **Directory Discovery** | Manual (file picker) + optional tree API | Simple, clear user intent |

---

## Database Schema (Phase A)

```sql
-- New table: managed directories
CREATE TABLE directories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,           -- e.g., /Users/user/docs
    name TEXT NOT NULL,                  -- e.g., "My Documents"
    enabled BOOLEAN DEFAULT 1,           -- included in search?
    priority INTEGER DEFAULT 0,          -- sort order in UI
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    last_indexed INTEGER,                -- timestamp of last index
    notes TEXT                           -- user notes
);

-- New table: directory statistics (parallel to repository_stats)
CREATE TABLE directory_stats (
    directory_id INTEGER PRIMARY KEY,
    index_type TEXT NOT NULL,            -- 'keyword' or 'vector'
    total_files_indexed INTEGER,
    total_size_bytes INTEGER,
    initial_index_time_seconds REAL,
    initial_index_timestamp INTEGER,
    last_reindex_time_seconds REAL,
    last_reindex_timestamp INTEGER,
    UNIQUE(directory_id, index_type)
);

-- Extend existing table: file_metadata
-- Add two columns to distinguish repo vs directory files:
ALTER TABLE file_metadata ADD COLUMN source_type TEXT DEFAULT 'repository';
ALTER TABLE file_metadata ADD COLUMN source_id TEXT;
-- source_type: 'repository' or 'directory'
-- source_id: repository name OR directory id (as string)
```

---

## API Examples

### Add Directory
```json
POST /directories
{
  "path": "/Users/user/projects/docs",
  "name": "Documentation Folder",
  "enabled": true,
  "notes": "Shared company documentation"
}

Response: DirectoryInfo { id: 5, path: "...", ... }
```

### List Directories
```json
GET /directories

Response: [
  { id: 1, path: "...", name: "...", enabled: true, ... },
  { id: 2, path: "...", name: "...", enabled: false, ... }
]
```

### Search with Directories
```json
POST /search/hybrid
{
  "query": "authentication",
  "repositories": ["xLLMArionComply"],
  "directories": [1, 3],          // NEW: Include these directory IDs
  "file_types": [".md", ".py"],
  "limit": 10
}

Response: SearchResponse {
  results: [{ file_path: "...", source_type: "directory", ... }],
  repositories_searched: ["xLLMArionComply"],
  directories_searched: [1, 3],   // NEW
  ...
}
```

---

## Core Implementation Tasks

### Phase A: Database
- [ ] Create migration file: `001_add_directories_table.sql`
- [ ] Implement `migration_manager.py` to run migrations
- [ ] Update `MetadataDatabase` to support source_type/source_id
- [ ] Add directory CRUD methods to MetadataDatabase

### Phase B: Models
- [ ] Add DirectoryInfo model
- [ ] Add DirectoryRequest model
- [ ] Add DirectoryStatsInfo model
- [ ] Update SearchRequest to accept directories parameter

### Phase C: Indexers
- [ ] Modify FileScanner to support arbitrary paths
- [ ] Update MeilisearchIndexer to handle source_type/source_id
- [ ] Update VectorIndexer to handle source_type/source_id
- [ ] Add `index_directory()` methods to both indexers

### Phase D: Search
- [ ] Update KeywordSearch to filter by directories
- [ ] Update VectorSearch to filter by directories
- [ ] Update HybridSearch to handle mixed sources
- [ ] Add source info to result objects

### Phase E: API
- [ ] Create `src/myragdb/api/routes/directories.py`
- [ ] Implement GET /directories (list)
- [ ] Implement POST /directories (add)
- [ ] Implement GET /directories/{id} (get)
- [ ] Implement PATCH /directories/{id} (update)
- [ ] Implement DELETE /directories/{id} (delete)
- [ ] Implement POST /directories/{id}/reindex (reindex)
- [ ] Register routes in server.py

### Phase F: Directory UI
- [ ] Create DirectoriesPage.tsx
- [ ] Create DirectoryList.tsx component
- [ ] Create DirectoryCard.tsx component (show status, stats)
- [ ] Create DirectoryForm.tsx component (add/edit dialog)
- [ ] Create DirectoryBrowser.tsx (tree picker)
- [ ] Create useDirectories.ts hook
- [ ] Create directoryService.ts API client
- [ ] Add "Directories" to Settings sidebar

### Phase G: Search Filter UI
- [ ] Update searchStore.ts to track selected directories
- [ ] Update SearchFilters.tsx to show directory selector
- [ ] Implement hierarchical display in filters
- [ ] Update useSearch hook to pass directories to API
- [ ] Test multi-select/deselect functionality

---

## Testing Checklist

### Unit Tests
- [ ] Directory CRUD in database
- [ ] File scanning with source tagging
- [ ] Search filtering by directory
- [ ] Result ranking with mixed sources

### Integration Tests
- [ ] Add directory → index → search → results include directory files
- [ ] Filter by directory only (not repos)
- [ ] Filter by repo only (not directories)
- [ ] Filter by both
- [ ] Directory reindex updates stats

### UI Tests
- [ ] Add directory via form
- [ ] Directory appears in list
- [ ] Can edit directory settings
- [ ] Can delete directory
- [ ] Directory selector appears in search filters
- [ ] Can toggle directory in search filter

### E2E Tests
- [ ] Full workflow: add directory → search → get results → open file

---

## Migration from Current State

**No migration needed!** This is additive:
- Existing repositories continue working unchanged
- New directories are added alongside
- Search defaults to all sources
- Users gradually adopt directories

**Backward Compatibility:** 100% - old code/API unchanged

---

## Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Add directory | < 100ms | Lightweight DB insert |
| Index directory (1000 files) | < 5s | Similar to repo indexing |
| List directories | < 50ms | Small table, few queries |
| Search with directory filter | < 500ms | Same as repository filtering |
| Store 100+ directories | < 100MB index | Minimal overhead |

---

## Next Steps After Implementation

1. **Phase 4 (Future):** Add file watcher for auto-reindexing
2. **Phase 4 (Future):** Directory groups/workspaces
3. **Phase 5 (Future):** Import/export directory configs
4. **Phase 5 (Future):** Remote directory support

---

## Files to Create/Modify

### Backend Files
**Create:**
- `src/myragdb/db/migrations/001_add_directories_table.sql`
- `src/myragdb/db/migration_manager.py`
- `src/myragdb/api/routes/directories.py`
- `src/myragdb/services/directory_service.py` (optional)

**Modify:**
- `src/myragdb/db/file_metadata.py`
- `src/myragdb/api/models.py`
- `src/myragdb/api/server.py`
- `src/myragdb/indexers/file_scanner.py`
- `src/myragdb/indexers/meilisearch_indexer.py`
- `src/myragdb/indexers/vector_indexer.py`
- `src/myragdb/search/keyword_search.py`
- `src/myragdb/search/vector_search.py`
- `src/myragdb/search/hybrid_search.py`

### Frontend Files
**Create:**
- `web-ui/src/pages/DirectoriesPage.tsx`
- `web-ui/src/components/directories/DirectoryList.tsx`
- `web-ui/src/components/directories/DirectoryCard.tsx`
- `web-ui/src/components/directories/DirectoryForm.tsx`
- `web-ui/src/components/directories/DirectoryBrowser.tsx`
- `web-ui/src/hooks/useDirectories.ts`
- `web-ui/src/services/directoryService.ts`

**Modify:**
- `web-ui/src/stores/searchStore.ts`
- `web-ui/src/components/search/SearchFilters.tsx`
- `web-ui/src/components/layout/Sidebar.tsx`
- `web-ui/src/hooks/useSearch.ts`

### Documentation Files
**Create/Modify:**
- `DIRECTORIES_FEATURE_IMPLEMENTATION_PLAN.md` (detailed - created)
- `README.md` (add directories section)
- `docs/USER_MANUAL.md` (add directory management guide)

---

## Verification Points

After each phase, verify:
- **Phase A:** Migrations run successfully, schema correct
- **Phase B:** Models serialize/deserialize without errors
- **Phase C:** Can index a test directory, files appear in indexes
- **Phase D:** Search returns results from directories with correct filtering
- **Phase E:** All API endpoints respond with correct status codes
- **Phase F:** UI renders, add/edit/delete work, no console errors
- **Phase G:** Directory filter appears, multi-select works, search filters by directory

---

## Rollback Plan

If critical issues found:
1. Database: Schema migrations are reversible (though data may be lost)
2. API: New endpoints can be disabled without affecting existing API
3. UI: New components can be hidden via feature flag
4. No breaking changes to existing functionality

---

**Questions:** libor@arionetworks.com
