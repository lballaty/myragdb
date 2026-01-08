// File: tests/regression/regression-runner.ts
// Description: Test execution manager for regression test suite
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-08

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as readline from 'readline';

/**
 * Test suite category for filtering execution.
 *
 * Business Purpose: Allows users to select specific test categories
 * to run rather than the full test suite, enabling faster feedback
 * for targeted testing scenarios.
 */
interface TestSuite {
  name: string;
  grep: string;
  duration: string;
  description: string;
}

/**
 * Test result for summary reporting.
 *
 * Business Purpose: Tracks individual test results for summary
 * generation and trend analysis.
 */
interface TestResult {
  suite: string;
  passed: number;
  failed: number;
  duration: number;
  timestamp: string;
}

/**
 * Regression Test Runner
 *
 * Business Purpose: Provides CLI interface for running different
 * regression test categories with appropriate filtering and reporting.
 * Supports incremental testing patterns for different development phases.
 *
 * Example:
 *   npm run test:regression
 *   Select: 2) Fast Regression (20-30 min)
 *   Tests execute with filtered grep patterns
 *   Results summarized and stored
 */
class RegressionTestRunner {
  private readonly testDir = path.join(__dirname, '..');
  private readonly testResultsDir = path.join(this.testDir, 'test-results');
  private readonly testCategoriesFile = path.join(
    this.testDir,
    'test-categories.json'
  );

  private suites: TestSuite[] = [
    {
      name: 'Smoke Tests (5-10 min)',
      grep: '@smoke',
      duration: '5-10 minutes',
      description: 'Quick verification of critical functionality',
    },
    {
      name: 'Fast Regression (20-30 min)',
      grep: '@fast',
      duration: '20-30 minutes',
      description: 'Quick full regression test',
    },
    {
      name: 'API Tests (15-25 min)',
      grep: '@api',
      duration: '15-25 minutes',
      description: 'Backend API functionality',
    },
    {
      name: 'UI Tests (15-25 min)',
      grep: '@ui',
      duration: '15-25 minutes',
      description: 'Frontend UI functionality',
    },
    {
      name: 'Search Tests (20-30 min)',
      grep: '@search',
      duration: '20-30 minutes',
      description: 'Search functionality testing',
    },
    {
      name: 'Integration Tests (30-45 min)',
      grep: '@integration',
      duration: '30-45 minutes',
      description: 'Multi-component workflow testing',
    },
    {
      name: 'Full Regression (60-120 min)',
      grep: '',
      duration: '60-120 minutes',
      description: 'Complete test suite - all tests',
    },
    {
      name: 'Custom (Enter grep pattern)',
      grep: '',
      duration: 'Variable',
      description: 'Custom test selection',
    },
  ];

  /**
   * Display test suite options and get user selection.
   *
   * Business Purpose: Provides interactive menu for selecting
   * test suite to execute.
   */
  private async promptSuiteSelection(): Promise<TestSuite> {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    console.log('\n╔════════════════════════════════════════════════════════════╗');
    console.log('║     MyRAGDB Regression Test Suite Runner                   ║');
    console.log('╚════════════════════════════════════════════════════════════╝\n');

    this.suites.forEach((suite, index) => {
      console.log(`${index + 1}) ${suite.name}`);
      console.log(`   ${suite.description}`);
      console.log(`   Duration: ${suite.duration}\n`);
    });

    return new Promise((resolve) => {
      rl.question(
        'Select test suite (1-8): ',
        (answer: string) => {
          rl.close();

          const selection = parseInt(answer, 10);
          if (selection < 1 || selection > this.suites.length) {
            console.log('Invalid selection. Running smoke tests.');
            resolve(this.suites[0]);
          } else {
            const selectedSuite = this.suites[selection - 1];

            // Handle custom grep pattern
            if (selectedSuite.grep === '' && selection !== 7) {
              rl.once('close', () => {
                const rl2 = readline.createInterface({
                  input: process.stdin,
                  output: process.stdout,
                });

                rl2.question(
                  'Enter grep pattern (e.g., @api @critical): ',
                  (pattern: string) => {
                    rl2.close();
                    selectedSuite.grep = pattern || '';
                    resolve(selectedSuite);
                  }
                );
              });
            } else {
              resolve(selectedSuite);
            }
          }
        }
      );
    });
  }

  /**
   * Build Playwright test command with appropriate flags.
   *
   * Business Purpose: Constructs CLI command for running Playwright
   * tests with correct grep filters and output formatting.
   */
  private buildPlaywrightCommand(suite: TestSuite): string {
    let cmd = 'npm test';

    if (suite.grep) {
      cmd += ` -- --grep "${suite.grep}"`;
    }

    // Always use JSON reporter for results parsing
    cmd += ' -- --reporter=json,html,list';

    return cmd;
  }

