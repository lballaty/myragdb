# MyRAGDB Search API Reference

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/SEARCH_API_REFERENCE.md
**Description:** Complete REST API reference for MyRAGDB hybrid search functionality
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

The MyRAGDB Search API provides comprehensive search capabilities combining keyword matching and semantic understanding across multiple repositories and directories. All endpoints are REST-based and return JSON responses.

**Base URL:** `http://localhost:3003/api/v1`

**Protocol:** HTTP REST
**Content-Type:** application/json
**Authentication:** None (future phases will add API keys)

---

## Core Concepts

### Search Types

MyRAGDB supports three search paradigms:

1. **Hybrid Search** (Recommended)
   - Combines keyword matching with semantic understanding
   - Uses Reciprocal Rank Fusion (RRF) to merge results
   - Best for natural language queries
   - Endpoint: `POST /search/hybrid`

2. **Keyword Search**
   - Fast exact and fuzzy matching
   - Uses Meilisearch for typo-tolerant search
   - Best for specific terms and file names
   - Endpoint: `POST /search/keyword`

3. **Semantic Search**
   - Understanding meaning and intent
   - Uses ChromaDB with sentence transformers
   - Best for conceptual searches
   - Endpoint: `POST /search/semantic`

### Filter Types

All search endpoints support the following filters:

| Filter | Type | Format | Example | Purpose |
|--------|------|--------|---------|---------|
| `repositories` | List[string] | Repository names | `["xLLMArionComply"]` | Search specific repos |
| `directories` | List[int] | Directory IDs | `[1, 2, 3]` | Search managed directories |
| `folder_filter` | string | Folder path | `"src/components"` | Scope to folder |
| `extension_filter` | string | File extension | `".py"` | Filter by file type |
| `file_types` | List[string] | Extensions | `[".md", ".py"]` | Multiple file types |
| `date_from` | string | ISO 8601 (YYYY-MM-DD) | `"2025-01-01"` | From date (inclusive) |
| `date_to` | string | ISO 8601 (YYYY-MM-DD) | `"2026-01-07"` | To date (inclusive) |
| `min_score` | float | 0.0 to 1.0 | `0.5` | Minimum relevance threshold |
| `limit` | int | 1 to 100 | `10` | Max results to return |

---

## Hybrid Search Endpoint

### POST /search/hybrid

Execute hybrid search combining keyword and semantic approaches.

