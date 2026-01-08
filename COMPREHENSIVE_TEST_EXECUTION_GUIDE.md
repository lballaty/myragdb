# Comprehensive Chat Test Suite Execution Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/COMPREHENSIVE_TEST_EXECUTION_GUIDE.md
**Description:** Complete guide to running 300+ comprehensive chat and dashboard tests
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-08

---

## Quick Start

### Run All Chat Tests (Comprehensive Suite)
```bash
npm test ui-chat*.spec.ts
```
**Duration:** 60-120 minutes
**Coverage:** 300+ tests covering all chat and dashboard functionality

### Run Quick Sanity Check
```bash
npm test -- --grep "@smoke"
```
**Duration:** 5-10 minutes
**Coverage:** Critical path tests only

### Run Pre-Push Tests
```bash
npm test -- --grep "@fast"
```
**Duration:** 20-30 minutes
**Coverage:** Full quick regression

---

## Test Execution by Duration

### 5-10 Minutes - Smoke Tests
```bash
npm test -- --grep "@smoke"
```
**When:** After every code change
**What:** Critical functionality verification
**Tests:** ~20-30 tests
**Purpose:** Catch obvious breakage immediately

### 20-30 Minutes - Fast Regression
```bash
npm test -- --grep "@fast"
```
**When:** Before git push
**What:** Quick full regression
**Tests:** ~150-180 tests
**Purpose:** Catch regressions before pushing

### 30-60 Minutes - Comprehensive Chat Tests
```bash
npm test -- --grep "@chat"
```
**When:** Before pull request
**What:** All chat-related tests
**Tests:** ~150+ tests
**Purpose:** Full chat feature verification

### 60-120 Minutes - Complete Suite
```bash
npm test ui-chat*.spec.ts
```
**When:** Before release
**What:** Entire test suite
**Tests:** 300+ tests
**Purpose:** Comprehensive verification

### Variable (30+ minutes) - Slow Tests Only
```bash
npm test -- --grep "@slow"
```
**When:** Before release or after major changes
**What:** All long-running tests
**Tests:** ~100+ tests
**Purpose:** Thorough scenario and workflow testing

---

## Test Execution by Feature Area

### Chat Tester Page Tests
```bash
npm test -- --grep "@scenario-chat"
```
**Duration:** 10-15 minutes
**Tests:** 25+ tests
**Coverage:** Chat model selection, message input, token counting, context compression

### LLM Manager Configuration Tests
```bash
npm test -- --grep "@scenario-llm"
```
**Duration:** 10-15 minutes
**Tests:** 25+ tests
**Coverage:** Gemini, OpenAI, Anthropic setup workflows

### Dashboard Tab Tests
```bash
npm test -- --grep "@dashboard"
```
**Duration:** 10-15 minutes
**Tests:** 40+ tests
**Coverage:** All 6 main dashboard tabs

### Search Functionality Tests
```bash
npm test -- --grep "@scenario-search"
```
**Duration:** 8-12 minutes
**Tests:** 15+ tests
**Coverage:** Search input, submission, results, filtering

### Repository Management Tests
```bash
npm test -- --grep "@scenario-repo"
```
**Duration:** 8-10 minutes
**Tests:** 15+ tests
**Coverage:** Repository list, add, enable/disable, delete

### Directory Management Tests
```bash
npm test -- --grep "@scenario-dir"
```
**Duration:** 8-10 minutes
**Tests:** 15+ tests
**Coverage:** Directory list, add, enable/disable, delete

### Activity Monitor Tests
```bash
npm test -- --grep "@activity"
```
**Duration:** 5-8 minutes
**Tests:** 6+ tests
**Coverage:** Activity logs, server logs, filtering

### Observability Tests
```bash
npm test -- --grep "@observability"
```
**Duration:** 5-8 minutes
**Tests:** 6+ tests
**Coverage:** System metrics, statistics, recent errors

---

## Test Execution by Element Type

### Button Element Tests
```bash
npm test -- --grep "@button"
```
**Duration:** 15-20 minutes
**Tests:** 50+ tests
**Coverage:** Every button click, hover, focus, disabled state

### Input Field Tests
```bash
npm test -- --grep "@input"
```
**Duration:** 20-25 minutes
**Tests:** 50+ tests
**Coverage:** Text input, clear, validation, focus/blur

### Dropdown Tests
```bash
npm test -- --grep "@dropdown"
```
**Duration:** 10-15 minutes
**Tests:** 30+ tests
**Coverage:** Open, select options, keyboard navigation

### Toggle/Checkbox Tests
```bash
npm test -- --grep "@toggle"
```
**Duration:** 10-12 minutes
**Tests:** 30+ tests
**Coverage:** On/off states, click, keyboard, visual feedback

### Form Tests
```bash
npm test -- --grep "@form"
```
**Duration:** 8-10 minutes
**Tests:** 20+ tests
**Coverage:** Form submission, validation, reset

---

## Test Execution by State/Type

