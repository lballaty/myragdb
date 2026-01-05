# MyRAGDB Port Reservations
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/PORT-RESERVATIONS.md
**Description:** Port reservation registry for MyRAGDB services
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04
**Last Updated:** 2026-01-04
**Last Updated By:** Libor Ballaty <libor@arionetworks.com>

---

## Reserved Ports

```
MyRAGDB Services:
└── 3003 - MyRAGDB API & Web UI (FastAPI)    [myragdb]
```

## Port Details

### 3003 - MyRAGDB API & Web UI
- **Service**: MyRAGDB Hybrid Search System
- **Technology**: FastAPI (Python)
- **Purpose**:
  - REST API for search operations (hybrid, BM25, semantic)
  - Web UI for search interface and activity monitoring
  - Health check and statistics endpoints
- **Endpoints**:
  - `GET /` - Web UI
  - `GET /health` - Health check
  - `GET /stats` - Index statistics
  - `POST /search/hybrid` - Hybrid search
  - `POST /search/keyword` - Keyword search
  - `POST /search/semantic` - Vector semantic search
- **Start Command**: `python -m myragdb.api.server`
- **Environment Variable**: `MYRAGDB_PORT=3003`

## Integration Notes

This port is reserved separately from the main ArionComply project ports. MyRAGDB is an independent service providing search capabilities across multiple repositories.

---

Questions: libor@arionetworks.com
