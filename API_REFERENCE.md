# Agent Platform API Reference

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/API_REFERENCE.md
**Description:** Complete REST API reference for agent platform orchestration
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

The Agent Platform provides REST API endpoints for executing templates, workflows, managing skills, and discovering available capabilities.

**Base URL:** `http://localhost:3003/api/v1/agent`

All endpoints return JSON responses and support error handling with appropriate HTTP status codes.

---

## Authentication

Currently no authentication required. In future phases, API key and OAuth support will be added.

---

## Response Format

All successful responses return 200-201 status codes with JSON body:

```json
{
  "status": "completed|failed|error",
  "result": {},
  "error": null
}
```

Error responses return appropriate status codes:

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Execution Endpoints

### Execute Template-Based Request

Execute a pre-built workflow template with parameters.

**Endpoint:** `POST /api/v1/agent/execute`

**Request Body:**
```json
{
  "request_type": "code_search",
  "parameters": {
    "query": "authentication",
    "limit": 10
  },
  "execution_id": "exec_12345"
}
```

**Request Model Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_type` | string | Yes | Template type (e.g., 'code_search', 'code_review') |
| `parameters` | object | No | Parameters for template substitution |
| `execution_id` | string | No | Optional execution tracking ID |

**Response:**
```json
{
  "execution_id": "exec_12345",
  "workflow_name": "code_search",
  "status": "completed",
  "result": {
    "results": [
      {
        "file_path": "src/auth.py",
        "snippet": "def authenticate(token): ...",
        "score": 0.95
      }
    ]
  },
  "error": null,
  "steps_completed": 1,
  "total_steps": 1,
  "step_details": [
    {
      "skill": "search",
      "status": "success",
      "error": null,
      "output": {...}
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Execution completed (check status field for success/failure)
- `404 Not Found` - Template not found
- `500 Internal Server Error` - Execution failed

**Examples:**

```bash
# Basic search
curl -X POST http://localhost:3003/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "code_search",
    "parameters": {
      "query": "authentication flow",
      "limit": 5
    }
  }'

# Code analysis
curl -X POST http://localhost:3003/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "code_analysis",
    "parameters": {
      "query": "JWT token validation",
      "language": "python"
    }
  }'

# With execution tracking
curl -X POST http://localhost:3003/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "code_search",
    "parameters": {"query": "error handling"},
    "execution_id": "exec_user_12345"
  }'
```

---

### Execute Custom Workflow

Execute a custom workflow definition with specified steps.

**Endpoint:** `POST /api/v1/agent/execute-workflow`

**Request Body:**
```json
{
  "name": "custom_analysis",
  "steps": [
    {
      "skill": "search",
      "id": "find_code",
      "input": {
        "query": "database connection",
        "limit": 5
      },
      "description": "Find database connection code"
    },
    {
      "skill": "code_analysis",
      "id": "analyze",
      "input": {
        "code": "{{ find_code.results[0].snippet }}",
        "language": "python"
      },
      "description": "Analyze the code structure"
    }
  ],
  "context": {}
}
```

**Request Model Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Workflow name |
| `steps` | array | Yes | Workflow steps |
| `context` | object | No | Initial execution context |

**Step Model Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skill` | string | Yes | Skill name to execute |
| `id` | string | No | Step identifier for variable interpolation |
| `input` | object | Yes | Input for skill |
| `description` | string | No | Step description |

**Response:**
```json
{
  "execution_id": "auto_generated_id",
  "workflow_name": "custom_analysis",
  "status": "completed",
  "result": {
    "structures": [
      {
        "name": "DatabaseConnection",
        "type": "class"
      }
    ]
  },
  "error": null,
  "steps_completed": 2,
  "total_steps": 2,
  "step_details": [...]
}
```

**Status Codes:**
- `200 OK` - Execution completed
- `400 Bad Request` - Invalid workflow definition
- `500 Internal Server Error` - Execution failed

**Example:**
```bash
curl -X POST http://localhost:3003/api/v1/agent/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "name": "search_and_analyze",
    "steps": [
      {
        "skill": "search",
        "id": "search",
        "input": {"query": "authentication"}
      },
      {
        "skill": "code_analysis",
        "id": "analyze",
        "input": {
          "code": "{{ search.results[0].snippet }}",
          "language": "python"
        }
      }
    ]
  }'
```

---

## Template Endpoints

### List Available Templates

Get list of all registered workflow templates.

**Endpoint:** `GET /api/v1/agent/templates`

**Response:**
```json
{
  "total": 7,
  "templates": [
    {
      "id": "code_search",
      "name": "Basic Code Search",
      "description": "Search for code across repositories",
      "category": "search",
      "parameters": {
        "query": {
          "type": "string",
          "required": true
        },
        "limit": {
          "type": "integer",
          "required": false,
          "default": 10
        }
      },
      "step_count": 1
    },
    {
      "id": "code_review",
      "name": "Code Review",
      "description": "Find code, analyze, and generate report",
      "category": "analysis",
      "parameters": {...},
      "step_count": 3
    }
  ]
}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| None | - | - |

**Status Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:3003/api/v1/agent/templates
```

---

### Get Template Information

Get detailed information about a specific template.

**Endpoint:** `GET /api/v1/agent/templates/{template_id}`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `template_id` | string | Template identifier |

**Response:**
```json
{
  "id": "code_search",
  "name": "Basic Code Search",
  "description": "Search for code across repositories",
  "category": "search",
  "parameters": {
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
    },
    "repository": {
      "type": "string",
      "required": false,
      "description": "Repository filter"
    }
  },
  "step_count": 1,
  "steps": [
    {
      "skill": "search",
      "description": "Search for code"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Template not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:3003/api/v1/agent/templates/code_search
```

---

### Register Custom Template

Register a new workflow template.

**Endpoint:** `POST /api/v1/agent/templates`

**Request Body:**
```json
{
  "template_id": "my_custom_template",
  "name": "My Custom Workflow",
  "description": "Custom workflow description",
  "steps": [
    {
      "skill": "search",
      "input": {"query": "{{ query }}"}
    }
  ],
  "parameters": {
    "query": {
      "type": "string",
      "required": true,
      "description": "Search query"
    }
  }
}
```

**Request Model Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template_id` | string | Yes | Unique template identifier |
| `name` | string | Yes | Human-readable name |
| `description` | string | No | Template description |
| `steps` | array | Yes | Workflow steps |
| `parameters` | object | No | Template parameters |

**Response:**
```json
{
  "status": "success",
  "template_id": "my_custom_template",
  "message": "Template 'my_custom_template' registered"
}
```

**Status Codes:**
- `200 OK` - Template registered
- `500 Internal Server Error` - Registration failed

**Example:**
```bash
curl -X POST http://localhost:3003/api/v1/agent/templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "my_template",
    "name": "My Template",
    "description": "My custom workflow",
    "steps": [
      {
        "skill": "search",
        "input": {"query": "{{ query }}"}
      }
    ],
    "parameters": {
      "query": {"type": "string", "required": true}
    }
  }'
```

---

## Skill Endpoints

### List Available Skills

Get list of all registered skills.

**Endpoint:** `GET /api/v1/agent/skills`

**Response:**
```json
{
  "total": 5,
  "skills": [
    {
      "name": "search",
      "description": "Search code across repositories",
      "input_schema": {
        "query": {
          "type": "string",
          "required": true,
          "description": "Search query"
        }
      },
      "output_schema": {
        "results": {
          "type": "array",
          "description": "Search results"
        }
      },
      "required_config": []
    },
    {
      "name": "code_analysis",
      "description": "Analyze code structure",
      "input_schema": {...},
      "output_schema": {...},
      "required_config": []
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:3003/api/v1/agent/skills
```

---

### Get Skill Information

Get detailed information about a specific skill.

**Endpoint:** `GET /api/v1/agent/skills/{skill_name}`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `skill_name` | string | Skill name |

**Response:**
```json
{
  "name": "search",
  "description": "Search code across repositories",
  "input_schema": {
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
    },
    "repository_filter": {
      "type": "string",
      "required": false,
      "description": "Repository name filter"
    }
  },
  "output_schema": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file_path": {"type": "string"},
          "snippet": {"type": "string"},
          "score": {"type": "number"}
        }
      }
    },
    "total_results": {
      "type": "integer"
    },
    "search_time_ms": {
      "type": "integer"
    }
  },
  "required_config": []
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Skill not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:3003/api/v1/agent/skills/search
curl http://localhost:3003/api/v1/agent/skills/code_analysis
```

---

## Orchestrator Endpoints

### Get Orchestrator Information

Get overall orchestrator capabilities and status.

**Endpoint:** `GET /api/v1/agent/info`

**Response:**
```json
{
  "total_skills": 5,
  "total_templates": 7,
  "available_skills": [
    "search",
    "code_analysis",
    "report",
    "llm",
    "sql"
  ],
  "available_templates": [
    "code_search",
    "code_analysis",
    "code_review",
    "search_and_analyze",
    "search_analyze_report",
    "multi_repo_search",
    "search_with_filters"
  ],
  "has_session_manager": true,
  "has_search_engine": true
}
```

**Status Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:3003/api/v1/agent/info
```

---

### Health Check

Check if agent platform is operational.

**Endpoint:** `GET /api/v1/agent/health`

**Response:**
```json
{
  "status": "healthy",
  "message": "Agent platform orchestrator is operational"
}
```

**Status Codes:**
- `200 OK` - Service healthy
- `500 Internal Server Error` - Service unhealthy

**Example:**
```bash
curl http://localhost:3003/api/v1/agent/health
```

---

## Error Handling

### Error Responses

All errors return appropriate HTTP status codes with error details:

**400 Bad Request** - Invalid input:
```json
{
  "detail": "Invalid request: query parameter is required"
}
```

**404 Not Found** - Resource not found:
```json
{
  "detail": "Template 'unknown_template' not found"
}
```

**500 Internal Server Error** - Server error:
```json
{
  "detail": "Execution failed: skill not found"
}
```

### Handling in Client Code

```python
import requests

try:
    response = requests.post(
        "http://localhost:3003/api/v1/agent/execute",
        json={
            "request_type": "code_search",
            "parameters": {"query": "authentication"}
        }
    )
    response.raise_for_status()
    result = response.json()

    if result["status"] == "completed":
        print("Success:", result["result"])
    elif result["status"] == "failed":
        print("Workflow failed:", result["error"])

except requests.exceptions.HTTPError as e:
    print(f"HTTP Error {e.response.status_code}: {e.response.json()}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

---

## Rate Limiting

Currently no rate limiting. Future versions will implement:
- Per-IP rate limits
- Per-API-key rate limits
- Execution queue management

---

## Pagination

List endpoints return all results. Future versions will support:
- `limit` parameter (default 100)
- `offset` parameter (default 0)
- Total count in response

---

## API Examples

### Example 1: Simple Code Search

```bash
curl -X POST http://localhost:3003/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "code_search",
    "parameters": {
      "query": "user authentication",
      "limit": 5
    }
  }' | jq '.result'
```

### Example 2: Search and Analyze

```bash
curl -X POST http://localhost:3003/api/v1/agent/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "name": "analyze_auth",
    "steps": [
      {
        "skill": "search",
        "id": "find",
        "input": {"query": "authentication", "limit": 3}
      },
      {
        "skill": "code_analysis",
        "id": "analyze",
        "input": {
          "code": "{{ find.results[0].snippet }}",
          "language": "python"
        }
      }
    ]
  }' | jq '.step_details'
```

### Example 3: Get All Templates

```bash
curl http://localhost:3003/api/v1/agent/templates | jq '.templates[] | {id, name, description}'
```

### Example 4: Register Custom Template

```bash
curl -X POST http://localhost:3003/api/v1/agent/templates \
  -H "Content-Type: application/json" \
  -d @my_template.json
```

### Example 5: Python Client

```python
import requests
import asyncio

BASE_URL = "http://localhost:3003/api/v1/agent"

class AgentClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url

    def execute_template(self, request_type, parameters):
        """Execute a template."""
        response = requests.post(
            f"{self.base_url}/execute",
            json={
                "request_type": request_type,
                "parameters": parameters
            }
        )
        response.raise_for_status()
        return response.json()

    def list_templates(self):
        """List available templates."""
        response = requests.get(f"{self.base_url}/templates")
        response.raise_for_status()
        return response.json()

    def get_skill_info(self, skill_name):
        """Get skill details."""
        response = requests.get(f"{self.base_url}/skills/{skill_name}")
        response.raise_for_status()
        return response.json()

# Usage
client = AgentClient()
result = client.execute_template("code_search", {"query": "auth", "limit": 5})
print(result["result"])
```

---

## Integration Examples

### Integration with Python Agents

```python
from myragdb.agent.orchestration import AgentOrchestrator
from myragdb.agent.skills import SkillRegistry

# Initialize orchestrator
registry = SkillRegistry()
orchestrator = AgentOrchestrator(skill_registry=registry)

# Execute template
result = await orchestrator.execute_request(
    "code_search",
    {"query": "authentication", "limit": 10}
)

# Execute custom workflow
workflow = {
    "name": "analysis",
    "steps": [
        {"skill": "search", "id": "find", "input": {"query": "auth"}},
        {"skill": "code_analysis", "id": "analyze",
         "input": {"code": "{{ find.results[0].snippet }}"}}
    ]
}
result = await orchestrator.execute_workflow(workflow)
```

### Integration with Web UI

```javascript
// Fetch templates
async function listTemplates() {
  const response = await fetch('/api/v1/agent/templates');
  const data = await response.json();
  return data.templates;
}

// Execute template
async function executeTemplate(templateId, params) {
  const response = await fetch('/api/v1/agent/execute', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      request_type: templateId,
      parameters: params
    })
  });
  const result = await response.json();
  return result;
}
```

---

## API Documentation Auto-Generation

FastAPI auto-generates API documentation:

- **Swagger UI:** `http://localhost:3003/docs`
- **ReDoc:** `http://localhost:3003/redoc`
- **OpenAPI JSON:** `http://localhost:3003/openapi.json`

---

For more information:
- See `AGENT_PLATFORM_QUICKSTART.md` for usage examples
- See `src/myragdb/api/agent_routes.py` for implementation
- See `API_REFERENCE.md` (this document)

Questions: libor@arionetworks.com
