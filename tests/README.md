# MyRAGDB Test Suite

**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/README.md`
**Description:** Overview and getting started guide for MyRAGDB regression test suite
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-08

---

## Overview

The MyRAGDB Test Suite provides comprehensive automated testing covering:

- **API Layer** - Search, skills, templates, directories
- **UI Layer** - Navigation, repository/directory management, workflows
- **Integration Tests** - End-to-end workflows combining API and UI
- **Performance Tests** - Search latency, indexing speed
- **Database Tests** - Schema integrity, data consistency

All tests support **incremental execution** with flexible filtering by category, enabling quick smoke tests (5 min) or comprehensive regression runs (2 hours).

---

## Quick Start

### Run All Tests
```bash
npm test
```

### Run Smoke Tests (5-10 min)
```bash
npm test -- --grep "@smoke"
```

### Run with Interactive Dashboard
```bash
npm run test:ui
```
Opens browser UI at `http://localhost:3004`

---

## Documentation

- **[TEST_EXECUTION_GUIDE.md](./TEST_EXECUTION_GUIDE.md)** - Quick reference for common test commands
- **[REGRESSION_TEST_SUITE.md](./REGRESSION_TEST_SUITE.md)** - Complete test strategy and architecture
- **[test-categories.json](./test-categories.json)** - Test categorization metadata

---

## Directory Structure

```
tests/
├── README.md                          # This file
├── TEST_EXECUTION_GUIDE.md           # Quick command reference
├── REGRESSION_TEST_SUITE.md          # Complete documentation
├── test-categories.json              # Test categories & metadata
├── playwright.config.ts              # Playwright configuration
│
├── e2e/                              # End-to-end tests
│   ├── fixtures.ts                   # Shared test fixtures
│   ├── api-*.spec.ts                 # API tests
│   │   ├── api-search.spec.ts
│   │   ├── api-execution.spec.ts
│   │   ├── api-skills.spec.ts
│   │   ├── api-templates.spec.ts
│   │   ├── api-directories.spec.ts
│   │   └── api-orchestrator.spec.ts
│   │
│   ├── ui-*.spec.ts                  # UI tests
│   │   ├── ui-navigation.spec.ts
│   │   ├── ui-repository-management.spec.ts
│   │   ├── ui-directories.spec.ts
│   │   └── ui-search-workflow.spec.ts
│   │
│   └── utils/                        # Test utilities
│
├── regression/                       # Test management tools
│   ├── regression-runner.ts          # CLI test runner
│   ├── regression-ui.ts              # Web dashboard
│   └── README.md                     # Tool documentation
│
├── test-results/                     # Generated test results
│   ├── results.json                  # Detailed test results
│   ├── junit.xml                     # JUnit format for CI/CD
│   ├── report.html                   # Interactive HTML report
│   ├── history.json                  # Results history for trending
│   └── videos/                       # Videos of failed tests
│
└── fixtures/                         # Test data
    ├── repos/                        # Test repositories
    └── dirs/                         # Test directories
```

---

## Test Categories

Tests are tagged with multiple categories for flexible filtering:

### Execution Speed
- `@smoke` - Fast critical tests (< 5 sec each)
- `@fast` - Quick tests (< 30 sec each)
- `@slow` - Long-running tests (> 30 sec each)

### Feature Area
- `@api` - Backend API tests
- `@ui` - Frontend UI tests
- `@search` - Search functionality
- `@workflow` - Workflow execution
- `@repository` - Repository management
- `@directory` - Directory management
- `@skill` - Skill operations
- `@template` - Template operations

### Scope
- `@unit` - Single component
- `@integration` - Multiple components
- `@e2e` - Full system
- `@critical` - Must pass before release

---

## Running Tests

### By Duration

**Smoke Tests (5-10 minutes)**
```bash
npm test -- --grep "@smoke"
```
Run after every code change for quick feedback.

**Fast Regression (20-30 minutes)**
```bash
npm test -- --grep "@fast"
```
Run before pushing code to catch regressions.

**Full Regression (60-120 minutes)**
```bash
npm test
```
Run before releases for comprehensive testing.

### By Feature

**Search functionality:**
```bash
npm test -- --grep "@search"
```

**Repository management:**
```bash
npm test -- --grep "@repository"
```

**Directory management:**
```bash
npm test -- --grep "@directory"
```

**API endpoints:**
```bash
npm test -- --grep "@api"
```

**UI components:**
```bash
npm test -- --grep "@ui"
```

### By Browser

**Chromium only:**
```bash
npm test -- --project=chromium
```

**Firefox only:**
```bash
npm test -- --project=firefox
```

**Both (default):**
```bash
npm test
```

---

## Test Management Dashboard

Interactive web UI for managing test execution.

### Start Dashboard
```bash
npm run test:ui
```

### Features
- **Test Selection** - Choose suites or custom grep patterns
- **Live Progress** - Real-time execution tracking
- **Results History** - View and trending past results
- **Performance Metrics** - Test duration and status

### API Endpoints
- `GET /api/suites` - Available test suites
- `POST /api/execute` - Execute test suite
- `GET /api/status` - Current execution status
- `GET /api/results` - Results history
- `GET /api/categories` - Test categories reference

---

## Test Suites

### API Tests (api-*.spec.ts)

**Search API** - Keyword and semantic search
- Hybrid search execution
- Search filtering and ranking
- Performance < 300ms

