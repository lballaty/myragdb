# Non-Repository Directory Indexing Implementation Plan

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/DIRECTORIES_FEATURE_IMPLEMENTATION_PLAN.md
**Description:** Detailed implementation plan for adding non-repository directory indexing and management to MyRAGDB
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07
**Last Updated:** 2026-01-07

---

## Executive Summary

This document outlines the complete implementation strategy for adding **non-repository directory support** to MyRAGDB. The feature mirrors the existing repository management UI/API but applies it to arbitrary directories, enabling users to index and search across both git repositories and standalone directory trees with unified filtering and search capabilities.

---

## Feature Overview

### Current State
- Only git repositories can be indexed
- Repositories are auto-discovered and managed via dedicated UI
- Search filtering available only by repository

### Desired State
- Both repositories **and** arbitrary directories can be indexed
- Directories are manually added via UI tree view/file picker
- Unified management UI (parallel to repositories)
- Unified search filtering (hierarchical directory selection)
- All three search modes work with directories: keyword, vector, hybrid

### Key Principles
1. **Functional Parity:** Directory management mirrors repository management
2. **Persistent Metadata:** Directories tracked in database like repositories
3. **Unified Search:** Same filtering logic applies to both types
4. **Hierarchical Selection:** Multi-level directory selection in search filters
5. **Incremental Indexing:** Supports watching and reindexing directories

---

## Architecture Design

### Data Model

#### New Entities

**1. Managed Directory (Database)**
```
Directory
├── id (auto-increment primary key)
├── path (absolute directory path, unique)
├── name (user-friendly name)
├── enabled (boolean, default true)
├── priority (ordering in UI, default 0)
├── created_at (timestamp)
├── updated_at (timestamp)
├── last_indexed (timestamp, nullable)
└── notes (optional user notes)
```

**2. Directory Statistics (Database)**
```
DirectoryStats
├── directory_id (FK to directory)
├── index_type ('keyword' or 'vector')
├── total_files_indexed (count)
├── total_size_bytes (sum)
├── initial_index_time_seconds (real)
├── last_reindex_time_seconds (real)
└── last_reindex_timestamp (timestamp)
```

**3. File Metadata Extension**
```
Current file_metadata table:
  file_path (TEXT PRIMARY KEY)
  repository (TEXT NOT NULL)     ← Only for repo files
  ...

New structure needed:
  file_path (TEXT PRIMARY KEY)
  source_type ('repository' or 'directory')
  source_id (either repo name OR directory_id)
  ...
```

### API Design

#### REST Endpoints - Directory Management

```
GET /directories
  Purpose: List all managed directories
  Response: List[DirectoryInfo]

POST /directories
  Purpose: Add new directory to index
  Request: {path: str, name: str, enabled?: bool, notes?: str}
  Response: DirectoryInfo

GET /directories/{directory_id}
  Purpose: Get directory details and stats
  Response: DirectoryInfo (with stats)

PATCH /directories/{directory_id}
  Purpose: Update directory settings
  Request: {enabled?: bool, name?: str, notes?: str}
  Response: DirectoryInfo

DELETE /directories/{directory_id}
  Purpose: Remove directory from index
  Response: {success: bool}

POST /directories/{directory_id}/reindex
  Purpose: Force reindex of specific directory
  Query: full_reindex?: bool
  Response: {status: str, files_indexed: int}

GET /directories/discover
  Purpose: Discover directories (optional helper for UI tree picker)
  Query: path?: str, recursive?: bool
  Response: List[DirectoryInfo] (sub-directories found)
```

#### REST Endpoints - Search Integration

```
POST /search/hybrid (EXTENDED)
  Current: repositories?: List[str], folder_filter?: str
  New: directories?: List[int]  (directory IDs to search)

  Behavior:
  - If both repositories and directories provided: search both
  - If neither provided: search all
  - If only one type: search that type only

POST /search/keyword (EXTENDED)
  Same extensions as /search/hybrid

POST /search/semantic (EXTENDED)
  Same extensions as /search/hybrid
```

---

## Implementation Phases

### Phase A: Database & Data Model (2-3 hours)

#### A1: Schema Migration
**Files to Create/Modify:**
- `src/myragdb/db/migrations/` (new directory)
- `src/myragdb/db/migrations/001_add_directories_table.sql` (new file)

