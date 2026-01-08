# MyRAGDB Regression Test Suite
**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/REGRESSION_TEST_SUITE.md`
**Description:** Comprehensive regression testing strategy and implementation guide
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-08

---

## Overview

The MyRAGDB Regression Test Suite provides automated testing across:
- **API Layer** - Search, skill execution, template management
- **UI Layer** - Navigation, repository/directory management, workflows
- **Integration Tests** - End-to-end workflows combining API and UI
- **Performance Tests** - Indexing speed, search latency
- **Database Tests** - Schema integrity, data consistency

This allows incremental testing with categorization for quick smoke tests or comprehensive regression runs.

---

## Test Architecture

### Test Organization

```
tests/
├── playwright.config.ts          # Playwright configuration
├── e2e/                          # End-to-end tests
│   ├── api-*.spec.ts            # API-specific tests
│   ├── ui-*.spec.ts             # UI-specific tests
│   ├── integration-*.spec.ts     # Full workflow tests
│   ├── fixtures.ts              # Shared test fixtures
│   └── utils/                   # Test utilities
├── regression/                   # Regression test suite
│   ├── regression-runner.ts      # Test execution manager
│   ├── regression-ui.ts          # Test management dashboard
│   └── test-categories.json      # Test categorization
├── performance/                  # Performance tests
└── REGRESSION_TEST_SUITE.md     # This file
```

### Test Categories & Tags

Tests are tagged with multiple categories for flexible execution:

#### Execution Speed
- `@smoke` - Fast critical tests (< 5 seconds each)
- `@fast` - Quick tests (< 30 seconds)
- `@slow` - Long-running tests (> 30 seconds)

#### Scope
- `@unit` - Single component tests
- `@integration` - Multiple components
- `@e2e` - Full system workflows
- `@critical` - Must pass before release

#### Feature Area
- `@api` - Backend API tests
- `@ui` - Frontend UI tests
- `@search` - Search functionality
- `@workflow` - Workflow execution
- `@indexing` - File indexing operations
- `@repository` - Repository management
- `@directory` - Directory management
- `@skill` - Skill execution
- `@template` - Template operations

#### Type
- `@smoke` - Smoke/sanity tests
- `@regression` - Regression tests
- `@performance` - Performance benchmarks
- `@compatibility` - Browser/OS compatibility

---

## Running Tests

### Quick Start

```bash
# Run all tests
npm test

# Run tests with UI manager
npm run test:ui

# Run specific tag
npm test -- --grep @smoke
npm test -- --grep @fast
npm test -- --grep @critical
```

### Selective Execution

```bash
# Smoke tests only (5-10 min)
npm test -- --grep "@smoke"

# Fast tests (< 30 sec each) - 20-30 min
npm test -- --grep "@fast"

# API tests only
npm test -- --grep "@api"

# UI tests only
npm test -- --grep "@ui"

# Search functionality
npm test -- --grep "@search"

# Repository management
npm test -- --grep "@repository"

# Directory management
npm test -- --grep "@directory"

# Workflow execution
npm test -- --grep "@workflow"

# Combined filters (AND)
npm test -- --grep "(@api|@ui) & @critical"

# Full regression (all tests)
npm test
```

### Browser-Specific Testing

```bash
# Chromium only
npm test -- --project=chromium

# Firefox only
npm test -- --project=firefox

# Both browsers (default)
npm test
```

### Advanced Options

```bash
# Show headed browser (see actions)
npm test -- --headed

# Debug mode with inspector
npm test -- --debug

# Single file
npm test tests/e2e/ui-navigation.spec.ts

# Watch mode (re-run on changes)
npm test -- --watch

# Parallel execution (use with caution)
npm test -- --workers=2

# Generate HTML report
npm test -- --reporter=html