### Button State Tests (All Variations)
```bash
npm test -- --grep "@button-state"
```
**Duration:** 15-20 minutes
**Tests:** 40+ tests
**Coverage:** Normal, hover, focus, active, disabled, loading states

### Input State Tests (All Variations)
```bash
npm test -- --grep "@input-state"
```
**Duration:** 20-25 minutes
**Tests:** 50+ tests
**Coverage:** Empty, filled, focused, blurred, disabled, error states

### Dropdown State Tests (All Variations)
```bash
npm test -- --grep "@dropdown-state"
```
**Duration:** 10-15 minutes
**Tests:** 30+ tests
**Coverage:** Closed, open, selected, keyboard states

### Toggle State Tests (All Variations)
```bash
npm test -- --grep "@toggle-state"
```
**Duration:** 10-12 minutes
**Tests:** 30+ tests
**Coverage:** On, off, active, focused, rapid click states

---

## Test Execution by Test Type

### Accessibility Tests (a11y)
```bash
npm test -- --grep "@a11y"
```
**Duration:** 10-15 minutes
**Tests:** 30+ tests
**Coverage:** ARIA labels, keyboard navigation, focus, semantic HTML

### Responsive Design Tests
```bash
npm test -- --grep "@responsive"
```
**Duration:** 15-20 minutes
**Tests:** 15+ tests
**Coverage:** Mobile (375x667), Tablet (768x1024), Desktop (1920x1080)

### Workflow Tests
```bash
npm test -- --grep "@workflow"
```
**Duration:** 20-30 minutes
**Tests:** 25+ tests
**Coverage:** Complete multi-step user workflows

### Scenario Tests
```bash
npm test -- --grep "@scenario"
```
**Duration:** 30-40 minutes
**Tests:** 55+ tests
**Coverage:** Complete workflows and user scenarios

### Edge Case Tests
```bash
npm test -- --grep "@edge-case"
```
**Duration:** 10-15 minutes
**Tests:** 20+ tests
**Coverage:** Boundary conditions, unusual inputs

### Error Handling Tests
```bash
npm test -- --grep "@error-case"
```
**Duration:** 10-15 minutes
**Tests:** 20+ tests
**Coverage:** Error scenarios and recovery

### Stress Tests
```bash
npm test -- --grep "@stress"
```
**Duration:** 5-10 minutes
**Tests:** 10+ tests
**Coverage:** Rapid interactions, concurrent actions

---

## Combined Execution Patterns

### Chat Tests Only (Fast + Slow)
```bash
npm test -- --grep "@chat"
```
**Duration:** 30-60 minutes
**Tests:** 150+ tests
**Coverage:** All chat interface tests

### Dashboard Tests Only
```bash
npm test -- --grep "@dashboard @fast"
```
**Duration:** 15-20 minutes
**Tests:** 40+ tests
**Coverage:** All main dashboard tabs

### Accessibility and Responsive (Full Coverage)
```bash
npm test -- --grep "@a11y|@responsive"
```
**Duration:** 25-35 minutes
**Tests:** 45+ tests
**Coverage:** All accessibility and responsive tests

### All Button and Input Tests
```bash
npm test -- --grep "@button|@input"
```
**Duration:** 35-45 minutes
**Tests:** 100+ tests
**Coverage:** Every button and input interaction

### All State-Based Tests
```bash
npm test -- --grep "@state"
```
**Duration:** 25-35 minutes
**Tests:** 50+ tests
**Coverage:** All state persistence and changes

### Workflows and Scenarios (Complete Interactions)
```bash
npm test -- --grep "@workflow|@scenario"
```
**Duration:** 40-60 minutes
**Tests:** 80+ tests
**Coverage:** All multi-step user workflows

### Fast + Accessibility (Pre-PR Check)
```bash
npm test -- --grep "@fast|@a11y"
```
**Duration:** 30-40 minutes
**Tests:** 180+ tests
**Coverage:** Quick regression + accessibility

### Everything Except Slow Tests
```bash
npm test -- --grep "^((?!@slow).)*$"
```
**Duration:** 30-45 minutes
**Tests:** 200+ tests
**Coverage:** Most tests except long-running ones

---

## Specific Test Execution Examples

### LLM Manager - All Variations
```bash
npm test -- --grep "@llm-manager"
```
Tests all LLM provider configurations and API key inputs

### Chat Message Handling
```bash
npm test -- --grep "@scenario-chat.*message"
```
Tests message input, display, formatting, and history

### Tab Navigation Complete
```bash
npm test -- --grep "@tab"
```
Tests all tab navigation and switching

### Model Selection Workflows
```bash
npm test -- --grep "model.*selection|MODEL.*SELECT"
```
Tests model dropdown selection across chat and LLM manager

### Focus and Keyboard Navigation
```bash
npm test -- --grep "@focus|@keyboard"
```
Tests keyboard accessibility throughout the app

### Visual and Layout Tests
```bash
npm test -- --grep "@visual|@responsive|@hover"
```
Tests appearance, layout, and hover states

---

## Test Files Available