**Schema Changes:**
```sql
-- New tables
CREATE TABLE directories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    priority INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    last_indexed INTEGER,
    notes TEXT
);

CREATE INDEX idx_directories_path ON directories(path);
CREATE INDEX idx_directories_enabled ON directories(enabled);

-- Directory statistics
CREATE TABLE directory_stats (
    directory_id INTEGER PRIMARY KEY,
    index_type TEXT NOT NULL,
    total_files_indexed INTEGER,
    total_size_bytes INTEGER,
    initial_index_time_seconds REAL,
    initial_index_timestamp INTEGER,
    last_reindex_time_seconds REAL,
    last_reindex_timestamp INTEGER,
    FOREIGN KEY(directory_id) REFERENCES directories(id),
    UNIQUE(directory_id, index_type)
);

-- Modify file_metadata to support both repos and directories
ALTER TABLE file_metadata ADD COLUMN source_type TEXT DEFAULT 'repository';
ALTER TABLE file_metadata ADD COLUMN source_id TEXT;

-- Create composite index for fast lookups
CREATE INDEX idx_file_source ON file_metadata(source_type, source_id);
```

#### A2: Implement Migration System
**Files to Create:**
- `src/myragdb/db/migration_manager.py` (new file)

**Responsibilities:**
- Track schema version
- Apply pending migrations
- Handle rollback if needed
- Run on server startup

#### A3: Update MetadataDatabase Class
**Files to Modify:**
- `src/myragdb/db/file_metadata.py`

**Changes:**
- Support `source_type` and `source_id` in all methods
- Add methods for directory stats tracking
- Update indices to use new schema

**Methods to Add:**
```python
def add_directory(path: str, name: str, notes: str = None) -> int
def get_directory(directory_id: int) -> DirectoryInfo
def list_directories(enabled_only: bool = False) -> List[DirectoryInfo]
def update_directory(directory_id: int, **fields) -> DirectoryInfo
def delete_directory(directory_id: int) -> bool
def directory_exists(path: str) -> bool
```

---

### Phase B: API Models & Serialization (1 hour)

**Files to Modify:**
- `src/myragdb/api/models.py`

**New Models:**
```python
class DirectoryInfo(BaseModel):
    """Managed directory with status and statistics."""
    id: int
    path: str
    name: str
    enabled: bool
    priority: int
    created_at: int
    updated_at: int
    last_indexed: Optional[int]
    notes: Optional[str]
    stats: Optional[DirectoryStatsInfo]

class DirectoryStatsInfo(BaseModel):
    """Statistics for a directory's indexing."""
    total_files_indexed: int
    total_size_bytes: int
    index_type: str
    initial_index_time_seconds: Optional[float]
    last_reindex_time_seconds: Optional[float]
    last_reindex_timestamp: Optional[int]

class DirectoryRequest(BaseModel):
    """Request to add/update directory."""
    path: str
    name: str
    enabled: bool = True
    notes: Optional[str] = None

class DirectoryDiscoveryInfo(BaseModel):
    """Directory info for tree view discovery."""
    path: str
    name: str
    is_directory: bool
    children: Optional[List['DirectoryDiscoveryInfo']] = None
```

**Modified Models:**
```python
class SearchRequest(BaseModel):
    # Existing fields...
    repositories: Optional[List[str]] = None  # repo names
    directories: Optional[List[int]] = None   # directory IDs (NEW)
```

---

### Phase C: Indexer Extensions (3-4 hours)

**Files to Modify:**
- `src/myragdb/indexers/file_scanner.py`
- `src/myragdb/indexers/meilisearch_indexer.py`
- `src/myragdb/indexers/vector_indexer.py`
- `src/myragdb/indexers/index_manager.py` (if exists)

#### C1: FileScanner Enhancement
**Current Behavior:** Walks repository directories

**New Behavior:**
- Support both repository paths and arbitrary directory paths
- Accept `source_type` and `source_id` parameters
- Yield files with proper metadata tagging

**Changes:**
```python
def scan_directory(
    path: str,
    source_type: str,  # 'repository' or 'directory'
    source_id: str,    # repo name or directory_id
    exclude_patterns: List[str] = None
) -> Iterator[FileInfo]:
    """Scan directory and yield indexable files."""
```

#### C2: Meilisearch Indexer Enhancement
**Changes:**
- Accept `source_type` and `source_id` in indexing calls
- Store these as document fields for filtering
- Support filtering in search by source

**Key Changes:**
```python
async def index_directory(
    directory_id: int,
    directory_path: str,
    full_reindex: bool = False,
    exclude_patterns: List[str] = None
):
    """Index a non-repository directory."""
```

#### C3: Vector Indexer Enhancement
**Same approach as Meilisearch:**
- Accept source metadata
- Store in ChromaDB metadata
- Support filtering by directory_id

---

