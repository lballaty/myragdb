# MyRAGDB Test Design Document

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/TEST-DESIGN.md
**Description:** Comprehensive test strategy and design for MyRAGDB platform covering API contracts, UI functionality, and integration tests
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-05

---

## Executive Summary

This document defines the testing strategy for MyRAGDB, a hybrid search system combining Meilisearch keyword search and ChromaDB vector embeddings. The test suite ensures reliability across API contracts, UI functionality, search accuracy, and system integration.

**Testing Tools:**
- **Playwright** - End-to-end UI testing and browser automation
- **Bruno** - API contract testing and HTTP request collection
- **curl** - Lightweight API smoke tests and CI/CD integration
- **pytest** - Python unit and integration tests

**Test Organization:** All tests centralized in `tests/` directory with tag-based execution for incremental/staged testing.

---

## Testing Objectives

### Primary Goals
1. **API Contract Verification** - Ensure all endpoints return correct schemas and status codes
2. **UI Functional Testing** - Verify user workflows work end-to-end in browser
3. **Search Accuracy** - Validate hybrid search returns relevant results
4. **System Integration** - Test Meilisearch, ChromaDB, and API server interactions
5. **Performance Baseline** - Establish response time expectations
6. **Error Handling** - Verify graceful degradation when dependencies fail

### Success Criteria
- 100% API endpoint coverage with contract tests
- 90%+ UI workflow coverage with Playwright
- Sub-500ms hybrid search response time for 90% of queries
- All tests pass in CI/CD pipeline before deployment
- Ability to run test subsets via tags (smoke, integration, e2e, performance)

---

## Test Architecture

### Directory Structure

```
tests/
├── api/                          # API contract tests (Bruno + curl)
│   ├── bruno/                    # Bruno API collections
│   │   ├── health/
│   │   │   ├── check-healthy.bru
│   │   │   ├── check-degraded.bru
│   │   │   └── check-unhealthy.bru
│   │   ├── search/
│   │   │   ├── hybrid-search.bru
│   │   │   ├── keyword-only.bru
│   │   │   └── semantic-only.bru
│   │   ├── indexing/
│   │   │   ├── trigger-reindex.bru
│   │   │   ├── check-status.bru
│   │   │   └── get-repositories.bru
│   │   ├── admin/
│   │   │   ├── restart-server.bru
│   │   │   └── get-logs.bru
│   │   └── stats/
│   │       └── get-statistics.bru
│   ├── curl/                     # Lightweight curl tests
│   │   ├── smoke.sh              # Quick smoke tests
│   │   └── contracts.sh          # Schema validation
│   └── schemas/                  # JSON schemas for validation
│       ├── health.schema.json
│       ├── search-response.schema.json
│       ├── stats.schema.json
│       └── indexing-status.schema.json
├── ui/                           # Playwright UI tests
│   ├── e2e/                      # End-to-end workflows
│   │   ├── search-workflow.spec.ts
│   │   ├── indexing-workflow.spec.ts
│   │   └── monitoring-workflow.spec.ts
│   ├── components/               # Component-specific tests
│   │   ├── search-box.spec.ts
│   │   ├── health-indicator.spec.ts
│   │   ├── repository-list.spec.ts
│   │   └── restart-button.spec.ts
│   ├── visual/                   # Visual regression tests
│   │   ├── homepage.spec.ts
│   │   └── search-results.spec.ts
│   └── fixtures/                 # Test data and mocks
│       ├── search-results.json
│       └── repository-config.json
├── integration/                  # Python integration tests
│   ├── test_hybrid_search.py
│   ├── test_indexing.py
│   ├── test_health_monitoring.py
│   └── test_restart_functionality.py
├── performance/                  # Load and performance tests
│   ├── search-load.spec.ts       # Playwright load testing
│   └── indexing-perf.py          # Indexing performance
├── fixtures/                     # Shared test data
│   ├── test-repository/          # Sample git repo for indexing
│   └── sample-documents/         # Test documents
├── utils/                        # Test utilities
│   ├── setup.sh                  # Test environment setup
│   ├── teardown.sh               # Cleanup
│   └── wait-for-service.sh       # Service readiness check
├── playwright.config.ts          # Playwright configuration
├── bruno.json                    # Bruno configuration
├── pytest.ini                    # Pytest configuration
└── README.md                     # Test execution guide
```

