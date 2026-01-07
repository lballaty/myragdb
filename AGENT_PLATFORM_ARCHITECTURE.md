# MyRAGDB Agent Platform Architecture
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/AGENT_PLATFORM_ARCHITECTURE.md
**Description:** Complete architecture for agent orchestration platform with extensible skills framework
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Executive Summary

MyRAGDB evolves from a **hybrid search service** into an **extensible agent platform** that orchestrates multi-agent workflows. The system maintains complete backward compatibility while adding:

- **Cloud LLM Integration**: Gemini, ChatGPT, Claude (API key, OAuth, CLI auth)
- **Agent Orchestration**: Deterministic-first, LLM-assisted routing
- **Extensible Skills**: SQL, reporting, code analysis, custom capabilities
- **Workflow Templates**: Pre-built patterns for common use cases
- **Zero Restart**: Switch models/agents without server restart

This is perfect for your workshop/book because it demonstrates:
- Real-world LLM integration patterns
- Agent orchestration architecture
- Building extensible platforms
- Workshop-ready code examples

---

## System Context: What Stays, What's Added

```
EXISTING MYRAGDB (Preserved Unchanged)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
├─ Hybrid Search Engine (Meilisearch + Vector)
├─ Repository Indexing & Watching
├─ File Metadata Database
├─ Local LLM Management (10 models on ports 8081-8092)
├─ Query Rewriting Service
└─ Observability & Logging


ADDITIONS: AGENT PLATFORM LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER (NEW)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  AgentOrchestrator                                               │
│  • Receives user query/request                                   │
│  • Routes to template OR LLM for planning                        │
│  • Executes skill sequences                                      │
│  • Synthesizes results                                           │
│                                                                   │
│         ├─ WorkflowEngine                                        │
│         │  • Executes deterministic workflows                    │
│         │  • Manages state between steps                         │
│         │  • Error handling & retry logic                        │
│         │                                                         │
│         ├─ SkillRegistry                                         │
│         │  • Discovers available skills                          │
│         │  • Validates skill compatibility                       │
│         │  • Manages skill lifecycle                             │
│         │                                                         │
│         └─ TemplateEngine                                        │
│            • Loads YAML workflows                                │
│            • Template matching & routing                         │
│            • User-defined templates                              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SKILLS LAYER (NEW)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Skill (Abstract Base)                                           │
│  • Input validation                                              │
│  • Execute deterministically                                     │
│  • Output formatting                                             │
│                                                                   │
│  Built-in Skills:                                                │
│  ├─ SearchSkill: Query MyRAGDB search engine                    │
│  ├─ SQLSkill: Query databases (Supabase, PostgreSQL, etc)      │
│  ├─ ReportSkill: Generate formatted reports                     │
│  ├─ CodeAnalysisSkill: Parse and analyze code                  │
│  ├─ DataTransformSkill: Map/filter/aggregate results           │
│  └─ LLMSkill: Call LLM for reasoning/summarization             │
│                                                                   │
│  User-Defined Skills:                                            │
│  └─ [Easily add new capabilities]                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│           LLM LAYER (EXISTING + CLOUD SUPPORT)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  LLM Session Manager (NEW)                                       │
│  • Track active LLM (local or cloud)                            │
│  • Switch without restart                                        │
│  • Credential management                                         │
│                                                                   │
│  Provider Registry (NEW)                                         │
│  ├─ Local LLMs (preserved)                                       │
│  └─ Cloud Providers (NEW): Gemini, ChatGPT, Claude              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│         SEARCH & DATA LAYER (EXISTING - UNCHANGED)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  HybridSearchEngine (Meilisearch + ChromaDB)                     │
│  RepositoryIndexer                                               │
│  FileMetadataDB                                                  │
│  ObservabilityDB                                                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Breakdown

### 1. ORCHESTRATION LAYER

#### A. Agent Orchestrator (Main Router)

```python
class AgentOrchestrator:
    """
    Main orchestration engine. Routes requests to workflows or LLM planner.

    Business Purpose: Determine if request matches a pre-built template
    (deterministic execution) or needs LLM reasoning (adaptive execution).

    Workflow:
    1. Receive user query
    2. Try to match against templates (fast path)
    3. If no match, ask LLM to plan workflow (slow path)
    4. Execute chosen workflow using WorkflowEngine
    5. Return synthesized results
    """

    async def execute(self, user_query: str, context: Dict = None) -> AgentResult:
        """
        Execute a user request, routing to appropriate agent workflow.

        Args:
            user_query: Natural language request
            context: Optional context (user_id, session_id, etc)

        Returns:
            AgentResult with final output + execution trace
        """

        # 1. Try to match against templates (deterministic)
        matching_template = self.template_engine.find_matching_template(user_query)

        if matching_template:
            # Fast path: Execute pre-built workflow
            return await self.workflow_engine.execute(
                template=matching_template,
                user_query=user_query,
                context=context
            )

        # 2. No template match: Ask LLM to plan workflow
        workflow_plan = await self.llm_planner.plan_workflow(
            user_query=user_query,
            available_skills=self.skill_registry.list_available()
        )

        # 3. Validate and execute planned workflow
        if self.workflow_engine.validate_plan(workflow_plan):
            return await self.workflow_engine.execute_plan(workflow_plan)
        else:
            return AgentResult(
                success=False,
                error="LLM-planned workflow validation failed"
            )
