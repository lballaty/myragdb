# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/orchestration/workflow_engine.py
# Description: Engine for executing deterministic skill-based workflows
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Any, Dict, List, Optional
import json

from myragdb.agent.skills.base import Skill, SkillExecutionError
from myragdb.agent.skills.registry import SkillRegistry


class WorkflowStep:
    """
    Represents a single step in a workflow execution.

    Business Purpose: Encapsulates a skill invocation with input parameters
    and metadata for execution tracking.
    """

    def __init__(
        self,
        skill_name: str,
        input_data: Dict[str, Any],
        step_id: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Initialize workflow step.

        Args:
            skill_name: Name of skill to execute
            input_data: Input parameters for skill
            step_id: Optional unique step identifier
            description: Optional description of what this step does
        """
        self.skill_name = skill_name
        self.input_data = input_data
        self.step_id = step_id or f"{skill_name}_{id(self)}"
        self.description = description or f"Execute {skill_name}"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.success: bool = False


class WorkflowExecution:
    """
    Represents the execution state of a workflow.

    Business Purpose: Tracks workflow execution progress, results, and errors
    for auditing and debugging.
    """

    def __init__(self, workflow_id: str, workflow_name: str):
        """
        Initialize workflow execution.

        Args:
            workflow_id: Unique workflow execution ID
            workflow_name: Name of workflow being executed
        """
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.steps: List[WorkflowStep] = []
        self.current_step_index: int = 0
        self.status: str = "pending"  # pending, running, completed, failed
        self.error: Optional[str] = None
        self.final_result: Optional[Dict[str, Any]] = None

    def add_step(self, step: WorkflowStep) -> None:
        """Add step to workflow."""
        self.steps.append(step)

    def get_step_result(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get result from a previous step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step.result
        return None

    def get_context(self) -> Dict[str, Any]:
        """Get all previous step results as context for variable interpolation."""
        context: Dict[str, Any] = {}
        for step in self.steps[:self.current_step_index]:
            context[step.step_id] = step.result
        return context


class WorkflowEngine:
    """
    Engine for executing deterministic skill-based workflows.

    Business Purpose: Execute YAML-defined workflows that compose multiple
    skills in sequence, enabling deterministic automation of complex tasks
    before resorting to LLM-based orchestration.

    Architecture:
    1. Load workflow definition (YAML or dict)
    2. Validate workflow structure and skills exist
    3. Execute steps sequentially
    4. Pass results between steps via variable interpolation
    5. Handle errors gracefully
    6. Return aggregated results

    Example:
        engine = WorkflowEngine(skill_registry)
        execution = await engine.execute_workflow(
            workflow={
                "name": "code_review",
                "steps": [
                    {
                        "skill": "search",
                        "input": {"query": "authentication implementation"}
                    },
                    {
                        "skill": "code_analysis",
                        "input": {"code": "{{search_step.results[0].snippet}}"}
                    }
                ]
            }
        )
        print(execution.final_result)
    """

    def __init__(self, skill_registry: SkillRegistry):
        """
        Initialize WorkflowEngine.

        Args:
            skill_registry: SkillRegistry instance for skill lookup
        """
        self.skill_registry = skill_registry

    async def execute_workflow(
        self,
        workflow: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow definition.

        Business Purpose: Run a deterministic workflow by executing skills
        in sequence, handling variable interpolation and error propagation.

        Args:
            workflow: Workflow definition (dict with "name" and "steps")
            context: Optional initial context variables
            execution_id: Optional execution ID for tracking

        Returns:
            WorkflowExecution with results and status

        Raises:
            ValueError: If workflow structure is invalid
        """
        # Validate workflow
        if not isinstance(workflow, dict):
            raise ValueError("Workflow must be a dictionary")

        workflow_name = workflow.get("name", "unnamed_workflow")
        steps_def = workflow.get("steps", [])

        if not isinstance(steps_def, list) or not steps_def:
            raise ValueError("Workflow must have 'steps' list with at least one step")

        # Create execution tracker
        exec_id = execution_id or f"{workflow_name}_{id(self)}"
        execution = WorkflowExecution(exec_id, workflow_name)

        # Add initial context if provided
        if context:
            execution.final_result = context

        # Build step list
        for step_def in steps_def:
            if not isinstance(step_def, dict):
                raise ValueError(f"Step must be a dictionary: {step_def}")

            skill_name = step_def.get("skill")
            if not skill_name:
                raise ValueError("Each step must have a 'skill' field")

            input_data = step_def.get("input", {})
            step_id = step_def.get("id", f"{skill_name}_{len(execution.steps)}")
            description = step_def.get("description")

            step = WorkflowStep(skill_name, input_data, step_id, description)
            execution.add_step(step)

        # Execute steps
        execution.status = "running"

        for step_index, step in enumerate(execution.steps):
            execution.current_step_index = step_index

            try:
                # Get skill instance
                skill = self.skill_registry.get(step.skill_name)
                if not skill:
                    raise ValueError(f"Skill '{step.skill_name}' not found in registry")

                # Interpolate variables in input
                interpolated_input = self._interpolate_variables(
                    step.input_data,
                    execution.get_context()
                )

                # Validate input against skill schema
                if not await skill.validate_input(interpolated_input):
                    raise ValueError(
                        f"Input validation failed for skill '{step.skill_name}'. "
                        f"Input: {interpolated_input}, Schema: {skill.input_schema}"
                    )

                # Execute skill
                result = await skill.execute(interpolated_input)

                step.result = result
                step.success = True
                execution.final_result = result

            except Exception as e:
                step.error = str(e)
                step.success = False
                execution.status = "failed"
                execution.error = f"Step '{step.skill_name}' failed: {str(e)}"

                # Check if step has error handler
                if step_def.get("on_error") == "continue":
                    continue
                else:
                    # Default: stop on error
                    return execution

        # All steps completed successfully
        if execution.status != "failed":
            execution.status = "completed"

        return execution

    def _interpolate_variables(
        self,
        data: Any,
        context: Dict[str, Any]
    ) -> Any:
        """
        Interpolate variables in data using context.

        Business Purpose: Support variable references like {{step_id.field.subfield}}
        to pass results between workflow steps.

        Args:
            data: Data structure containing potential variable references
            context: Execution context with available values

        Returns:
            Data with variables interpolated
        """
        if isinstance(data, str):
            # Handle {{var}} syntax
            if data.startswith("{{") and data.endswith("}}"):
                var_path = data[2:-2].strip()
                return self._resolve_variable(var_path, context)
            return data

        elif isinstance(data, dict):
            return {k: self._interpolate_variables(v, context) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._interpolate_variables(item, context) for item in data]

        return data

    def _resolve_variable(self, path: str, context: Dict[str, Any]) -> Any:
        """
        Resolve a variable path in context.

        Business Purpose: Support dot notation for nested field access.

        Args:
            path: Variable path like "step_id.results[0].text"
            context: Context dictionary

        Returns:
            Resolved value or original path string if not found
        """
        parts = path.split(".")
        if not parts:
            return None

        # Get root step result
        step_id = parts[0]
        if step_id not in context:
            return f"{{{{{path}}}}}"  # Return unresolved variable

        value = context[step_id]

        # Traverse remaining parts
        for part in parts[1:]:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list):
                try:
                    # Handle array indexing like "results[0]"
                    if "[" in part:
                        field, index_str = part.split("[")
                        index = int(index_str.rstrip("]"))
                        value = value[index]
                        if field and isinstance(value, dict):
                            value = value.get(field)
                    else:
                        # Can't traverse into list without index
                        return f"{{{{{path}}}}}"
                except (ValueError, IndexError, KeyError):
                    return f"{{{{{path}}}}}"
            else:
                return f"{{{{{path}}}}}"

        return value

    def validate_workflow(self, workflow: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate workflow structure and skill availability.

        Business Purpose: Check workflow validity before execution.

        Args:
            workflow: Workflow definition to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(workflow, dict):
            return False, "Workflow must be a dictionary"

        steps = workflow.get("steps")
        if not isinstance(steps, list) or not steps:
            return False, "Workflow must have non-empty 'steps' list"

        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return False, f"Step {i} must be a dictionary"

            skill_name = step.get("skill")
            if not skill_name:
                return False, f"Step {i} missing 'skill' field"

            if not self.skill_registry.has_skill(skill_name):
                return False, f"Skill '{skill_name}' not found in registry (step {i})"

        return True, None

    def get_workflow_info(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get information about a workflow.

        Business Purpose: Describe workflow structure for planning and debugging.

        Args:
            workflow: Workflow definition

        Returns:
            Dictionary with workflow information
        """
        steps = workflow.get("steps", [])
        step_info = []

        for step in steps:
            skill_name = step.get("skill", "unknown")
            skill = self.skill_registry.get(skill_name)
            step_info.append({
                "skill": skill_name,
                "description": step.get("description", ""),
                "input_schema": skill.input_schema if skill else None
            })

        return {
            "name": workflow.get("name", "unnamed"),
            "description": workflow.get("description", ""),
            "step_count": len(steps),
            "steps": step_info
        }
