# Comprehensive Testing Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/TESTING_GUIDE.md
**Description:** Guide to running and maintaining the comprehensive test suites
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

This project includes comprehensive testing infrastructure with:
- **57+ Playwright E2E tests** covering UI and API
- **13+ Bruno API tests** covering all endpoints
- **20+ Python unit tests** for core components
- **Tag-based organization** for batch execution
- **Memory-safe configuration** with single worker

Total test coverage: All 9 API endpoints, all UI components, all major workflows

---

## Test Organization

### Tags for Batch Execution

```
@smoke       - Quick smoke tests (< 5 sec) - Run first
@fast       - Fast tests (< 30 sec) - Run regularly
@integration - Integration tests (< 2 min) - Run before commits
@ui         - UI/E2E tests - Batch separately
@api        - API tests - Batch separately
@execution  - Template/workflow execution tests
@discovery  - Template/skill discovery tests
@templates  - Template-specific tests
@skills     - Skill-specific tests
@orchestrator - Orchestrator tests
@error-handling - Error case tests
@workflow   - Workflow execution tests
@accessibility - Accessibility tests
```

### Running by Tag (Batch Execution)

**Avoid memory overload by running small batches:**

```bash
# Run smoke tests first (< 5 sec per test)
npm run test:smoke
# Or manually:
npx playwright test --grep "@smoke"

# Run fast tests (< 30 sec per test)
npm run test:fast
npx playwright test --grep "@fast"

# Run specific category (small batch)
npx playwright test --grep "@execution"
npx playwright test --grep "@discovery"
npx playwright test --grep "@skills"

# Run UI tests separately (batch)
npx playwright test --grep "@ui"

# Run error handling tests
npx playwright test --grep "@error-handling"
```

---

## Setup Instructions

### Prerequisites

```bash
# Python 3.8+
# Node.js 16+
# Running backend on port 3002
# Running UI on port 3003
```

### Install Dependencies

```bash
# Install Playwright
npm install --save-dev @playwright/test

# Install Bruno (API testing)
npm install --save-dev @usebruno/cli

# Install Axios for API tests
npm install --save-dev axios
```

### Configure Environment

```bash
# Copy environment template
cp .env.test.example .env.test

# Edit with your values
API_BASE_URL=http://localhost:3002
UI_BASE_URL=http://localhost:3003
```

---

## Running Tests

### Playwright Tests

#### Run all E2E tests
```bash
npx playwright test
```

#### Run specific test file
```bash
npx playwright test tests/e2e/api-execution.spec.ts
```

#### Run tests matching pattern
```bash
npx playwright test --grep "should execute code_search"
```

#### Run tests with specific tag (memory-safe batches)
```bash
# Small batch - smoke tests
npx playwright test --grep "@smoke"

# Medium batch - fast tests
npx playwright test --grep "@fast"

# API tests only
npx playwright test --grep "@api"

# UI tests only
npx playwright test --grep "@ui"

# Error handling tests
npx playwright test --grep "@error-handling"
```

#### Run in debug mode
```bash
npx playwright test --debug
```

#### Run with headed browser (see UI)
```bash
npx playwright test --headed
```

#### Run with tracing
```bash
npx playwright test --trace on
```

#### View test report
```bash
npx playwright show-report
```

### Bruno API Tests

#### Run all Bruno tests
```bash
bruno run bruno/MyRAGDB.collection.json
```

#### Run specific folder
```bash
bruno run bruno/Agent\ Platform/Execution
```

#### Run with environment
```bash
bruno run bruno/MyRAGDB.collection.json --env dev
```

#### Run specific test
```bash
bruno run bruno/Agent\ Platform/Health\ Check/Health\ Check.bru
```

### Python Unit Tests

#### Run all unit tests
```bash
pytest tests/ -v
```

#### Run specific test file
```bash
pytest tests/test_agent_platform.py -v
```

#### Run specific test
```bash
pytest tests/test_agent_platform.py::TestSkillRegistry::test_register_skill -v
```

#### Run with coverage
```bash
pytest tests/ --cov=src/myragdb --cov-report=html
```

---

## Test Suites Breakdown

### API Execution Tests (10 tests)
**File:** `tests/e2e/api-execution.spec.ts`
**Tags:** `@api @integration @execution @fast`

Tests:
1. Execute code_search template
2. Execute code_analysis template
3. Execute code_review template
4. Track execution progress
5. Reject missing required parameter
6. Reject unknown template
7. Execute custom workflow
8. Handle step errors with on_error
9. Support variable interpolation
10. Include step details in response