### Phase D: Search Integration (2-3 hours)

**Files to Modify:**
- `src/myragdb/search/hybrid_search.py`
- `src/myragdb/search/keyword_search.py`
- `src/myragdb/search/vector_search.py`

#### D1: Keyword Search Updates
**Change:** Support directory filtering

```python
async def search(
    query: str,
    repositories: List[str] = None,
    directories: List[int] = None,
    file_types: List[str] = None,
    limit: int = 10
) -> List[SearchResult]:
    """Execute keyword search with directory filtering."""
    filters = []

    if repositories:
        repo_filter = {"in": ["repository", repositories]}
        filters.append(repo_filter)

    if directories:
        dir_filter = {"in": ["source_id", [str(d) for d in directories]]}
        filters.append(dir_filter)
```

#### D2: Vector Search Updates
**Same approach:** Extend ChromaDB where clause

```python
where_clause = {
    "$and": [
        {"source_type": {"$eq": "directory"}},
        {"source_id": {"$in": [str(d) for d in directories]}}
    ]
}
```

#### D3: Result Post-Processing
**Change:** Include source information in results

```python
def add_source_info(results: List[SearchResult]) -> List[SearchResult]:
    """Add source_type and source_name to each result."""
    for result in results:
        if result.source_type == 'directory':
            result.source_name = metadata_db.get_directory(result.source_id).name
```

---

### Phase E: API Endpoints (2 hours)

**Files to Create/Modify:**
- `src/myragdb/api/routes/directories.py` (new file)
- `src/myragdb/api/server.py` (modify to include new routes)

#### E1: Directory Management Routes
```python
# src/myragdb/api/routes/directories.py

@router.get("/directories", response_model=List[DirectoryInfo])
async def list_directories(enabled_only: bool = False):
    """List all managed directories."""

@router.post("/directories", response_model=DirectoryInfo)
async def add_directory(request: DirectoryRequest):
    """Add new directory to index."""

@router.get("/directories/{directory_id}", response_model=DirectoryInfo)
async def get_directory(directory_id: int):
    """Get directory details."""

@router.patch("/directories/{directory_id}", response_model=DirectoryInfo)
async def update_directory(directory_id: int, request: DirectoryRequest):
    """Update directory settings."""

@router.delete("/directories/{directory_id}")
async def delete_directory(directory_id: int):
    """Delete directory from index."""

@router.post("/directories/{directory_id}/reindex")
async def reindex_directory(directory_id: int, full_reindex: bool = False):
    """Reindex specific directory."""

@router.get("/directories/discover")
async def discover_directories(path: str, recursive: bool = False):
    """Helper for UI tree picker (optional)."""
```

#### E2: Search Endpoint Updates
**Modify existing:** `/search/hybrid`, `/search/keyword`, `/search/semantic`

```python
# src/myragdb/api/routes/search.py (modify existing)

@app.post("/search/hybrid")
async def hybrid_search(request: SearchRequest):
    # Handle new directories field
    results = await search_service.search(
        query=request.query,
        repositories=request.repositories,
        directories=request.directories,  # NEW
        file_types=request.file_types,
        limit=request.limit
    )
```

---

### Phase F: UI - Directory Management Page (4-5 hours)

**Files to Create:**
- `web-ui/src/pages/DirectoriesPage.tsx` (new)
- `web-ui/src/components/directories/` (new directory)
  - `DirectoryList.tsx`
  - `DirectoryCard.tsx`
  - `DirectoryForm.tsx`
  - `DirectoryBrowser.tsx` (tree picker)
- `web-ui/src/hooks/useDirectories.ts` (new)
- `web-ui/src/services/directoryService.ts` (new)

#### F1: Data Fetching & State Management

**File:** `web-ui/src/services/directoryService.ts`
```typescript
export const directoryService = {
  async listDirectories(): Promise<DirectoryInfo[]> { ... },
  async addDirectory(req: DirectoryRequest): Promise<DirectoryInfo> { ... },
  async updateDirectory(id: number, req: DirectoryRequest): Promise<DirectoryInfo> { ... },
  async deleteDirectory(id: number): Promise<void> { ... },
  async reindexDirectory(id: number, full?: boolean): Promise<ReindexResult> { ... },
  async discoverDirectories(path: string): Promise<DirectoryDiscoveryInfo[]> { ... },
};
```