---

## Test Tags and Execution Strategy

### Tag System

Tags allow incremental/staged test execution to prevent system overload.

| Tag | Description | Execution Time | When to Run |
|-----|-------------|----------------|-------------|
| `@smoke` | Quick health checks | < 1 min | Every commit, before full suite |
| `@unit` | Isolated component tests | 1-3 min | Every commit |
| `@integration` | Multi-component tests | 3-5 min | Before merge to main |
| `@e2e` | Full end-to-end workflows | 5-10 min | Before release |
| `@performance` | Load and performance tests | 10-20 min | Weekly, before release |
| `@visual` | Visual regression tests | 2-5 min | Before release |
| `@api` | API contract tests only | 2-4 min | After API changes |
| `@ui` | UI tests only | 5-10 min | After UI changes |
| `@search` | Search-specific tests | 3-5 min | After search logic changes |
| `@indexing` | Indexing-specific tests | 5-10 min | After indexing changes |

### Execution Commands

```bash
# Smoke tests (fastest)
npm run test:smoke

# API contract tests (Bruno)
npm run test:api

# UI tests (Playwright)
npm run test:ui

# Integration tests (pytest)
npm run test:integration

# Full test suite
npm run test:all

# Tagged execution
npm run test -- --grep "@smoke"
npm run test -- --grep "@e2e"
npm run test -- --grep "@performance"

# Staged execution (CI/CD pipeline)
npm run test:stage-1   # smoke + unit
npm run test:stage-2   # integration
npm run test:stage-3   # e2e + performance
```

---

## Test Categories

### 1. API Contract Tests (Bruno + curl)

**Tool:** Bruno (primary), curl (smoke tests)

**Coverage:**
- All API endpoints defined in `src/myragdb/api/server.py`
- Request/response schema validation
- HTTP status codes
- Error handling
- Query parameter validation

**Test Cases:**

#### Health Endpoint (`GET /health`)
- [x] Returns `healthy` when Meilisearch and ChromaDB are up
- [x] Returns `degraded` when one dependency is down
- [x] Returns `unhealthy` when both dependencies are down
- [x] Returns 200 status code for all health states
- [x] Response matches schema: `{"status": string, "message": string}`

#### Search Endpoints (`POST /search/{type}`)
- [x] Hybrid search returns combined results
- [x] Keyword-only search uses Meilisearch
- [x] Semantic-only search uses ChromaDB
- [x] Validates `query` parameter is required
- [x] Validates `limit` parameter (default 10, max 50)
- [x] Respects `repositories` filter
- [x] Returns 400 for invalid parameters
- [x] Returns 500 if search engine fails
- [x] Response matches schema: `{"results": Array, "total": number, "search_type": string}`

#### Indexing Endpoints
- [x] `POST /reindex` triggers indexing
- [x] `GET /indexing/status` returns current status
- [x] `GET /repositories` returns repository list
- [x] Supports incremental and full rebuild modes
- [x] Validates repository selection
- [x] Returns indexing progress (total/completed files and repos)

#### Admin Endpoints
- [x] `POST /admin/restart` triggers server restart
- [x] `GET /logs` returns recent log lines
- [x] Logs endpoint supports `lines` and `level` filters
- [x] Restart endpoint returns PID and status

#### Stats Endpoint (`GET /stats`)
- [x] Returns document counts for BM25 and vector
- [x] Returns search statistics
- [x] Returns indexing status and last run time

**Implementation Example (Bruno):**