**Run:** `npx playwright test api-execution.spec.ts --grep "@execution"`

---

### API Templates Tests (11 tests)
**File:** `tests/e2e/api-templates.spec.ts`
**Tags:** `@api @discovery @fast`

Tests:
1. List all templates
2. Validate template fields
3. Include built-in templates
4. Get specific template info
5. Validate query parameter
6. Handle optional parameters
7. Return 404 for unknown
8. Register custom template
9. Retrieve registered template
10. Validate categories
11. Validate step counts

**Run:** `npx playwright test api-templates.spec.ts --grep "@discovery"`

---

### API Skills Tests (14 tests)
**File:** `tests/e2e/api-skills.spec.ts`
**Tags:** `@api @discovery @fast`

Tests:
1. List all skills
2. Validate skill fields
3. Include core skills
4. Get search skill info
5. Validate search parameters
6. Validate search output
7. Get code_analysis skill
8. Get report skill
9. Get llm skill
10. Return 404 for unknown
11. Validate input schemas
12. Validate output schemas
13. Validate required_config
14. Validate descriptions

**Run:** `npx playwright test api-skills.spec.ts --grep "@discovery"`

---

### API Orchestrator Tests (12 tests)
**File:** `tests/e2e/api-orchestrator.spec.ts`
**Tags:** `@api @orchestrator @fast`

Tests:
1. Return health status
2. Validate health message
3. Return orchestrator info
4. Validate skill count
5. Validate template count
6. List core skills
7. List core templates
8. Validate session manager flag
9. Validate search engine flag
10. Consistent skill counts
11. Match skill lists
12. Match template lists

**Run:** `npx playwright test api-orchestrator.spec.ts --grep "@orchestrator"`

---

### Bruno API Tests (13 tests)
**File:** `bruno/Agent Platform/`
**Tags:** Various (@health, @smoke, @execution, etc.)

Tests:
- Health Check (1)
- Execute Code Search (3)
- Execute Custom Workflow (3)
- List Templates (3)
- Get Template Info (2)
- Register Template (1)
- List Skills (2)
- Get Skill Info (2)
- Get Orchestrator Info (3)
- Error Cases (3)

**Run:** `bruno run bruno/MyRAGDB.collection.json`

---

### UI Navigation Tests (6 tests)
**File:** `tests/e2e/ui-navigation.spec.ts`
**Tags:** `@ui @smoke @fast`

Tests:
1. Load home page
2. Display main navigation
3. Display repository list
4. Handle page refresh
5. Be responsive
6. Handle back/forward navigation

**Run:** `npx playwright test ui-navigation.spec.ts --grep "@ui"`

---

### UI Repository Management Tests (8 tests)
**File:** `tests/e2e/ui-repository-management.spec.ts`
**Tags:** `@ui @integration`

Tests:
1. Display repository list
2. Scroll repository list
3. Handle bulk actions
4. Maintain state after refresh
5. Handle empty states
6. Keyboard accessible
7. Handle network errors
8. Display appropriately

**Run:** `npx playwright test ui-repository-management.spec.ts --grep "@ui"`

---

### UI Search Workflow Tests (12 tests)
**File:** `tests/e2e/ui-search-workflow.spec.ts`
**Tags:** `@ui @integration @workflow`

Tests:
1. Have search interface
2. Handle search input
3. Execute workflows
4. Display results
5. Handle parameter input
6. Support template selection
7. Handle loading states
8. Handle form submission
9. Display execution history
10. Allow result filtering
11. Handle pagination
12. Support all workflows

**Run:** `npx playwright test ui-search-workflow.spec.ts --grep "@workflow"`

---

## Test Batch Execution Strategy

### Quick Smoke Tests (< 30 seconds)
```bash
npx playwright test --grep "@smoke"
```
**What it tests:** Basic functionality, health checks, quick operations

### Fast Tests (< 2 minutes)
```bash
npx playwright test --grep "@fast"
```
**What it tests:** Individual endpoints, quick flows, no external delays

### Integration Tests (< 5 minutes)
```bash
npx playwright test --grep "@integration"
```
**What it tests:** Multi-step workflows, error handling, state management

### Complete Suite (< 20 minutes)
```bash
# Run in batches to avoid memory issues
npx playwright test --grep "@api"
npx playwright test --grep "@ui"
npx playwright test --grep "@error-handling"
```