```

#### B. Workflow Engine (Executor)

```python
class WorkflowEngine:
    """
    Executes deterministic multi-step workflows.

    State Management:
    - Passes output from one skill as input to next
    - Maintains execution context/history
    - Handles errors and retries

    Example workflow:
    1. SearchSkill("authentication") → code_snippets
    2. CodeAnalysisSkill(code_snippets) → findings
    3. ReportSkill(findings) → markdown_report
    4. LLMSkill(markdown_report) → executive_summary
    """

    async def execute(
        self,
        template: WorkflowTemplate,
        user_query: str,
        context: Dict = None
    ) -> AgentResult:
        """Execute a workflow template"""

        execution_state = ExecutionState(
            template_id=template.id,
            user_query=user_query,
            context=context,
            steps=[]
        )

        for step in template.steps:
            try:
                skill = self.skill_registry.get(step.skill_name)

                # Prepare skill input (may reference previous step outputs)
                step_input = self._prepare_input(step, execution_state)

                # Execute skill
                step_output = await skill.execute(step_input)

                # Store result
                execution_state.steps.append({
                    "step_name": step.name,
                    "skill": step.skill_name,
                    "input": step_input,
                    "output": step_output,
                    "duration": step.duration
                })

            except SkillExecutionError as e:
                # Handle error: retry, fallback, or fail
                if step.retry_count > 0:
                    # Retry logic
                    pass
                elif step.fallback_skill:
                    # Use fallback skill
                    pass
                else:
                    return AgentResult(
                        success=False,
                        error=f"Step {step.name} failed: {e}"
                    )

        # Return final result
        return AgentResult(
            success=True,
            output=execution_state.steps[-1]["output"],
            execution_trace=execution_state
        )
```

#### C. Skill Registry (Discovery)

```python
class SkillRegistry:
    """
    Central registry for available skills/tools.

    Purpose: Discover, validate, and manage skill lifecycle.
    Enables dynamic skill loading and composition.
    """

    def register_skill(self, skill: Skill) -> None:
        """Register a new skill"""
        self.skills[skill.name] = skill
        self.skill_cache.invalidate()  # Clear cache

    def get(self, skill_name: str) -> Skill:
        """Get skill by name"""
        return self.skills.get(skill_name)

    def list_available(self) -> List[SkillInfo]:
        """List all available skills with metadata"""
        return [
            SkillInfo(
                name=skill.name,
                description=skill.description,
                input_schema=skill.input_schema,
                output_schema=skill.output_schema,
                required_config=skill.required_config
            )
            for skill in self.skills.values()
        ]

    def validate_composition(self, workflow: Workflow) -> bool:
        """Validate that workflow steps form valid skill chain"""
        for step in workflow.steps:
            if not self.get(step.skill_name):
                return False

            # Validate input/output compatibility
            if step != workflow.steps[0]:  # Not first step
                prev_step = workflow.steps[workflow.steps.index(step) - 1]
                prev_output_schema = self.get(prev_step.skill_name).output_schema
                current_input_schema = self.get(step.skill_name).input_schema

                if not self._schemas_compatible(prev_output_schema, current_input_schema):
                    return False

        return True
