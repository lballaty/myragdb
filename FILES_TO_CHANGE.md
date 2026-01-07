# Directory Indexing Feature - Complete File Change List

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/FILES_TO_CHANGE.md
**Description:** Exhaustive list of all files to be created/modified for the directories feature
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

**Total Files:** 23
- **New Files:** 13
- **Modified Files:** 10
- **Estimated Changes:** ~3,000 lines of code
- **Estimated Time:** 18-24 hours

---

## Backend Files

### Phase A: Database & Migrations

#### NEW FILES

**1. `src/myragdb/db/migrations/001_add_directories_table.sql`**
```
Status: NEW
Purpose: SQL migration to add directories support
Content:
  - CREATE TABLE directories
  - CREATE TABLE directory_stats
  - ALTER TABLE file_metadata (add source_type, source_id)
  - CREATE INDEX statements
Size: ~80 lines
Dependencies: None (runs on startup)
```

**2. `src/myragdb/db/migration_manager.py`**
```
Status: NEW
Purpose: Handle database schema versioning and migrations
Content:
  class MigrationManager:
    - track_schema_version()
    - run_pending_migrations()
    - apply_migration(version)
    - rollback_migration(version)
Size: ~150 lines
Dependencies: sqlite3, pathlib
```

#### MODIFIED FILES

**3. `src/myragdb/db/file_metadata.py`**
```
Status: MODIFIED
Changes:
  - Add source_type and source_id to all methods
  - Add directory CRUD methods:
    - add_directory(path, name, notes)
    - get_directory(directory_id)
    - list_directories(enabled_only)
    - update_directory(directory_id, **fields)
    - delete_directory(directory_id)
    - directory_exists(path)
  - Add directory stats methods:
    - save_directory_stats(directory_id, stats)
    - get_directory_stats(directory_id)
  - Update file tracking to support both sources
  - Update queries to filter by source_type
Size: +250 lines (from ~300 to ~550)
```

---

### Phase B: API Models

#### MODIFIED FILES

**4. `src/myragdb/api/models.py`**
```
Status: MODIFIED
Changes:
  NEW MODELS:
  - DirectoryInfo (id, path, name, enabled, priority, created_at, etc.)
  - DirectoryStatsInfo (total_files, total_size, timings, etc.)
  - DirectoryRequest (path, name, enabled, notes)
  - DirectoryDiscoveryInfo (for tree picker)

  MODIFIED MODELS:
  - SearchRequest: Add directories?: List[int] parameter
  - SearchResponse: Ensure directories field works
  - SearchResultItem: Add source_type, source_name fields (optional)

Size: +200 lines (from ~200 to ~400)
```

---

### Phase C: Indexers

#### MODIFIED FILES

**5. `src/myragdb/indexers/file_scanner.py`**
```
Status: MODIFIED
Changes:
  - Update scan_directory() signature to accept source_type, source_id
  - Yield FileInfo with source metadata
  - Handle both repository paths and arbitrary directories
  - Maintain exclude patterns support for both types

  NEW METHODS:
  - scan_arbitrary_directory(path, directory_id, exclude_patterns)

Size: +100 lines (from ~200 to ~300)
```

**6. `src/myragdb/indexers/meilisearch_indexer.py`**
```
Status: MODIFIED
Changes:
  - Update index_file() to include source_type, source_id in document
  - Create source field in Meilisearch for filtering
  - Update search filtering to support source filtering

  NEW METHODS:
  - index_directory(directory_id, directory_path, full_reindex)
  - unindex_directory(directory_id)

Size: +150 lines (from ~300 to ~450)
```

**7. `src/myragdb/indexers/vector_indexer.py`**
```
Status: MODIFIED
Changes:
  - Update add_embedding() to include source metadata in ChromaDB metadata
  - Update search() to support where clause filtering by directory_id

  NEW METHODS:
  - index_directory(directory_id, directory_path, full_reindex)
  - unindex_directory(directory_id)

Size: +150 lines (from ~250 to ~400)
```

---

### Phase D: Search Logic

#### MODIFIED FILES

