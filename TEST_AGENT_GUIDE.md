# MyRAGDB Test Agent Guide
**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/TEST_AGENT_GUIDE.md`
**Description:** Comprehensive guide for using the intelligent test agent for automated testing
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-09
**Last Updated:** 2026-01-10

## Overview

The MyRAGDB Test Agent is an intelligent automation system for comprehensive test management. It provides:

- **Automated Test Discovery:** Find and categorize 161+ tests automatically
- **Smart Test Execution:** Run tests with flexible filtering and categorization
- **Advanced Reporting:** Generate HTML, JSON, Markdown, and JUnit reports
- **Coverage Analysis:** Track code coverage with detailed metrics
- **CI/CD Integration:** Full GitHub Actions compatibility
- **Performance Tracking:** Monitor test execution times and trends

## Quick Start

### Using the Test Agent via Claude Code

```bash
# Discover all tests
/test discover

# Run smoke tests (quick validation, ~5-10 minutes)
/test run smoke

# Run with coverage report
/test run all --coverage

# Generate markdown report
/test report --format markdown

# Get test statistics
/test stats --by category
```

### Using the Test Agent Script Directly

```bash
# Activate venv first
source venv/bin/activate

# Discover tests
python scripts/test_agent.py discover

# Run tests
python scripts/test_agent.py run tests/test_agent_platform.py

# Generate statistics
python scripts/test_agent.py stats --group-by category
```

## Test Organization

### Current Test Structure

```
MyRAGDB Tests (161 total)
├── Root Level Tests (11)
│   ├── test_comprehensive.py - Full system functionality
│   ├── test_critical.py - Critical path validation
│   ├── test_mcp.py - MCP connectivity
│   ├── test_mcp_stdio.py - MCP stdio communication
│   └── test_mcp_tools.py - MCP tool execution
│
├── Backend Tests (70+)
│   ├── tests/test_agent_platform.py - Agent orchestration
│   ├── tests/test_llm_endpoints.py - LLM API endpoints
│   ├── tests/test_directory_endpoints.py - Directory management
│   ├── tests/test_cloud_llm_ui.py - Cloud LLM UI
│   └── tests/unit/llm/test_auth.py - Authentication
│
├── Frontend Tests (16+)
│   ├── tests/e2e/api-*.spec.ts - API endpoint tests (5 files)
│   ├── tests/e2e/ui-*.spec.ts - UI component tests (11+ files)
│   └── tests/playwright.config.ts - Playwright configuration
│
└── Script Tests (11)
    ├── scripts/test_file_discovery.py
    └── scripts/test_observability_db.py
```

### Test Categorization

Tests are organized by multiple dimensions:

**By Speed (Execution Time):**
- `@smoke` - < 5 seconds per test, 5-10 min total (15 tests)
- `@fast` - < 30 seconds per test, 20-30 min total (45 tests)
- `@slow` - > 30 seconds per test, 60+ min total (101 tests)

**By Scope:**
- `@unit` - Single component tests
- `@integration` - Multiple components
- `@e2e` - Full system workflows
- `@critical` - Must-pass tests for release

**By Feature Area:**
- `@api` - Backend API endpoints
- `@ui` - Frontend user interface
- `@search` - Search functionality
- `@indexing` - File indexing operations
- `@repository` - Repository management
- `@directory` - Directory management
- `@skill` - Skill operations
- `@template` - Template operations
- `@workflow` - Workflow execution

## Commands Guide

### Test Discovery

```bash
# Discover all tests
/test discover

# Discover tests in specific file
/test discover --pattern tests/test_agent_platform.py

# Show discovery summary
/test discover --summary
```

### Test Execution

#### By Speed

```bash
# Quick validation (5-10 min)
/test run smoke

# Fast tests (20-30 min)
/test run fast

# All tests including slow (60+ min)
/test run all

# Critical path only (for pre-release)
/test run critical
```

#### By Category

```bash
# API tests
/test run @api

# UI tests
/test run @ui

# Search functionality
/test run @search

# Indexing operations
/test run @indexing

# Repository management
/test run @repository

# Directory management
/test run @directory

# Skill operations
/test run @skill

# Template operations
/test run @template

# Workflow tests
/test run @workflow
```

#### By Test Type

```bash
# Unit tests only
/test run unit

# Integration tests only
/test run integration

# End-to-end tests only
/test run e2e

# All unit + integration (no E2E)
/test run --exclude e2e
```

#### With Coverage

```bash
# Include coverage report
/test run all --coverage

# Coverage for specific category
/test run @api --coverage

# Coverage with verbose output
/test run all --coverage --verbose
```

#### With Verbosity

```bash
# Verbose output
/test run all --verbose