```

#### D. Template Engine (Workflow Matching)

```python
class TemplateEngine:
    """
    Loads and matches workflow templates.

    Templates are YAML definitions of common workflows.
    User query matched against templates to find best match.
    """

    async def load_templates(self) -> None:
        """Load templates from YAML files"""
        template_dir = Path("workflows/templates")

        for template_file in template_dir.glob("*.yaml"):
            with open(template_file) as f:
                template_data = yaml.safe_load(f)
                template = WorkflowTemplate.from_dict(template_data)
                self.templates[template.id] = template

    def find_matching_template(self, user_query: str) -> Optional[WorkflowTemplate]:
        """Find best matching template for user query"""

        # Use semantic similarity or keyword matching
        best_match = None
        best_score = 0.0

        for template in self.templates.values():
            # Try keyword matching first
            keyword_score = self._keyword_match_score(user_query, template.keywords)

            if keyword_score > best_score:
                best_score = keyword_score
                best_match = template

        # If keyword match not good enough, return None
        # (LLM orchestrator will plan instead)
        if best_score > 0.6:
            return best_match

        return None

    def create_template(self, name: str, workflow_definition: dict) -> WorkflowTemplate:
        """Allow users to create custom templates"""
        template = WorkflowTemplate(
            id=slugify(name),
            name=name,
            description=workflow_definition.get("description"),
            keywords=workflow_definition.get("keywords", []),
            steps=workflow_definition.get("steps", [])
        )

        # Validate before saving
        if not self.validate_template(template):
            raise ValueError("Invalid template definition")

        # Save to file
        template_file = Path(f"workflows/templates/{template.id}.yaml")
        template_file.write_text(yaml.dump(template.to_dict()))

        # Reload templates
        self.templates[template.id] = template

        return template
```

### 2. SKILLS LAYER

#### A. Skill Base Class

```python
class Skill(ABC):
    """
    Abstract base for all skills/tools.

    A skill is a deterministic, self-contained capability
    that takes input, processes it, and returns output.

    Example skills:
    - SearchSkill: Query code/documentation
    - SQLSkill: Query databases
    - ReportSkill: Generate reports
    - CodeAnalysisSkill: Analyze code structure
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Pydantic schema for input validation"""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Dict[str, Any]:
        """Pydantic schema for output"""
        pass

    @property
    def required_config(self) -> List[str]:
        """List of required configuration keys"""
        return []

    @abstractmethod
    async def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill deterministically"""
        pass

    async def validate(self, input: Dict[str, Any]) -> bool:
        """Validate input against schema"""
        try:
            self.input_schema.validate(input)
            return True
        except ValidationError:
            return False
```

#### B. Built-in Skills: Search

```python
class SearchSkill(Skill):
    """
    Search MyRAGDB for code/documentation.

    Input:
        {
            "query": "authentication flow",
            "search_type": "hybrid",  # keyword, vector, hybrid
            "limit": 10
        }

    Output:
        {
            "results": [
                {
                    "file": "auth.py",
                    "snippet": "def authenticate()...",
                    "score": 0.95,
                    "type": "code"
                },
                ...
            ]
        }
    """

    def __init__(self, search_engine: HybridSearchEngine):
        super().__init__(
            name="search",
            description="Search codebase for files and documentation"
        )
        self.search_engine = search_engine

    @property
    def input_schema(self):
        return {
            "query": {"type": "string", "required": True},
            "search_type": {"type": "string", "enum": ["keyword", "vector", "hybrid"]},
            "limit": {"type": "integer", "default": 10}
        }

    @property
    def output_schema(self):
        return {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "snippet": {"type": "string"},
                        "score": {"type": "number"},
                        "type": {"type": "string"}
                    }
                }
            }
        }

    async def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search"""
        results = await self.search_engine.search(
            query=input["query"],
            search_type=input.get("search_type", "hybrid"),
            limit=input.get("limit", 10)
        )

        return {
            "results": [
                {
                    "file": r.file_path,
                    "snippet": r.content[:500],  # First 500 chars
                    "score": r.score,
                    "type": r.type
                }
                for r in results
            ]
        }
