# Agent Platform CLI Reference

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/CLI_REFERENCE.md
**Description:** Complete command-line interface reference for agent platform
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

The Agent Platform provides comprehensive CLI commands for executing templates, managing workflows, and discovering capabilities.

**Command Format:** `myragdb agent <command> [options] [arguments]`

---

## Getting Started

### Check Installation

```bash
# Verify CLI is available
myragdb agent --help

# Should output usage and available commands
```

### Common Options

All commands support:
- `--help` - Show command help
- `--json` - Output as JSON (where applicable)

---

## Core Commands

### execute - Run a Template

Execute a pre-built workflow template with parameters.

**Usage:**
```bash
myragdb agent execute <request_type> [--param KEY=VALUE ...] [--json]
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `request_type` | Template type to execute (required) |

**Options:**
| Option | Description |
|--------|-------------|
| `--param KEY=VALUE` | Parameter in format KEY=VALUE (can be used multiple times) |
| `--json` | Output as JSON instead of formatted text |
| `--help` | Show help message |

**Examples:**

```bash
# Simple search
myragdb agent execute code_search --param query="authentication"

# With multiple parameters
myragdb agent execute code_search \
  --param query="JWT authentication" \
  --param limit=10

# Repository filter
myragdb agent execute code_search \
  --param query="database connection" \
  --param repository="myapp"

# Get JSON output
myragdb agent execute code_search \
  --param query="error handling" \
  --json

# Code analysis
myragdb agent execute code_analysis \
  --param query="class definition" \
  --param language="python"

# Code review with report
myragdb agent execute code_review \
  --param query="authentication" \
  --param limit=5

# Security audit
myragdb agent execute security_audit \
  --param security_topic="encryption" \
  --param limit=10
```

**Output:**
```
Status: completed
Steps: 1/1
Result:
{
  "results": [
    {
      "file_path": "src/auth.py",
      "snippet": "def authenticate(token): ...",
      "score": 0.95
    }
  ]
}
```

---

### workflow - Execute Custom Workflow

Execute a custom workflow from a YAML or JSON file.

**Usage:**
```bash
myragdb agent workflow <workflow_file> [--json]
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `workflow_file` | Path to workflow file (YAML or JSON) |

**Options:**
| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--help` | Show help |

**Examples:**

```bash
# Execute workflow from YAML file
myragdb agent workflow my_workflow.yaml

# Execute workflow from JSON file
myragdb agent workflow my_workflow.json

# Get JSON output
myragdb agent workflow my_workflow.yaml --json
```

**Example Workflow File (YAML):**
```yaml
name: "search_and_analyze"
steps:
  - skill: "search"
    id: "find"
    input:
      query: "authentication"
      limit: 5

  - skill: "code_analysis"
    id: "analyze"
    input:
      code: "{{ find.results[0].snippet }}"
      language: "python"

  - skill: "report"
    id: "report"
    input:
      title: "Analysis Report"
      content:
        - section: "Found Code"
          data:
            results: "{{ find.results }}"
        - section: "Structure"
          data:
            structures: "{{ analyze.structures }}"
```

---

### templates - List Available Templates

List all registered workflow templates.

**Usage:**
```bash
myragdb agent templates
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help` | Show help |

**Example:**
```bash
myragdb agent templates
```

**Output:**
```
Available Templates:
================================================================================

ID: code_search
Name: Basic Code Search
Description: Search for code across repositories
Steps: 1
Parameters:
  - query
  - limit
  - repository

ID: code_analysis
Name: Code Analysis
Description: Search and analyze code structure
Steps: 2
Parameters:
  - query
  - language
  - analysis_type

...
```

---

### template-info - Show Template Details

Display detailed information about a specific template.

**Usage:**
```bash
myragdb agent template-info <template_id>
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `template_id` | Template identifier |

**Options:**
| Option | Description |
|--------|-------------|
| `--help` | Show help |

**Examples:**

```bash
# Get info about code_search template
myragdb agent template-info code_search

# Get info about code_review template
myragdb agent template-info code_review
```

**Output:**
```
Template: Basic Code Search
Description: Search for code across repositories
Category: search

Steps: 1

Parameters:
  query:
    Type: string
    Required: True
    Description: Code search query

  limit:
    Type: integer
    Required: False
    Default: 10
    Description: Maximum results

  repository:
    Type: string
    Required: False
    Description: Repository name filter
```

---

### template-register - Register Custom Template

Register a new workflow template from file.

**Usage:**
```bash
myragdb agent template-register <template_file> --id <template_id>
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `template_file` | Path to template file (YAML or JSON) |

**Options:**
| Option | Description |
|--------|-------------|
| `--id ID` | Template ID (used to reference template) (required) |
| `--help` | Show help |

**Examples:**

```bash
# Register from YAML
myragdb agent template-register my_template.yaml --id my_template

# Register from JSON
myragdb agent template-register my_template.json --id my_workflow

# Complex template
myragdb agent template-register ./templates/custom.yaml --id custom_audit
```

**Example Template File:**
```yaml
name: "my_custom_template"
description: "Custom workflow template"
category: "analysis"
parameters:
  query:
    type: "string"
    required: true
    description: "Search query"
  limit:
    type: "integer"
    required: false
    default: 10

