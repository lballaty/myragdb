# Agent Platform Quick Start Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/AGENT_PLATFORM_QUICKSTART.md
**Description:** Quick reference for using the agent platform orchestration system
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Quick Start

### 1. Basic Setup

```python
from myragdb.agent.skills import SkillRegistry, SearchSkill
from myragdb.agent.orchestration import AgentOrchestrator
from myragdb.search.hybrid_search import HybridSearchEngine

# Initialize components
skill_registry = SkillRegistry()
orchestrator = AgentOrchestrator(skill_registry=skill_registry)

# Register SearchSkill (requires HybridSearchEngine instance)
# search_engine = HybridSearchEngine(...)
# search_skill = SearchSkill(search_engine)
# skill_registry.register_skill(search_skill)
```

### 2. Execute Built-in Templates

```python
# Use pre-built templates for common tasks
result = await orchestrator.execute_request(
    request_type="code_search",
    parameters={
        "query": "authentication flow",
        "limit": 10
    }
)

print(result["status"])      # "completed" or "failed"
print(result["result"])      # Final execution result
print(result["step_details"]) # Per-step results
```

### 3. Available Built-in Templates

#### `code_search`
Find code across repositories.
```python
await orchestrator.execute_request(
    "code_search",
    {
        "query": "JWT authentication",
        "limit": 10,
        "repository": "xLLMArionComply"  # Optional
    }
)
```

#### `code_analysis`
Search and analyze code structure.
```python
await orchestrator.execute_request(
    "code_analysis",
    {
        "query": "class AuthenticationManager",
        "language": "python"
    }
)
```

#### `code_review`
Find code, analyze, and generate report.
```python
await orchestrator.execute_request(
    "code_review",
    {
        "query": "error handling",
        "limit": 3
    }
)
```

---

## Custom Workflows

### Execute a Custom Workflow

```python
workflow = {
    "name": "custom_analysis",
    "steps": [
        {
            "skill": "search",
            "id": "find_code",
            "input": {
                "query": "database connection",
                "limit": 5
            }
        },
        {
            "skill": "code_analysis",
            "id": "analyze",
            "input": {
                "code": "{{ find_code.results[0].snippet }}",
                "language": "python"
            }
        },
        {
            "skill": "report",
            "id": "create_report",
            "input": {
                "title": "Database Connection Analysis",
                "content": [
                    {
                        "section": "Code Analysis",
                        "data": {"text": "{{ analyze.structures }}"}
                    }
                ]
            }
        }
    ]
}

result = await orchestrator.execute_workflow(workflow)
print(result["status"])      # Execution status
print(result["result"])      # Report content
```

---

## Working with Skills

### Register a Custom Skill

```python
from myragdb.agent.skills import Skill

class CustomSkill(Skill):
    def __init__(self):
        super().__init__(
            name="custom",
            description="My custom skill"
        )

    @property
    def input_schema(self):
        return {
            "param1": {"type": "string", "required": True},
            "param2": {"type": "integer", "default": 10}
        }

    @property
    def output_schema(self):
        return {
            "result": {"type": "string"}
        }

    async def execute(self, input_data):
        return {"result": f"Processed: {input_data['param1']}"}

# Register
skill_registry.register_skill(CustomSkill())

# Use in workflow
workflow = {
    "name": "with_custom",
    "steps": [
        {
            "skill": "custom",
            "input": {"param1": "test", "param2": 5}
        }
    ]
}
```

### Available Built-in Skills

#### SearchSkill
Query hybrid search engine.
```python
{
    "skill": "search",
    "input": {
        "query": "authentication",      # Required
        "limit": 10,                    # Optional, default 10
        "repository_filter": "repo",    # Optional
        "directories": [1, 2],          # Optional
        "folder_filter": "src",         # Optional
        "extension_filter": ".py",      # Optional
        "rewrite_query": True           # Optional, default True
    }
}
```
Returns: `{"results": [...], "total_results": N, "search_time_ms": X}`

#### LLMSkill
Call active LLM.
```python
{
    "skill": "llm",
    "input": {
        "prompt": "Summarize this...",  # Required
        "max_tokens": 1000,             # Optional
        "temperature": 0.7,             # Optional
        "stream": False                 # Optional
    }
}
```
Returns: `{"response": "...", "model": "...", "tokens_used": N}`

