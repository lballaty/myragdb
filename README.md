# MyRAGDB

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/README.md
**Description:** Hybrid search system for semantic code and documentation discovery
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04

---

## Overview

MyRAGDB is a laptop-wide hybrid search service that combines BM25 keyword search with vector embeddings to enable AI agents to intelligently discover, cross-reference, and learn from code and documentation across all development projects.

**Key Features:**
- 🔍 **Hybrid Search** - Combines keyword (BM25) and semantic (vector) search
- 🚀 **Fast** - Sub-300ms search across thousands of files
- 🤖 **Agent-First** - Built for AI agent integration
- 🏠 **Local-First** - All data stays on your machine
- 📚 **Multi-Repository** - Search across all your projects simultaneously

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/lballaty/myragdb.git
cd myragdb

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Configure repositories
cp config/repositories.yaml.example config/repositories.yaml
# Edit config/repositories.yaml with your repo paths

# Run initial indexing
python scripts/initial_index.py

# Start server
python -m myragdb.api.server
```

### Usage

#### CLI Search

```bash
# Search from command line
python -m myragdb.cli search "authentication flow"

# With filters
python -m myragdb.cli search "JWT tokens" --repos xLLMArionComply --limit 5
```

#### Python Client (for Agents)

```python
from myragdb import SearchClient

client = SearchClient()
results = client.search("how to implement rate limiting")

for result in results:
    print(f"{result.file_path} (score: {result.score})")
    print(f"  {result.snippet}")
```

#### Web UI

```bash
# Start backend
python -m myragdb.api.server

# In another terminal, start frontend
cd web-ui
npm install
npm run dev

# Open browser to http://localhost:5173
```

## Architecture

```
┌─────────────────────────────────────────┐
│  FastAPI REST Service (localhost:3002)  │
├─────────────────────────────────────────┤
│  POST /search/hybrid    (BM25 + Vector) │
│  POST /search/bm25      (Keyword only)  │
│  POST /search/semantic  (Vector only)   │
│  GET  /stats            (Statistics)    │
└─────────────────────────────────────────┘
           │                    │
    ┌──────┴────────┐    ┌─────┴──────────┐
    │  BM25 Index   │    │  Vector Index  │
    │   (Whoosh)    │    │   (ChromaDB)   │
    └───────────────┘    └────────────────┘
```

## Project Status

**Current Phase:** Phase 1 - Minimal CLI-Ready System
**Next Milestone:** Working CLI search and agent integration

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed roadmap.
See [TODO.md](TODO.md) for granular task tracking.

## Documentation

- [System Specification](universal-search-service-spec.md) - Backend architecture
- [Web UI Specification](WEB-UI-SPEC.md) - Frontend design
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Development roadmap
- [TODO](TODO.md) - Task tracking

## Development

```bash
# Activate virtual environment
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run server with auto-reload
uvicorn myragdb.api.server:app --reload --port 3002
```

## Configuration

Edit `config/repositories.yaml` to add your repositories:

```yaml
repositories:
  - name: MyProject
    path: /path/to/your/project
    enabled: true
    file_patterns:
      include:
        - "**/*.md"
        - "**/*.py"
      exclude:
        - "**/node_modules/**"
        - "**/.git/**"
```

## License

Private project - All rights reserved

---

**Questions:** libor@arionetworks.com