```

#### C. Built-in Skills: SQL

```python
class SQLSkill(Skill):
    """
    Execute SQL queries against configured databases.

    Supports multiple databases (Supabase, PostgreSQL, etc)
    Input query is validated before execution (security)

    Input:
        {
            "database": "supabase",
            "query": "SELECT * FROM users WHERE role = 'admin'",
            "safe_mode": true
        }

    Output:
        {
            "rows": [...],
            "row_count": 42,
            "execution_time_ms": 123
        }
    """

    def __init__(self, database_config: Dict):
        super().__init__(
            name="sql",
            description="Execute SQL queries against configured databases"
        )
        self.database_config = database_config
        self.connections = {}

    @property
    def required_config(self):
        return ["database_connections"]

    @property
    def input_schema(self):
        return {
            "database": {"type": "string", "required": True},
            "query": {"type": "string", "required": True},
            "safe_mode": {"type": "boolean", "default": True}
        }

    @property
    def output_schema(self):
        return {
            "rows": {"type": "array"},
            "row_count": {"type": "integer"},
            "execution_time_ms": {"type": "number"}
        }

    async def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query safely"""
        database = input["database"]
        query = input["query"]
        safe_mode = input.get("safe_mode", True)

        # Validate query (prevent DELETE/DROP in safe mode)
        if safe_mode:
            if not self._is_safe_query(query):
                raise SkillExecutionError("Query not allowed in safe mode")

        # Execute
        start_time = time.time()

        conn = await self._get_connection(database)
        cursor = await conn.cursor()
        await cursor.execute(query)
        rows = await cursor.fetchall()

        duration_ms = (time.time() - start_time) * 1000

        return {
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": duration_ms
        }

    def _is_safe_query(self, query: str) -> bool:
        """Check if query is safe in safe mode"""
        forbidden = ["DELETE", "DROP", "TRUNCATE", "ALTER"]
        query_upper = query.upper()
        return not any(f in query_upper for f in forbidden)

    async def _get_connection(self, database: str):
        """Get or create database connection"""
        if database not in self.connections:
            conn = await self._create_connection(database)
            self.connections[database] = conn
        return self.connections[database]

    async def _create_connection(self, database: str):
        """Create new database connection"""
        config = self.database_config[database]
        # Implementation depends on database type
        # (PostgreSQL, MySQL, Supabase, etc)
        pass
```

#### D. Built-in Skills: Report

```python
class ReportSkill(Skill):
    """
    Generate formatted reports from data.

    Input:
        {
            "title": "Security Audit Report",
            "sections": [
                {
                    "heading": "Executive Summary",
                    "content": "Found 5 vulnerabilities..."
                },
                {
                    "heading": "Findings",
                    "items": [
                        {"severity": "high", "description": "..."},
                        ...
                    ]
                }
            ],
            "format": "markdown"  # markdown, html, pdf
        }

    Output:
        {
            "report": "# Security Audit Report\n...",
            "format": "markdown",
            "byte_size": 5432
        }
    """

    def __init__(self):
        super().__init__(
            name="report",
            description="Generate formatted reports from structured data"
        )

    @property
    def input_schema(self):
        return {
            "title": {"type": "string", "required": True},
            "sections": {"type": "array", "required": True},
            "format": {"type": "string", "enum": ["markdown", "html", "pdf"]}
        }

    @property
    def output_schema(self):
        return {
            "report": {"type": "string"},
            "format": {"type": "string"},
            "byte_size": {"type": "integer"}
        }

    async def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report"""
        format = input.get("format", "markdown")

        if format == "markdown":
            report = self._generate_markdown(input)
        elif format == "html":
            report = self._generate_html(input)
        elif format == "pdf":
            report = self._generate_pdf(input)

        return {
            "report": report,
            "format": format,
            "byte_size": len(report.encode())
        }

    def _generate_markdown(self, data: Dict) -> str:
        """Generate Markdown report"""
        lines = [f"# {data['title']}\n"]

        for section in data["sections"]:
            lines.append(f"## {section['heading']}\n")

            if "content" in section:
                lines.append(section["content"])
            elif "items" in section:
                for item in section["items"]:
                    if isinstance(item, dict):
                        lines.append(f"- {item.get('description', str(item))}")
                    else:
                        lines.append(f"- {item}")

            lines.append("")

        return "\n".join(lines)