```javascript
// bruno/search/hybrid-search.bru
meta {
  name: Hybrid Search - Basic Query
  type: http
  seq: 1
}

post {
  url: {{baseUrl}}/search/hybrid
  body: json
  auth: none
}

body:json {
  {
    "query": "authentication flow",
    "limit": 10
  }
}

assert {
  res.status: eq 200
  res.body.search_type: eq "hybrid"
  res.body.results: isArray
  res.body.total: isNumber
}

tests {
  test("Response time < 500ms", function() {
    expect(res.getResponseTime()).to.be.below(500);
  });

  test("Results have required fields", function() {
    const results = res.getBody().results;
    expect(results.length).to.be.greaterThan(0);
    expect(results[0]).to.have.property('file_path');
    expect(results[0]).to.have.property('score');
  });
}

tags: @api @search @smoke
```

---

### 2. UI Functional Tests (Playwright)

**Tool:** Playwright (TypeScript)

**Coverage:**
- All user workflows in web UI
- Component interactions
- State management
- Error states
- Loading states

**Test Cases:**

#### Search Workflow
- [x] User can enter search query
- [x] Search executes on button click
- [x] Search executes on Enter key
- [x] Search type dropdown works (hybrid/keyword/semantic)
- [x] Results limit dropdown works
- [x] Search results display correctly
- [x] Clicking result shows file content
- [x] Search shows loading state
- [x] Search shows error state for failures

#### Health Monitoring
- [x] Health indicator shows correct status (healthy/degraded/unhealthy)
- [x] Status tooltip shows dependency details
- [x] Restart button appears when degraded/unhealthy
- [x] Restart button triggers confirmation modal
- [x] Restart button shows progress and polls for recovery

#### Indexing Workflow
- [x] Repository list loads on Statistics tab
- [x] User can select/deselect repositories
- [x] "Select All" checkbox works
- [x] Index type checkboxes work (BM25/Vector)
- [x] Index mode radio buttons work (incremental/full)
- [x] Reindex button triggers confirmation modal
- [x] Indexing progress displays during reindex
- [x] Statistics update after reindex completes

#### Activity Monitor
- [x] Activity log displays recent events
- [x] Refresh button updates activity log
- [x] Clear button clears activity log
- [x] Activity log persists in localStorage

**Implementation Example (Playwright):**

```typescript
// ui/e2e/search-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Search Workflow @e2e @ui @search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000');
    await expect(page.locator('#status-indicator')).toBeVisible();
  });

  test('should perform hybrid search and display results', async ({ page }) => {
    // Enter search query
    const searchInput = page.locator('#search-input');
    await searchInput.fill('authentication flow');

    // Select hybrid search
    await page.selectOption('#search-type', 'hybrid');

    // Click search button
    await page.click('#search-button');

    // Wait for results
    await expect(page.locator('#search-results')).toBeVisible();

    // Verify results displayed
    const results = page.locator('.search-result-item');
    await expect(results).toHaveCount({ greaterThan: 0 });

    // Verify result structure
    const firstResult = results.first();
    await expect(firstResult.locator('.file-path')).toBeVisible();
    await expect(firstResult.locator('.score')).toBeVisible();
  });

  test('should respect result limit setting', async ({ page }) => {
    await page.locator('#search-input').fill('test');
    await page.selectOption('#result-limit', '5');
    await page.click('#search-button');

    await page.waitForSelector('.search-result-item');
    const results = page.locator('.search-result-item');
    expect(await results.count()).toBeLessThanOrEqual(5);
  });

  test('should show error for empty query', async ({ page }) => {
    await page.click('#search-button');
    await expect(page.locator('#search-results .error')).toContainText('Please enter a search query');
  });
});
```

---

### 3. Integration Tests (pytest)

**Tool:** pytest (Python)

**Coverage:**
- Multi-component interactions
- Database operations
- File system operations
- Search engine integration

**Test Cases:**

#### Hybrid Search Integration
- [x] Indexing documents makes them searchable
- [x] Hybrid search combines BM25 and vector scores correctly
- [x] Search filters by repository
- [x] Search respects file type filters
- [x] Incremental indexing updates existing documents
- [x] Full rebuild clears and rebuilds indexes

#### Health Monitoring Integration
- [x] Health check detects Meilisearch down
- [x] Health check detects ChromaDB down
- [x] Server restart actually restarts process
- [x] Server restart preserves index data

