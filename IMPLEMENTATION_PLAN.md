# MyRAGDB Implementation Plan

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/IMPLEMENTATION_PLAN.md
**Description:** Detailed implementation plan for MyRAGDB hybrid search system
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04

---

## Overview

Build a laptop-wide hybrid search service combining BM25 keyword search with vector embeddings to enable AI agents to intelligently discover and cross-reference code and documentation across all development projects.

## Implementation Strategy

**Approach:** Build full system architecture but deliver working functionality incrementally via "vertical slices"

**Key Principles:**
- Commit after each logical feature completion
- Maintain working state at all commits
- Test each component before moving forward
- Update TODO.md to track granular tasks

---

## Key Technical Decisions

### Confirmed Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Package Name** | `myragdb` | Simple, clear, matches repo name |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` | Fast on CPU (50-100ms), small (80MB), good quality |
| **BM25 Engine** | Whoosh | Pure Python, easy to embed, sufficient for 10K-100K docs |
| **Vector Store** | ChromaDB | Local-first, good Python API, works well with embeddings |
| **API Framework** | FastAPI | Async, auto docs, type hints, Python ecosystem |
| **Web Framework** | React 18 + TypeScript + Vite | Modern, fast, good DX |
| **Port** | 3002 | Per original spec |

### Initial Configuration

**Repositories to Index:**
- `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/xLLMArionComply`
- `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/RepoDot`

**File Types (Priority Order):**
1. `.md` - Markdown documentation
2. `.py` - Python code
3. `.ts`, `.tsx` - TypeScript code
4. `.dart` - Dart/Flutter code

---

## Phase 1: Minimal CLI-Ready System

**Goal:** Working search from command line and Python client
**Estimated Time:** 4-6 hours
**Success Criteria:** Can search from terminal and use in agent code immediately

### Deliverables

1. **Project Structure**
   - Initialize Python package structure
   - Create configuration system
   - Set up dependencies
   - Add .gitignore

2. **Core Indexing**
   - BM25 indexer (Whoosh) - basic implementation
   - Vector indexer (ChromaDB + all-MiniLM-L6-v2)
   - File scanner to discover documents
   - Index xLLMArionComply repository

3. **Search Implementation**
   - Hybrid search (combine BM25 + vector)
   - Result merging and ranking
   - Score normalization

4. **FastAPI Backend**
   - Single endpoint: `POST /search/hybrid`
   - Request/response models (Pydantic)
   - Basic error handling
   - CORS for local development

5. **CLI Interface**
   - Command: `python -m myragdb.cli search "query"`
   - Display formatted results
   - Show scores and file paths

6. **Python Client Library**
   - `SearchClient` class
   - Simple API for agents
   - Example usage

### Verification Steps

```bash
# Install package
pip install -e .

# Start server
python -m myragdb.api.server

# Search from CLI (in new terminal)
python -m myragdb.cli search "authentication flow"

# Use in Python
from myragdb import SearchClient
client = SearchClient()
results = client.search("JWT tokens")
```

---

## Phase 2: Production Backend

**Goal:** Robust, multi-repo, configurable system
**Estimated Time:** 3-4 hours
**Success Criteria:** Production-grade backend ready for agent integration

### Deliverables

1. **Multi-Repository Support**
   - YAML configuration for repositories
   - Repository filtering in queries
   - Index RepoDot and other configured repos
   - Repository priority weighting

2. **Complete API Surface**
   - `POST /search/bm25` - Keyword-only search
   - `POST /search/semantic` - Vector-only search
   - `POST /search/hybrid` - Combined search (already exists)
   - `GET /stats` - Index statistics
   - `POST /index/repository` - Trigger reindexing
   - `GET /repositories` - List configured repos

3. **Metadata Management**
   - SQLite database for file metadata
   - Track: file_path, repository, last_modified, content_hash, last_indexed
   - Incremental indexing (only changed files)
   - Deduplication