#### CodeAnalysisSkill
Extract code structure.
```python
{
    "skill": "code_analysis",
    "input": {
        "code": "def foo(): ...",       # Required
        "language": "python",           # Optional, default python
        "analysis_type": "structure"    # Optional: structure|imports|functions|classes|patterns
    }
}
```
Returns: `{"structures": [...], "imports": [...], "patterns": [...], "complexity_estimate": "low|medium|high"}`

#### ReportSkill
Generate formatted reports.
```python
{
    "skill": "report",
    "input": {
        "title": "My Report",          # Required
        "content": [                    # Required
            {
                "section": "Findings",
                "data": {
                    "text": "Some text",
                    "items": ["item1", "item2"],
                    "pairs": {"key": "value"},
                    "results": [{"file_path": "...", "score": 0.9}]
                }
            }
        ],
        "format": "markdown",           # Optional: markdown|json|text
        "include_metadata": True        # Optional, default True
    }
}
```
Returns: `{"report": "...", "format": "...", "sections": N}`

#### SQLSkill
Execute database queries (placeholder, pending Phase 1C).
```python
{
    "skill": "sql",
    "input": {
        "query": "SELECT * FROM users",  # Required
        "database": "prod",              # Optional
        "limit_rows": 100,               # Optional
        "timeout_seconds": 30            # Optional
    }
}
```

---

## Template Management

### List Available Templates
```python
templates = orchestrator.list_available_templates()
for tmpl in templates:
    print(f"{tmpl['name']}: {tmpl['description']}")
```

### Get Template Info
```python
info = orchestrator.template_engine.get_template_info("code_search")
print(info["parameters"])  # Required and optional parameters
print(info["step_count"])  # Number of steps
```

### Register Custom Template
```python
template = {
    "name": "my_workflow",
    "description": "My custom workflow",
    "parameters": {
        "query": {"type": "string", "required": True},
        "limit": {"type": "integer", "default": 10}
    },
    "steps": [
        # ... steps ...
    ]
}

orchestrator.template_engine.register_template("my_workflow", template)

# Or load from file
orchestrator.register_template_from_file("./templates/my_workflow.yaml")
```

---

## LLM Session Management

### Switch LLM Providers

```python
from myragdb.llm.session_manager import SessionManager

session_manager = SessionManager()

# Switch to Claude (requires ANTHROPIC_API_KEY env var)
await session_manager.switch_to_cloud(
    provider_type="claude",
    model_id="claude-3-opus-20240229",
    auth_method="api_key",
    credentials={"api_key": "sk-ant-..."}
)

# Switch to Gemini
await session_manager.switch_to_cloud(
    provider_type="gemini",
    model_id="gemini-1.5-pro",
    auth_method="api_key",
    credentials={"api_key": "..."}
)

# Get active session
session = session_manager.get_active_session()
print(session.model_id)         # Currently active model
print(session.provider_type)    # "claude", "gemini", "chatgpt"
```

---

## Variable Interpolation

Variables are passed between workflow steps using `{{step_id.field}}` syntax:

```python
workflow = {
    "name": "chain_steps",
    "steps": [
        {
            "skill": "search",
            "id": "find_auth",
            "input": {"query": "authentication"}
        },
        {
            "skill": "code_analysis",
            "id": "analyze",
            # Use result from previous step
            "input": {
                "code": "{{ find_auth.results[0].snippet }}",
                "language": "python"
            }
        },
        {
            "skill": "report",
            "id": "report",
            # Can access nested fields
            "input": {
                "title": "Analysis Report",
                "content": [
                    {
                        "section": "Structures Found",
                        # Array indexing: results[0]
                        "data": {"items": "{{ analyze.structures }}"}
                    }
                ]
            }
        }
    ]
}
```

Supported variable paths:
- `{{ step_id }}` - Entire step result
- `{{ step_id.field }}` - Nested field access
- `{{ step_id.results[0] }}` - Array indexing
- `{{ step_id.results[0].path }}` - Combined

---

## Error Handling

### Check Execution Status

```python
result = await orchestrator.execute_request("code_search", params)

if result["status"] == "completed":
    print("Success:", result["result"])
elif result["status"] == "failed":
    print("Error:", result["error"])

# Check individual step status
for step in result["step_details"]:
    print(f"{step['skill']}: {step['status']}")
    if step["status"] == "failed":
        print(f"  Error: {step['error']}")
```