# Minimal output
/test run all --quiet

# Detailed failure information
/test run all --verbose --tb=short
```

#### Advanced Options

```bash
# Stop on first failure
/test run all --fail-fast

# Parallel execution (use with caution)
/test run all --workers 4

# Collect tests without running
/test run all --collect-only

# Use specific Python version
/test run all --python 3.11

# Add environment variables
/test run all --env "TEST_ENV=staging"
```

### Test Reporting

#### Report Generation

```bash
# Markdown report
/test report --format markdown

# HTML report
/test report --format html

# JSON report
/test report --format json

# Generate all report formats
/test report --format all
```

#### Coverage Reports

```bash
# Include coverage in report
/test report --coverage

# Coverage-only report
/test report --coverage --format html

# Generate coverage badge
/test report --coverage --badge
```

#### Compare Results

```bash
# Compare current vs previous run
/test report --compare

# Compare with specific baseline
/test report --compare --baseline main
```

### Test Statistics

#### General Statistics

```bash
# Show test counts
/test stats

# Show by category
/test stats --by category

# Show by speed
/test stats --by speed

# Show by type
/test stats --by type

# Show by file
/test stats --by file
```

#### Performance Analysis

```bash
# Show slowest tests
/test stats --slow --limit 20

# Show flaky tests (failures over last N runs)
/test stats --flaky

# Show test execution trends
/test stats --trends

# Performance comparison
/test stats --compare
```

## Frontend Testing (Playwright)

### UI Test Execution

```bash
# Run all UI tests
/test ui run all

# Run with browser visible
/test ui run all --headed

# Run in debug mode
/test ui run all --debug

# Run specific browser
/test ui run all --browser chromium
/test ui run all --browser firefox

# Run specific test file
/test ui run tests/e2e/ui-navigation.spec.ts

# Interactive mode
/test ui run --interactive
```

### UI Test Reporting

```bash
# Generate UI test report
/test ui report

# HTML report with videos
/test ui report --format html

# JUnit report for CI
/test ui report --format junit

# Screenshots of failures
/test ui report --screenshots
```

## CI/CD Integration

### GitHub Actions Integration

```bash
# Prepare results for CI
/test ci-prepare

# Generate JUnit XML
/test ci-generate-junit

# Check CI readiness
/test ci-check

# Simulate CI run
/test ci-simulate --ci github-actions
```

### Artifact Generation

Test results are automatically generated in multiple formats:

- **HTML Report:** `tests/test-results/report.html`
- **JSON Results:** `tests/test-results/results.json`
- **JUnit XML:** `tests/test-results/junit.xml`
- **Coverage HTML:** `tests/test-results/coverage/index.html`
- **Coverage XML:** `tests/test-results/coverage.xml`

### CI Pipeline Best Practices

1. **Before each commit (smoke tests):**
   ```bash
   /test run smoke
   ```

2. **Before pull request (category-specific):**
   ```bash
   /test run @directory --coverage  # For directory changes
   /test run @search --coverage      # For search changes
   ```

3. **Before release (full regression):**
   ```bash
   /test run all --coverage
   /test ci-check
   ```

4. **In GitHub Actions:**
   ```yaml
   - name: Run tests
     run: |
       source venv/bin/activate
       /test run all --coverage
       /test ci-generate-junit
   ```

## Performance Targets

### Test Duration Expectations

- **Smoke tests:** 5-10 minutes total
- **Fast tests:** 20-30 minutes total
- **All tests:** 60-120 minutes total
- **Individual test:** < 30 seconds (ideally)

### Code Coverage Targets

- **Minimum coverage:** 80%
- **Target coverage:** 85%+
- **Critical path:** 95%+

### API Performance Targets

- **Search:** < 300ms
- **Skill execution:** < 1000ms
- **Template operations:** < 500ms
- **File indexing:** < 100ms per file

## Test Creation Workflow

### Creating a New Test

```bash
# Create new test interactively
/test create --name test_new_feature --type unit --category @api

# Create test from failing endpoint
/test create --from-error "Failed to fetch /api/v1/directories"

# Create test from code change
/test create --from-change src/myragdb/api/routes/directories.py

# Create test for coverage gaps
/test create --coverage-gaps --min-coverage 85
```

### Test Template Structure

New tests should follow this structure:

```python
# File: tests/test_feature_name.py
# Description: Test feature_name functionality
# Author: Your Name
# Created: YYYY-MM-DD

import pytest
from unittest.mock import patch, AsyncMock

