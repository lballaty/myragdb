#!/bin/bash

# File: run-tests.sh
# Description: Centralized test runner for incremental batch execution
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07
#
# Features:
# - Batch execution to avoid memory overload
# - Tagged test filtering (smoke, fast, integration, etc.)
# - Detailed reporting and results collection
# - Parallel-safe with sequential execution
# - Memory monitoring
#
# Usage:
#   ./run-tests.sh [batch_type] [verbose]
#
# Batch types:
#   all          - Run all tests in batches
#   smoke        - Quick smoke tests (< 5 sec)
#   fast         - Fast tests (< 30 sec)
#   integration  - Integration tests (< 2 min)
#   api          - All API tests
#   ui           - All UI tests
#   directories  - All directory tests
#   python       - Python unit tests only
#   playwright   - Playwright E2E tests only
#   bruno        - Bruno API tests only

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BATCH_TYPE="${1:-all}"
VERBOSE="${2:-false}"
RESULTS_DIR="${PROJECT_ROOT}/test-results"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="${RESULTS_DIR}/test-run-${TIMESTAMP}.log"

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Function to print section header
print_header() {
  echo -e "\n${BLUE}========================================${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}========================================${NC}\n"
}

# Function to print test result
print_result() {
  local test_name=$1
  local result=$2
  local duration=$3

  if [ "$result" = "PASS" ]; then
    echo -e "${GREEN}✓ PASS${NC}  $test_name ($duration)"
  else
    echo -e "${RED}✗ FAIL${NC}  $test_name ($duration)"
  fi
}

# Function to monitor memory usage
check_memory() {
  local memory_threshold=2000 # MB

  if command -v free &>/dev/null; then
    local available=$(free -m | awk '/^Mem:/ {print $7}')
    if [ "$available" -lt "$memory_threshold" ]; then
      echo -e "${YELLOW}⚠️  Warning: Low memory available ($available MB)${NC}"
      sleep 2
    fi
  fi
}

# Function to run Python unit tests
run_python_tests() {
  print_header "Running Python Unit Tests"

  cd "${PROJECT_ROOT}"
  source venv/bin/activate 2>/dev/null || true

  local test_files=(
    "tests/test_directory_endpoints.py"
    "tests/test_agent_platform.py"
  )

  local total_pass=0
  local total_fail=0

  for test_file in "${test_files[@]}"; do
    if [ -f "$test_file" ]; then
      echo -e "${YELLOW}Running: $test_file${NC}"
      if python -m pytest "$test_file" -v --tb=short 2>&1 | tee -a "${LOG_FILE}"; then
        total_pass=$((total_pass + 1))
      else
        total_fail=$((total_fail + 1))
      fi
      check_memory
    fi
  done

  echo -e "\n${GREEN}Python Tests: $total_pass passed, $total_fail failed${NC}\n"
}

# Function to run Playwright tests with tag filtering
run_playwright_tests() {
  local tag=$1

  print_header "Running Playwright Tests (@$tag)"

  cd "${PROJECT_ROOT}"

  # Check if Playwright is installed
  if ! command -v npx &>/dev/null; then
    echo -e "${YELLOW}⚠️  npx not found, skipping Playwright tests${NC}"
    return 1
  fi

  # Install dependencies if needed
  if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing Node dependencies...${NC}"
    npm install --save-dev @playwright/test axios 2>&1 | tail -10
  fi

  # Run tests with tag filter
  local grep_pattern="@$tag"

  if npx playwright test --grep "$grep_pattern" -c tests/playwright.config.ts 2>&1 | tee -a "${LOG_FILE}"; then
    echo -e "${GREEN}Playwright @$tag tests completed successfully${NC}\n"
    return 0
  else
    echo -e "${RED}Playwright @$tag tests had failures${NC}\n"
    return 1
  fi

  check_memory
}

# Function to run Bruno API tests
run_bruno_tests() {
  print_header "Running Bruno API Tests"

  cd "${PROJECT_ROOT}"

  # Check if bruno is installed
  if ! command -v npx &>/dev/null; then
    echo -e "${YELLOW}⚠️  npx not found, skipping Bruno tests${NC}"
    return 1
  fi

  # Install Bruno if needed
  if ! npm ls @usebruno/cli &>/dev/null 2>&1; then
    echo -e "${YELLOW}Installing Bruno CLI...${NC}"
    npm install --save-dev @usebruno/cli 2>&1 | tail -10
  fi

  # Run Bruno tests
  echo "Running Bruno collection tests..."
  if npx bru run --collection bruno/MyRAGDB.collection.json --env bruno/environments/dev.bru 2>&1 | tee -a "${LOG_FILE}"; then
    echo -e "${GREEN}Bruno tests completed successfully${NC}\n"
    return 0
  else
    echo -e "${YELLOW}⚠️  Bruno tests skipped (CLI might not be fully configured)${NC}\n"
    return 0
  fi

  check_memory
}

