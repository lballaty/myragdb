# MyRAGDB Documentation

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/README.md
**Description:** Index of all documentation files for MyRAGDB
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Available Documentation

### User Documentation

- **[USER_MANUAL.md](USER_MANUAL.md)** - Complete user manual
  - Installation and setup
  - Web UI guide
  - Search features
  - Repository management
  - LLM integration
  - API reference
  - Troubleshooting
  - Best practices

- **[USER_MANUAL.html](USER_MANUAL.html)** - HTML version of user manual
  - Open directly in browser
  - No server required
  - Same content as markdown version

### Technical Documentation

- **[myragdb-SYSTEM_ARCHITECTURE.md](myragdb-SYSTEM_ARCHITECTURE.md)** - System architecture
  - Technical overview
  - Database schemas
  - Component design
  - Performance optimizations
  - Deployment guide

- **[universal-search-service-spec.md](universal-search-service-spec.md)** - API specification
  - REST API endpoints
  - Request/response formats
  - Search algorithms
  - Python client library

- **[WEB-UI-SPEC.md](WEB-UI-SPEC.md)** - Web UI specification
  - UI components
  - Feature requirements
  - User workflows
  - Design guidelines

### Implementation Documentation

- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Development roadmap
  - Phase breakdown
  - Feature milestones
  - Technical requirements

---

## How to Access Documentation

### From Web UI

1. Start the MyRAGDB server
2. Open http://localhost:3002
3. Click **📖 User Manual** button in header

### From Browser (Standalone)

1. Navigate to `docs/` directory
2. Open `USER_MANUAL.html` in any browser
3. No server required

### From Terminal

```bash
# View markdown in terminal
cat docs/USER_MANUAL.md | less

# Or use a markdown viewer
glow docs/USER_MANUAL.md
```

### From API

```bash
# Fetch user manual via API (when server is running)
curl http://localhost:3002/docs/USER_MANUAL.md
```

---

## Documentation Updates

When updating documentation:

1. **Edit markdown files** - Primary source of truth
2. **Update version dates** - In file headers
3. **Test HTML rendering** - Open USER_MANUAL.html to verify
4. **Commit changes** - Include clear description of updates

---

## Questions or Issues

For documentation questions or improvements:
- **Email**: libor@arionetworks.com
- **Location**: `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/`

---

*Last updated: 2026-01-07*