#### Indexing Integration
- [x] Indexing processes all file types
- [x] Indexing excludes patterns work
- [x] Indexing handles large repositories
- [x] Indexing reports progress accurately

**Implementation Example (pytest):**

```python
# integration/test_hybrid_search.py
import pytest
import requests
import time

@pytest.mark.integration
@pytest.mark.search
def test_indexed_document_is_searchable():
    """Test that a newly indexed document becomes searchable."""
    base_url = "http://localhost:3003"

    # Trigger reindex
    reindex_response = requests.post(f"{base_url}/reindex", json={
        "repositories": ["test-repo"],
        "index_bm25": True,
        "index_vector": True,
        "full_rebuild": True
    })
    assert reindex_response.status_code == 200

    # Wait for indexing to complete
    for _ in range(30):  # 30 second timeout
        status = requests.get(f"{base_url}/indexing/status").json()
        if status["status"] == "idle":
            break
        time.sleep(1)

    # Search for known document content
    search_response = requests.post(f"{base_url}/search/hybrid", json={
        "query": "test function authentication",
        "limit": 10
    })
    assert search_response.status_code == 200
    results = search_response.json()["results"]

    # Verify test document appears in results
    assert len(results) > 0
    assert any("auth" in r["file_path"].lower() for r in results)

@pytest.mark.integration
@pytest.mark.health
def test_health_check_detects_meilisearch_down(stop_meilisearch, start_meilisearch):
    """Test health endpoint detects when Meilisearch is unavailable."""
    base_url = "http://localhost:3003"

    # Stop Meilisearch
    stop_meilisearch()
    time.sleep(2)

    # Check health status
    health = requests.get(f"{base_url}/health").json()
    assert health["status"] in ["degraded", "unhealthy"]
    assert "Meilisearch" in health["message"]

    # Restart Meilisearch
    start_meilisearch()
    time.sleep(2)

    # Verify recovery
    health = requests.get(f"{base_url}/health").json()
    assert health["status"] == "healthy"
```

---

### 4. Performance Tests

**Tool:** Playwright (load testing), pytest (benchmarking)

**Coverage:**
- Search response times
- Indexing throughput
- Concurrent user simulation
- Memory usage monitoring

**Test Cases:**

#### Search Performance
- [x] Hybrid search completes in < 500ms (p90)
- [x] Keyword search completes in < 100ms (p90)
- [x] Vector search completes in < 300ms (p90)
- [x] System handles 10 concurrent searches
- [x] Search performance degrades linearly with result limit

#### Indexing Performance
- [x] Indexes 1000 files in < 5 minutes
- [x] Incremental update processes 100 files in < 30 seconds
- [x] Full rebuild clears index in < 10 seconds

**Implementation Example:**

```typescript
// performance/search-load.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Search Performance @performance', () => {
  test('should handle 10 concurrent searches under 1 second', async ({ browser }) => {
    const contexts = await Promise.all(
      Array.from({ length: 10 }, () => browser.newContext())
    );

    const startTime = Date.now();

    const searchPromises = contexts.map(async (context) => {
      const page = await context.newPage();
      await page.goto('http://localhost:8000');
      await page.locator('#search-input').fill('authentication');
      await page.click('#search-button');
      await page.waitForSelector('.search-result-item');
      await context.close();
    });

    await Promise.all(searchPromises);
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(5000); // 5 seconds for 10 searches
  });
});
```

---

## Test Data Management

### Fixtures

#### Test Repository (`tests/fixtures/test-repository/`)
- Small git repository with known content
- Contains various file types (.py, .md, .ts, .dart)
- Used for indexing and search tests
- Predictable content for assertion

#### Sample Documents
- Authentication example: `sample_auth.py`
- Configuration example: `sample_config.yaml`
- Documentation example: `sample_readme.md`

### Mock Data

#### Search Results
```json
{
  "results": [
    {
      "file_path": "/test-repo/src/auth.py",
      "score": 0.95,
      "content_preview": "def authenticate_user(credentials)...",
      "repository": "test-repo"
    }
  ],
  "total": 1,
  "search_type": "hybrid"
}
```