**File:** `web-ui/src/hooks/useDirectories.ts`
```typescript
export const useDirectories = () => {
  return useQuery({
    queryKey: ['directories'],
    queryFn: () => directoryService.listDirectories(),
    staleTime: 10 * 60 * 1000,
  });
};

export const useAddDirectory = () => {
  return useMutation({
    mutationFn: (req: DirectoryRequest) =>
      directoryService.addDirectory(req),
    onSuccess: () => queryClient.invalidateQueries(['directories']),
  });
};

// Similar hooks for update, delete, reindex
```

#### F2: UI Components

**File:** `web-ui/src/pages/DirectoriesPage.tsx`
```typescript
// Settings page with sidebar navigation
// Main content: DirectoryList with add/manage controls
// Responsive layout similar to RepositoriesPage
```

**File:** `web-ui/src/components/directories/DirectoryCard.tsx`
```typescript
// Card showing:
// - Directory path
// - User-defined name
// - Status (enabled/disabled)
// - File count and size
// - Last indexed timestamp
// - Action buttons: Edit, Reindex, Disable, Remove
// - Expandable stats section
```

**File:** `web-ui/src/components/directories/DirectoryForm.tsx`
```typescript
// Form for adding/editing directory:
// - Path input with validation
// - Name input
// - Notes textarea
// - Enabled toggle
// - Submit/Cancel buttons
```

**File:** `web-ui/src/components/directories/DirectoryBrowser.tsx`
```typescript
// Tree view file picker:
// - Hierarchical directory navigation
// - Search to filter directories
// - Single/multi-select
// - Recent directories list
// - Bookmarks support
```

#### F3: Add to Main Navigation
**Modify:** `web-ui/src/components/layout/Sidebar.tsx`
```typescript
// Add "Directories" link alongside "Repositories"
// Route: /settings/directories
```

---

### Phase G: UI - Search Filter Integration (2-3 hours)

**Files to Modify:**
- `web-ui/src/stores/searchStore.ts`
- `web-ui/src/components/search/SearchFilters.tsx`

#### G1: Store Update
```typescript
interface SearchState {
  // Existing fields...
  selectedDirectories: number[];  // NEW: directory IDs
  toggleDirectory: (id: number) => void;  // NEW
  // ... other methods
}
```

#### G2: Filter Component Update
**Modify:** `SearchFilters.tsx`

Add hierarchical directory selector:
```typescript
// Show as expandable/collapsible section
// Similar to repository checkboxes but organized hierarchically
// Display: [Enabled] Path/to/Directory (123 files)
//
// Structure:
// Directories
//   [✓] ~/projects/site (1,245 files)
//   [✓] ~/projects/tools (456 files)
//   [ ] ~/archive/old (0 files)
```

#### G3: Search Request Update
**Modify:** `web-ui/src/hooks/useSearch.ts`

Pass `directories` to search API:
```typescript
const results = await searchService.search({
  query,
  repositories: selectedRepos,
  directories: selectedDirectories,  // NEW
  file_types: selectedFileTypes,
  search_type: searchType,
});
```

---

### Phase H: File Watcher Support (Phase 4 - Future)

**Files to Modify:**
- `src/myragdb/indexers/file_watcher.py`

**Changes:**
- Extend to watch arbitrary directories
- Track both repository and directory roots
- Trigger reindexing on file changes

**Implementation Note:** This is Phase 4 scope (not covered in initial implementation)

---

## Implementation Order

### Sprint 1 (Day 1 - Morning)
1. ✅ Phase A: Database schema & migrations
2. ✅ Phase B: API models
3. ✅ Phase C1-C3: Indexer extensions

### Sprint 2 (Day 1 - Afternoon)
4. ✅ Phase D: Search integration
5. ✅ Phase E: API endpoints

### Sprint 3 (Day 2 - Morning)
6. ✅ Phase F: Directory management UI

### Sprint 4 (Day 2 - Afternoon)
7. ✅ Phase G: Search filter integration
8. ✅ Testing & integration

### Deferred (Phase 4)
9. ⏸️ Phase H: File watcher support

---

## Testing Strategy

### Unit Tests
- Database migration logic
- Directory CRUD operations
- Search filtering with directories
- Result merging from mixed sources

### Integration Tests
- Index directory → search → verify results
- Filter by directory only
- Filter by repository only
- Filter by both
- Add/remove directories mid-session

### E2E Tests
- Add directory via UI
- Search with directory filter
- Update directory settings
- Remove directory

### Manual Verification
- Verify directory stats are accurate
- Verify search results include directory metadata
- Verify UI shows both repositories and directories
- Verify search filtering works hierarchically

---

## Migration Strategy

### Phase 1: Backward Compatibility
- New schema version (v2) applied on startup
- Existing `repository` field in file_metadata still works
- Search defaults to all sources if not specified