# Output coverage
npm test -- --reporter=json > test-results.json
```

---

## Test Suites

### 1. API Tests (`tests/e2e/api-*.spec.ts`)

#### API Search (`api-search.spec.ts`) - @api @search @integration
- Hybrid search with keyword + semantic
- Search filtering (repository, directory, date)
- Search result ranking and sorting
- Performance: < 300ms response time

#### API Execution (`api-execution.spec.ts`) - @api @workflow @integration
- Skill execution workflows
- Parameter validation
- Error handling
- Result persistence

#### API Skills (`api-skills.spec.ts`) - @api @skill
- List available skills
- Skill metadata retrieval
- Skill parameter validation
- Skill execution success/failure

#### API Templates (`api-templates.spec.ts`) - @api @template
- Template CRUD operations
- Template instantiation
- Template execution with parameters
- Template version management

#### API Directories (`api-directories.spec.ts`) - @api @directory
- Add/remove managed directories
- List directories
- Directory statistics
- Directory file indexing status

#### API Orchestrator (`api-orchestrator.spec.ts`) - @api @integration
- Multi-step workflows
- Skill chaining
- Data flow between skills
- Complex scheduling

### 2. UI Tests (`tests/e2e/ui-*.spec.ts`)

#### Navigation (`ui-navigation.spec.ts`) - @ui @smoke @fast
- Home page loads
- Navigation elements present
- Page responsiveness
- Back/forward navigation
- Refresh handling

#### Repository Management (`ui-repository-management.spec.ts`) - @ui @repository @fast
- Display repository list
- Enable/disable repositories
- Update repository settings
- Repository statistics display
- Incremental indexing indicator

#### Directory Management (`ui-directories.spec.ts`) - @ui @directory @fast
- Add new directory
- Display directory list
- Enable/disable directories
- Update directory settings
- Directory file counts
- Indexing status

#### Search Workflow (`ui-search-workflow.spec.ts`) - @ui @search @workflow
- Search input interaction
- Result display
- Filter application
- Result ranking/sorting
- Pagination if applicable

### 3. Integration Tests (`tests/e2e/integration-*.spec.ts`)

#### End-to-End Workflows
- Index repositories -> Search -> View results
- Add directory -> Index -> Search across both sources
- Execute skill -> View output in UI
- Complex multi-step workflows

---

## Test Execution Patterns

### Pattern 1: Smoke Tests (Fast Verification)
**Duration:** 5-10 minutes
**Purpose:** Verify critical paths work after code changes

```bash
npm test -- --grep "@smoke"
```

**Coverage:**
- App loads
- Basic navigation works
- API responds
- Search executes
- Results display
- No JavaScript errors

### Pattern 2: Fast Regression (Quick Full Regression)
**Duration:** 20-30 minutes
**Purpose:** Catch obvious regressions quickly

```bash
npm test -- --grep "@fast"
```

**Coverage:**
- All smoke tests
- Basic functionality for each feature
- Error handling
- Basic integration flows

### Pattern 3: Complete Regression (Full Suite)
**Duration:** 60-120 minutes
**Purpose:** Comprehensive testing before release

```bash
npm test
```

**Coverage:**
- All tests including @slow
- All edge cases
- Performance benchmarks
- Compatibility across browsers
- Full integration scenarios

### Pattern 4: Feature-Specific Testing
**Duration:** Variable
**Purpose:** Test specific feature area after changes

```bash
# Test search changes
npm test -- --grep "@search"

# Test repository changes
npm test -- --grep "@repository"

# Test workflow changes
npm test -- --grep "@workflow"
```

### Pattern 5: API-Only Testing
**Duration:** 20-30 minutes
**Purpose:** Test backend without UI

```bash
npm test -- --grep "@api"
```

### Pattern 6: UI-Only Testing
**Duration:** 15-25 minutes
**Purpose:** Test frontend without API complexity

```bash
npm test -- --grep "@ui"
```

---

## Test Management Dashboard

The Test Management Dashboard (`tests/regression/regression-ui.ts`) provides:

### Features
- **Test Selection UI** - Select tests by category/tag
- **Execution Progress** - Real-time test execution tracking
- **Result Summary** - Pass/fail breakdown by category
- **Detailed Results** - View individual test logs
- **Performance Metrics** - Test duration, memory usage
- **Historical Trending** - Track quality over time

### Running the Dashboard

```bash
npm run test:ui
```

Opens browser interface at `http://localhost:3004` (configurable) with:
- Test suite selection
- Execute button
- Live progress display
- Results filtering and sorting
- Export results to JSON/HTML

---

## Incremental Testing Strategy

### On Each Commit
```bash
npm test -- --grep "@smoke"  # 5-10 min
```

### Before Push to Remote
```bash
npm test -- --grep "@fast"   # 20-30 min
```