**8. `src/myragdb/search/keyword_search.py`**
```
Status: MODIFIED
Changes:
  - Update search() signature: add directories?: List[int]
  - Build Meilisearch filter for directories if provided
  - Handle mixed repository/directory sources

Size: +50 lines (from ~150 to ~200)
```

**9. `src/myragdb/search/vector_search.py`**
```
Status: MODIFIED
Changes:
  - Update search() signature: add directories?: List[int]
  - Build ChromaDB where clause for directory_id filtering
  - Handle mixed sources

Size: +50 lines (from ~150 to ~200)
```

**10. `src/myragdb/search/hybrid_search.py`**
```
Status: MODIFIED
Changes:
  - Update search() signature: add directories?: List[int]
  - Pass directories to both keyword_search and vector_search
  - Merge results from both sources
  - Normalize scores properly

Size: +30 lines (from ~100 to ~130)
```

---

### Phase E: API Endpoints

#### NEW FILES

**11. `src/myragdb/api/routes/directories.py`**
```
Status: NEW
Purpose: All directory management endpoints
Content:
  - @router.get("/directories")
  - @router.post("/directories")
  - @router.get("/directories/{directory_id}")
  - @router.patch("/directories/{directory_id}")
  - @router.delete("/directories/{directory_id}")
  - @router.post("/directories/{directory_id}/reindex")
  - @router.get("/directories/discover")

Size: ~250 lines
Dependencies: FastAPI, MetadataDatabase, Indexers
```

#### MODIFIED FILES

**12. `src/myragdb/api/server.py`**
```
Status: MODIFIED
Changes:
  - Import new directories router
  - app.include_router(directories_router)
  - Update /search endpoints to pass directories parameter to search service

Size: +20 lines (small addition)
```

---

### Phase F-G: Service Layer (Optional)

#### NEW FILES (Optional)

**13. `src/myragdb/services/directory_service.py`** (OPTIONAL - for cleaner separation)
```
Status: NEW (Optional)
Purpose: Business logic for directory operations
Content:
  class DirectoryService:
    - add_directory()
    - remove_directory()
    - reindex_directory()
    - get_directory_info()
    - etc.

Size: ~200 lines
Rationale: Keep routes thin, put logic here
```

---

## Frontend Files

### Phase F: Directory Management UI

#### NEW FILES

**14. `web-ui/src/pages/DirectoriesPage.tsx`**
```
Status: NEW
Purpose: Main directories management page in settings
Content:
  - Page layout with sidebar
  - DirectoryList component integration
  - Add Directory button
  - Empty state

Size: ~150 lines
```

**15. `web-ui/src/components/directories/DirectoryList.tsx`**
```
Status: NEW
Purpose: Display list of managed directories
Content:
  - Render DirectoryCard for each directory
  - Handle loading/error states
  - Manage add directory modal

Size: ~200 lines
```

**16. `web-ui/src/components/directories/DirectoryCard.tsx`**
```
Status: NEW
Purpose: Single directory card with collapsible details
Content:
  - Show directory info (name, path, status)
  - Show indexing stats
  - Action buttons (Edit, Reindex, Disable, Remove)
  - Expandable details section

Size: ~300 lines
```

**17. `web-ui/src/components/directories/DirectoryForm.tsx`**
```
Status: NEW
Purpose: Modal form for adding/editing directories
Content:
  - Path input with Browse button
  - Name input
  - Notes textarea
  - Enabled toggle
  - Submit/Cancel buttons
  - Form validation

Size: ~250 lines
```

**18. `web-ui/src/components/directories/DirectoryBrowser.tsx`**
```
Status: NEW
Purpose: Tree view file system picker
Content:
  - Hierarchical directory tree
  - Search to filter directories
  - Recent directories list
  - Bookmarks support
  - Single path selection

Size: ~300 lines
```

#### NEW FILES - Hooks & Services

**19. `web-ui/src/hooks/useDirectories.ts`**
```
Status: NEW
Purpose: React Query hooks for directory operations
Content:
  - useDirectories() - List all directories
  - useAddDirectory() - Add mutation
  - useUpdateDirectory() - Update mutation
  - useDeleteDirectory() - Delete mutation
  - useReindexDirectory() - Reindex mutation

Size: ~150 lines
```