---

## Memory Management

### Configuration
- **Single worker** - Prevents memory overload
- **Sequential execution** - No parallel tests
- **Tag-based batching** - Run small groups

### Typical Memory Usage
- Per-test: 50-100 MB
- Per-batch (10 tests): 500-1000 MB
- Max safe batch: 10-15 tests

### Best Practice
```bash
# Good - 10 tests, ~1 GB memory
npx playwright test --grep "@smoke"

# Good - 15 tests, ~1.5 GB memory
npx playwright test --grep "@fast"

# Split - Avoid running all 50+ tests at once
npx playwright test --grep "@api"
npx playwright test --grep "@ui"
```

---

## Continuous Integration

### CI/CD Pipeline

```bash
#!/bin/bash

# Run smoke tests first
npx playwright test --grep "@smoke"
if [ $? -ne 0 ]; then exit 1; fi

# Run API tests in batches
npx playwright test --grep "@api" --grep "@execution"
npx playwright test --grep "@api" --grep "@discovery"
npx playwright test --grep "@api" --grep "@orchestrator"

# Run UI tests
npx playwright test --grep "@ui"

# Run error handling tests
npx playwright test --grep "@error-handling"

# Run Python unit tests
pytest tests/ -v
```

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '16'
      - run: npm ci
      - run: npx playwright test --grep "@smoke"
      - run: npx playwright test --grep "@fast"
      - run: pytest tests/ -v
```

---

## Test Reports

### View HTML Report
```bash
npx playwright show-report
```

### Generate Coverage Report
```bash
pytest tests/ --cov=src/myragdb --cov-report=html
open htmlcov/index.html
```

### Export Results
```bash
# JSON output for parsing
npx playwright test --reporter=json > results.json

# JUnit for CI systems
npx playwright test --reporter=junit
```

---

## Adding New Tests

### Template for API Test
```typescript
import { test, expect } from './fixtures';

test.describe('Feature Name - @api @tag', () => {
  test('should do something @fast', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/endpoint');

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('field');
  });
});
```

### Template for UI Test
```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name - @ui @tag', () => {
  test('should do something', async ({ page }) => {
    await page.goto('http://localhost:3003');
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

### Template for Bruno Test
```bru
meta {
  name: Test Name
  type: http
  tags: @api, @category, @fast
}

post {
  url: {{api_base_url}}/endpoint
}

assert {
  res.status: eq 200
}

tests {
  test("should validate", function() {
    expect(res.status).to.equal(200);
  });
}
```

---

## Troubleshooting

### Tests Timing Out
```bash
# Increase timeout
npx playwright test --timeout=60000

# Run single test
npx playwright test -g "specific test name"
```

### Memory Issues
```bash
# Run smaller batches
npx playwright test --grep "@smoke"

# Use single worker (default)
# Workers are already limited to 1
```

### UI Tests Not Finding Elements
```bash
# Run in headed mode to see what's happening
npx playwright test --headed --grep "@ui"

# Use debug mode
npx playwright test --debug
```

### API Connection Issues
```bash
# Verify backend is running
curl http://localhost:3002/api/v1/agent/health

# Verify UI is running
curl http://localhost:3003

# Check environment variables
echo $API_BASE_URL
```

---

## Test Maintenance

### Regular Maintenance
- Review test output weekly
- Update tests when API changes
- Add tests for new features
- Remove tests for deprecated features

### Updating Tests
```bash
# Run affected tests after code change
npx playwright test affected-feature.spec.ts

# Verify all tests still pass
npx playwright test --grep "@fast"
```

### Performance Monitoring
- Log test execution time
- Alert on slowdowns
- Optimize slow tests
- Monitor memory usage

---

## Best Practices

1. **Run in Batches** - Never run all 50+ tests at once
2. **Use Tags** - Always tag tests appropriately
3. **Isolate Tests** - Each test should be independent
4. **Fast Tests First** - Smoke tests before integration
5. **Clear Names** - Test names should describe what they test
6. **Assertions** - Always include meaningful assertions
7. **Error Handling** - Test error cases, not just happy path
8. **Keep Updated** - Update tests when code changes

---

## Questions

For questions about testing:
- See test file comments for implementation details
- Review test fixtures in `tests/e2e/fixtures.ts`
- Check Bruno collection in `bruno/` folder
- Review individual test files for patterns

Questions: libor@arionetworks.com