### Phase 2: Data Migration
- Migration script populates `source_type='repository'` for all existing records
- Populates `source_id` from `repository` field

### Phase 3: Gradual Adoption
- Repositories continue working as before
- Users gradually add directories
- Search automatically includes both

---

## Configuration Files

### Configuration Additions
**File:** `config/repositories.yaml`

```yaml
# Existing format
repositories:
  - path: /Users/user/projects/repo1
    enabled: true

# Could extend to:
repositories:
  - path: /Users/user/projects/repo1
    enabled: true

# New section for directories
directories:
  - path: /Users/user/data/docs
    name: Documentation
    enabled: true
    notes: "Shared documentation files"
```

---

## Error Handling

### Directory Validation
- Path must exist and be readable
- Path must be absolute
- Path cannot be duplicated
- Cannot index inside another indexed path (optional)

### Permission Handling
- Log warnings if directory becomes unreadable
- Skip files that cannot be read
- Mark directory as "sync error" in UI

### Recovery
- Gracefully handle deleted directories
- Rescan on startup to detect changes
- Manual retry available in UI

---

## Performance Considerations

### Scalability Targets
- Support 100+ managed directories
- Each directory: 1,000-10,000 files
- Total indexed size: 50GB+

### Optimization Strategies
- Batch directory scanning
- Parallel indexing across directories
- Incremental updates
- Caching of directory stats

---

## Success Criteria

### Phase A-B (Database & Models)
- [ ] Schema migration runs successfully
- [ ] All new database methods work
- [ ] API models serialize/deserialize correctly

### Phase C-D (Indexing & Search)
- [ ] Can index arbitrary directories
- [ ] Search returns results from directories
- [ ] Filtering by directory works
- [ ] Results show correct source information

### Phase E (API)
- [ ] All endpoints respond correctly
- [ ] CRUD operations work
- [ ] Search filtering works via API

### Phase F-G (UI)
- [ ] Directories page loads and displays directories
- [ ] Can add/edit/delete directories
- [ ] Search filter shows directory options
- [ ] Filtering by directories in search works

### Phase H (Watcher)
- [ ] Directories auto-reindex on file changes
- [ ] UI reflects index status

---

## Dependencies & Breaking Changes

### No Breaking Changes
- Existing API continues to work
- Existing database schema preserved
- Existing indexes not affected

### New Dependencies
- None (uses existing libraries)

### Configuration Changes
- Optional: Add directories section to config
- Automatic: Migration runs on startup

---

## Rollback Plan

If issues occur:
1. Keep schema versioning simple (v1 → v2)
2. Old code ignores new tables
3. Migration is reversible (though data loss possible)
4. Manual rollback: Remove `directories` tables

---

## Documentation Updates

### Files to Update/Create
1. `README.md` - Add section on directory indexing
2. `USER_MANUAL.md` - Add directory management guide
3. `API_REFERENCE.md` - Document new endpoints (if exists)
4. `WEB-UI-SPEC.md` - Update with directory UI details
5. `docs/FEATURE_DIRECTORIES.md` (new) - User guide for directories

### Documentation Content
- How to add a directory
- How to search with directories
- UI walkthrough
- API examples
- Configuration examples

---

## Timeline & Resource Estimate

| Phase | Hours | Priority | Owner |
|-------|-------|----------|-------|
| A: Database | 2-3 | 1 | Backend |
| B: Models | 1 | 1 | Backend |
| C: Indexers | 3-4 | 1 | Backend |
| D: Search | 2-3 | 1 | Backend |
| E: API | 2 | 1 | Backend |
| F: Directory UI | 4-5 | 1 | Frontend |
| G: Search Filter UI | 2-3 | 1 | Frontend |
| Testing & Integration | 2-3 | 1 | QA/Dev |
| **Total** | **18-24 hours** | | |

---

## Future Enhancements (Phase 4+)

1. **Auto-Watching:** File watcher for automatic reindexing
2. **Hierarchical Selection:** More sophisticated tree-based selection
3. **Directory Groups:** Organize directories into groups/workspaces
4. **Import/Export:** Share directory configurations
5. **Remote Directories:** Support for network/cloud directories
6. **Ignore Rules:** Per-directory exclude patterns

---

## Related Documents

- `IMPLEMENTATION_PLAN.md` - Overall project plan
- `WEB-UI-SPEC.md` - UI specifications
- `universal-search-service-spec.md` - System architecture
- `docs/myragdb-SYSTEM_ARCHITECTURE.md` - Technical architecture

---

**Questions:** libor@arionetworks.com