  /**
   * Execute tests and capture results.
   *
   * Business Purpose: Runs Playwright with specified filters
   * and captures results for reporting.
   */
  private executeTests(command: string): TestResult {
    console.log('\n═══════════════════════════════════════════════════════════');
    console.log(`Executing: ${command}`);
    console.log('═══════════════════════════════════════════════════════════\n');

    const startTime = Date.now();

    try {
      // Execute command and capture output
      const output = execSync(command, {
        cwd: this.testDir,
        stdio: 'inherit',
        encoding: 'utf-8',
      });

      const duration = Date.now() - startTime;

      // Parse results from JSON report if available
      const jsonResultsPath = path.join(
        this.testResultsDir,
        'results.json'
      );
      let passed = 0;
      let failed = 0;

      if (fs.existsSync(jsonResultsPath)) {
        try {
          const results = JSON.parse(
            fs.readFileSync(jsonResultsPath, 'utf-8')
          );
          passed = results.stats?.expected || 0;
          failed = results.stats?.failures || 0;
        } catch (e) {
          console.log('Could not parse results file');
        }
      }

      return {
        suite: 'Test Suite',
        passed,
        failed,
        duration,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      console.error('\n❌ Tests failed or errored');

      return {
        suite: 'Test Suite',
        passed: 0,
        failed: 1,
        duration,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Display test results summary.
   *
   * Business Purpose: Presents human-readable summary of test
   * execution with pass/fail counts and timing.
   */
  private displayResultsSummary(result: TestResult): void {
    console.log('\n═══════════════════════════════════════════════════════════');
    console.log('                      TEST RESULTS SUMMARY                  ');
    console.log('═══════════════════════════════════════════════════════════\n');

    const status = result.failed === 0 ? '✅ PASS' : '❌ FAIL';
    const duration = (result.duration / 1000).toFixed(2);

    console.log(`Status:           ${status}`);
    console.log(`Passed:           ${result.passed}`);
    console.log(`Failed:           ${result.failed}`);
    console.log(`Duration:         ${duration}s`);
    console.log(`Timestamp:        ${result.timestamp}`);

    console.log('\n═══════════════════════════════════════════════════════════');

    if (result.failed === 0) {
      console.log('🎉 All tests passed! Great work!');
    } else {
      console.log(`⚠️  ${result.failed} test(s) failed. Check logs above.`);
    }

    console.log('\n📊 View detailed report: npx playwright show-report');
    console.log('═══════════════════════════════════════════════════════════\n');
  }

  /**
   * Store test result for historical trending.
   *
   * Business Purpose: Saves test results to file for trend analysis
   * and quality tracking over time.
   */
  private storeResults(result: TestResult): void {
    const resultsHistoryPath = path.join(
      this.testResultsDir,
      'history.json'
    );
    let history: TestResult[] = [];

    // Ensure results directory exists
    if (!fs.existsSync(this.testResultsDir)) {
      fs.mkdirSync(this.testResultsDir, { recursive: true });
    }

    // Load existing history
    if (fs.existsSync(resultsHistoryPath)) {
      try {
        history = JSON.parse(fs.readFileSync(resultsHistoryPath, 'utf-8'));
      } catch (e) {
        history = [];
      }
    }

    // Add new result
    history.push(result);

    // Keep last 50 results
    if (history.length > 50) {
      history = history.slice(-50);
    }

    // Save updated history
    fs.writeFileSync(resultsHistoryPath, JSON.stringify(history, null, 2));

    console.log(`📁 Results stored: ${resultsHistoryPath}`);
  }

  /**
   * Main entry point for regression test runner.
   *
   * Business Purpose: Orchestrates the full test execution flow
   * from user selection through result reporting.
   */
  async run(): Promise<void> {
    try {
      // Get user selection
      const suite = await this.promptSuiteSelection();

      // Build and execute tests
      const command = this.buildPlaywrightCommand(suite);
      const result = this.executeTests(command);

      // Display results
      this.displayResultsSummary(result);

      // Store for trending
      this.storeResults(result);

      // Exit with appropriate code
      process.exit(result.failed === 0 ? 0 : 1);
    } catch (error) {
      console.error('Error running tests:', error);
      process.exit(1);
    }
  }
}

// Run if executed directly
if (require.main === module) {
  const runner = new RegressionTestRunner();
  runner.run();
}

export { RegressionTestRunner, TestSuite, TestResult };
