# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/orchestration/template_engine.py
# Description: Engine for loading and managing workflow templates
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import os
from typing import Any, Dict, List, Optional
import yaml
import json

from myragdb.agent.orchestration.workflow_engine import WorkflowEngine


class TemplateLibrary:
    """
    Library for managing workflow templates.

    Business Purpose: Store and retrieve pre-built workflow templates
    for common tasks, reducing boilerplate and enabling code reuse.
    """

    def __init__(self):
        """Initialize template library."""
        self.templates: Dict[str, Dict[str, Any]] = {}

    def register_template(self, template_id: str, template: Dict[str, Any]) -> None:
        """
        Register a workflow template.

        Args:
            template_id: Unique template identifier
            template: Workflow template definition
        """
        self.templates[template_id] = template

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template definition or None if not found
        """
        return self.templates.get(template_id)

    def list_templates(self) -> List[str]:
        """
        List available template IDs.

        Returns:
            List of template identifiers
        """
        return list(self.templates.keys())

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template to delete

        Returns:
            True if deleted, False if not found
        """
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False


class TemplateEngine:
    """
    Engine for loading, validating, and executing workflow templates.

    Business Purpose: Provide template management for deterministic workflows,
    supporting YAML/JSON formats, variable substitution, and reusable workflow
    patterns.

    Workflow Template Structure:
    ```yaml
    name: review_authentication
    description: Find and analyze authentication implementations
    category: code_review
    parameters:
      query:
        type: string
        description: Search query
        default: "authentication"
      limit:
        type: integer
        description: Result limit
        default: 10
    steps:
      - skill: search
        id: find_code
        description: Find authentication implementations
        input:
          query: "{{ query }}"
          limit: "{{ limit }}"
      - skill: code_analysis
        id: analyze_code
        input:
          code: "{{ find_code.results[0].snippet }}"
          language: python
      - skill: report
        input:
          title: "Authentication Implementation Review"
          content:
            - section: Findings
              data:
                text: "{{ analyze_code.analysis }}"
    ```

    Example:
        engine = TemplateEngine(workflow_engine, template_dir="./templates")
        template = engine.load_template("review_authentication")
        execution = await engine.execute_template(
            template_id="review_authentication",
            parameters={"query": "JWT auth", "limit": 5}
        )
    """

    def __init__(self, workflow_engine: WorkflowEngine, template_dir: Optional[str] = None):
        """
        Initialize TemplateEngine.

        Args:
            workflow_engine: WorkflowEngine instance
            template_dir: Optional directory to load templates from
        """
        self.workflow_engine = workflow_engine
        self.template_dir = template_dir
        self.library = TemplateLibrary()

        # Load templates from directory if provided
        if template_dir and os.path.isdir(template_dir):
            self._load_templates_from_directory(template_dir)

    def _load_templates_from_directory(self, directory: str) -> None:
        """
        Load all templates from a directory.

        Business Purpose: Auto-discover YAML/JSON template files.

        Args:
            directory: Directory containing template files
        """
        for filename in os.listdir(directory):
            if filename.endswith((".yaml", ".yml", ".json")):
                filepath = os.path.join(directory, filename)
                try:
                    template = self.load_template_from_file(filepath)
                    template_id = os.path.splitext(filename)[0]
                    self.library.register_template(template_id, template)
                except Exception as e:
                    print(f"[TemplateEngine] Failed to load template {filename}: {e}")

    def load_template_from_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load template from file.

        Args:
            filepath: Path to template file (YAML or JSON)

        Returns:
            Template definition

        Raises:
            ValueError: If file format is unsupported or parsing fails
        """
        if not os.path.isfile(filepath):
            raise ValueError(f"Template file not found: {filepath}")

        try:
            with open(filepath, 'r') as f:
                if filepath.endswith('.json'):
                    template = json.load(f)
                elif filepath.endswith(('.yaml', '.yml')):
                    template = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported file format: {filepath}")

            return template

        except Exception as e:
            raise ValueError(f"Failed to parse template file {filepath}: {str(e)}")

    def register_template(self, template_id: str, template: Dict[str, Any]) -> None:
        """
        Register a workflow template.

        Args:
            template_id: Unique template identifier
            template: Workflow template definition
        """
        self.library.register_template(template_id, template)

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template definition or None
        """
        return self.library.get_template(template_id)

    def list_templates(self) -> List[str]:
        """List available template IDs."""
        return self.library.list_templates()

    def validate_template(self, template: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a template definition.

        Business Purpose: Check template structure before execution.

        Args:
            template: Template to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(template, dict):
            return False, "Template must be a dictionary"

        # Required fields
        if "name" not in template:
            return False, "Template must have 'name' field"

        # Steps
        steps = template.get("steps")
        if not isinstance(steps, list) or not steps:
            return False, "Template must have non-empty 'steps' list"

        # Validate workflow structure
        is_valid, error = self.workflow_engine.validate_workflow(template)
        return is_valid, error

    async def execute_template(
        self,
        template_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> Any:
        """
        Execute a template by ID.

        Business Purpose: Run a registered template with parameter substitution.

        Args:
            template_id: Template identifier
            parameters: Optional parameters for template variables
            execution_id: Optional execution ID for tracking

        Returns:
            WorkflowExecution with results

        Raises:
            ValueError: If template not found or invalid
        """
        template = self.library.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")

        # Validate template
        is_valid, error = self.validate_template(template)
        if not is_valid:
            raise ValueError(f"Template validation failed: {error}")

        # Substitute parameters
        workflow = self._substitute_parameters(template, parameters or {})

        # Execute workflow
        execution = await self.workflow_engine.execute_workflow(
            workflow=workflow,
            context=parameters,
            execution_id=execution_id
        )

        return execution

    def _substitute_parameters(
        self,
        template: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Substitute parameters in template.

        Business Purpose: Replace template variables with parameter values.

        Args:
            template: Template with parameter placeholders
            parameters: Parameter values

        Returns:
            Template with substituted values
        """
        import copy
        workflow = copy.deepcopy(template)

        # Substitute in steps
        for step in workflow.get("steps", []):
            step["input"] = self._substitute_dict(
                step.get("input", {}),
                parameters
            )

        return workflow

    def _substitute_dict(
        self,
        data: Any,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        Recursively substitute parameters in data.

        Args:
            data: Data with potential variable references
            parameters: Parameter values

        Returns:
            Data with variables substituted
        """
        if isinstance(data, str):
            # Simple parameter substitution: {{ param_name }}
            for param_name, param_value in parameters.items():
                placeholder = f"{{{{ {param_name} }}}}"
                if placeholder in data:
                    return param_value
            return data

        elif isinstance(data, dict):
            return {k: self._substitute_dict(v, parameters) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._substitute_dict(item, parameters) for item in data]

        return data

    def get_template_info(self, template_id: str) -> Dict[str, Any]:
        """
        Get information about a template.

        Business Purpose: Describe template structure and requirements.

        Args:
            template_id: Template identifier

        Returns:
            Dictionary with template metadata

        Raises:
            ValueError: If template not found
        """
        template = self.library.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")

        return {
            "id": template_id,
            "name": template.get("name"),
            "description": template.get("description", ""),
            "category": template.get("category", ""),
            "parameters": template.get("parameters", {}),
            "step_count": len(template.get("steps", [])),
            "workflow_info": self.workflow_engine.get_workflow_info(template)
        }
