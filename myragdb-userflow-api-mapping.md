# MyRAGDB API Mapping and User Flow Documentation
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/myragdb-userflow-api-mapping.md
**Description:** Complete mapping of frontend API calls to backend endpoints with user flows
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-10

---

## API Structure Analysis

### Updated State (As of 2026-01-10) - More Consistent API Structure

1. **Root Level Routes** (no prefix) - Main app routes (health, search, repositories, etc.)
2. **`/api/v1/*` Routes** - All modular routers:
   - `/api/v1/directories/*` - Directory management (UPDATED)
   - `/api/v1/activities` - Activity logs
   - `/api/v1/llm-config/*` - LLM configuration
   - `/api/v1/observability/*` - Observability metrics

The directories router has been updated to use `/api/v1` prefix for consistency.

---

## Backend API Endpoints

### Main App Routes (server.py - NO PREFIX)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Static file server |
| `/health` | GET | Health check |
| `/version` | GET | Version info |
| `/admin/restart` | POST | Restart server |
| `/logs` | GET | Get logs |
| `/stats` | GET | Statistics |
| `/repositories` | GET | List repositories |
| `/repositories/discover` | POST | Discover repos |
| `/repositories/add-batch` | POST | Add multiple repos |
| `/repositories/{repo_name}` | DELETE | Delete repository |
| `/repositories/{repository}/auto-reindex` | POST | Toggle auto-reindex |
| `/repositories/{repository}/readme` | GET | Get README |
| `/search/hybrid` | POST | Hybrid search |
| `/search/keyword` | POST | Keyword search |
| `/search/semantic` | POST | Semantic search |
| `/reindex` | POST | Trigger reindex |
| `/stop-indexing` | POST | Stop indexing |
| `/llm/models` | GET | List LLM models |
| `/llm/start` | POST | Start LLM |
| `/llm/stop` | POST | Stop LLM |
| `/llm/session` | GET | Get LLM session |
| `/llm/providers` | GET | List providers |
| `/llm/validate-credentials` | POST | Validate creds |
| `/llm/switch` | POST | Switch LLM |
| `/llm/authenticated` | GET | Check auth status |
| `/llm/logout/{provider}` | POST | Logout provider |
| `/llm/health` | GET | LLM health check |
| `/observability/stats` | GET | Observability stats |
| `/observability/metrics` | POST | Get metrics |
| `/observability/cleanup` | POST | Cleanup old data |
| `/watcher/status` | GET | Watcher status |

### Directories Router (prefix: `/api/v1/directories`) - UPDATED
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/directories` | GET | List directories |
| `/api/v1/directories` | POST | Add directory |
| `/api/v1/directories/browse` | GET | Browse filesystem |
| `/api/v1/directories/bulk-update` | PATCH | Bulk enable/disable |
| `/api/v1/directories/reindex` | POST | Reindex all dirs |
| `/api/v1/directories/{id}` | GET | Get directory |
| `/api/v1/directories/{id}` | PATCH | Update directory |
| `/api/v1/directories/{id}` | DELETE | Delete directory |
| `/api/v1/directories/{id}/reindex` | POST | Reindex single dir |
| `/api/v1/directories/{id}/discover` | GET | Discover files |

### Activities Router (prefix: `/api/v1`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/activities` | GET | Get activity log |

### LLM Config Router (prefix: `/api/v1`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/llm-config/provider` | GET | Get provider config |
| `/api/v1/llm-config/provider` | POST | Set provider config |
| `/api/v1/llm-config/provider` | DELETE | Delete config |
| `/api/v1/llm-config/provider/{provider}` | GET | Get specific provider |
| `/api/v1/llm-config/provider/{provider}` | PUT | Update provider |

### Observability Router (prefix: `/api/v1`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/observability/metrics` | POST | Get detailed metrics |
| `/api/v1/observability/cleanup` | POST | Cleanup old metrics |

---

## Frontend API Calls (app.js)

### Current API_BASE_URL Setting
```javascript
const API_BASE_URL = 'http://localhost:3003';  // NO /api/v1 suffix
```

### All Frontend API Calls
| Frontend Call | Backend Endpoint | Status |
|---------------|------------------|--------|
| `${API_BASE_URL}/health` | `/health` | ✅ Works |
| `${API_BASE_URL}/version` | `/version` | ✅ Works |
| `${API_BASE_URL}/admin/restart` | `/admin/restart` | ✅ Works |
| `${API_BASE_URL}/logs` | `/logs` | ✅ Works |
| `${API_BASE_URL}/stats` | `/stats` | ✅ Works |
| `${API_BASE_URL}/repositories` | `/repositories` | ✅ Works |
| `${API_BASE_URL}/repositories/discover` | `/repositories/discover` | ✅ Works |
| `${API_BASE_URL}/repositories/add-batch` | `/repositories/add-batch` | ✅ Works |
| `${API_BASE_URL}/repositories/${name}/readme` | `/repositories/{name}/readme` | ✅ Works |
| `${API_BASE_URL}/search/${type}` | `/search/{type}` | ✅ Works |
| `${API_BASE_URL}/reindex` | `/reindex` | ✅ Works |
| `${API_BASE_URL}/llm/models` | `/llm/models` | ✅ Works |
| `${API_BASE_URL}/llm/providers` | `/llm/providers` | ✅ Works |
| `${API_BASE_URL}/llm/start` | `/llm/start` | ✅ Works |
| `${API_BASE_URL}/llm/stop` | `/llm/stop` | ✅ Works |
| `${API_BASE_URL}/api/v1/directories` | `/api/v1/directories` | ✅ Works |
| `${API_BASE_URL}/api/v1/directories/${id}` | `/api/v1/directories/{id}` | ✅ Works |
| `${API_BASE_URL}/api/v1/directories/${id}/reindex` | `/api/v1/directories/{id}/reindex` | ✅ Works |
| `${API_BASE_URL}/api/v1/directories/browse` | `/api/v1/directories/browse` | ✅ Works |
| `${API_BASE_URL}/api/v1/directories/bulk-update` | `/api/v1/directories/bulk-update` | ✅ Works |
| `${API_BASE_URL}/api/v1/directories/reindex` | `/api/v1/directories/reindex` | ✅ Works |