steps:
  - skill: "search"
    id: "find"
    input:
      query: "{{ query }}"
      limit: "{{ limit }}"

  - skill: "code_analysis"
    id: "analyze"
    input:
      code: "{{ find.results[0].snippet }}"
```

---

### skills - List Available Skills

List all registered skills with descriptions.

**Usage:**
```bash
myragdb agent skills
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help` | Show help |

**Example:**
```bash
myragdb agent skills
```

**Output:**
```
Available Skills:
================================================================================

Name: search
Description: Search code across repositories

Name: code_analysis
Description: Analyze code structure and extract components

Name: report
Description: Generate formatted reports from data

Name: llm
Description: Call active LLM with prompts

Name: sql
Description: Execute database queries
```

---

### skill-info - Show Skill Details

Display detailed information about a specific skill including schema.

**Usage:**
```bash
myragdb agent skill-info <skill_name>
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `skill_name` | Skill name |

**Options:**
| Option | Description |
|--------|-------------|
| `--help` | Show help |

**Examples:**

```bash
# Get info about search skill
myragdb agent skill-info search

# Get info about code_analysis skill
myragdb agent skill-info code_analysis

# Get info about report skill
myragdb agent skill-info report
```

**Output:**
```
Skill: search
Description: Search code across repositories

Input Schema:
{
  "query": {
    "type": "string",
    "required": true,
    "description": "Code search query"
  },
  "limit": {
    "type": "integer",
    "required": false,
    "default": 10,
    "description": "Maximum results"
  }
}

Output Schema:
{
  "results": {
    "type": "array",
    "description": "Search results"
  },
  "total_results": {
    "type": "integer"
  }
}
```

---

### info - Show Orchestrator Information

Display orchestrator capabilities and available resources.

**Usage:**
```bash
myragdb agent info
```

**Options:**
| Option | Description |
|--------|-------------|
| `--help` | Show help |

**Example:**
```bash
myragdb agent info
```

**Output:**
```
Agent Platform Information:
================================================================================
Total Skills: 5
Total Templates: 7
Session Manager: ✓
Search Engine: ✓

Available Skills (5):
  - search
  - code_analysis
  - report
  - llm
  - sql

Available Templates (7):
  - code_search
  - code_analysis
  - code_review
  - search_and_analyze
  - search_analyze_report
  - multi_repo_search
  - search_with_filters
```

---

## Parameter Types and Formats

### String Parameters

```bash
# Simple string
--param query="authentication"

# String with spaces
--param query="user authentication flow"

# String with special characters
--param query="error handling & logging"
```

### Integer Parameters

```bash
# Integer values
--param limit=10
--param max_results=50
--param timeout=30
```

### Boolean Parameters

```bash
# Boolean true (as string, converted automatically)
--param include_analysis=true
--param cache=false
```

### Array Parameters

```bash
# Arrays as JSON
--param repositories='["repo1", "repo2"]'
--param directories='[1, 2, 3]'
```

### Object Parameters

```bash
# Objects as JSON
--param filters='{"folder": "src", "extension": ".py"}'
```

---

## JSON Output Format

Use `--json` flag to get structured output:

```bash
# Get JSON output
myragdb agent execute code_search --param query="auth" --json
```

**JSON Output Structure:**
```json
{
  "execution_id": "auto_generated",
  "workflow_name": "code_search",
  "status": "completed",
  "result": {
    "results": [...]
  },
  "error": null,
  "steps_completed": 1,
  "total_steps": 1,
  "step_details": [...]
}
```

**Parse with jq:**
```bash
# Get just the results
myragdb agent execute code_search --param query="auth" --json | jq '.result.results'

# Get step details
myragdb agent execute code_search --param query="auth" --json | jq '.step_details'

# Get status and errors
myragdb agent execute code_search --param query="auth" --json | jq '{status, error}'
```

---

## Error Handling

### Common Errors

**"Error: Parameter must be in format KEY=VALUE"**
```bash
# ❌ WRONG
myragdb agent execute code_search query="auth"

# ✅ CORRECT
myragdb agent execute code_search --param query="auth"
```

**"Template not found"**
```bash
# ❌ WRONG - Template doesn't exist
myragdb agent execute unknown_template --param query="test"

# ✅ CORRECT - Use existing template
myragdb agent execute code_search --param query="test"
```

**"Workflow file not found"**
```bash
# ❌ WRONG - Path is relative
myragdb agent workflow workflow.yaml

# ✅ CORRECT - Use absolute path or verify file exists
myragdb agent workflow /full/path/to/workflow.yaml
```

---

## Practical Examples

### Example 1: Find Authentication Code

```bash
# Search for authentication code
myragdb agent execute code_search \
  --param query="authentication" \
  --param limit=5

# Output shows:
# Status: completed
# Steps: 1/1
# Result: [list of files with authentication code]
```

### Example 2: Analyze Code Pattern