**Execution API** - Workflow execution
- Skill execution with parameters
- Multi-step workflows
- Error handling

**Skills API** - Available skills
- List skills
- Get metadata
- Execute with parameters

**Templates API** - Template operations
- Create/read/update/delete
- Template execution
- Version management

**Directories API** - Directory management
- Add/remove directories
- List and statistics
- Indexing status

**Orchestrator API** - Complex workflows
- Multi-step execution
- Skill chaining
- Data flow

### UI Tests (ui-*.spec.ts)

**Navigation** - Page structure and responsiveness
- Home page loads
- Navigation elements
- Refresh handling
- Back/forward navigation

**Repository Management** - Repository controls
- Display repository list
- Enable/disable toggles
- Settings updates
- Statistics display

**Directory Management** - Directory controls
- Add/remove directories
- Enable/disable toggles
- File counts
- Indexing status

**Search Workflow** - Search interactions
- Search input
- Result display
- Filtering
- Sorting/pagination

---

## Execution Patterns

### Development Workflow

```
After code change:
  npm test -- --grep "@smoke"           # 5-10 min

Before git push:
  npm test -- --grep "@fast"            # 20-30 min

Before pull request:
  npm test                              # 60-120 min (all tests)
```

### CI/CD Integration

```yaml
# On every push
- npm test -- --grep "@smoke"

# On pull request
- npm test -- --grep "@fast"

# Before merge to main
- npm test
```

### Nightly Automated Testing

```bash
# Full regression + performance benchmarks
npm test
```

---

## Performance Targets

### API Response Time
- Search request: < 300ms
- Skill execution: < 1000ms
- Template operation: < 500ms

### UI Response Time
- Page load: < 2s
- Search result display: < 1s
- Navigation transition: < 500ms

### Test Execution Time
- Smoke test: < 5s each
- Fast test: < 30s each
- Full suite: < 120 minutes

---

## Viewing Results

### HTML Report
```bash
npx playwright show-report
```

### JSON Results
```bash
cat tests/test-results/results.json | jq .
```

### Results History
```bash
cat tests/test-results/history.json
```

---

## Prerequisites

### Required Services
- **API Server** - Running on `localhost:3002`
- **UI Server** - Running on `localhost:3003`

### Start Services
```bash
npm run dev  # Starts both API and UI
```

### Test Data
- Test repositories in `tests/fixtures/repos`
- Test directories in `tests/fixtures/dirs`
- Auto-indexed during test setup

---

## Troubleshooting

### Tests Won't Start
```bash
# Ensure services are running
npm run dev

# Check ports
lsof -i :3003 :3002
```

### Element Not Found
- Page not fully loaded - increase timeout
- Element selector changed - update test
- UI doesn't exist - check implementation

### Flaky Tests
- Increase timeout on timing-sensitive tests
- Add explicit wait conditions
- Check network stability

### Database Locked
```bash
# Reset test data
rm -rf data/
npm run dev  # Will recreate
```

---

## Best Practices

### Writing Tests

1. **Descriptive names** - Name clearly describes what's tested
2. **Single responsibility** - Each test verifies one behavior
3. **Use fixtures** - Share setup code via fixtures.ts
4. **Tag appropriately** - Add all relevant category tags
5. **Independent tests** - Don't depend on other tests
6. **Data attributes** - Use `data-testid` for reliable selection

### Test Maintenance

1. **Review tags quarterly** - Keep categories relevant
2. **Fix flakiness** - Investigate intermittent failures
3. **Update selectors** - When UI changes, update tests
4. **Document changes** - Update this README when adding tests
5. **Archive obsolete tests** - Move to separate file if no longer needed

---

## CI/CD Setup

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Start services
        run: npm run dev &

      - name: Wait for services
        run: sleep 10

      - name: Run tests
        run: npm test

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: tests/test-results/
```

---

## Advanced Usage

### Custom Grep Pattern
```bash
npm test -- --grep "@api.*@critical"
```

### Run with Browser Visible
```bash
npm test -- --headed
```

### Debug Mode
```bash
npm test -- --debug
```

### Watch Mode
```bash
npm test -- --watch
```

### Parallel Execution
```bash
npm test -- --workers=2
```

---

## Metrics & Reporting

### Test Metrics
- **Pass Rate** - Percentage of tests passing
- **Flakiness** - How often test fails intermittently
- **Coverage** - Which features have tests
- **Duration** - Time to run each category
- **Trend** - Pass rate over time

### Results Dashboard
View at: http://localhost:3004 after running `npm run test:ui`

---

## Support & Questions

- **Documentation** - See REGRESSION_TEST_SUITE.md
- **Quick Reference** - See TEST_EXECUTION_GUIDE.md
- **Test Categories** - See test-categories.json
- **Source Code** - See tests/e2e/*.spec.ts

---

## Contributing

When adding new tests:

1. Create file in `tests/e2e/` with `.spec.ts` extension
2. Add appropriate tags (use existing ones)
3. Use shared fixtures from `fixtures.ts`
4. Update documentation with new tests
5. Ensure test is independent and repeatable

---

## Related Documentation

- [Test Execution Guide](./TEST_EXECUTION_GUIDE.md)
- [Regression Test Suite](./REGRESSION_TEST_SUITE.md)
- [Test Categories](./test-categories.json)
- [Playwright Docs](https://playwright.dev)

---

**Last Updated:** 2026-01-08
**Status:** Complete and operational
**Maintenance:** Quarterly review recommended