```

#### E. Built-in Skills: LLM

```python
class LLMSkill(Skill):
    """
    Call LLM for reasoning, summarization, classification.

    This is the "intelligent" skill. Use when you need LLM reasoning.

    Input:
        {
            "prompt": "Summarize these findings in 2 sentences",
            "context": "Found 5 high-severity bugs...",
            "model_id": "gemini-pro",  # optional, uses session default
            "temperature": 0.5
        }

    Output:
        {
            "response": "The code has critical security issues...",
            "model_used": "gemini-pro",
            "tokens_used": 150
        }
    """

    def __init__(self, session_manager):
        super().__init__(
            name="llm",
            description="Use LLM for reasoning, summarization, classification"
        )
        self.session_manager = session_manager

    @property
    def input_schema(self):
        return {
            "prompt": {"type": "string", "required": True},
            "context": {"type": "string"},
            "model_id": {"type": "string"},
            "temperature": {"type": "number", "default": 0.5}
        }

    @property
    def output_schema(self):
        return {
            "response": {"type": "string"},
            "model_used": {"type": "string"},
            "tokens_used": {"type": "integer"}
        }

    async def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM"""
        session = self.session_manager.get_active_session()
        model_id = input.get("model_id", session.model_id)

        full_prompt = input["prompt"]
        if input.get("context"):
            full_prompt = f"{input['context']}\n\n{input['prompt']}"

        provider = get_provider(session.provider_type)

        response = await provider.generate(
            prompt=full_prompt,
            model_id=model_id,
            temperature=input.get("temperature", 0.5)
        )

        return {
            "response": response,
            "model_used": model_id,
            "tokens_used": self._estimate_tokens(response)
        }
```

---

## Workflow Templates (YAML)

Templates define common workflows. Users run them by name or LLM picks them.

### Example 1: Code Security Audit

```yaml
# workflows/templates/code-security-audit.yaml

id: code-security-audit
name: Code Security Audit
description: Find security issues in codebase

keywords:
  - security
  - audit
  - vulnerability
  - bug
  - bug-hunt

steps:
  - name: Find Security-Related Code
    skill: search
    input:
      query: "authentication security password encryption credentials api_key"
      search_type: "keyword"
      limit: 20

  - name: Analyze Code for Issues
    skill: code_analysis
    input:
      code: "{{ steps[0].output.results }}"
      checks:
        - sql_injection
        - xss
        - auth_bypass
        - hardcoded_secrets

  - name: Generate Report
    skill: report
    input:
      title: "Security Audit Report"
      sections:
        - heading: "Executive Summary"
          content: "Scanned {{ steps[0].output.row_count }} files"
        - heading: "Findings"
          items: "{{ steps[1].output.issues }}"

  - name: LLM Summary
    skill: llm
    input:
      prompt: "Create a 2-sentence executive summary of these security findings"
      context: "{{ steps[2].output.report }}"
```

### Example 2: Data Analysis Workflow

```yaml
# workflows/templates/data-analysis.yaml

id: data-analysis
name: Database Analysis Report
description: Query database and generate analysis report

keywords:
  - database
  - analysis
  - report
  - data
  - statistics

steps:
  - name: Query Database
    skill: sql
    input:
      database: "supabase"
      query: "SELECT user_id, COUNT(*) as activity_count FROM events GROUP BY user_id"
      safe_mode: true

  - name: Transform Data
    skill: data_transform
    input:
      data: "{{ steps[0].output.rows }}"
      operations:
        - type: "sort"
          field: "activity_count"
          order: "desc"
        - type: "filter"
          field: "activity_count"
          condition: "> 10"

  - name: Generate Report
    skill: report
    input:
      title: "User Activity Analysis"
      format: "markdown"
      sections:
        - heading: "Summary"
          content: "Analyzed {{ steps[0].output.row_count }} users"
        - heading: "Top Users"
          items: "{{ steps[1].output.data }}"
```

---

## API Endpoints (New)

```
Orchestration Endpoints:
  POST   /agent/execute         - Execute query (template or LLM-planned)
  GET    /agent/templates       - List available workflow templates
  POST   /agent/templates       - Create new template
  GET    /agent/templates/{id}  - Get template details

Skills Endpoints:
  GET    /skills               - List all available skills
  GET    /skills/{name}        - Get skill schema and details
  POST   /skills/validate      - Validate skill chain composition

Workflow Endpoints:
  POST   /workflows/execute    - Execute workflow (internal use)
  GET    /workflows/history    - Get past executions + traces
  GET    /workflows/history/{id} - Get detailed trace
```

---

## Minimal Changes to Existing Code

### 1. `server.py` Changes

```python
# Only additions, no removal of existing code

from myragdb.agent.orchestrator import AgentOrchestrator
from myragdb.agent.registry import SkillRegistry

# Initialize at startup (alongside existing search engine)
agent_orchestrator = AgentOrchestrator(
    workflow_engine=workflow_engine,
    skill_registry=skill_registry,
    template_engine=template_engine,
    llm_planner=llm_planner
)

# New endpoints
@app.post("/agent/execute")
async def execute_agent(request: AgentRequest):
    result = await agent_orchestrator.execute(
        user_query=request.query,
        context=request.context
    )
    return result.to_dict()

# Note: ALL existing endpoints remain unchanged
# GET  /search
# POST /search
# GET  /llm/models
# POST /llm/start
# POST /llm/stop
# etc.
```

### 2. `llm_router.py` Changes

```python
# Only enhancement, no breaking changes

async def route_query(query, task_type):
    """Enhanced: Now checks active session"""

    session = session_manager.get_active_session()

    if session.provider_type == "local":
        # EXISTING LOGIC: Route to local port
        port = PORT_MAPPING[task_type]
        return await call_local_llm(port, query)
    else:
        # NEW: Route to cloud provider
        provider = provider_registry.get_provider(session.provider_type)
        return await provider.generate(query, session.model_id)
```

### 3. `cli.py` Changes

```python
# New commands added (existing commands unchanged)

# Existing commands still work:
# python -m myragdb.cli search
# python -m myragdb.cli index

# New commands:
@click.group()
def agent():
    """Agent orchestration commands"""
    pass

@agent.command()
@click.argument('query')
def execute(query):
    """Execute agent workflow"""
    # Call /agent/execute endpoint
    pass

@agent.command()
def templates():
    """List available templates"""
    # Call /agent/templates endpoint
    pass

@agent.command()
@click.argument('template_name')
def run_template(template_name):
    """Run a specific template"""
    pass
```

---

## Directory Structure

```
myragdb/
├── src/myragdb/
│   ├── agent/                      # NEW: Agent platform
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # AgentOrchestrator
│   │   ├── workflow_engine.py      # WorkflowEngine
│   │   ├── template_engine.py      # TemplateEngine
│   │   ├── registry.py             # SkillRegistry
│   │   ├── skills/                 # Skill implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Skill base class
│   │   │   ├── search_skill.py
│   │   │   ├── sql_skill.py
│   │   │   ├── report_skill.py
│   │   │   ├── code_analysis_skill.py
│   │   │   └── llm_skill.py
│   │   └── models.py               # Data models
│   │
│   ├── llm/                        # ENHANCED: LLM layer
│   │   ├── session_manager.py      # NEW: Session management
│   │   ├── providers/              # NEW: Provider abstraction
│   │   │   ├── base_provider.py
│   │   │   ├── local_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   ├── chatgpt_provider.py
│   │   │   └── claude_provider.py
│   │   ├── llm_router.py           # ENHANCED: Cloud support
│   │   └── auth_config.py          # NEW: Auth management
│   │
│   ├── api/
│   │   ├── server.py               # ENHANCED: New endpoints
│   │   └── models.py               # ENHANCED: New models
│   │
│   ├── search/                     # UNCHANGED
│   │   └── hybrid_search.py
│   ├── indexers/                   # UNCHANGED
│   ├── db/                         # UNCHANGED
│   └── cli.py                      # ENHANCED: New commands
│
├── workflows/                      # NEW: Template definitions
│   └── templates/
│       ├── code-security-audit.yaml
│       ├── data-analysis.yaml
│       ├── code-documentation.yaml
│       └── README.md               # Guide for creating templates
│
└── config/
    └── llm.yaml                    # NEW: LLM configuration
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create SessionManager + CloudLLMProvider abstraction
- [ ] Test cloud LLM switching without restart
- [ ] Verify zero breaking changes to existing system

### Phase 2: Agent Framework (Week 2-3)
- [ ] Implement Skill base class
- [ ] Build core skills (Search, SQL, Report)
- [ ] Create SkillRegistry

### Phase 3: Orchestration (Week 3-4)
- [ ] Build WorkflowEngine + TemplateEngine
- [ ] Create AgentOrchestrator
- [ ] Implement LLM planner

### Phase 4: Templates & UI (Week 4-5)
- [ ] Create 5-10 example templates (YAML)
- [ ] UI for template gallery
- [ ] CLI commands for agent execution

### Phase 5: Workshop Content (Week 5-6)
- [ ] Documentation for each component
- [ ] Tutorial notebooks
- [ ] Book chapters

---

## Key Design Principles

1. **Deterministic-first**: Templates run without LLM when possible
2. **LLM as orchestrator**: Only use LLM for planning/reasoning
3. **Extensible skills**: Easy to add new capabilities
4. **Zero breaking changes**: All existing APIs work unchanged
5. **Workshop-ready**: Complete, teachable architecture

---

## Examples for Your Workshop

### Example 1: Search → Report (Template-based)

```python
# User runs pre-built template
result = await orchestrator.execute(
    user_query="Generate security report for authentication code"
)

# Output: Markdown report, no LLM needed (template-driven)
print(result.output)
```

### Example 2: Complex Analysis (LLM-planned)

```python
# No matching template, LLM plans workflow
result = await orchestrator.execute(
    user_query="Find all user management bugs and estimate time to fix each"
)

# LLM planner:
# 1. SearchSkill("user management bugs")
# 2. CodeAnalysisSkill(results)
# 3. LLMSkill("estimate time to fix")
# 4. ReportSkill("compile findings")
```

### Example 3: Custom Agent Creation

```python
# Workshop attendee creates new skill
class MetricsSkill(Skill):
    name = "metrics"

    async def execute(self, input):
        # Implement custom metric calculation
        pass

# Register it
skill_registry.register_skill(MetricsSkill())

# Use in new template
template = TemplateEngine.create_template("metrics-report", {
    "steps": [
        {"skill": "search", "input": {...}},
        {"skill": "metrics", "input": {...}},
        {"skill": "report", "input": {...}}
    ]
})
```

---

## Summary

This architecture:

✅ **Preserves** all existing MyRAGDB functionality
✅ **Adds** cloud LLM support (3 auth methods)
✅ **Introduces** agent orchestration (deterministic-first)
✅ **Enables** skill extensibility (easy to add capabilities)
✅ **Supports** workflow templates (pre-built patterns)
✅ **Teaches** complete AI application architecture

Perfect for your workshop and book because it demonstrates real-world patterns while staying practical and understandable.

**Questions:** libor@arionetworks.com