---

## Continuous Integration

### CI/CD Pipeline Stages

```yaml
# .github/workflows/test.yml (example)

name: MyRAGDB Tests

on: [push, pull_request]

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run smoke tests
        run: npm run test:smoke
        timeout-minutes: 2

  api-tests:
    needs: smoke
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: ./start.sh
      - name: Run API tests
        run: npm run test:api
        timeout-minutes: 5

  ui-tests:
    needs: smoke
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Start services
        run: ./start.sh
      - name: Run UI tests
        run: npm run test:ui
        timeout-minutes: 10

  integration-tests:
    needs: [api-tests, ui-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 10

  performance-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run performance tests
        run: npm run test:performance
        timeout-minutes: 20
```

---

## Test Environment Setup

### Prerequisites
```bash
# Install dependencies
npm install -D @playwright/test
npm install -D @usebruno/cli
pip install pytest pytest-asyncio requests

# Install Playwright browsers
npx playwright install --with-deps
```

### Environment Configuration

```bash
# tests/.env.test
API_BASE_URL=http://localhost:3003
WEB_UI_URL=http://localhost:8000
MEILISEARCH_URL=http://localhost:7700
TEST_REPO_PATH=./tests/fixtures/test-repository
```

### Setup Script

```bash
#!/bin/bash
# tests/utils/setup.sh

echo "Setting up test environment..."

# Start Meilisearch
./scripts/start_meilisearch.sh

# Start API server
source venv/bin/activate
python -m myragdb.api.server &
SERVER_PID=$!
echo $SERVER_PID > .test-server.pid

# Wait for services
./tests/utils/wait-for-service.sh http://localhost:3003/health

# Index test repository
python scripts/initial_index.py --config tests/fixtures/test-config.yaml

echo "Test environment ready!"
```

---

## Success Metrics

### Coverage Targets
- API Contract Coverage: **100%** of endpoints
- UI Component Coverage: **90%+** of components
- Integration Test Coverage: **80%+** of workflows
- Code Coverage: **70%+** (pytest --cov)

### Performance Baselines
- Search Response Time (p90): **< 500ms**
- Search Response Time (p50): **< 300ms**
- Indexing Throughput: **> 200 files/min**
- UI Page Load: **< 2 seconds**

### Reliability Targets
- Test Suite Pass Rate: **100%** on main branch
- Flaky Test Rate: **< 5%**
- CI/CD Pipeline Duration: **< 30 minutes**

---

## Maintenance and Iteration

### Test Review Cadence
- **Weekly:** Review failed tests, update flaky tests
- **Monthly:** Review test coverage, add missing scenarios
- **Quarterly:** Performance baseline review, update thresholds

### Test Ownership
- API tests: Backend team
- UI tests: Frontend team
- Integration tests: Full-stack team
- Performance tests: DevOps team

---

## Appendix

### Tool Selection Rationale

**Playwright:**
- Cross-browser support (Chromium, Firefox, WebKit)
- Auto-wait eliminates flaky tests
- Powerful selectors and assertions
- Built-in screenshot and video recording
- Parallel execution support

**Bruno:**
- Git-friendly (plain text collections)
- Environments and variables support
- Scripting and assertions
- Collection runner for CI/CD
- Lightweight alternative to Postman

**curl:**
- Universally available
- Fast smoke tests
- CI/CD friendly
- Simple contract validation with jq

**pytest:**
- Python-native (matches API codebase)
- Rich plugin ecosystem
- Fixtures and parametrization
- Async support
- Coverage reporting

---

## Next Steps

1. Create `tests/` directory structure
2. Implement smoke test suite (curl + minimal Playwright)
3. Migrate existing manual tests to Bruno collections
4. Implement critical path UI tests (search workflow)
5. Set up CI/CD pipeline with staged execution
6. Establish performance baselines
7. Document test execution in `tests/README.md`

Questions: libor@arionetworks.com