class TestFeatureName:
    """Test suite for feature_name."""

    @pytest.mark.asyncio
    @pytest.mark.fast
    @pytest.mark.api
    async def test_feature_operation(self):
        """Test basic feature operation."""
        # Setup
        # Execute
        # Assert
        pass

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_feature_with_dependencies(self):
        """Test feature with system dependencies."""
        # Setup
        # Execute
        # Assert
        pass
```

### Pytest Markers

Use these markers in new tests:

```python
# Speed
@pytest.mark.smoke    # Quick test (< 5 seconds)
@pytest.mark.fast     # Fast test (< 30 seconds)
@pytest.mark.slow     # Slow test (> 30 seconds)

# Scope
@pytest.mark.unit        # Unit test
@pytest.mark.integration # Integration test
@pytest.mark.e2e         # End-to-end test
@pytest.mark.critical    # Critical path test

# Feature Areas
@pytest.mark.api         # API endpoint test
@pytest.mark.ui          # UI test
@pytest.mark.search      # Search functionality test
@pytest.mark.indexing    # Indexing test
@pytest.mark.repository  # Repository test
@pytest.mark.directory   # Directory test
@pytest.mark.skill       # Skill test
@pytest.mark.template    # Template test
@pytest.mark.workflow    # Workflow test

# Special
@pytest.mark.asyncio     # Async test
@pytest.mark.skip        # Skip test
@pytest.mark.xfail       # Expected failure
```

## Troubleshooting

### Common Issues

#### Tests not discovered
```bash
# Check pytest configuration
pytest --collect-only

# Verify test file naming
ls tests/test_*.py

# Check for syntax errors
python -m py_compile tests/test_file.py
```

#### Failing tests
```bash
# Run with verbose output
/test run --verbose

# Run specific failing test
/test run tests/test_file.py::TestClass::test_function

# Get stack trace
/test run --verbose --tb=long
```

#### Coverage not generated
```bash
# Install coverage tools
source venv/bin/activate
pip install pytest-cov

# Run with explicit coverage
pytest --cov=src/myragdb --cov-report=html
```

#### Database/fixture issues
```bash
# Reset test database
rm -rf tests/test-results/

# Re-run with fresh fixtures
/test run --reset-fixtures
```

## Best Practices

### Before Every Commit
```bash
# Run smoke tests (quick validation)
/test run smoke

# Verify your changes don't break tests
/test run @<your-feature>
```

### Before Pull Request
```bash
# Run tests for changed feature areas
/test run @directory --coverage
/test run @search --coverage

# Generate report
/test report --format markdown
```

### Before Release
```bash
# Run full regression
/test run all --coverage

# Verify CI readiness
/test ci-check

# Generate comprehensive report
/test report --format html
```

### Regular Maintenance
```bash
# Weekly: Check test coverage trends
/test stats --trends

# Monthly: Identify and fix flaky tests
/test stats --flaky

# Quarterly: Performance review
/test stats --slow --limit 30
```

## Integration with Development

### Local Development Workflow

1. **Before commit:**
   ```bash
   source venv/bin/activate
   /test run smoke
   git add .
   git commit -m "..."
   ```

2. **Before push:**
   ```bash
   /test run @<your-feature> --coverage
   ```

3. **After pull request merge:**
   ```bash
   /test run all --coverage --ci-exit-code
   ```

### In Pull Request Review

1. **Commenter checks tests:**
   ```
   /test run @changes
   ```

2. **View coverage report:**
   ```
   /test report --coverage --compare
   ```

3. **Approve if tests pass:**
   ```
   All smoke tests passed ✓
   Coverage +2% improvement ✓
   ```

## Advanced Topics

### Custom Test Filters

Combine markers with pytest syntax:

```bash
# Tests that are either fast OR unit
/test run --markers "fast or unit"

# Tests that are NOT slow and ARE api
/test run --markers "not slow and api"

# Tests that are critical but not skipped
/test run --markers "critical and not skip"
```

### Test Dependencies

Some tests depend on others running first:

```bash
# Run with dependency resolution
/test run --resolve-dependencies

# Show dependency graph
/test analyze --dependencies
```

### Performance Profiling

Profile test execution:

```bash
# Show slowest tests with timing breakdown
/test analyze --profile

# Generate execution timeline
/test analyze --timeline
```

## Support & Questions

For help with the test agent:

- **Documentation:** `TEST_AGENT_GUIDE.md` (this file)
- **Command Help:** `/test --help`
- **Questions:** libor@arionetworks.com

## See Also

- `TEST_EXECUTION_GUIDE.md` - Quick reference
- `REGRESSION_TEST_SUITE.md` - Test strategy
- `UI_TESTING_GUIDE.md` - UI testing details
- `.claude/commands/test.md` - Slash command documentation