4. **Advanced Search Features**
   - File type filtering
   - Date range filtering
   - Min score thresholds
   - Configurable result limits
   - Snippet extraction with context

5. **Production Quality**
   - Structured logging (structlog)
   - Error handling with proper HTTP codes
   - Request validation
   - Performance metrics
   - Health check endpoint

6. **Agent Library Enhancements**
   - `QueryBuilder` for complex queries
   - Retry logic
   - Timeout handling
   - Example agent implementations

### Verification Steps

```bash
# Test all endpoints
curl http://localhost:3002/stats
curl -X POST http://localhost:3002/search/bm25 -H "Content-Type: application/json" -d '{"query": "auth"}'

# Test multi-repo search
python -m myragdb.cli search "authentication" --repos xLLMArionComply RepoDot

# Test agent library
python agent_library/examples/documentation_sync.py
```

---

## Phase 3: Web UI Foundation

**Goal:** Browser-based search interface
**Estimated Time:** 6-8 hours
**Success Criteria:** Functional web UI for search and exploration

### Deliverables

1. **React Project Setup**
   - Vite + React 18 + TypeScript
   - Tailwind CSS configuration
   - Project structure per spec
   - Development server

2. **Core Components**
   - `SearchBar` - Input with debouncing
   - `SearchResults` - Results list
   - `ResultCard` - Individual result display
   - `SearchFilters` - Repository/file type filters
   - `Loading` - Loading states

3. **State Management**
   - Zustand store for search state
   - Settings store for preferences
   - Local storage persistence

4. **API Integration**
   - API client service
   - React Query for data fetching
   - Error handling
   - Loading states

5. **Basic Pages**
   - Search page (main interface)
   - Simple layout with header
   - Responsive design (desktop focus first)

6. **File Preview**
   - Simple text preview (not Monaco yet)
   - Syntax highlighting with Prism.js
   - Line number highlighting
   - Copy to clipboard

### Verification Steps

```bash
# Start backend
python -m myragdb.api.server

# Start frontend (new terminal)
cd web-ui
npm run dev

# Open browser
# Navigate to http://localhost:5173
# Search for "authentication flow"
# Verify results display
# Test filters
# Test preview
```

---

## Phase 4: Advanced Features

**Goal:** Polish and power features
**Estimated Time:** 8-10 hours
**Success Criteria:** Feature-complete system per spec

### Deliverables

1. **Auto-Indexing**
   - File watcher (watchdog)
   - Debounced reindexing
   - Background task queue
   - Progress reporting

2. **Settings Page**
   - Repository management UI
   - Add/remove/edit repositories
   - Manual reindex triggers
   - File pattern configuration

3. **Statistics Dashboard**
   - Index size and file counts
   - Search performance metrics
   - Repository status
   - Performance graphs (recharts)

4. **Search History**
   - Track recent searches
   - Save favorite searches
   - Search suggestions
   - Quick access

5. **Enhanced UI**
   - Monaco editor for preview
   - Keyboard shortcuts
   - Dark mode
   - Virtualized scrolling for large result sets
   - Result pagination

6. **Code-Aware Features**
   - Smart chunking for code files
   - Function/class detection
   - Jump to definition (within preview)
   - Syntax-aware snippet extraction

### Verification Steps

```bash
# Test file watching
# Edit a file in indexed repo
# Wait 5 seconds
# Search for content - should find updated version

# Test settings UI
# Add new repository via UI
# Verify indexing starts
# Check stats dashboard

# Test keyboard shortcuts
# Press Cmd+K - focus search
# Navigate with j/k
# Open preview with Enter
```

---

## Phase 5: Operations & Polish

**Goal:** Production deployment and final polish
**Estimated Time:** 2-3 hours
**Success Criteria:** System runs reliably, auto-starts, fully tested

### Deliverables

1. **System Service Setup**
   - launchd plist configuration
   - Auto-start on boot
   - Service management scripts
   - Log rotation