**Note:** Frontend now uses `/api/v1/directories/*` routes for directories. Other `/api/v1/*` routes (activities, llm-config, observability) are still not used by the frontend.

---

## User Flows

### 1. Search Flow
```
User enters search query
→ app.js: fetch(`${API_BASE_URL}/search/hybrid`)
→ Backend: POST /search/hybrid
→ Returns search results
```

### 2. Repository Management Flow
```
User clicks "Scan for Repositories"
→ app.js: fetch(`${API_BASE_URL}/repositories/discover`)
→ Backend: POST /repositories/discover
→ Returns discovered repos

User adds selected repos
→ app.js: fetch(`${API_BASE_URL}/repositories/add-batch`)
→ Backend: POST /repositories/add-batch
→ Repos added to index
```

### 3. Directory Management Flow
```
User adds directory
→ app.js: fetch(`${API_BASE_URL}/api/v1/directories`)
→ Backend: POST /api/v1/directories
→ Directory added

User deletes directory
→ app.js: fetch(`${API_BASE_URL}/api/v1/directories/${id}`)
→ Backend: DELETE /api/v1/directories/{id}
→ Directory removed

User reindexes selected directories
→ app.js: fetch(`${API_BASE_URL}/api/v1/directories/${id}/reindex`)
→ Backend: POST /api/v1/directories/{id}/reindex
→ Reindexing triggered
```

### 4. LLM Management Flow
```
User starts LLM
→ app.js: fetch(`${API_BASE_URL}/llm/start`)
→ Backend: POST /llm/start
→ LLM process started

User stops LLM
→ app.js: fetch(`${API_BASE_URL}/llm/stop`)
→ Backend: POST /llm/stop
→ LLM process stopped
```

---

## Current Status (RESOLVED)

### ✅ Consistency Improvements Made
- Directories router moved from `/directories/*` to `/api/v1/directories/*`
- Frontend updated to use `/api/v1/directories/*` endpoints
- All modular routers now consistently use `/api/v1` prefix

### Remaining Structure
1. **Root Level Routes**: Main app routes (health, search, repositories, etc.)
2. **`/api/v1/*` Routes**: All modular routers (directories, activities, llm-config, observability)

### Unused API Endpoints (Still Present)
- `/api/v1/activities` - Not called by frontend (could be used for future features)
- `/api/v1/llm-config/*` - Not called by frontend (backend-only configuration)
- `/api/v1/observability/*` - Not called by frontend (duplicates exist at root)

---

## Implementation Status

### ✅ Partial Implementation of Option B Completed

We chose **Option B: Move Everything to `/api/v1`** for consistency and implemented the most critical part:

**Completed:**
1. ✅ Changed directories router: `prefix="/api/v1/directories"`
2. ✅ Updated all frontend directories API calls to use `/api/v1/directories/*`
3. ✅ Updated documentation to reflect changes

**Still Pending (Future Work):**
1. ⏳ Move main app routes under `/api/v1` router (health, search, repositories, etc.)
2. ⏳ Update `API_BASE_URL = 'http://localhost:3003/api/v1'` (when all routes are moved)

### Current Hybrid State
- **Root Level**: Main app routes (`/health`, `/search/*`, `/repositories/*`, etc.)
- **`/api/v1`**: All modular routers (directories, activities, llm-config, observability)

This hybrid approach works well:
- Main app routes remain stable at root (no breaking changes for existing integrations)
- New modular features use `/api/v1` prefix (better organization going forward)
- Frontend works correctly with both patterns

---

## Testing Checklist

After implementing changes, test:

- [ ] Health check endpoint
- [ ] Search (hybrid, keyword, semantic)
- [ ] Repository listing
- [ ] Repository discovery
- [ ] Repository addition
- [ ] Directory listing
- [ ] Directory addition
- [ ] Directory deletion
- [ ] Directory reindexing (single)
- [ ] Directory reindexing (selected)
- [ ] Directory bulk operations
- [ ] LLM start/stop
- [ ] Statistics loading
- [ ] Activity logging
- [ ] Version check

---

Questions: libor@arionetworks.com