# Test Execution Guide

**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/TEST_EXECUTION_GUIDE.md`
**Description:** Quick reference for executing regression tests
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-08

---

## Quick Start

### Run All Tests
```bash
npm test
```

### Run Smoke Tests (Quick Check)
```bash
npm test -- --grep "@smoke"
```

### Run Tests with Interactive Dashboard
```bash
npm run test:ui
```
Opens browser at `http://localhost:3004`

---

## Test Commands by Scenario

### During Development

**Quick validation (5-10 min):**
```bash
npm test -- --grep "@smoke"
```

**Before committing (5-10 min):**
```bash
npm test -- --grep "@smoke"
```

### Before Pushing to Remote

**Quick regression (20-30 min):**
```bash
npm test -- --grep "@fast"
```

### Before Pull Request

**Full regression (60-120 min):**
```bash
npm test
```

### Feature-Specific Testing

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

**Workflows:**
```bash
npm test -- --grep "@workflow"
```

---

## Test Execution Patterns

### Pattern: Smoke Tests (5-10 minutes)
Use after small code changes to quickly verify critical paths.

```bash
npm test -- --grep "@smoke"
```

**What it tests:**
- App loads successfully
- Basic navigation works
- API responds
- No JavaScript errors

---

### Pattern: Fast Regression (20-30 minutes)
Use before pushing code to catch obvious regressions.

```bash
npm test -- --grep "@fast"
```

**What it tests:**
- All smoke tests
- Basic functionality for each feature
- Common error cases
- Basic integrations

---

### Pattern: Complete Regression (60-120 minutes)
Use before releases for comprehensive testing.

```bash
npm test
```

**What it tests:**
- Everything (all @smoke, @fast, and @slow tests)
- All edge cases
- Full integration scenarios
- Performance benchmarks

---

## Advanced Execution

### Run with Browser Visible
```bash
npm test -- --headed
```

### Run Single Test File
```bash
npm test tests/e2e/ui-navigation.spec.ts
```

### Run Tests in Debug Mode
```bash
npm test -- --debug
```

### Generate HTML Report
```bash
npm test -- --reporter=html
npx playwright show-report
```

### Run Only Chromium
```bash
npm test -- --project=chromium
```

### Run Only Firefox
```bash
npm test -- --project=firefox
```

### Custom Grep Pattern
```bash
npm test -- --grep "@api.*@critical"
```

---

## Interactive Dashboard

### Start Dashboard
```bash
npm run test:ui
```

### Features
- Select test suites from UI
- Custom grep patterns
- Live execution status
- Real-time progress tracking
- Results history
- Performance trending

### Access Points
- **UI:** http://localhost:3004
- **API:** http://localhost:3004/api/*

---

## View Test Results

### HTML Report
```bash
npx playwright show-report
```

### JSON Results
```bash
cat tests/test-results/results.json | jq .
```

### JUnit Format (for CI/CD)
```bash
cat tests/test-results/junit.xml
```

---

## Test Categories Reference

### Speed
- `@smoke` - < 5 seconds each
- `@fast` - < 30 seconds each
- `@slow` - > 30 seconds each

### Type
- `@api` - Backend API
- `@ui` - Frontend UI
- `@integration` - Multi-component
- `@e2e` - Full system

### Features
- `@search` - Search functionality
- `@workflow` - Workflow execution
- `@repository` - Repository management
- `@directory` - Directory management
- `@skill` - Skill operations
- `@template` - Template operations

### Priority
- `@critical` - Must pass before release
- `@regression` - Prevent regressions
- `@smoke` - Sanity checks

---

## Troubleshooting

### Tests Won't Start
```bash
# Make sure services are running
npm run dev                    # In another terminal

# Check ports
lsof -i :3003 :3002          # UI and API ports
```

### Tests Timeout
```bash
# Increase timeout
npm test -- --timeout=60000
```

### Flaky Tests
```bash
# Run same test multiple times
npm test tests/e2e/ui-navigation.spec.ts -- --repeat=5
```

### Clear Test Data
```bash
# Remove test artifacts
rm -rf tests/test-results/
rm -rf tests/.playwright/
```

---

## Continuous Integration

### GitHub Actions Example
```yaml
- name: Run Smoke Tests
  run: npm test -- --grep "@smoke"

- name: Run Full Regression
  run: npm test

- name: Upload Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: tests/test-results/
```

---

## NPM Scripts Setup

Add to `package.json`:
```json
{
  "scripts": {
    "test": "playwright test",
    "test:ui": "ts-node tests/regression/regression-ui.ts",
    "test:regression": "ts-node tests/regression/regression-runner.ts",
    "test:smoke": "playwright test --grep '@smoke'",
    "test:fast": "playwright test --grep '@fast'",
    "test:api": "playwright test --grep '@api'",
    "test:watch": "playwright test --watch",
    "test:debug": "playwright test --debug",
    "test:report": "playwright show-report"
  }
}
```

---

## Performance Targets

### Test Duration
- Smoke: 5-10 minutes
- Fast regression: 20-30 minutes
- Full regression: 60-120 minutes

### API Response Times
- Search: < 300ms
- Skill execution: < 1000ms
- Template operations: < 500ms

### Acceptable Flakiness
- 0% - No flaky tests
- If test fails occasionally, investigate and fix

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `port 3003 in use` | UI server already running | `lsof -i :3003` then kill process |
| `Cannot find element` | UI not fully loaded | Increase timeout or add wait |
| `ECONNREFUSED` | API server not running | Start: `npm run dev` |
| `Database locked` | Previous test didn't cleanup | `rm data/*.db` and retry |
| `Flaky test` | Race condition or timing issue | Add explicit waits or retry logic |

---

## Questions?

- See full documentation: [REGRESSION_TEST_SUITE.md](./REGRESSION_TEST_SUITE.md)
- Check test categories: [test-categories.json](./test-categories.json)
- View test source: `tests/e2e/*.spec.ts`

---

**Last Updated:** 2026-01-08
