// File: tests/regression/regression-ui.ts
// Description: Web-based UI dashboard for managing and executing regression tests
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-08

import express, { Express, Request, Response } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

/**
 * Test execution status for live tracking.
 *
 * Business Purpose: Tracks current test execution progress
 * for real-time UI updates.
 */
interface ExecutionStatus {
  isRunning: boolean;
  currentTest?: string;
  progress: number;
  startTime?: number;
  output: string[];
}

/**
 * Historical test result for trending.
 *
 * Business Purpose: Stores test results over time for
 * quality metrics and trend analysis.
 */
interface HistoricalResult {
  timestamp: string;
  passed: number;
  failed: number;
  duration: number;
  suite: string;
}

/**
 * Test Management Dashboard Server
 *
 * Business Purpose: Provides web-based UI for selecting,
 * executing, and monitoring regression tests. Allows tracking
 * test quality over time and filtering by various criteria.
 *
 * Endpoints:
 * - GET /                     - Dashboard UI
 * - GET /api/suites          - Available test suites
 * - POST /api/execute        - Execute test suite
 * - GET /api/status          - Execution status
 * - GET /api/results         - Test results history
 * - GET /api/categories      - Test categories reference
 *
 * Example:
 *   npm run test:ui
 *   Open http://localhost:3004
 */
class TestManagementDashboard {
  private app: Express;
  private port = 3004;
  private testDir = path.join(__dirname, '..');
  private execution: ExecutionStatus = {
    isRunning: false,
    progress: 0,
    output: [],
  };