2. **Performance Optimization**
   - Index caching
   - Embedding cache
   - Query optimization
   - Bundle size optimization (frontend)

3. **Testing**
   - Unit tests for indexers
   - Integration tests for API
   - E2E tests for web UI (Playwright)
   - Performance benchmarks

4. **Documentation**
   - README with quick start
   - API documentation (OpenAPI)
   - Agent integration guide
   - Troubleshooting guide
   - Architecture diagrams

5. **Deployment**
   - Installation script
   - Initial indexing script
   - Backup/restore procedures
   - Upgrade path

### Verification Steps

```bash
# Install as service
./scripts/install_service.sh

# Reboot
sudo reboot

# Verify service running
launchctl list | grep myragdb

# Run full test suite
pytest tests/

# Run benchmarks
python scripts/benchmark.py

# Check all docs render properly
```

---

## Detailed Task Breakdown (TODO.md)

Tasks will be tracked in `TODO.md` with granular items for each phase. Each task will be marked as:
- `[ ]` Pending
- `[~]` In Progress
- `[x]` Completed

Format:
```markdown
## Phase 1: Minimal CLI-Ready System

### 1.1 Project Structure
- [ ] Create directory structure
- [ ] Initialize setup.py
- [ ] Create requirements.txt
- [ ] Add .gitignore
...
```

---

## Commit Strategy

### Commit Frequency
- After each logical unit of work (typically 30-60 min)
- After each TODO item completion
- When switching between major components
- Before and after refactoring

### Commit Message Format

```
<type>: <short description>

<detailed description if needed>

Questions: libor@arionetworks.com
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code restructure
- `docs:` Documentation
- `test:` Testing
- `chore:` Maintenance

### Example Commits

```
feat: initialize project structure

Create base directory layout, setup.py, and requirements.txt
for myragdb package.

Questions: libor@arionetworks.com
```

```
feat: implement BM25 indexer with Whoosh

Add Whoosh-based BM25 indexer supporting file scanning,
indexing, and keyword search.

Questions: libor@arionetworks.com
```

---

## Success Metrics

### Phase 1 Success
- ✅ Can search from CLI
- ✅ Agent code can use SearchClient
- ✅ Search returns relevant results
- ✅ Response time < 500ms

### Phase 2 Success
- ✅ Multiple repositories indexed
- ✅ All API endpoints functional
- ✅ Incremental indexing works
- ✅ Metadata tracked correctly

### Phase 3 Success
- ✅ Web UI loads and works
- ✅ Search results display correctly
- ✅ Filters work
- ✅ Preview shows file content

### Phase 4 Success
- ✅ File changes auto-reindex
- ✅ Settings page manages repos
- ✅ Stats dashboard shows metrics
- ✅ Dark mode works

### Phase 5 Success
- ✅ Service auto-starts
- ✅ Tests pass
- ✅ Performance meets targets
- ✅ Documentation complete

---

## Risk Mitigation

### Potential Issues & Solutions

| Risk | Mitigation |
|------|------------|
| Embedding model too slow | Use smaller model or cache embeddings aggressively |
| Index size too large | Implement compression, exclude large binary files |
| Search quality poor | Tune BM25 parameters, adjust hybrid weights |
| Memory usage too high | Implement lazy loading, index streaming |
| File watching CPU intensive | Debounce aggressively, selective watching |

---

## Timeline Estimate

| Phase | Hours | Cumulative |
|-------|-------|------------|
| Phase 1 | 4-6 | 6h |
| Phase 2 | 3-4 | 10h |
| Phase 3 | 6-8 | 18h |
| Phase 4 | 8-10 | 28h |
| Phase 5 | 2-3 | 31h |

**Total: ~31 hours for complete system**

---

## Next Steps

1. ✅ Document implementation plan (this file)
2. **Next:** Create detailed TODO.md with granular tasks
3. **Next:** Start Phase 1 implementation
4. **Next:** Commit incrementally as tasks complete

---

**Ready to build!**

Questions: libor@arionetworks.com
