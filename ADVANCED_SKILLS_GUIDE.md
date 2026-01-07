# Advanced Skills Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/ADVANCED_SKILLS_GUIDE.md
**Description:** Comprehensive guide to advanced agent skills
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Table of Contents

1. [Overview](#overview)
2. [Data Visualization Skill](#data-visualization-skill)
3. [Code Generation Skill](#code-generation-skill)
4. [Slack Integration Skill](#slack-integration-skill)
5. [Webhook Integration Skill](#webhook-integration-skill)
6. [Usage Examples](#usage-examples)
7. [Configuration](#configuration)
8. [Error Handling](#error-handling)

---

## Overview

Advanced skills extend the MyRAGDB agent platform with powerful new capabilities:

| Skill | Purpose | Use Cases |
|-------|---------|-----------|
| **Data Visualization** | Generate charts and visualizations | Reports, dashboards, analysis |
| **Code Generation** | Generate and refactor code | Development, refactoring, testing |
| **Slack Integration** | Send messages to Slack | Notifications, team communication |
| **Webhook Integration** | Call external APIs and webhooks | Integrations, workflows, triggers |

### Architecture

Each skill:
- Extends the `Skill` base class
- Implements `execute()` async method
- Includes configuration class
- Provides validation
- Logs activities

---

## Data Visualization Skill

Generate interactive charts and visualizations from data.

### Supported Chart Types

- **line** - Time series and trend data
- **bar** - Categorical comparisons
- **pie** - Distribution and composition
- **doughnut** - Alternative to pie charts
- **scatter** - Correlation analysis
- **bubble** - Three-variable relationships
- **radar** - Multi-dimensional analysis
- **heatmap** - Pattern detection

### Export Formats

- **json** - Raw data format
- **html** - Interactive HTML with Chart.js
- **svg** - Scalable vector graphics
- **png** - Raster image with matplotlib

### Basic Usage

```python
from myragdb.agent.skills import DataVisualizationSkill

skill = DataVisualizationSkill()

# Generate line chart
result = await skill.execute(
    chart_type="line",
    title="Monthly Sales Trends",
    labels=["Jan", "Feb", "Mar", "Apr", "May"],
    datasets=[
        {
            "label": "2024 Sales",
            "data": [10000, 15000, 20000, 18000, 25000],
        },
        {
            "label": "2023 Sales",
            "data": [8000, 12000, 14000, 16000, 20000],
        },
    ],
    x_label="Month",
    y_label="Sales ($)",
    export_format="html",
)

# Access results
if result['status'] == 'success':
    chart_html = result['data']['chart_html']
    with open('sales_chart.html', 'w') as f:
        f.write(chart_html)
```

### Advanced Examples

**Pie Chart with Custom Colors:**
```python
result = await skill.execute(
    chart_type="pie",
    title="Market Share",
    labels=["Product A", "Product B", "Product C"],
    datasets=[
        {
            "label": "Revenue Share",
            "data": [45, 30, 25],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"],
        },
    ],
    export_format="png",
)

image_base64 = result['data']['chart_base64_png']
```

**Scatter Plot for Correlation:**
```python
result = await skill.execute(
    chart_type="scatter",
    title="Price vs Performance",
    labels=[],
    datasets=[
        {
            "label": "Devices",
            "data": [
                {"x": 100, "y": 50},
                {"x": 200, "y": 75},
                {"x": 300, "y": 90},
            ],
        },
    ],
    x_label="Price ($)",
    y_label="Performance Score",
)
```

### Configuration

```python
from myragdb.agent.skills.data_visualization_skill import (
    DataVisualizationSkill,
    VisualizationConfig
)

config = VisualizationConfig(
    max_data_points=2000,
    default_chart_type="bar",
    width=1280,
    height=720,
    theme="dark",
    include_legend=True,
    include_grid=True,
)

skill = DataVisualizationSkill(config)
```

---

## Code Generation Skill

Generate, refactor, and optimize code across multiple languages.

### Supported Languages

- Python
- JavaScript/TypeScript
- Java
- Go
- Rust
- C++
- C#
- SQL

### Supported Actions

| Action | Purpose | Example |
|--------|---------|---------|
| **generate** | Create new code from description | Generate function from spec |
| **refactor** | Improve existing code | Improve readability |
| **generate_tests** | Create unit tests | Generate pytest tests |
| **format** | Format code with style guidelines | Apply black formatting |
| **documentation** | Generate code documentation | Create docstrings |
| **optimize** | Optimize for performance | Suggest improvements |

### Basic Usage

```python
from myragdb.agent.skills import CodeGenerationSkill

skill = CodeGenerationSkill()

# Generate a function
result = await skill.execute(
    action="generate",
    language="python",
    function_name="calculate_fibonacci",
    description="Calculate Fibonacci number at position n",
    language_features=["recursion", "memoization"],
)

if result['status'] == 'success':
    code = result['data']['code']
    print(code)
```

### Advanced Examples

**Refactor Code for Performance:**
```python
original_code = """
def search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1
"""

result = await skill.execute(
    action="refactor",
    language="python",
    code=original_code,
    improvements=["performance", "readability"],
)

optimized = result['data']['refactored_code']
```

**Generate Unit Tests:**
```python
function_code = "def add(a, b):\n    return a + b"

result = await skill.execute(
    action="generate_tests",
    language="python",
    code=function_code,
    test_framework="pytest",
)

test_code = result['data']['test_code']
```

**Generate Documentation:**
```python
result = await skill.execute(
    action="documentation",
    language="python",
    code="def calculate_average(values):\n    return sum(values) / len(values)",
    doc_format="docstring",
)

docs = result['data']['documentation']
```

### Configuration

```python
from myragdb.agent.skills.code_generation_skill import (
    CodeGenerationSkill,
    CodeGenerationConfig
)

config = CodeGenerationConfig(
    max_code_length=10000,
    supported_languages=[
        "python", "javascript", "typescript",
        "java", "go", "rust"
    ],
    enable_formatting=True,
    enable_validation=True,
)

skill = CodeGenerationSkill(config)
```

---

## Slack Integration Skill

Send messages and notifications to Slack channels.

### Supported Actions

| Action | Purpose | Example |
|--------|---------|---------|
| **send_message** | Send simple text message | Notify channel of completion |
| **send_rich_message** | Send formatted message with blocks | Rich notification with details |
| **send_thread** | Reply to message thread | Keep related messages together |
| **add_reaction** | Add emoji reaction | React to message |
| **upload_file** | Upload file to channel | Share generated reports |
| **update_message** | Edit existing message | Update status message |

### Setup

1. **Create Slack App** at api.slack.com
2. **Get Webhook URL:**
   ```
   Incoming Webhooks > Add New Webhook to Workspace
   ```
3. **Set environment variable:**
   ```bash
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
   ```

### Basic Usage

```python
from myragdb.agent.skills import SlackIntegrationSkill

skill = SlackIntegrationSkill()

# Send simple message
result = await skill.execute(
    action="send_message",
    channel="#automation",
    message="Agent execution completed successfully!",
)

if result['status'] == 'success':
    print("Message sent to Slack")
```

### Advanced Examples

**Send Rich Formatted Message:**
```python
result = await skill.execute(
    action="send_rich_message",
    channel="#reports",
    title="Daily Report Summary",
    blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Daily Automation Report*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Status:*\n✅ Success"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Duration:*\n5 minutes 32 seconds"
                }
            ]
        }
    ],
)
```

**Create Thread Reply:**
```python
result = await skill.execute(
    action="send_thread",
    channel="#automation",
    thread_ts="1234567890.123456",
    message="Follow-up: All validation tests passed",
)
```

**Upload Report File:**
```python
result = await skill.execute(
    action="upload_file",
    channel="#reports",
    file_path="/tmp/daily_report.pdf",
    file_name="Daily_Report_2026-01-07.pdf",
)
```

### Configuration

```python
from myragdb.agent.skills.slack_integration_skill import (
    SlackIntegrationSkill,
    SlackIntegrationConfig
)

config = SlackIntegrationConfig(
    webhook_url="https://hooks.slack.com/...",
    default_channel="#general",
    enable_threading=True,
    enable_reactions=True,
    max_message_length=4000,
)

skill = SlackIntegrationSkill(config)
```

---

## Webhook Integration Skill

Call external APIs and webhooks, trigger workflows.

### Supported Actions

| Action | Purpose | Example |
|--------|---------|---------|
| **call_webhook** | Call HTTP endpoint | Trigger external workflow |
| **verify_signature** | Verify webhook signature | Validate incoming webhooks |
| **trigger_workflow** | Trigger workflow with parameters | Start external automation |
| **batch_webhooks** | Call multiple webhooks | Batch operations |

### HTTP Methods Supported

- GET - Retrieve data
- POST - Create resources
- PUT - Replace resources
- PATCH - Update resources
- DELETE - Remove resources
- HEAD - Check existence

### Basic Usage

```python
from myragdb.agent.skills import WebhookIntegrationSkill

skill = WebhookIntegrationSkill()

# Call external API
result = await skill.execute(
    action="call_webhook",
    url="https://api.example.com/webhooks/events",
    method="POST",
    payload={
        "event_type": "agent_completed",
        "status": "success",
        "duration_seconds": 45,
    },
    headers={
        "Authorization": "Bearer token123",
    },
)

if result['status'] == 'success':
    status_code = result['data']['status_code']
    print(f"Webhook called: {status_code}")
```

### Advanced Examples

**Call with Authentication:**
```python
result = await skill.execute(
    action="call_webhook",
    url="https://api.example.com/data",
    method="GET",
    auth_type="bearer",
    auth_value="eyJ0eXAi...",
    timeout=30,
)
```

**Verify Webhook Signature:**
```python
result = await skill.execute(
    action="verify_signature",
    payload='{"event":"activation"}',
    signature="provided_signature_from_webhook",
    secret="webhook_secret_key",
    algorithm="sha256",
)

if result['data']['valid']:
    print("Webhook signature is valid")
```

**Trigger Workflow:**
```python
result = await skill.execute(
    action="trigger_workflow",
    url="https://workflows.example.com/trigger",
    workflow_id="daily_report",
    parameters={
        "date": "2026-01-07",
        "format": "pdf",
    },
    method="POST",
)
```

**Batch Webhook Calls:**
```python
webhooks = [
    {
        "url": "https://api1.example.com/webhook",
        "method": "POST",
        "payload": {"action": "sync"},
    },
    {
        "url": "https://api2.example.com/webhook",
        "method": "POST",
        "payload": {"action": "notify"},
    },
]

result = await skill.execute(
    action="batch_webhooks",
    webhooks=webhooks,
)

print(f"Successful: {result['data']['successful']}/{result['data']['total_webhooks']}")
```

### Configuration

```python
from myragdb.agent.skills.webhook_integration_skill import (
    WebhookIntegrationSkill,
    WebhookIntegrationConfig
)

config = WebhookIntegrationConfig(
    timeout_seconds=30,
    max_retries=3,
    retry_backoff_multiplier=2.0,
    verify_ssl=True,
    max_payload_size=10 * 1024 * 1024,
    allowed_hosts=[
        "api.example.com",
        "webhooks.example.com",
    ],
)

skill = WebhookIntegrationSkill(config)
```

---

## Usage Examples

### Example 1: Generate Report and Send to Slack

```python
async def generate_and_share_report():
    viz_skill = DataVisualizationSkill()
    slack_skill = SlackIntegrationSkill()

    # Generate chart
    chart_result = await viz_skill.execute(
        chart_type="bar",
        title="Weekly Performance",
        labels=["Mon", "Tue", "Wed", "Thu", "Fri"],
        datasets=[{
            "label": "Tasks Completed",
            "data": [12, 19, 3, 5, 2],
        }],
    )

    # Send to Slack
    if chart_result['status'] == 'success':
        await slack_skill.execute(
            action="send_rich_message",
            channel="#reports",
            title="Weekly Performance Report",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": chart_result['data']['chart_json'],
                }
            }],
        )
```

### Example 2: Generate Tests and Create Pull Request via Webhook

```python
async def generate_tests_and_create_pr():
    codegen_skill = CodeGenerationSkill()
    webhook_skill = WebhookIntegrationSkill()

    # Generate tests
    test_result = await codegen_skill.execute(
        action="generate_tests",
        language="python",
        code="def process_data(items): return [x*2 for x in items]",
        test_framework="pytest",
    )

    # Create PR via webhook
    if test_result['status'] == 'success':
        await webhook_skill.execute(
            action="call_webhook",
            url="https://github.com/repos/owner/repo/pulls",
            method="POST",
            payload={
                "title": "Add tests for data processing",
                "body": test_result['data']['test_code'],
                "head": "add-tests",
                "base": "main",
            },
            auth_type="bearer",
            auth_value="github_token",
        )
```

### Example 3: Workflow with Multiple Skills

```python
async def comprehensive_analysis():
    """Execute comprehensive analysis workflow."""

    # 1. Generate visualization
    viz_skill = DataVisualizationSkill()
    chart = await viz_skill.execute(
        chart_type="line",
        title="Analysis Results",
        labels=list(range(10)),
        datasets=[{"label": "Metric", "data": list(range(10))}],
    )

    # 2. Generate documentation
    codegen_skill = CodeGenerationSkill()
    docs = await codegen_skill.execute(
        action="documentation",
        language="python",
        code="def analyze(): pass",
        doc_format="docstring",
    )

    # 3. Notify team via Slack
    slack_skill = SlackIntegrationSkill()
    await slack_skill.execute(
        action="send_message",
        channel="#analysis",
        message="Analysis complete. See report for details.",
    )

    # 4. Trigger external workflow
    webhook_skill = WebhookIntegrationSkill()
    await webhook_skill.execute(
        action="trigger_workflow",
        url="https://workflow.example.com/trigger",
        workflow_id="post_analysis",
        parameters={"report_id": "analysis_001"},
    )
```

---

## Configuration

### Environment Variables

```bash
# Slack Integration
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
export SLACK_BOT_TOKEN="xoxb-..."

# Webhook Integration
export WEBHOOK_TIMEOUT_SECONDS=30
export WEBHOOK_MAX_RETRIES=3
export WEBHOOK_ALLOWED_HOSTS="api.example.com,webhooks.example.com"

# Data Visualization
export VISUALIZATION_MAX_DATA_POINTS=1000
export VISUALIZATION_WIDTH=1024
export VISUALIZATION_HEIGHT=640
```

### Programmatic Configuration

All advanced skills support configuration objects:

```python
from myragdb.agent.skills import (
    DataVisualizationSkill,
    CodeGenerationSkill,
    SlackIntegrationSkill,
    WebhookIntegrationSkill,
)
from myragdb.agent.skills.data_visualization_skill import VisualizationConfig
from myragdb.agent.skills.code_generation_skill import CodeGenerationConfig
from myragdb.agent.skills.slack_integration_skill import SlackIntegrationConfig
from myragdb.agent.skills.webhook_integration_skill import WebhookIntegrationConfig

# Configure all skills
viz_config = VisualizationConfig(max_data_points=2000)
codegen_config = CodeGenerationConfig(enable_formatting=True)
slack_config = SlackIntegrationConfig(webhook_url="...")
webhook_config = WebhookIntegrationConfig(timeout_seconds=60)

# Initialize with configs
viz_skill = DataVisualizationSkill(viz_config)
codegen_skill = CodeGenerationSkill(codegen_config)
slack_skill = SlackIntegrationSkill(slack_config)
webhook_skill = WebhookIntegrationSkill(webhook_config)
```

---

## Error Handling

All advanced skills implement consistent error handling:

```python
result = await skill.execute(**params)

if result['status'] == 'success':
    # Access result data
    data = result['data']
    print(f"Success: {data}")
else:
    # Handle error
    error = result['error']
    print(f"Error: {error}")
```

### Common Errors

| Error | Cause | Resolution |
|-------|-------|-----------|
| URL not in allowed hosts | Security restriction | Add URL to allowed_hosts |
| Unsupported language | Language not supported | Use supported language |
| Message too long | Exceeds max length | Shorten message |
| Missing config | Required config missing | Set environment variable or config |
| Webhook timeout | Service unavailable | Check service, increase timeout |

### Debugging

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("myragdb.agent.skills")
logger.setLevel(logging.DEBUG)

# Now all skill operations will log detailed information
```

---

## References

- [Skill Framework](./src/myragdb/agent/skills/base.py)
- [Production Guide](./PRODUCTION_GUIDE.md)
- [Authentication Guide](./AUTHENTICATION_GUIDE.md)

---

**Questions: libor@arionetworks.com**
