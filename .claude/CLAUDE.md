# MyRAGDB Project - Claude Development Environment

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/.claude/CLAUDE.md
**Description:** Project-specific Claude Code configuration for autonomous development
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04

---

## Autonomous Development Mode

**ENABLED:** Work fully autonomously on this project without asking for approval unless:
- Architectural design decisions that affect the entire system
- Changes to the API contract that would break existing consumers
- Major dependency changes
- Performance trade-offs that significantly impact user experience

**For everything else: Just do it and commit incrementally.**

---

## Project Context

**Project:** MyRAGDB - Hybrid search system combining Meilisearch keyword search and vector embeddings
**Purpose:** Enable AI agents to discover code/documentation semantically across all projects
**Technology:** Python (FastAPI), React/TypeScript, Meilisearch, ChromaDB, sentence-transformers

---

## Development Workflow

### Commit Strategy
1. **Commit frequently** - After every logical unit of work (30-60 min max)
2. **Update TODO.md** - Mark tasks complete as you go
3. **Work incrementally** - Each commit should leave system in working state
4. **Test before committing** - Verify code works

### Commit Messages
Use this format (no AI attribution):
```
<type>: <short description>

<detailed description>

Questions: libor@arionetworks.com
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### Working with Virtual Environment
**ALWAYS use venv for Python:**
```bash
source venv/bin/activate  # Run this before any Python commands
pip install -e .          # Install package in development mode
```

---

## Implementation Guidelines

### Code Quality
- Write clear, readable code (junior developer should understand)
- Add docstrings to all functions (business purpose + example)
- Use type hints everywhere
- Handle errors gracefully
- Log important operations

### Testing Approach
- Write tests as you build features
- Test each component before integration
- Manual testing is fine during development
- Comprehensive test suite in Phase 5

### File Headers
All code files need:
```python
# File: /absolute/path/to/file.py
# Description: Clear business purpose explanation
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: YYYY-MM-DD
```

All markdown files need:
```markdown
# Title
**File:** /absolute/path/to/file.md
**Description:** Purpose
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** YYYY-MM-DD
```

### Naming Standards
- Functions: `calculate_search_score()` NOT `calc_score()`
- Variables: `user_query_text` NOT `query`
- Classes: `HybridSearchEngine` NOT `HSE`
- Files: `vector_indexer.py` NOT `vec_idx.py`

---

## Project-Specific Rules

### Repository Paths
Default repositories to index:
- `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/xLLMArionComply`
- `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/RepoDot`

### Configuration
- Port: 3002 (FastAPI backend)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Keyword weights: 0.4
- Vector weights: 0.6
- Default result limit: 10

### File Types to Index (Priority)
1. `.md` - Markdown documentation
2. `.py` - Python code
3. `.ts`, `.tsx` - TypeScript code
4. `.dart` - Dart/Flutter code

### Exclude Patterns
- `**/node_modules/**`
- `**/.git/**`
- `**/venv/**`
- `**/archive-*/**`
- `**/*.lock`
- `**/__pycache__/**`

---

## Phase Execution

### Current Phase: Phase 1 - Minimal CLI-Ready System
**Goal:** Working search from CLI and Python client

**Track progress in TODO.md** - Mark tasks with:
- `[ ]` Pending
- `[~]` In Progress
- `[x]` Completed

### Implementation Order
Follow TODO.md task order strictly. Complete each section before moving to next.

### When Stuck
- Check specifications (universal-search-service-spec.md, WEB-UI-SPEC.md)
- Check implementation plan (IMPLEMENTATION_PLAN.md)
- If truly blocked by a design decision, ask user
- Otherwise, make reasonable choice and document in commit message

---

## Testing & Validation

### Phase 1 Success Criteria
- ✅ Can search from CLI: `python -m myragdb.cli search "query"`
- ✅ Agent code works: `from myragdb import SearchClient`
- ✅ Search returns relevant results
- ✅ Response time < 500ms

### How to Test
```bash
# Activate venv
source venv/bin/activate

# Start server
python -m myragdb.api.server

# In another terminal (also activate venv):
python -m myragdb.cli search "authentication flow"
```

---

## Dependencies Installation

When adding new code that requires dependencies:
```bash
source venv/bin/activate
pip install -e .  # Installs from setup.py
```

If you add new dependencies:
1. Add to setup.py `install_requires`
2. Add to requirements.txt
3. Run `pip install -e .`
4. Commit both files

---

## Directory Structure Reference

```
myragdb/
├── src/myragdb/          # Main package
│   ├── api/              # FastAPI server
│   ├── indexers/         # Meilisearch and vector indexing
│   ├── search/           # Search logic
│   └── db/               # Metadata database
├── agent_library/        # Client for agents
├── config/               # YAML configuration
├── scripts/              # Utility scripts
├── tests/                # Test suite
├── data/                 # Indexes (gitignored)
└── venv/                 # Virtual environment (gitignored)
```

---

## Error Handling

### When Code Fails
1. Read error message carefully
2. Check file paths are correct
3. Verify venv is activated
4. Check imports are correct
5. Fix and test
6. Commit the fix

### When Tests Fail
1. Determine if production code bug or test infrastructure issue
2. Fix the root cause (usually production code during development)
3. Test manually to verify
4. Commit

---

## Performance Targets

### Search Performance
- Keyword search: < 50ms
- Vector search: < 200ms
- Hybrid search: < 300ms
- Index update: < 100ms per file

### Scalability Targets
- Total files: 10,000 (initial), 50,000 (target)
- Index size: ~3GB
- Memory usage: < 8GB

If performance is slow:
- Add caching
- Optimize queries
- Profile and fix bottlenecks
- Document performance in commit message

---

## Communication

### When to Ask User
- Architectural design decisions
- API contract changes
- Major dependency changes
- Performance trade-offs requiring business judgment

### When NOT to Ask User
- Implementation details
- Code organization
- Minor refactoring
- Bug fixes
- Test writing
- Documentation updates
- Dependency version updates (within constraints)

**Default: Just build it. Ask only when truly necessary.**

---

## Incremental Delivery

### Build Vertical Slices
Each phase should deliver working functionality:
- Phase 1: CLI works, agents can use it
- Phase 2: Multi-repo, full API
- Phase 3: Web UI works
- Phase 4: Advanced features
- Phase 5: Production ready

### Always Keep It Working
- Every commit should leave code in runnable state
- If breaking change needed, do it in one commit
- Test before committing

---

## Example Development Session

```bash
# Morning: Start work
cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
source venv/bin/activate

# Work on feature (e.g., keyword indexer)
# Write code in src/myragdb/indexers/meilisearch_indexer.py
# Test manually
python -c "from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer; ..."

# Update TODO.md - mark task complete
# Commit
git add src/myragdb/indexers/meilisearch_indexer.py TODO.md
git commit -m "feat: implement keyword indexer with Meilisearch
..."

# Continue with next task
```

---

## Current Status

**Phase:** 1 (Minimal CLI-Ready System)
**Last Commit:** Project structure initialization
**Next Task:** Configuration system (TODO.md section 1.2)

---

**Remember: You have full autonomy. Build, test, commit, repeat. Only ask when critical design decisions are needed.**

Questions: libor@arionetworks.com