  private testSuites = [
    {
      id: 'smoke',
      name: 'Smoke Tests',
      grep: '@smoke',
      duration: '5-10 min',
      description: 'Quick verification of critical functionality',
    },
    {
      id: 'fast',
      name: 'Fast Regression',
      grep: '@fast',
      duration: '20-30 min',
      description: 'Quick full regression test',
    },
    {
      id: 'api',
      name: 'API Tests',
      grep: '@api',
      duration: '15-25 min',
      description: 'Backend API functionality',
    },
    {
      id: 'ui',
      name: 'UI Tests',
      grep: '@ui',
      duration: '15-25 min',
      description: 'Frontend UI functionality',
    },
    {
      id: 'search',
      name: 'Search Tests',
      grep: '@search',
      duration: '20-30 min',
      description: 'Search functionality testing',
    },
    {
      id: 'integration',
      name: 'Integration Tests',
      grep: '@integration',
      duration: '30-45 min',
      description: 'Multi-component workflow testing',
    },
    {
      id: 'full',
      name: 'Full Regression',
      grep: '',
      duration: '60-120 min',
      description: 'Complete test suite - all tests',
    },
  ];

  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
  }

  /**
   * Configure Express middleware for serving UI and API.
   *
   * Business Purpose: Prepares Express server for handling
   * both static UI assets and JSON API requests.
   */
  private setupMiddleware(): void {
    this.app.use(express.json());
    this.app.use(express.static(path.join(__dirname, 'public')));
  }

  /**
   * Setup API and static content routes.
   *
   * Business Purpose: Defines endpoints for test management
   * including UI serving, test suite listing, and execution.
   */
  private setupRoutes(): void {
    // Main UI page
    this.app.get('/', (_req: Request, res: Response) => {
      res.send(this.renderDashboardHTML());
    });

    // API: Get available test suites
    this.app.get('/api/suites', (_req: Request, res: Response) => {
      res.json(this.testSuites);
    });

    // API: Execute test suite
    this.app.post('/api/execute', (req: Request, res: Response) => {
      const { suiteId, customGrep } = req.body;

      if (this.execution.isRunning) {
        return res.status(409).json({ error: 'Tests already running' });
      }

      // Find suite or use custom grep
      const suite = this.testSuites.find((s) => s.id === suiteId);
      const grep = customGrep || suite?.grep || '';

      this.startTestExecution(grep);
      res.json({ success: true, message: 'Tests started' });
    });

    // API: Get execution status
    this.app.get('/api/status', (_req: Request, res: Response) => {
      res.json(this.execution);
    });

    // API: Get results history
    this.app.get('/api/results', (_req: Request, res: Response) => {
      const historyFile = path.join(
        this.testDir,
        'test-results',
        'history.json'
      );

      if (!fs.existsSync(historyFile)) {
        return res.json([]);
      }

      try {
        const history = JSON.parse(fs.readFileSync(historyFile, 'utf-8'));
        res.json(history);
      } catch (e) {
        res.json([]);
      }
    });

    // API: Get test categories reference
    this.app.get('/api/categories', (_req: Request, res: Response) => {
      const categoriesFile = path.join(this.testDir, 'test-categories.json');

      if (!fs.existsSync(categoriesFile)) {
        return res.json({});
      }

      try {
        const categories = JSON.parse(
          fs.readFileSync(categoriesFile, 'utf-8')
        );
        res.json(categories);
      } catch (e) {
        res.json({});
      }
    });

    // API: Stop running tests
    this.app.post('/api/stop', (_req: Request, res: Response) => {
      if (!this.execution.isRunning) {
        return res.status(400).json({ error: 'No tests running' });
      }

      // TODO: Implement graceful test termination
      res.json({ success: true, message: 'Stop requested' });
    });

    // API: Clear results history
    this.app.post('/api/clear-history', (_req: Request, res: Response) => {
      const historyFile = path.join(
        this.testDir,
        'test-results',
        'history.json'
      );

      if (fs.existsSync(historyFile)) {
        fs.unlinkSync(historyFile);
      }

      res.json({ success: true, message: 'History cleared' });
    });
  }

  /**
   * Start asynchronous test execution.
   *
   * Business Purpose: Executes Playwright tests in background
   * while maintaining UI responsiveness through status polling.
   */
  private startTestExecution(grep: string): void {
    this.execution.isRunning = true;
    this.execution.progress = 0;
    this.execution.output = [];
    this.execution.startTime = Date.now();

    // Execute in background
    setTimeout(() => {
      this.runTests(grep);
    }, 100);
  }

  /**
   * Execute tests and capture output.
   *
   * Business Purpose: Runs Playwright command and streams
   * output to execution status for real-time UI updates.
   */
  private runTests(grep: string): void {
    try {
      let command = 'npm test';

      if (grep) {
        command += ` -- --grep "${grep}"`;
      }

      command += ' -- --reporter=json,html,list';

      const output = execSync(command, {
        cwd: this.testDir,
        encoding: 'utf-8',
      });

      this.execution.output.push(output);
      this.execution.isRunning = false;
      this.execution.progress = 100;
    } catch (error: any) {
      this.execution.output.push(`Error: ${error.message}`);
      this.execution.isRunning = false;
      this.execution.progress = 100;
    }
  }

  /**
   * Render HTML for test management dashboard.
   *
   * Business Purpose: Generates complete web UI for
   * selecting and executing test suites with live results.
   */
  private renderDashboardHTML(): string {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MyRAGDB Test Management Dashboard</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      overflow: hidden;
    }

    header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
    }

    header h1 {
      font-size: 28px;
      margin-bottom: 10px;
    }

    header p {
      opacity: 0.9;
      font-size: 14px;
    }

    .content {
      padding: 30px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
    }

    .section {
      display: flex;
      flex-direction: column;
    }

    .section h2 {
      font-size: 18px;
      margin-bottom: 20px;
      color: #333;
      border-bottom: 2px solid #667eea;
      padding-bottom: 10px;
    }

    .suite-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .suite-card {
      padding: 16px;
      border: 2px solid #e0e0e0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      background: #f9f9f9;
    }

    .suite-card:hover {
      border-color: #667eea;
      background: #f0f3ff;
      transform: translateX(4px);
    }

    .suite-card.active {
      border-color: #667eea;
      background: #e8edff;
    }

    .suite-name {
      font-weight: 600;
      color: #333;
      margin-bottom: 4px;
    }

    .suite-desc {
      font-size: 12px;
      color: #666;
      margin-bottom: 8px;
    }

    .suite-duration {
      font-size: 11px;
      color: #999;
    }

    .controls {
      display: flex;
      gap: 12px;
      margin-top: 20px;
    }

    button {
      flex: 1;
      padding: 12px 20px;
      border: none;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }

    .btn-primary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .btn-secondary {
      background: #f0f0f0;
      color: #333;
    }

    .btn-secondary:hover {
      background: #e0e0e0;
    }

    .status-panel {
      background: #f9f9f9;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 20px;
      margin-top: 20px;
    }

    .status-line {
      display: flex;
      justify-content: space-between;
      margin-bottom: 12px;
      font-size: 14px;
    }

    .status-label {
      color: #666;
      font-weight: 500;
    }

    .status-value {
      color: #333;
      font-weight: 600;
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background: #e0e0e0;
      border-radius: 4px;
      overflow: hidden;
      margin-top: 12px;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      width: 0%;
      transition: width 0.3s ease;
    }

    .output-panel {
      background: #1e1e1e;
      color: #00ff00;
      border-radius: 8px;
      padding: 16px;
      font-family: 'Monaco', 'Courier New', monospace;
      font-size: 12px;
      height: 400px;
      overflow-y: auto;
      margin-top: 20px;
    }

    .output-line {
      margin-bottom: 4px;
      white-space: pre-wrap;
      word-wrap: break-word;
    }

    .results-chart {
      margin-top: 30px;
      padding: 20px;
      background: #f9f9f9;
      border-radius: 8px;
    }

    .chart-title {
      font-weight: 600;
      margin-bottom: 16px;
      color: #333;
    }

    .chart-item {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
    }

    .chart-label {
      min-width: 80px;
      font-size: 12px;
      color: #666;
    }

    .chart-bar {
      flex: 1;
      height: 24px;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      border-radius: 4px;
      margin: 0 12px;
      position: relative;
    }

    .chart-value {
      min-width: 40px;
      text-align: right;
      font-size: 12px;
      font-weight: 600;
      color: #333;
    }

    .custom-grep {
      margin-top: 20px;
      padding: 16px;
      background: #f0f3ff;
      border-radius: 8px;
      border: 1px solid #e0e0ff;
    }

    .custom-grep label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: #333;
      margin-bottom: 8px;
    }

    .custom-grep input {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 13px;
    }

    .footer {
      background: #f9f9f9;
      border-top: 1px solid #e0e0e0;
      padding: 16px 30px;
      font-size: 12px;
      color: #999;
      text-align: center;
    }

    @media (max-width: 768px) {
      .content {
        grid-template-columns: 1fr;
      }

      header h1 {
        font-size: 22px;
      }
    }

    .status-icon {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      margin-right: 8px;
    }

    .status-icon.running {
      background: #ffa500;
      animation: pulse 1s infinite;
    }

    .status-icon.success {
      background: #4caf50;
    }

    .status-icon.failure {
      background: #f44336;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🧪 MyRAGDB Test Management</h1>
      <p>Regression Test Suite - Interactive Execution Dashboard</p>
    </header>

    <div class="content">
      <div class="section">
        <h2>Select Test Suite</h2>
        <div class="suite-list" id="suiteList"></div>

        <div class="custom-grep">
          <label for="customGrep">Or enter custom grep pattern:</label>
          <input type="text" id="customGrep" placeholder="e.g., @api @search">
        </div>

        <div class="controls">
          <button class="btn-primary" id="executeBtn" onclick="executeTests()">
            ▶ Execute Tests
          </button>
          <button class="btn-secondary" id="stopBtn" onclick="stopTests()" disabled>
            ⏹ Stop
          </button>
        </div>
      </div>

      <div class="section">
        <h2>Execution Status</h2>
        <div class="status-panel">
          <div class="status-line">
            <span class="status-label">Status:</span>
            <span class="status-value">
              <span class="status-icon" id="statusIcon"></span>
              <span id="statusText">Ready</span>
            </span>
          </div>
          <div class="status-line">
            <span class="status-label">Progress:</span>
            <span class="status-value" id="progressText">0%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
          </div>
          <div class="status-line" style="margin-top: 12px;">
            <span class="status-label">Duration:</span>
            <span class="status-value" id="durationText">--</span>
          </div>
        </div>

        <div class="output-panel" id="outputPanel"></div>
      </div>
    </div>

    <div style="padding: 0 30px; padding-bottom: 30px;">
      <div class="section">
        <h2>Results History</h2>
        <div class="results-chart" id="resultsChart"></div>
      </div>
    </div>

    <div class="footer">
      MyRAGDB Regression Test Suite • Last Updated: 2026-01-08 •
      <a href="./REGRESSION_TEST_SUITE.md" target="_blank" style="color: #667eea; text-decoration: none;">Documentation</a>
    </div>
  </div>

  <script>
    let selectedSuite = null;
    let statusInterval = null;

    async function loadSuites() {
      const response = await fetch('/api/suites');
      const suites = await response.json();

      const suiteList = document.getElementById('suiteList');
      suiteList.innerHTML = suites
        .map(
          (suite) => \`
        <div class="suite-card" onclick="selectSuite(this, '\${suite.id}')">
          <div class="suite-name">\${suite.name}</div>
          <div class="suite-desc">\${suite.description}</div>
          <div class="suite-duration">⏱ \${suite.duration}</div>
        </div>
      \`
        )
        .join('');
    }

    function selectSuite(element, suiteId) {
      document.querySelectorAll('.suite-card').forEach((el) => {
        el.classList.remove('active');
      });
      element.classList.add('active');
      selectedSuite = suiteId;
    }

    async function executeSuite() {
      const customGrep = document.getElementById('customGrep').value;
      const payload = selectedSuite
        ? { suiteId: selectedSuite }
        : { customGrep };

      const response = await fetch('/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        updateStatus();
        startStatusPolling();
      }
    }

    async function updateStatus() {
      const response = await fetch('/api/status');
      const status = await response.json();

      const statusIcon = document.getElementById('statusIcon');
      const statusText = document.getElementById('statusText');
      const progressFill = document.getElementById('progressFill');
      const progressText = document.getElementById('progressText');
      const durationText = document.getElementById('durationText');

      if (status.isRunning) {
        statusIcon.classList.remove('success', 'failure');
        statusIcon.classList.add('running');
        statusText.textContent = 'Running...';
        document.getElementById('stopBtn').disabled = false;
      } else {
        statusIcon.classList.remove('running');
        statusIcon.classList.add(status.output.some((o) => o.includes('Error')) ? 'failure' : 'success');
        statusText.textContent = status.output.some((o) => o.includes('Error')) ? 'Failed' : 'Completed';
        document.getElementById('stopBtn').disabled = true;
      }

      progressFill.style.width = status.progress + '%';
      progressText.textContent = status.progress + '%';

      if (status.startTime) {
        const duration = Math.floor((Date.now() - status.startTime) / 1000);
        durationText.textContent = \`\${duration}s\`;
      }

      const outputPanel = document.getElementById('outputPanel');
      outputPanel.innerHTML = status.output
        .map((line) => \`<div class="output-line">\${escapeHtml(line)}</div>\`)
        .join('');
      outputPanel.scrollTop = outputPanel.scrollHeight;
    }

    function startStatusPolling() {
      if (statusInterval) clearInterval(statusInterval);
      statusInterval = setInterval(updateStatus, 1000);
    }

    async function stopTests() {
      await fetch('/api/stop', { method: 'POST' });
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    // Initialize
    loadSuites();
    updateStatus();
    loadResultsHistory();

    async function loadResultsHistory() {
      const response = await fetch('/api/results');
      const results = await response.json();

      if (results.length === 0) {
        document.getElementById('resultsChart').innerHTML = '<p>No results yet. Run tests to see history.</p>';
        return;
      }

      const recentResults = results.slice(-10);

      const chartHtml = \`
        <div class="chart-title">Recent Test Results (Last 10)</div>
        \${recentResults
          .map(
            (r) => \`
          <div class="chart-item">
            <div class="chart-label">\${new Date(r.timestamp).toLocaleDateString()}</div>
            <div class="chart-bar" style="width: \${(r.passed / (r.passed + r.failed)) * 100}%"></div>
            <div class="chart-value">\${r.passed}/\${r.passed + r.failed}</div>
          </div>
        \`
          )
          .join('')}
      \`;

      document.getElementById('resultsChart').innerHTML = chartHtml;
    }

    async function executeSuite() {
      const customGrep = document.getElementById('customGrep').value;
      const payload = selectedSuite
        ? { suiteId: selectedSuite }
        : { customGrep };

      const response = await fetch('/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        updateStatus();
        startStatusPolling();
      }
    }

    function executeSuite() {
      const customGrep = document.getElementById('customGrep').value;
      const payload = selectedSuite
        ? { suiteId: selectedSuite }
        : { customGrep };

      fetch('/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).then((response) => {
        if (response.ok) {
          updateStatus();
          startStatusPolling();
        }
      });
    }

    window.executeSuite = executeSuite;
    window.selectSuite = selectSuite;
    window.stopTests = stopTests;
  </script>
</body>
</html>
`;
  }

  /**
   * Start the test management dashboard server.
   *
   * Business Purpose: Starts Express server on configured port
   * to serve the test management UI.
   */
  start(): void {
    this.app.listen(this.port, () => {
      console.log(`\n╔═══════════════════════════════════════════════════════╗`);
      console.log(`║  MyRAGDB Test Management Dashboard                   ║`);
      console.log(`║  📊 http://localhost:${this.port}                         ║`);
      console.log(`║                                                       ║`);
      console.log(`║  Features:                                            ║`);
      console.log(`║  • Select and execute test suites                     ║`);
      console.log(`║  • Custom grep patterns                               ║`);
      console.log(`║  • Live execution status                              ║`);
      console.log(`║  • Results history and trending                       ║`);
      console.log(`║                                                       ║`);
      console.log(`║  API Endpoints:                                       ║`);
      console.log(`║  GET  /api/suites        - Available test suites      ║`);
      console.log(`║  POST /api/execute       - Execute test suite         ║`);
      console.log(`║  GET  /api/status        - Execution status           ║`);
      console.log(`║  GET  /api/results       - Results history            ║`);
      console.log(`║  GET  /api/categories    - Test categories            ║`);
      console.log(`║                                                       ║`);
      console.log(`╚═══════════════════════════════════════════════════════╝\n`);
    });
  }
}

// Run if executed directly
if (require.main === module) {
  const dashboard = new TestManagementDashboard();
  dashboard.start();
}

export { TestManagementDashboard };
