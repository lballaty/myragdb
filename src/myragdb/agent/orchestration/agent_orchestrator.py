# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/orchestration/agent_orchestrator.py
# Description: Main orchestrator for agent-based task execution
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Any, Dict, List, Optional

from myragdb.agent.skills.registry import SkillRegistry
from myragdb.agent.orchestration.workflow_engine import WorkflowEngine, WorkflowExecution
from myragdb.agent.orchestration.template_engine import TemplateEngine


class AgentOrchestrator:
    """
    Main orchestrator for agent-based task execution.

    Business Purpose: Coordinate skill execution using three strategies:
    1. Template-based: Fast, deterministic workflows for known patterns
    2. LLM-based: Dynamic planning when task requires reasoning
    3. Fallback: Default behaviors for common requests

    Architecture:
    ```
    User Request
         ↓
    ┌─────────────────────────────────┐
    │ AgentOrchestrator               │
    │                                 │
    │ 1. Classify request type        │
    │ 2. Match to template (if exists)│ ← TemplateEngine
    │ 3. Execute workflow             │ ← WorkflowEngine
    │ 4. Aggregate results            │
    │ 5. Return response              │
    └─────────────────────────────────┘
         ↓
    Task Result
    ```

    Example:
        orchestrator = AgentOrchestrator(
            skill_registry=registry,
            session_manager=session,
            search_engine=search
        )

        # Template-based execution (deterministic)
        result = await orchestrator.execute_request(
            request_type="code_review",
            parameters={"query": "authentication", "limit": 10}
        )

        # Direct workflow execution
        result = await orchestrator.execute_workflow(
            workflow={
                "name": "custom_search",
                "steps": [...]
            }
        )
    """

    def __init__(
        self,
        skill_registry: SkillRegistry,
        workflow_engine: Optional[WorkflowEngine] = None,
        template_engine: Optional[TemplateEngine] = None,
        session_manager: Optional[Any] = None,
        search_engine: Optional[Any] = None
    ):
        """
        Initialize AgentOrchestrator.

        Args:
            skill_registry: SkillRegistry with registered skills
            workflow_engine: Optional WorkflowEngine (creates if not provided)
            template_engine: Optional TemplateEngine (creates if not provided)
            session_manager: Optional SessionManager for LLM access
            search_engine: Optional HybridSearchEngine instance
        """
        self.skill_registry = skill_registry
        self.workflow_engine = workflow_engine or WorkflowEngine(skill_registry)
        self.template_engine = template_engine or TemplateEngine(self.workflow_engine)
        self.session_manager = session_manager
        self.search_engine = search_engine

        # Register built-in templates
        self._register_built_in_templates()

    def _register_built_in_templates(self) -> None:
        """Register built-in workflow templates for common tasks."""
        # Code Search Template
        self.template_engine.register_template(
            "code_search",
            {
                "name": "code_search",
                "description": "Search for code across repositories",
                "category": "search",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                        "required": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Result limit",
                        "default": 10
                    },
                    "repository": {
                        "type": "string",
                        "description": "Optional repository filter",
                        "required": False
                    }
                },
                "steps": [
                    {
                        "skill": "search",
                        "id": "search_step",
                        "input": {
                            "query": "{{ query }}",
                            "limit": "{{ limit }}",
                            "repository_filter": "{{ repository }}"
                        }
                    }
                ]
            }
        )

        # Code Analysis Template
        self.template_engine.register_template(
            "code_analysis",
            {
                "name": "code_analysis",
                "description": "Search and analyze code structure",
                "category": "analysis",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                        "required": True
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "default": "python"
                    }
                },
                "steps": [
                    {
                        "skill": "search",
                        "id": "find_code",
                        "input": {
                            "query": "{{ query }}",
                            "limit": 1
                        }
                    },
                    {
                        "skill": "code_analysis",
                        "id": "analyze",
                        "input": {
                            "code": "{{ find_code.results[0].snippet }}",
                            "language": "{{ language }}"
                        }
                    }
                ]
            }
        )

        # Code Review Template
        self.template_engine.register_template(
            "code_review",
            {
                "name": "code_review",
                "description": "Find code, analyze it, and generate review report",
                "category": "review",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Code to find and review",
                        "required": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of files to review",
                        "default": 3
                    }
                },
                "steps": [
                    {
                        "skill": "search",
                        "id": "find_code",
                        "input": {
                            "query": "{{ query }}",
                            "limit": "{{ limit }}"
                        }
                    },
                    {
                        "skill": "report",
                        "id": "generate_report",
                        "input": {
                            "title": "Code Review: {{ query }}",
                            "content": [
                                {
                                    "section": "Reviewed Files",
                                    "data": {"results": "{{ find_code.results }}"}
                                }
                            ],
                            "format": "markdown"
                        }
                    }
                ]
            }
        )

    async def execute_request(
        self,
        request_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a request using template-based orchestration.

        Business Purpose: Route requests to appropriate templates for
        deterministic, fast execution of common patterns.

        Args:
            request_type: Type of request (e.g., "code_search", "code_review")
            parameters: Request parameters for template substitution
            execution_id: Optional execution tracking ID

        Returns:
            Dictionary with execution results

        Raises:
            ValueError: If request type not found
        """
        # Check if template exists
        if request_type not in self.template_engine.list_templates():
            raise ValueError(
                f"Request type '{request_type}' not found. "
                f"Available: {', '.join(self.template_engine.list_templates())}"
            )

        # Execute template
        execution = await self.template_engine.execute_template(
            template_id=request_type,
            parameters=parameters or {},
            execution_id=execution_id
        )

        return self._format_execution_result(execution)

    async def execute_workflow(
        self,
        workflow: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a custom workflow directly.

        Business Purpose: Allow agents to execute custom workflows for
        non-standard or one-off task execution.

        Args:
            workflow: Workflow definition
            context: Optional initial context
            execution_id: Optional execution tracking ID

        Returns:
            Dictionary with execution results

        Raises:
            ValueError: If workflow is invalid
        """
        execution = await self.workflow_engine.execute_workflow(
            workflow=workflow,
            context=context,
            execution_id=execution_id
        )

        return self._format_execution_result(execution)

    def _format_execution_result(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """
        Format workflow execution results.

        Args:
            execution: Completed workflow execution

        Returns:
            Formatted result dictionary
        """
        return {
            "execution_id": execution.workflow_id,
            "workflow_name": execution.workflow_name,
            "status": execution.status,
            "result": execution.final_result,
            "error": execution.error,
            "steps_completed": sum(1 for s in execution.steps if s.success),
            "total_steps": len(execution.steps),
            "step_details": [
                {
                    "id": step.step_id,
                    "skill": step.skill_name,
                    "status": "success" if step.success else "failed",
                    "result": step.result,
                    "error": step.error
                }
                for step in execution.steps
            ]
        }

    def list_available_templates(self) -> List[Dict[str, Any]]:
        """
        List available workflow templates.

        Returns:
            List of template information dictionaries
        """
        templates = []
        for template_id in self.template_engine.list_templates():
            try:
                info = self.template_engine.get_template_info(template_id)
                templates.append(info)
            except Exception as e:
                print(f"[AgentOrchestrator] Error getting template {template_id}: {e}")

        return templates

    def list_available_skills(self) -> List[Dict[str, Any]]:
        """
        List available skills.

        Returns:
            List of skill information dictionaries
        """
        skills = []
        for skill_info in self.skill_registry.list_available():
            skills.append({
                "name": skill_info.name,
                "description": skill_info.description,
                "input_schema": skill_info.input_schema,
                "output_schema": skill_info.output_schema,
                "required_config": skill_info.required_config
            })
        return skills

    def register_template_from_file(self, filepath: str, template_id: Optional[str] = None) -> None:
        """
        Register a template from file.

        Args:
            filepath: Path to template file (YAML/JSON)
            template_id: Optional custom template ID (uses filename if not provided)
        """
        template = self.template_engine.load_template_from_file(filepath)
        if not template_id:
            import os
            template_id = os.path.splitext(os.path.basename(filepath))[0]

        self.template_engine.register_template(template_id, template)

    def register_custom_skill(self, skill: Any) -> None:
        """
        Register a custom skill.

        Business Purpose: Enable extensions with user-defined skills.

        Args:
            skill: Skill instance implementing Skill interface
        """
        self.skill_registry.register_skill(skill)

    def get_orchestrator_info(self) -> Dict[str, Any]:
        """
        Get orchestrator information and capabilities.

        Returns:
            Dictionary with orchestrator details
        """
        return {
            "total_skills": len(self.skill_registry.list_names()),
            "total_templates": len(self.template_engine.list_templates()),
            "available_skills": self.skill_registry.list_names(),
            "available_templates": self.template_engine.list_templates(),
            "has_session_manager": self.session_manager is not None,
            "has_search_engine": self.search_engine is not None
        }