**URL:** `http://localhost:3003/api/v1/search/hybrid`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "how to implement JWT authentication",
  "search_type": "hybrid",
  "repositories": ["xLLMArionComply"],
  "directories": [1],
  "folder_filter": "src/auth",
  "extension_filter": ".py",
  "file_types": [".py", ".md"],
  "date_from": "2025-01-01",
  "date_to": "2026-01-07",
  "min_score": 0.5,
  "limit": 10
}
```

**Request Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (natural language or keywords) |
| `search_type` | string | No | "hybrid" | Type of search: hybrid, keyword, semantic |
| `repositories` | string[] | No | All | Filter by specific repositories |
| `directories` | int[] | No | All | Filter by managed directory IDs |
| `folder_filter` | string | No | - | Limit search to specific folder path |
| `extension_filter` | string | No | - | Filter by single file extension (e.g., ".py") |
| `file_types` | string[] | No | - | Filter by multiple file extensions |
| `date_from` | string | No | - | Start date in YYYY-MM-DD format (inclusive) |
| `date_to` | string | No | - | End date in YYYY-MM-DD format (inclusive) |
| `min_score` | float | No | 0.0 | Minimum relevance score (0.0-1.0) |
| `limit` | int | No | 10 | Maximum results (1-100) |

**Response (200 OK):**
```json
{
  "results": [
    {
      "file_path": "/path/to/file.py",
      "repository": "xLLMArionComply",
      "relative_path": "src/auth/jwt_handler.py",
      "score": 0.92,
      "keyword_score": 0.85,
      "vector_score": 0.98,
      "snippet": "def validate_jwt_token(token: str) -> bool:\n    '''Validate JWT token expiration and signature.'''\n    try:\n        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])\n        return decoded is not None\n    except jwt.InvalidTokenError:\n        return False",
      "file_type": "py"
    }
  ],
  "query": "how to implement JWT authentication",
  "search_type": "hybrid",
  "total_results": 1,
  "response_time_ms": 145,
  "filters_applied": {
    "repositories": ["xLLMArionComply"],
    "date_range": "2025-01-01 to 2026-01-07",
    "min_score": 0.5
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `results` | object[] | Array of search result items |
| `results[].file_path` | string | Full absolute path to file |
| `results[].repository` | string | Source repository name |
| `results[].relative_path` | string | Path relative to repository root |
| `results[].score` | float | Combined relevance score (0-1) |
| `results[].keyword_score` | float | Keyword matching score |
| `results[].vector_score` | float | Semantic similarity score |
| `results[].snippet` | string | Relevant code/text excerpt (600 chars) |
| `results[].file_type` | string | File extension (py, ts, md, etc.) |
| `query` | string | Echoed search query |
| `search_type` | string | Type of search performed |
| `total_results` | int | Total number of results |
| `response_time_ms` | int | Time to execute search |
| `filters_applied` | object | Summary of filters that were applied |

**Example cURL Request:**
```bash
curl -X POST http://localhost:3003/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication",
    "limit": 5,
    "date_from": "2025-01-01",
    "date_to": "2026-01-07",
    "min_score": 0.6
  }'
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Query is required and must be at least 1 character"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "detail": "Search failed: Connection to Meilisearch failed"
}
```

---

## Keyword Search Endpoint

### POST /search/keyword

Execute keyword-only search using Meilisearch (fast, exact matching).

**URL:** `http://localhost:3003/api/v1/search/keyword`

**Request Body:**
```json
{
  "query": "JWT token",
  "limit": 10,
  "date_from": "2025-01-01",
  "date_to": "2026-01-07",
  "min_score": 0.3
}
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "file_path": "/path/to/file.py",
      "repository": "xLLMArionComply",
      "relative_path": "src/auth/jwt_handler.py",
      "score": 0.88,
      "keyword_score": 0.88,
      "vector_score": null,
      "snippet": "JWT token validation implementation...",
      "file_type": "py"
    }
  ],
  "query": "JWT token",
  "search_type": "keyword",
  "total_results": 15,
  "response_time_ms": 35
}
```

**Notes:**
- Faster than hybrid search (typically 20-50ms)
- Best for finding exact terms and file names
- No semantic understanding (won't find "how to authenticate" when searching "JWT")
- Supports typo tolerance (finds "authentiation" when searching "authentication")

---

## Semantic Search Endpoint

### POST /search/semantic

Execute semantic-only search using vector embeddings (conceptual understanding).

**URL:** `http://localhost:3003/api/v1/search/semantic`

**Request Body:**
```json
{
  "query": "how do users log in to the system",
  "limit": 10,
  "date_from": "2025-01-01",
  "date_to": "2026-01-07",
  "min_score": 0.4
}
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "file_path": "/path/to/file.py",
      "repository": "xLLMArionComply",
      "relative_path": "src/auth/login.py",
      "score": 0.85,
      "keyword_score": null,
      "vector_score": 0.85,
      "snippet": "def authenticate_user(username, password):\n    '''Handle user login and token generation.'''",
      "file_type": "py"
    }
  ],
  "query": "how do users log in to the system",
  "search_type": "semantic",
  "total_results": 8,
  "response_time_ms": 215
}
```

**Notes:**
- Slower than keyword search (typically 100-300ms)
- Understands meaning and intent
- Will find "login implementation" when searching "how users authenticate"
- Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings

---

## Date Range Filtering

### How Date Filtering Works

Files are indexed with their modification timestamp (`last_modified`). The `date_from` and `date_to` parameters filter results based on this timestamp.

**Date Format:** ISO 8601 (YYYY-MM-DD)

**Behavior:**
- `date_from`: Inclusive (results >= this date)
- `date_to`: Inclusive (results <= this date, end of day)
- Both optional - omit either to search without that constraint
- Applied after initial search, not during indexing

**Example 1: Search this year**
```json
{
  "query": "authentication",
  "date_from": "2026-01-01",
  "date_to": "2026-12-31"
}
```

**Example 2: Recent files only**
```json
{
  "query": "database migration",
  "date_from": "2025-12-01"
}
```

**Example 3: Specific month**
```json
{
  "query": "security",
  "date_from": "2025-06-01",
  "date_to": "2025-06-30"
}
```

---

## Score Filtering

### How Score Filtering Works

Each search result receives a relevance score between 0.0 and 1.0:

- **Keyword Score:** How well text matches (Meilisearch relevance)
- **Vector Score:** How semantically similar content is (0-1 normalized)
- **Combined Score (Hybrid):** RRF fusion of both scores

The `min_score` parameter filters out results below the threshold.

**Typical Score Ranges:**
- **0.0-0.3:** Weak match, consider removing
- **0.3-0.6:** Moderate match, may have false positives
- **0.6-0.8:** Good match, likely relevant
- **0.8-1.0:** Excellent match, highly relevant

**Example 1: High precision (only best results)**
```json
{
  "query": "JWT validation",
  "min_score": 0.8,
  "limit": 10
}
```

**Example 2: Broader recall (include loosely related)**
```json
{
  "query": "authentication",
  "min_score": 0.3,
  "limit": 50
}
```

---

## Health Check Endpoint

### GET /health

Check if the search service is healthy and all dependencies are available.

**URL:** `http://localhost:3003/health`

**Response (200 OK):**
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "services": {
    "meilisearch": "operational",
    "chromadb": "operational",
    "database": "operational"
  }
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "message": "ChromaDB unavailable",
  "services": {
    "meilisearch": "operational",
    "chromadb": "unavailable",
    "database": "operational"
  }
}
```

---

## Statistics Endpoint

### GET /stats

Get overall search statistics and index information.

**URL:** `http://localhost:3003/api/v1/stats`

**Response (200 OK):**
```json
{
  "total_searches": 1247,
  "avg_response_time_ms": 156,
  "total_indexed_files": 29,
  "repositories": [
    {
      "name": "xLLMArionComply",
      "total_files": 26731,
      "indexed_files": 26731,
      "status": "indexed"
    },
    {
      "name": "RepoTools",
      "total_files": 3282,
      "indexed_files": 3282,
      "status": "indexed"
    }
  ],
  "indexes": {
    "meilisearch": {
      "size_bytes": 494272512,
      "document_count": 29013,
      "status": "operational"
    },
    "chromadb": {
      "size_bytes": 4610000000,
      "collection_count": 2,
      "chunk_count": 365232,
      "status": "operational"
    }
  },
  "last_index_time": 1735000000
}
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Search completed, results returned |
| 400 | Bad Request | Missing required field, invalid format |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Database/service failure |
| 503 | Service Unavailable | Meilisearch or ChromaDB down |

**Error Response Format:**
```json
{
  "detail": "Detailed error message explaining what went wrong"
}
```

---

## Rate Limiting

Currently no rate limiting is enforced. Future versions will implement:
- Per-IP limits
- Per-API-key limits
- Request queuing

---

## Python Client Example

Using the SearchClient library:

```python
from agent_library import SearchClient, QueryBuilder

# Initialize client
client = SearchClient(base_url="http://localhost:3003")

# Simple search
results = client.search("JWT authentication")
for result in results:
    print(f"{result.relative_path}: {result.score}")

# Advanced filtered search using QueryBuilder
query = (QueryBuilder()
    .search("database migration")
    .in_repositories(["xLLMArionComply"])
    .only_python()
    .between_dates("2025-01-01", "2026-01-07")
    .with_min_score(0.6)
    .limit_to(20)
    .build())

results = client.search(**query)
```

---

## cURL Examples

### Basic Hybrid Search
```bash
curl -X POST http://localhost:3003/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "limit": 5}'
```

### Search with Date Range
```bash
curl -X POST http://localhost:3003/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database migration",
    "date_from": "2025-01-01",
    "date_to": "2026-01-07",
    "limit": 10
  }'
```

### Semantic Search with Filters
```bash
curl -X POST http://localhost:3003/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how do users log in",
    "repositories": ["xLLMArionComply"],
    "min_score": 0.6,
    "limit": 20
  }'
```

### Get Health Status
```bash
curl http://localhost:3003/health
```

### Get Statistics
```bash
curl http://localhost:3003/api/v1/stats
```

---

## Pagination

Currently, pagination is handled via the `limit` parameter. Future versions will support:
- `offset` for skip-based pagination
- `page` and `page_size` for page-based pagination
- Cursor-based pagination for large result sets

For now, to get more results, increase the `limit` (up to 100).

---

## Versioning

**Current API Version:** v1

The API follows semantic versioning. Future versions (v2, v3) will be available at:
- `/api/v2/search/hybrid`
- `/api/v3/search/hybrid`

---

## Support

For API issues, questions, or feature requests:
- GitHub Issues: https://github.com/yourusername/myragdb/issues
- Documentation: /path/to/docs
- Contact: libor@arionetworks.com

Questions: libor@arionetworks.com