**20. `web-ui/src/services/directoryService.ts`**
```
Status: NEW
Purpose: API client for directory endpoints
Content:
  - listDirectories()
  - addDirectory(req)
  - updateDirectory(id, req)
  - deleteDirectory(id)
  - reindexDirectory(id, full)
  - discoverDirectories(path)

Size: ~120 lines
```

---

### Phase G: Search Filter Integration

#### MODIFIED FILES

**21. `web-ui/src/stores/searchStore.ts`**
```
Status: MODIFIED
Changes:
  - Add selectedDirectories: number[] to state
  - Add toggleDirectory(id) method
  - Add selectAllDirectories() / clearAllDirectories() methods
  - Update search() to pass directories to API

Size: +80 lines (from ~300 to ~380)
```

**22. `web-ui/src/components/search/SearchFilters.tsx`**
```
Status: MODIFIED
Changes:
  - Add DIRECTORIES section (new)
  - Import useDirectories hook
  - Show hierarchical directory selector
  - Add "Select All" / "Clear All" buttons for directories
  - Style to match REPOSITORIES section

Size: +150 lines (from ~200 to ~350)
```

**23. `web-ui/src/components/layout/Sidebar.tsx`**
```
Status: MODIFIED
Changes:
  - Add "Directories" link to navigation
  - Route: /settings/directories
  - Icon and styling

Size: +15 lines (small addition)
```

---

## Summary Table

### Backend (10 files)

| File | Type | Size | Phase |
|------|------|------|-------|
| `db/migrations/001_add_directories_table.sql` | NEW | 80 | A |
| `db/migration_manager.py` | NEW | 150 | A |
| `db/file_metadata.py` | MOD | +250 | A |
| `api/models.py` | MOD | +200 | B |
| `indexers/file_scanner.py` | MOD | +100 | C |
| `indexers/meilisearch_indexer.py` | MOD | +150 | C |
| `indexers/vector_indexer.py` | MOD | +150 | C |
| `search/keyword_search.py` | MOD | +50 | D |
| `search/vector_search.py` | MOD | +50 | D |
| `search/hybrid_search.py` | MOD | +30 | D |
| `api/routes/directories.py` | NEW | 250 | E |
| `api/server.py` | MOD | +20 | E |
| `services/directory_service.py` | NEW (OPT) | 200 | - |

### Frontend (10 files)

| File | Type | Size | Phase |
|------|------|------|-------|
| `pages/DirectoriesPage.tsx` | NEW | 150 | F |
| `components/directories/DirectoryList.tsx` | NEW | 200 | F |
| `components/directories/DirectoryCard.tsx` | NEW | 300 | F |
| `components/directories/DirectoryForm.tsx` | NEW | 250 | F |
| `components/directories/DirectoryBrowser.tsx` | NEW | 300 | F |
| `hooks/useDirectories.ts` | NEW | 150 | F |
| `services/directoryService.ts` | NEW | 120 | F |
| `stores/searchStore.ts` | MOD | +80 | G |
| `components/search/SearchFilters.tsx` | MOD | +150 | G |
| `components/layout/Sidebar.tsx` | MOD | +15 | G |

---

## Change Complexity by File

### Simple Changes (< 30 lines)
- ✅ `api/server.py` - Just add import and router
- ✅ `search/hybrid_search.py` - Pass directories parameter through
- ✅ `components/layout/Sidebar.tsx` - Add navigation link

### Medium Changes (30-100 lines)
- 🟡 `search/keyword_search.py` - Add directory filter logic
- 🟡 `search/vector_search.py` - Add directory filter logic
- 🟡 `indexers/file_scanner.py` - Support arbitrary paths
- 🟡 `db/migrations/001_add_directories_table.sql` - Schema DDL
- 🟡 `hooks/useDirectories.ts` - Standard React Query hooks