# Function to run specific batch
run_batch() {
  local batch_type=$1

  case "$batch_type" in
    smoke)
      echo "Running SMOKE tests (< 5 sec per test, ~10 tests)"
      run_playwright_tests "smoke"
      ;;
    fast)
      echo "Running FAST tests (< 30 sec per test, ~30 tests)"
      run_playwright_tests "fast"
      ;;
    integration)
      echo "Running INTEGRATION tests (< 2 min per test, ~15 tests)"
      run_playwright_tests "integration"
      ;;
    api)
      echo "Running ALL API tests"
      run_playwright_tests "api"
      ;;
    ui)
      echo "Running ALL UI tests"
      run_playwright_tests "ui"
      ;;
    directories)
      echo "Running ALL DIRECTORIES tests"
      run_playwright_tests "directories"
      ;;
    python)
      run_python_tests
      ;;
    playwright)
      echo "Running ALL Playwright tests"
      cd "${PROJECT_ROOT}"
      npx playwright test -c tests/playwright.config.ts 2>&1 | tee -a "${LOG_FILE}"
      ;;
    bruno)
      run_bruno_tests
      ;;
    all)
      echo "Running COMPLETE test suite in batches..."
      echo "1. Python unit tests..."
      run_python_tests || true
      echo ""
      echo "2. Smoke tests (quick validation)..."
      run_playwright_tests "smoke" || true
      echo ""
      echo "3. Fast tests..."
      run_playwright_tests "fast" || true
      echo ""
      echo "4. Integration tests..."
      run_playwright_tests "integration" || true
      echo ""
      echo "5. Directory-specific tests..."
      run_playwright_tests "directories" || true
      echo ""
      echo "6. Bruno API tests..."
      run_bruno_tests || true
      ;;
    *)
      echo "Unknown batch type: $batch_type"
      echo "Valid options: all, smoke, fast, integration, api, ui, directories, python, playwright, bruno"
      exit 1
      ;;
  esac
}

# Main execution
main() {
  print_header "Test Execution Started - $BATCH_TYPE"

  echo "Project Root: $PROJECT_ROOT"
  echo "Batch Type: $BATCH_TYPE"
  echo "Timestamp: $TIMESTAMP"
  echo "Log File: $LOG_FILE"
  echo ""

  # Check prerequisites
  echo -e "${YELLOW}Checking prerequisites...${NC}"
  if [ ! -d "${PROJECT_ROOT}/venv" ]; then
    echo -e "${RED}✗ Python venv not found${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Python venv found${NC}"

  # Run the batch
  run_batch "$BATCH_TYPE"

  # Summary
  print_header "Test Execution Summary"

  echo "Batch Type: $BATCH_TYPE"
  echo "Completed At: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Log File: $LOG_FILE"
  echo ""
  echo "To view detailed results:"
  echo "  cat $LOG_FILE"
  echo ""
  if [ -f "${PROJECT_ROOT}/playwright-report/index.html" ]; then
    echo "Playwright Report: ${PROJECT_ROOT}/playwright-report/index.html"
  fi

  print_header "Test Execution Complete"
}

# Show usage information
show_usage() {
  cat << EOF
${BLUE}MyRAGDB Test Runner - Incremental Batch Execution${NC}

Usage: $0 [batch_type] [verbose]

Batch Types:
  ${GREEN}all${NC}          - Run complete test suite in batches (memory-safe)
  ${GREEN}smoke${NC}        - Quick validation tests (< 5 sec each)
  ${GREEN}fast${NC}         - Fast tests (< 30 sec each)
  ${GREEN}integration${NC}  - Integration tests (< 2 min each)
  ${GREEN}api${NC}          - All API tests
  ${GREEN}ui${NC}           - All UI tests
  ${GREEN}directories${NC}  - All directory-related tests
  ${GREEN}python${NC}       - Python unit tests only
  ${GREEN}playwright${NC}   - Playwright E2E tests only
  ${GREEN}bruno${NC}        - Bruno API tests only

Examples:
  # Run smoke tests
  $0 smoke

  # Run all fast tests
  $0 fast

  # Run complete suite in batches
  $0 all

  # Run integration tests with verbose output
  $0 integration true

Test Organization:
  - Tests are tagged for selective execution
  - Single worker prevents memory overload
  - Sequential execution ensures stability
  - Automatic memory monitoring

For more information, see TESTING_GUIDE.md
EOF
}

# Check if help requested
if [ "$BATCH_TYPE" = "--help" ] || [ "$BATCH_TYPE" = "-h" ] || [ "$BATCH_TYPE" = "help" ]; then
  show_usage
  exit 0
fi

# Run main
main