### Before Pull Request
```bash
npm test                      # All tests
```

### On Main Branch (CI/CD)
```bash
npm test -- --project=chromium --reporter=json
# Store results for trend analysis
```

---

## Test Data Management

### Setup Requirements

Tests require:
- MyRAGDB API running on localhost:3002
- UI running on localhost:3003
- Test repositories indexed in `/tests/fixtures/repos`
- Test directories available at `/tests/fixtures/dirs`

### Fixture Data

```
tests/fixtures/
├── repos/           # Test repositories
│   ├── test-repo-1/
│   └── test-repo-2/
└── dirs/            # Test directories
    ├── test-dir-1/
    └── test-dir-2/
```

### Database Reset Between Tests

Each test suite's `beforeEach` hook:
- Clears previous test data
- Resets database to clean state
- Initializes test fixtures
- Indexes test repositories/directories

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

## Troubleshooting

### Test Failures

#### "Server connection refused"
- Check API running: `http://localhost:3002`
- Check UI running: `http://localhost:3003`
- Restart services

#### "Timeout waiting for element"
- Element may not exist on page
- UI may not be fully loaded
- Network may be slow

#### "Database locked"
- Database file in use
- Previous test didn't cleanup
- Manual cleanup: `rm data/*.db`

#### "Flaky tests"
- Check network stability
- Increase timeout: `test.setTimeout(30000)`
- Add explicit wait conditions

### Debug Mode

```bash
# Run with browser visible
npm test -- --headed

# Step through with debugger
npm test -- --debug

# Verbose logging
npm test -- --reporter=verbose

# Save trace for inspection
npm test -- --trace=on
```

---

## Best Practices

### Writing Tests

1. **Use descriptive names** - Test name describes what it verifies
2. **Single responsibility** - Each test verifies one behavior
3. **Use fixtures** - Share setup code via fixtures
4. **Tag appropriately** - Add all relevant category tags
5. **Handle async properly** - Await all async operations
6. **No test interdependence** - Each test must be independent
7. **Use data attributes** - `data-testid` for reliable selection

### Test Maintenance

1. **Review tags quarterly** - Keep categories relevant
2. **Monitor flakiness** - Investigate and fix flaky tests
3. **Update selectors** - When UI changes, update tests
4. **Document changes** - Update this file when adding tests
5. **Archive old tests** - Move obsolete tests to separate file

### CI/CD Integration

1. **Run smoke tests per commit** - Quick feedback
2. **Run fast tests before merge** - Catch regressions early
3. **Run full suite nightly** - Comprehensive overnight testing
4. **Store results history** - Track quality trends
5. **Alert on failures** - Notify team of broken tests

---

## Test Results & Reporting

### Generated Artifacts

```
test-results/
├── results.json      # JSON detailed results
├── junit.xml         # JUnit format for CI systems
├── report.html       # Interactive HTML report
└── videos/           # Videos of failed tests
    └── failed-*.webm
```

### Viewing Results

```bash
# Open HTML report
npx playwright show-report

# View JSON results
cat test-results/results.json | jq .

# Check specific test
grep -A 20 "test-name" test-results/results.json
```

### Metrics

- **Pass Rate** - Percentage of tests passing
- **Flakiness** - How often test fails intermittently
- **Coverage** - Which features have tests
- **Duration** - Time to run each test category
- **Trend** - Pass rate over time

---

## Continuous Improvement

### Metrics to Track

1. Test execution time (should decrease)
2. Flaky test count (should be 0)
3. Feature coverage (should increase)
4. Pass rate (should be 100%)
5. Time to fix failures (should be < 1 hour)

### Regular Reviews

- **Weekly** - Check for new flaky tests
- **Monthly** - Review coverage gaps
- **Quarterly** - Optimize slow tests
- **Yearly** - Full test suite audit

---

## Additional Resources

- [Playwright Documentation](https://playwright.dev)
- [Test Categories Reference](./test-categories.json)
- [Fixtures Guide](./e2e/fixtures.ts)
- [Test Results](./test-results/)
- [Video Evidence](./test-results/videos/)

---

## Questions & Support

For questions about tests:
- Check existing test examples
- Review this documentation
- Contact: libor@arionetworks.com

---

**Last Updated:** 2026-01-08
**Status:** Complete and operational
