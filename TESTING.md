# MyRAGDB Testing Documentation

**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/TESTING.md`
**Description:** Central testing documentation for MyRAGDB project
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-08

---

## Overview

MyRAGDB has a comprehensive regression test suite with:

- **9+ test files** covering API, UI, and integration scenarios
- **100+ individual test cases** with flexible filtering
- **Web-based dashboard** for interactive test management
- **Incremental execution** - from 5-minute smoke tests to full 2-hour regression
- **Category-based filtering** - run tests by feature, type, or speed

---

## Test Suites

### Python Tests (Backend)

| Suite | Location | Purpose | Run |
|-------|----------|---------|-----|
| Critical Tests | `test_critical.py` | Core functionality verification | `python test_critical.py` |
| Comprehensive Tests | `test_comprehensive.py` | Full system testing | `python test_comprehensive.py` |
| Directory Indexing | `test_critical.py::test_4` | Directory scanning and indexing | `python test_critical.py` |
| Repository Discovery | `test_critical.py::test_1` | Repository finding | `python test_critical.py` |
| Database Integrity | `test_critical.py::test_2` | Schema and data validation | `python test_critical.py` |

### Playwright Tests (Frontend & E2E)

| Suite | Location | Purpose | Duration | Run |
|-------|----------|---------|----------|-----|
| Smoke Tests | `tests/e2e/*.spec.ts` | Critical path validation | 5-10 min | `npm test -- --grep "@smoke"` |
| Fast Regression | `tests/e2e/*.spec.ts` | Quick full regression | 20-30 min | `npm test -- --grep "@fast"` |
| API Tests | `tests/e2e/api-*.spec.ts` | Backend API functionality | 15-25 min | `npm test -- --grep "@api"` |
| UI Tests | `tests/e2e/ui-*.spec.ts` | Frontend functionality | 15-25 min | `npm test -- --grep "@ui"` |
| Integration Tests | `tests/e2e/*.spec.ts` | Multi-component workflows | 30-45 min | `npm test -- --grep "@integration"` |
| Full Regression | All tests | Complete test suite | 60-120 min | `npm test` |

---

## Quick Start

### 5-10 Minutes (Smoke Tests)
```bash
# Verify critical functionality
npm test -- --grep "@smoke"
python test_critical.py
```

### 20-30 Minutes (Fast Regression)
```bash
# Catch obvious regressions
npm test -- --grep "@fast"
```

### 60-120 Minutes (Full Regression)
```bash
# Comprehensive testing before release
npm test
python test_comprehensive.py
```

### Interactive Dashboard
```bash
npm run test:ui
# Opens http://localhost:3004
```

---

## Documentation Map

### For Different Audiences

**🚀 Quick Start**
- Start here: [tests/README.md](./tests/README.md)
- Common commands: [tests/TEST_EXECUTION_GUIDE.md](./tests/TEST_EXECUTION_GUIDE.md)

**📚 Complete Reference**
- Full strategy: [tests/REGRESSION_TEST_SUITE.md](./tests/REGRESSION_TEST_SUITE.md)
- Test categories: [tests/test-categories.json](./tests/test-categories.json)

**🔧 Implementation**
- Test runner: [tests/regression/regression-runner.ts](./tests/regression/regression-runner.ts)
- Dashboard: [tests/regression/regression-ui.ts](./tests/regression/regression-ui.ts)
- Fixtures: [tests/e2e/fixtures.ts](./tests/e2e/fixtures.ts)

**🧪 Test Files**
- API tests: [tests/e2e/api-*.spec.ts](./tests/e2e/)
- UI tests: [tests/e2e/ui-*.spec.ts](./tests/e2e/)
- Config: [tests/playwright.config.ts](./tests/playwright.config.ts)

---

## Test Execution Patterns

### Pattern 1: After Code Change (5-10 min)
```bash
npm test -- --grep "@smoke"
```
Validates critical paths work.

### Pattern 2: Before Push (20-30 min)
```bash
npm test -- --grep "@fast"
```
Catches obvious regressions before git push.

### Pattern 3: Before Pull Request (60-120 min)
```bash
npm test
python test_comprehensive.py
```
Full regression testing before opening PR.

### Pattern 4: Feature-Specific (Variable)
```bash
# Search changes
npm test -- --grep "@search"

# Repository changes
npm test -- --grep "@repository"

# Directory changes
npm test -- --grep "@directory"

# API changes
npm test -- --grep "@api"

# UI changes
npm test -- --grep "@ui"
```

### Pattern 5: Before Release
```bash
npm test                    # All Playwright tests
python test_comprehensive.py # All Python tests
npm run test:ui            # Dashboard verification
```

---

## Test Commands Reference

### All Tests
```bash
npm test                              # Run all Playwright tests
python test_critical.py             # Run critical Python tests
python test_comprehensive.py         # Run comprehensive Python tests
```

### By Duration
```bash
npm test -- --grep "@smoke"         # 5-10 minutes
npm test -- --grep "@fast"          # 20-30 minutes
npm test                             # 60-120 minutes (all)
```

### By Feature
```bash
npm test -- --grep "@search"        # Search functionality
npm test -- --grep "@workflow"      # Workflows
npm test -- --grep "@repository"    # Repository mgmt
npm test -- --grep "@directory"     # Directory mgmt
npm test -- --grep "@skill"         # Skills
npm test -- --grep "@template"      # Templates
```

### By Layer
```bash
npm test -- --grep "@api"           # Backend APIs
npm test -- --grep "@ui"            # Frontend UI
npm test -- --grep "@integration"   # Integration tests
```

### Advanced
```bash
npm test -- --headed                # Show browser
npm test -- --debug                 # Debug mode
npm test -- --project=chromium      # Chromium only
npm test -- --project=firefox       # Firefox only
npx playwright show-report          # View HTML report
```

### Dashboard
```bash
npm run test:ui                      # Interactive UI at localhost:3004
```

---

## Test Categories

### Speed
- `@smoke` - Critical fast tests (< 5 sec each)
- `@fast` - Quick tests (< 30 sec each)
- `@slow` - Long-running tests (> 30 sec each)

### Layer
- `@api` - Backend API tests
- `@ui` - Frontend UI tests
- `@integration` - Multi-component tests
- `@e2e` - Full system workflows

### Feature
- `@search` - Search functionality
- `@workflow` - Workflow execution
- `@repository` - Repository management
- `@directory` - Directory management
- `@skill` - Skill operations
- `@template` - Template operations
- `@indexing` - File indexing

### Priority
- `@critical` - Must pass before release
- `@regression` - Prevent regressions
- `@smoke` - Sanity checks

---

## Performance Targets

### API Response Time
- Search: < 300ms
- Skill execution: < 1000ms
- Template operations: < 500ms
- Directory operations: < 500ms

### UI Response Time
- Page load: < 2s
- Search results: < 1s
- Navigation: < 500ms

### Test Execution
- Smoke tests: 5-10 minutes
- Fast regression: 20-30 minutes
- Full regression: 60-120 minutes

---

## Results & Reporting

### View Results
```bash
npx playwright show-report          # HTML report
cat tests/test-results/results.json # JSON results
cat tests/test-results/history.json # Results history
```

### Generated Files
```
tests/test-results/
├── results.json                # Detailed test results
├── junit.xml                   # JUnit for CI/CD
├── report.html                 # Interactive report
├── history.json                # Results history
└── videos/                     # Failed test videos
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Smoke Tests
  run: npm test -- --grep "@smoke"

- name: Run Full Regression
  run: npm test

- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: tests/test-results/
```

---

## Troubleshooting

### Services Not Running
```bash
# Start API and UI
npm run dev
```

### Port Conflicts
```bash
# Check port usage
lsof -i :3002        # API port
lsof -i :3003        # UI port
lsof -i :3004        # Dashboard port

# Kill process
kill -9 <PID>
```

### Tests Timeout
- Increase timeout: `npm test -- --timeout=60000`
- Check network: `npm test -- --headed`
- Check services: Run `npm run dev`

### Database Issues
```bash
# Reset test data
rm -rf data/
npm run dev  # Recreates on startup
```

### Flaky Tests
- Increase timeout on timing-sensitive tests
- Add explicit wait conditions
- Check network stability

---

## Key Metrics

### Coverage
- **API Layer** - 6 test files covering all endpoints
- **UI Layer** - 4 test files covering all features
- **Integration** - Full workflow tests
- **Performance** - Response time benchmarks

### Quality
- **Pass Rate Target** - 100%
- **Flakiness Target** - 0%
- **Critical Tests** - Always passing

### Performance
- **Smoke tests** - 5-10 minutes
- **Fast regression** - 20-30 minutes
- **Full regression** - 60-120 minutes

---

## Maintenance

### Weekly
- Review flaky tests
- Check for new failures
- Monitor test execution time

### Monthly
- Review test coverage
- Update test documentation
- Optimize slow tests

### Quarterly
- Full test audit
- Review category tags
- Update performance targets

---

## Resources

### Documentation
- [tests/README.md](./tests/README.md) - Overview and quick start
- [tests/TEST_EXECUTION_GUIDE.md](./tests/TEST_EXECUTION_GUIDE.md) - Command reference
- [tests/REGRESSION_TEST_SUITE.md](./tests/REGRESSION_TEST_SUITE.md) - Complete strategy
- [tests/test-categories.json](./tests/test-categories.json) - Category definitions

### Test Files
- [tests/e2e/](./tests/e2e/) - All Playwright tests
- [test_critical.py](./test_critical.py) - Critical Python tests
- [test_comprehensive.py](./test_comprehensive.py) - Comprehensive Python tests

### Tools
- [tests/regression/regression-runner.ts](./tests/regression/regression-runner.ts) - CLI runner
- [tests/regression/regression-ui.ts](./tests/regression/regression-ui.ts) - Web dashboard
- [tests/playwright.config.ts](./tests/playwright.config.ts) - Playwright config

---

## Contact & Support

For questions about:
- **How to run tests** - See TEST_EXECUTION_GUIDE.md
- **What tests exist** - See tests/README.md
- **Test strategy** - See REGRESSION_TEST_SUITE.md
- **Specific tests** - Check test file itself

Contact: libor@arionetworks.com

---

## Summary

MyRAGDB has a **comprehensive, well-organized regression test suite** with:

✅ **9+ test files** with 100+ test cases
✅ **Flexible filtering** - by speed, feature, or layer
✅ **Interactive dashboard** - web UI for test management
✅ **Incremental patterns** - from 5-min smoke to 2-hour full
✅ **Complete documentation** - guides for all scenarios
✅ **Performance tracking** - results history and trending
✅ **CI/CD ready** - integrates with GitHub Actions and others

**Start testing:**
```bash
npm test -- --grep "@smoke"  # 5-10 minutes
npm run test:ui              # Interactive dashboard
```

---

**Last Updated:** 2026-01-08
**Status:** Complete and operational
**Next Review:** 2026-04-08