### Individual File Execution
```bash
# Original comprehensive tests
npm test tests/e2e/ui-chat.spec.ts

# New comprehensive suite (98 tests)
npm test tests/e2e/ui-chat-comprehensive.spec.ts

# Granular state testing (83 tests)
npm test tests/e2e/ui-chat-granular.spec.ts

# Workflow scenarios (55 tests)
npm test tests/e2e/ui-chat-scenarios.spec.ts

# All chat tests combined (300+ tests)
npm test ui-chat*.spec.ts
```

---

## Interactive Test Management

### Using Playwright Inspector
```bash
npm test -- --ui
```
Opens interactive test UI at `http://localhost:3004`

### Debug Single Test
```bash
npm test -- --grep "TAB-001"
```
Run only the "TAB-001" test with detailed output

### Watch Mode (Re-run on File Change)
```bash
npm test -- --watch
```
Tests re-run when test files change

### Run Tests with Headed Browser
```bash
npm test -- --headed
```
See browser interactions as tests run

---

## CI/CD Integration Examples

### GitHub Actions Example
```yaml
name: Test Chat Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1/3, 2/3, 3/3]  # Parallel execution

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm test -- --grep "@chat" --shard=${{ matrix.shard }}
```

### Pre-Commit Hook
```bash
#!/bin/bash
npm test -- --grep "@smoke"
if [ $? -ne 0 ]; then
  exit 1
fi
```

### Pre-Push Hook
```bash
#!/bin/bash
npm test -- --grep "@fast"
if [ $? -ne 0 ]; then
  exit 1
fi
```

---

## Troubleshooting Test Execution

### Tests Timing Out
```bash
# Increase timeout for slow tests
npm test -- --timeout 60000
```

### Tests Failing Due to Port Issues
```bash
# Verify server is running on port 3003
lsof -i :3003

# Stop server if needed
pkill -f "localhost:3003"

# Restart server
npm run dev
```

### Tests Failing Due to Missing Elements
```bash
# Run with debug output
npm test -- --grep "@chat" --debug
```

### Flaky Tests
```bash
# Run test multiple times to verify stability
npm test -- --grep "TEST-NAME" --repeat 5
```

---

## Test Performance Optimization

### Run Tests in Parallel (Sharding)
```bash
# Shard tests across 4 workers
npm test -- --shard=1/4
npm test -- --shard=2/4
npm test -- --shard=3/4
npm test -- --shard=4/4
```

### Skip Visual Comparisons (if not needed)
```bash
npm test -- --grep "^((?!@visual).)*$"
```

### Run Only Fast Tests (for development)
```bash
npm test -- --grep "@fast"
```

### Run Tests Without Screenshots/Videos (for speed)
```bash
npm test -- --grep "@chat" --trace off
```

---

## Reporting Test Results

### Generate HTML Report
```bash
npm test ui-chat*.spec.ts
# Report available at: playwright-report/index.html
```

### Generate JSON Report
```bash
npm test -- --reporter=json > test-results.json
```

### View Last Report
```bash
npx playwright show-report
```

---

## Test Maintenance Commands

### List All Available Tests
```bash
npm test -- --list
```

### Update Snapshots (if using visual comparisons)
```bash
npm test -- --update-snapshots
```

### Clear Test Cache
```bash
rm -rf .playwright/
npm test -- --install
```

---

## Summary Table

| Pattern | Duration | Tests | Use Case |
|---------|----------|-------|----------|
| `@smoke` | 5-10 min | 20-30 | After code changes |
| `@fast` | 20-30 min | 150-180 | Before git push |
| `@chat` | 30-60 min | 150+ | Before PR |
| `ui-chat*.spec.ts` | 60-120 min | 300+ | Before release |
| `@button\|@input` | 35-45 min | 100+ | Element testing |
| `@a11y` | 10-15 min | 30+ | Accessibility check |
| `@responsive` | 15-20 min | 15+ | Mobile testing |
| `@scenario\|@workflow` | 40-60 min | 80+ | Workflow verification |
| `@edge-case\|@stress` | 15-25 min | 30+ | Edge case verification |

---

## Quick Reference

```bash
# Quick sanity (5 min)
npm test -- --grep "@smoke"

# Pre-push (30 min)
npm test -- --grep "@fast"

# Chat tests (60 min)
npm test -- --grep "@chat"

# Full suite (120 min)
npm test ui-chat*.spec.ts

# By feature
npm test -- --grep "@chat @fast"        # Fast chat tests only
npm test -- --grep "@button"            # All button tests
npm test -- --grep "@a11y"              # Accessibility tests

# By state
npm test -- --grep "@button-state"      # Button state tests
npm test -- --grep "@input-state"       # Input state tests

# Interactive UI
npm test -- --ui                        # Open test management UI

# Debug single test
npm test -- --grep "TAB-001" --headed   # Run with visual browser
```

---

**Last Updated:** 2026-01-08
**Total Tests:** 300+ comprehensive tests
**Test Files:** 4 comprehensive test suites
**Execution Patterns:** 20+ different patterns available