### Complex Changes (100-250 lines)
- 🔴 `db/file_metadata.py` - Directory CRUD + stats methods
- 🔴 `api/models.py` - Multiple new models + SearchRequest update
- 🔴 `indexers/meilisearch_indexer.py` - Indexing logic for directories
- 🔴 `indexers/vector_indexer.py` - Vector embedding for directories
- 🔴 `api/routes/directories.py` - 7 new endpoints
- 🔴 `components/directories/DirectoryForm.tsx` - Form with validation
- 🔴 `components/directories/DirectoryBrowser.tsx` - Tree picker

### Very Complex (250+ lines)
- 🔴 `components/directories/DirectoryCard.tsx` - Card with multiple states
- 🔴 `components/search/SearchFilters.tsx` - Hierarchical selector

---

## Import/Dependency Map

### Backend Dependencies

```
api/server.py
  ├── imports: api/routes/directories.py (NEW)
  └── imports: api/routes/search.py (existing, modified)

api/routes/directories.py (NEW)
  ├── imports: api/models.py (modified)
  ├── imports: db/file_metadata.py (modified)
  ├── imports: indexers/meilisearch_indexer.py (modified)
  └── imports: indexers/vector_indexer.py (modified)

search/keyword_search.py (modified)
  └── calls: Meilisearch client (existing)

search/vector_search.py (modified)
  └── calls: ChromaDB client (existing)

indexers/*.py (modified)
  ├── imports: db/file_metadata.py (modified)
  └── calls: Meilisearch/ChromaDB (existing)

db/file_metadata.py (modified)
  └── calls: MetadataDatabase (existing)
```

### Frontend Dependencies

```
pages/DirectoriesPage.tsx (NEW)
  ├── imports: hooks/useDirectories.ts (NEW)
  ├── imports: components/directories/DirectoryList.tsx (NEW)
  └── imports: stores/settingsStore.ts (existing)

components/directories/*.tsx (NEW)
  ├── imports: services/directoryService.ts (NEW)
  ├── imports: hooks/useDirectories.ts (NEW)
  └── imports: common components (existing)

stores/searchStore.ts (modified)
  ├── NEW: selectedDirectories state
  └── calls: directoryService.ts (NEW)

components/search/SearchFilters.tsx (modified)
  ├── imports: hooks/useDirectories.ts (NEW)
  └── calls: searchStore.toggleDirectory() (NEW method)
```

---

## No Changes Needed

### These Files Stay Untouched
- Configuration system (`config/repositories.yaml`)
- Existing repository management (`api/routes/repositories.py`)
- Existing search results display (mostly)
- Database schema version 1 (new version 2 via migration)
- CLI interface (works with all sources)
- Python client library (works with all sources)

---

## Commit Strategy

### Suggested Commits (8 total)

1. **"feat: add database schema for directory indexing"**
   - `db/migrations/001_add_directories_table.sql`
   - `db/migration_manager.py`
   - `db/file_metadata.py`

2. **"feat: add DirectoryInfo models to API"**
   - `api/models.py`

3. **"feat: extend indexers for directory support"**
   - `indexers/file_scanner.py`
   - `indexers/meilisearch_indexer.py`
   - `indexers/vector_indexer.py`

4. **"feat: add directory filtering to search logic"**
   - `search/keyword_search.py`
   - `search/vector_search.py`
   - `search/hybrid_search.py`

5. **"feat: add directory management API endpoints"**
   - `api/routes/directories.py`
   - `api/server.py`

6. **"feat: add directory management UI (settings page)"**
   - `pages/DirectoriesPage.tsx`
   - `components/directories/DirectoryList.tsx`
   - `components/directories/DirectoryCard.tsx`
   - `components/directories/DirectoryForm.tsx`
   - `components/directories/DirectoryBrowser.tsx`

7. **"feat: add directory integration to search filters"**
   - `stores/searchStore.ts`
   - `components/search/SearchFilters.tsx`
   - `components/layout/Sidebar.tsx`
   - `hooks/useDirectories.ts`
   - `services/directoryService.ts`

8. **"test: add tests for directory feature"**
   - Test files (new)

---

## Ready To Start?

All files listed above are ready for implementation following the phases outlined in `DIRECTORIES_FEATURE_IMPLEMENTATION_PLAN.md`.

**Next Step:** Proceed to Phase A (database schema) or review any questions first?

---

Questions: libor@arionetworks.com