### Step Error Handling

Control behavior when a step fails:

```python
workflow = {
    "name": "with_error_handling",
    "steps": [
        {
            "skill": "search",
            "input": {"query": "..."}
        },
        {
            "skill": "code_analysis",
            "input": {"code": "{{ search.results[0].snippet }}"},
            "on_error": "continue"  # Continue even if this step fails
        }
    ]
}
```

Valid `on_error` values:
- `None` (default): Stop workflow if step fails
- `"continue"`: Continue to next step even if this one fails

---

## Orchestrator Info

### Get Available Skills and Templates

```python
info = orchestrator.get_orchestrator_info()
print(info["total_skills"])        # Number of registered skills
print(info["total_templates"])     # Number of registered templates
print(info["available_skills"])    # List of skill names
print(info["available_templates"]) # List of template IDs
print(info["has_session_manager"]) # Whether LLM available
print(info["has_search_engine"])   # Whether search available
```

### List Skills

```python
skills = orchestrator.list_available_skills()
for skill in skills:
    print(f"{skill['name']}: {skill['description']}")
    print(f"  Input: {skill['input_schema']}")
    print(f"  Output: {skill['output_schema']}")
```

---

## Common Patterns

### Pattern 1: Search → Report

```python
workflow = {
    "name": "search_and_report",
    "steps": [
        {
            "skill": "search",
            "id": "search",
            "input": {"query": "authentication", "limit": 10}
        },
        {
            "skill": "report",
            "id": "report",
            "input": {
                "title": "Search Results",
                "content": [{
                    "section": "Files Found",
                    "data": {"results": "{{ search.results }}"}
                }]
            }
        }
    ]
}
```

### Pattern 2: Search → Analyze → Report

```python
workflow = {
    "name": "search_analyze_report",
    "steps": [
        {"skill": "search", "id": "s1", "input": {"query": "JWT"}},
        {"skill": "code_analysis", "id": "a1",
         "input": {"code": "{{ s1.results[0].snippet }}"}},
        {"skill": "report", "id": "r1",
         "input": {"title": "JWT Analysis",
                   "content": [{"section": "Structure",
                                "data": {"text": "{{ a1 }}"}}]}}
    ]
}
```

### Pattern 3: Search Multiple Repos

```python
workflow = {
    "name": "multi_repo_search",
    "steps": [
        {"skill": "search", "input": {"query": "auth", "repository": "repo1"}},
        {"skill": "search", "input": {"query": "auth", "repository": "repo2"}}
    ]
}
```

---

## Best Practices

1. **Use Templates for Common Tasks**: Templates are fast and reliable
2. **Keep Workflows Linear**: Complex branches better handled by LLM
3. **Validate Input**: Skill schemas are automatically validated
4. **Handle Errors**: Check result status and step details
5. **Use Meaningful IDs**: Step IDs make variable interpolation clearer
6. **Comment Workflows**: YAML supports comments for documentation
7. **Test Custom Skills**: Implement unit tests before registering
8. **Monitor Execution**: Track execution status and timing

---

## Troubleshooting

### "Skill not found" Error
- Ensure skill is registered: `orchestrator.list_available_skills()`
- Check spelling of skill name in workflow

### "Template not found" Error
- List templates: `orchestrator.template_engine.list_templates()`
- Ensure template is registered or loaded from file

### Variable Interpolation Not Working
- Use correct syntax: `{{ step_id.field }}`
- Ensure step ID matches previous step's ID
- Check that previous step succeeded

### Step Failing
- Check step input matches input_schema
- Review step error details in result
- Try running step individually first

---

## Next Steps

1. **Register SearchSkill** with HybridSearchEngine instance
2. **Add LLMSkill** with SessionManager for LLM integration
3. **Create Custom Templates** for your workflows
4. **Implement Custom Skills** for domain-specific tasks
5. **Explore API Integration** (Phase 4, coming soon)

---

For more information, see:
- `AGENT_PLATFORM_PROGRESS.md`: Detailed implementation progress
- `src/myragdb/agent/orchestration/agent_orchestrator.py`: Main code
- Individual skill files in `src/myragdb/agent/skills/`

Questions: libor@arionetworks.com