```bash
# Find singleton pattern implementation
myragdb agent execute code_analysis \
  --param query="singleton pattern" \
  --param language="python"

# Output shows code structure analysis
```

### Example 3: Security Audit

```bash
# Audit encryption implementations
myragdb agent execute security_audit \
  --param security_topic="encryption" \
  --param limit=10

# Output shows all encryption-related code with analysis
```

### Example 4: Complex Workflow

```bash
# Execute custom workflow for complete analysis
myragdb agent workflow ./templates/search_analyze_report.yaml

# Output shows multi-step results:
# Step 1: Search results
# Step 2: Code analysis
# Step 3: Formatted report
```

### Example 5: Parse and Filter Results

```bash
# Get JSON output and filter with jq
myragdb agent execute code_search \
  --param query="jwt" \
  --json | jq '.result.results[] | {file_path, snippet, score}'

# Shows:
# {
#   "file_path": "src/auth.py",
#   "snippet": "def verify_jwt(token): ...",
#   "score": 0.95
# }
```

### Example 6: Register and Use Custom Template

```bash
# Register new template
myragdb agent template-register ./my_audit_template.yaml --id security_check

# List templates to verify registration
myragdb agent templates | grep security_check

# Execute the registered template
myragdb agent execute security_check --param security_topic="sql_injection"
```

---

## Tips and Tricks

### Using Environment Variables

```bash
# Set query as environment variable
export MY_QUERY="authentication"

# Use in command (bash substitution)
myragdb agent execute code_search --param query="$MY_QUERY"
```

### Batch Processing

```bash
# Process multiple queries
for query in "authentication" "encryption" "validation"; do
  myragdb agent execute code_search --param query="$query" --json
done
```

### Output to File

```bash
# Save results to file
myragdb agent execute code_search \
  --param query="auth" \
  --json > results.json

# Process results with jq
cat results.json | jq '.result.results'
```

### Scripting

```bash
#!/bin/bash

# Get list of templates
templates=$(myragdb agent templates --json | jq '.templates[].id')

# Execute each template with specific query
for template in $templates; do
  echo "Executing $template..."
  myragdb agent execute "$template" --param query="auth" --json
done
```

---

## Integration with Other Tools

### With curl

```bash
# Use curl to call CLI through shell
curl -s http://example.com/api/v1/agent/execute \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"request_type":"code_search","parameters":{"query":"auth"}}'
```

### With Python

```python
import subprocess
import json

# Execute CLI command
result = subprocess.run(
    ['myragdb', 'agent', 'execute', 'code_search',
     '--param', 'query=authentication', '--json'],
    capture_output=True,
    text=True
)

# Parse output
data = json.loads(result.stdout)
print(data['result'])
```

### With Docker

```bash
# Execute CLI in Docker container
docker run myragdb:latest \
  myragdb agent execute code_search \
  --param query="authentication"
```

---

## Performance Tips

### Optimize Query Parameters

```bash
# ❌ Too broad - returns many results
myragdb agent execute code_search --param query="code" --param limit=100

# ✅ More specific - better results
myragdb agent execute code_search --param query="jwt authentication" --param limit=10
```

### Use Filters

```bash
# ❌ No filter - searches all files
myragdb agent execute code_search --param query="auth"

# ✅ With filters - faster, more relevant
myragdb agent execute code_search \
  --param query="auth" \
  --param folder="src"
```

### Limit Results

```bash
# ❌ Default limit
myragdb agent execute code_search --param query="auth"

# ✅ Reduced limit
myragdb agent execute code_search --param query="auth" --param limit=5
```

---

## Troubleshooting

### CLI Not Found

```bash
# Verify installation
pip list | grep myragdb

# Reinstall if needed
pip install -e .
```

### Command Not Recognized

```bash
# Check venv activation
which myragdb

# Activate venv if needed
source venv/bin/activate
```

### Parameter Not Working

```bash
# Check template parameter names
myragdb agent template-info code_search

# Use correct parameter name
myragdb agent execute code_search --param query="auth"  # NOT "q"
```

### JSON Parse Error

```bash
# Invalid JSON in parameter
--param data='{"key": "value"}'  # Not valid bash JSON

# Escape properly
--param data='{"key":"value"}'  # Valid
```

---

## Complete Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `execute` | Run template | `myragdb agent execute code_search --param query="auth"` |
| `workflow` | Run custom workflow | `myragdb agent workflow my_workflow.yaml` |
| `templates` | List templates | `myragdb agent templates` |
| `template-info` | Show template details | `myragdb agent template-info code_search` |
| `template-register` | Register template | `myragdb agent template-register my.yaml --id my_id` |
| `skills` | List skills | `myragdb agent skills` |
| `skill-info` | Show skill details | `myragdb agent skill-info search` |
| `info` | Show orchestrator info | `myragdb agent info` |

---

For more information:
- See `AGENT_PLATFORM_QUICKSTART.md` for usage patterns
- See `API_REFERENCE.md` for REST API
- See `TEMPLATE_BEST_PRACTICES.md` for template design
- See `src/myragdb/cli/agent_commands.py` for implementation

Questions: libor@arionetworks.com
