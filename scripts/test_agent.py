#!/usr/bin/env python3
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/test_agent.py
# Description: Intelligent test agent for automated test management, execution, and reporting
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-09

"""
MyRAGDB Test Agent

Provides intelligent automation for test management including:
- Test discovery and categorization
- Test execution with filtering
- Comprehensive reporting (HTML, JSON, Markdown, JUnit)
- Code coverage analysis
- Test creation and organization
- CI/CD integration
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSpeed(Enum):
    """Test execution speed classification."""
    SMOKE = "smoke"  # < 5 seconds per test, 5-10 min total
    FAST = "fast"    # < 30 seconds per test, 20-30 min total
    SLOW = "slow"    # > 30 seconds per test, variable total


class TestType(Enum):
    """Test type classification."""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"


class TestCategory(Enum):
    """Test category by feature area."""
    API = "@api"
    UI = "@ui"
    SEARCH = "@search"
    INDEXING = "@indexing"
    REPOSITORY = "@repository"
    DIRECTORY = "@directory"
    SKILL = "@skill"
    TEMPLATE = "@template"
    WORKFLOW = "@workflow"


@dataclass
class TestMetadata:
    """Metadata for a single test."""
    file_path: str
    test_name: str
    test_class: Optional[str]
    test_function: str
    speed: TestSpeed
    test_type: TestType
    categories: List[TestCategory]
    is_async: bool
    duration_seconds: Optional[float] = None
    passed: Optional[bool] = None
    error_message: Optional[str] = None
    skipped: bool = False
    xfail: bool = False


@dataclass
class TestResultSummary:
    """Summary of test execution results."""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    xfail: int
    total_duration_seconds: float
    coverage_percent: Optional[float]
    tests: List[TestMetadata]
    timestamp: str


class TestAgent:
    """Intelligent test agent for MyRAGDB."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize test agent."""
        self.project_root = project_root or Path.cwd()
        self.tests_dir = self.project_root / "tests"
        self.test_results_dir = self.project_root / "tests" / "test-results"
        self.test_results_dir.mkdir(parents=True, exist_ok=True)
        self.src_dir = self.project_root / "src"

    def discover_tests(self, pattern: Optional[str] = None) -> List[TestMetadata]:
        """Discover all tests in the project."""
        logger.info("Discovering tests...")

        try:
            # Collect tests using pytest
            cmd = ["pytest", "--collect-only", "-q", "--quiet"]
            if pattern:
                cmd.append(pattern)
            else:
                cmd.extend(["tests/", str(self.project_root / "test_*.py")])

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            tests = self._parse_collected_tests(result.stdout)
            logger.info(f"Discovered {len(tests)} tests")
            return tests

        except Exception as e:
            logger.error(f"Error discovering tests: {e}")
            return []

    def _parse_collected_tests(self, output: str) -> List[TestMetadata]:
        """Parse pytest collected tests output."""
        tests = []
        for line in output.split("\n"):
            if "::" in line and "test_" in line:
                # Parse test path format: path/to/test_file.py::TestClass::test_function
                parts = line.strip().split("::")
                if len(parts) >= 2:
                    file_path = parts[0].strip()
                    test_name = parts[-1].strip()
                    test_class = parts[1].strip() if len(parts) > 2 else None

                    # Classify test
                    speed = self._classify_speed(test_name)
                    test_type = self._classify_type(test_name, file_path)
                    categories = self._classify_categories(test_name, file_path)
                    is_async = self._check_async(file_path, test_name)

                    metadata = TestMetadata(
                        file_path=file_path,
                        test_name=test_name,
                        test_class=test_class,
                        test_function=test_name,
                        speed=speed,
                        test_type=test_type,
                        categories=categories,
                        is_async=is_async
                    )
                    tests.append(metadata)

        return tests

    def _classify_speed(self, test_name: str) -> TestSpeed:
        """Classify test speed."""
        if "smoke" in test_name.lower():
            return TestSpeed.SMOKE
        elif any(x in test_name.lower() for x in ["quick", "fast", "simple"]):
            return TestSpeed.FAST
        else:
            return TestSpeed.SLOW

    def _classify_type(self, test_name: str, file_path: str) -> TestType:
        """Classify test type."""
        test_name_lower = test_name.lower()
        file_path_lower = file_path.lower()

        if "e2e" in test_name_lower or "e2e" in file_path_lower:
            return TestType.E2E
        elif "integration" in test_name_lower or "integration" in file_path_lower:
            return TestType.INTEGRATION
        elif "performance" in test_name_lower or "perf" in test_name_lower:
            return TestType.PERFORMANCE
        else:
            return TestType.UNIT

    def _classify_categories(self, test_name: str, file_path: str) -> List[TestCategory]:
        """Classify test categories."""
        categories = []
        combined = (test_name + file_path).lower()

        category_mapping = {
            TestCategory.API: ["api", "endpoint", "route"],
            TestCategory.UI: ["ui", "interface", "component"],
            TestCategory.SEARCH: ["search", "query"],
            TestCategory.INDEXING: ["index", "reindex"],
            TestCategory.REPOSITORY: ["repository", "repo"],
            TestCategory.DIRECTORY: ["directory", "dir"],
            TestCategory.SKILL: ["skill"],
            TestCategory.TEMPLATE: ["template"],
            TestCategory.WORKFLOW: ["workflow", "orchestrat"],
        }

        for category, keywords in category_mapping.items():
            if any(keyword in combined for keyword in keywords):
                categories.append(category)

        return categories if categories else [TestCategory.API]  # Default to API

    def _check_async(self, file_path: str, test_name: str) -> bool:
        """Check if test is async."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Simple check for async def
                return f"async def {test_name}" in content
        except Exception:
            return False

    def run_tests(
        self,
        pattern: Optional[str] = None,
        speed: Optional[TestSpeed] = None,
        categories: Optional[List[TestCategory]] = None,
        coverage: bool = False,
        verbose: bool = False,
        fail_fast: bool = False,
        workers: int = 1
    ) -> TestResultSummary:
        """Run tests with filtering options."""
        logger.info(f"Running tests (pattern={pattern}, speed={speed}, coverage={coverage})...")

        cmd = ["pytest"]

        if pattern:
            cmd.append(pattern)
        else:
            cmd.extend(["tests/", str(self.project_root / "test_*.py")])

        # Add markers for speed filtering
        markers = []
        if speed:
            markers.append(f"not slow" if speed == TestSpeed.FAST else "smoke")

        if categories:
            category_markers = [cat.value for cat in categories]
            markers.append(" or ".join(category_markers))

        if markers:
            cmd.extend(["-m", " and ".join(f"({m})" for m in markers)])

        # Add output options
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        if coverage:
            cmd.extend([
                f"--cov={self.src_dir / 'myragdb'}",
                "--cov-report=xml",
                f"--cov-report=html:{self.test_results_dir / 'coverage'}"
            ])

        if fail_fast:
            cmd.append("-x")

        # JSON report
        cmd.extend([
            f"--json-report={self.test_results_dir / 'results.json'}"
        ])

        # JUnit report for CI/CD
        cmd.extend([
            f"--junit-xml={self.test_results_dir / 'junit.xml'}"
        ])

        try:
            start_time = datetime.now()
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=False,
                text=True
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Parse results
            summary = self._parse_test_results(duration)
            return summary

        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return TestResultSummary(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                xfail=0,
                total_duration_seconds=0,
                coverage_percent=None,
                tests=[],
                timestamp=datetime.now().isoformat()
            )

    def _parse_test_results(self, duration: float) -> TestResultSummary:
        """Parse test results from pytest output."""
        try:
            results_file = self.test_results_dir / "results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    data = json.load(f)
                    passed = len([t for t in data.get("tests", []) if t.get("outcome") == "passed"])
                    failed = len([t for t in data.get("tests", []) if t.get("outcome") == "failed"])
                    skipped = len([t for t in data.get("tests", []) if t.get("outcome") == "skipped"])
                    xfail = len([t for t in data.get("tests", []) if t.get("outcome") == "xfail"])
                    total = passed + failed + skipped + xfail

                    return TestResultSummary(
                        total_tests=total,
                        passed=passed,
                        failed=failed,
                        skipped=skipped,
                        xfail=xfail,
                        total_duration_seconds=duration,
                        coverage_percent=None,
                        tests=[],
                        timestamp=datetime.now().isoformat()
                    )
        except Exception as e:
            logger.error(f"Error parsing results: {e}")

        return TestResultSummary(
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            xfail=0,
            total_duration_seconds=duration,
            coverage_percent=None,
            tests=[],
            timestamp=datetime.now().isoformat()
        )

    def generate_report(
        self,
        format: str = "markdown",
        coverage: bool = False,
        compare: bool = False
    ) -> str:
        """Generate test report in specified format."""
        logger.info(f"Generating {format} report...")

        if format == "markdown":
            return self._generate_markdown_report(coverage)
        elif format == "html":
            return self._generate_html_report(coverage)
        elif format == "json":
            return self._generate_json_report()
        else:
            logger.error(f"Unknown format: {format}")
            return ""

    def _generate_markdown_report(self, coverage: bool = False) -> str:
        """Generate markdown report."""
        report = "# Test Report\n\n"
        report += f"**Generated:** {datetime.now().isoformat()}\n\n"

        # Load test results
        try:
            results_file = self.test_results_dir / "results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    data = json.load(f)

                    # Summary
                    passed = len([t for t in data.get("tests", []) if t.get("outcome") == "passed"])
                    failed = len([t for t in data.get("tests", []) if t.get("outcome") == "failed"])
                    skipped = len([t for t in data.get("tests", []) if t.get("outcome") == "skipped"])
                    total = passed + failed + skipped

                    report += "## Summary\n\n"
                    report += f"- **Total Tests:** {total}\n"
                    report += f"- **Passed:** {passed} ✓\n"
                    report += f"- **Failed:** {failed} ✗\n"
                    report += f"- **Skipped:** {skipped} ⊘\n"
                    report += f"- **Success Rate:** {(passed/total*100):.1f}%\n\n"

                    # Failed tests details
                    if failed > 0:
                        report += "## Failed Tests\n\n"
                        for test in data.get("tests", []):
                            if test.get("outcome") == "failed":
                                report += f"- **{test.get('nodeid')}**\n"
                                if test.get("call", {}).get("longrepr"):
                                    report += f"  ```\n  {test['call']['longrepr']}\n  ```\n\n"

        except Exception as e:
            logger.error(f"Error generating markdown report: {e}")

        return report

    def _generate_html_report(self, coverage: bool = False) -> str:
        """Generate HTML report."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { background: #f0f0f0; padding: 10px; border-radius: 5px; }
                .passed { color: green; }
                .failed { color: red; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background: #4CAF50; color: white; }
            </style>
        </head>
        <body>
            <h1>Test Execution Report</h1>
            <div class="summary">
                <p>Generated: {timestamp}</p>
            </div>
            <table>
                <tr>
                    <th>Test</th>
                    <th>Status</th>
                    <th>Duration</th>
                </tr>
            </table>
        </body>
        </html>
        """.format(timestamp=datetime.now().isoformat())

        return html

    def _generate_json_report(self) -> str:
        """Generate JSON report."""
        try:
            results_file = self.test_results_dir / "results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    return json.dumps(json.load(f), indent=2)
        except Exception as e:
            logger.error(f"Error generating JSON report: {e}")

        return "{}"

    def get_test_stats(self, group_by: str = "category") -> Dict:
        """Get test statistics grouped by specified field."""
        logger.info(f"Gathering test statistics (group_by={group_by})...")

        tests = self.discover_tests()
        stats = {}

        if group_by == "category":
            for test in tests:
                for category in test.categories:
                    if category not in stats:
                        stats[category.value] = 0
                    stats[category.value] += 1

        elif group_by == "speed":
            for test in tests:
                speed_name = test.speed.value
                if speed_name not in stats:
                    stats[speed_name] = 0
                stats[speed_name] += 1

        elif group_by == "type":
            for test in tests:
                type_name = test.test_type.value
                if type_name not in stats:
                    stats[type_name] = 0
                stats[type_name] += 1

        return {
            "group_by": group_by,
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "total_tests": len(tests)
        }


def main():
    """Main entry point for test agent CLI."""
    parser = argparse.ArgumentParser(
        description="MyRAGDB Test Agent - Automated test management and execution"
    )

    subparsers = parser.add_subparsers(dest="command", help="Test agent commands")

    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover all tests")
    discover_parser.add_argument("--pattern", help="Test file pattern")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run tests")
    run_parser.add_argument("pattern", nargs="?", default=None, help="Test pattern to run")
    run_parser.add_argument("--speed", choices=["smoke", "fast", "slow"], help="Filter by test speed")
    run_parser.add_argument("--categories", nargs="+", help="Filter by test categories")
    run_parser.add_argument("--coverage", action="store_true", help="Include coverage report")
    run_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    run_parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate test report")
    report_parser.add_argument("--format", choices=["markdown", "html", "json"], default="markdown")
    report_parser.add_argument("--coverage", action="store_true", help="Include coverage data")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Get test statistics")
    stats_parser.add_argument("--group-by", choices=["category", "speed", "type"], default="category")

    args = parser.parse_args()

    agent = TestAgent()

    if args.command == "discover":
        tests = agent.discover_tests(args.pattern)
        print(f"\nDiscovered {len(tests)} tests:")
        for test in tests[:10]:  # Show first 10
            print(f"  - {test.file_path}::{test.test_name}")
        if len(tests) > 10:
            print(f"  ... and {len(tests) - 10} more")

    elif args.command == "run":
        speed = TestSpeed(args.speed) if args.speed else None
        result = agent.run_tests(
            pattern=args.pattern,
            speed=speed,
            coverage=args.coverage,
            verbose=args.verbose,
            fail_fast=args.fail_fast
        )
        print(f"\n{'='*60}")
        print(f"Test Results Summary")
        print(f"{'='*60}")
        print(f"Total:    {result.total_tests}")
        print(f"Passed:   {result.passed} ✓")
        print(f"Failed:   {result.failed} ✗")
        print(f"Skipped:  {result.skipped} ⊘")
        print(f"Duration: {result.total_duration_seconds:.2f}s")
        print(f"{'='*60}")

    elif args.command == "report":
        report = agent.generate_report(
            format=args.format,
            coverage=args.coverage
        )
        print(report)

    elif args.command == "stats":
        stats = agent.get_test_stats(group_by=args.group_by)
        print(f"\nTest Statistics (grouped by {args.group_by}):")
        print(f"Total: {stats['total_tests']}")
        for key, value in stats['stats'].items():
            print(f"  - {key}: {value}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
