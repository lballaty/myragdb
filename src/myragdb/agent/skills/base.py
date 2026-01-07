# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/base.py
# Description: Abstract base class and interfaces for agent skills
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SkillInputSchema(BaseModel):
    """Input schema for a skill"""
    pass


class SkillOutputSchema(BaseModel):
    """Output schema for a skill"""
    pass


class SkillInfo(BaseModel):
    """Metadata about a skill"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_config: List[str] = []


class Skill(ABC):
    """
    Abstract base class for all agent skills.

    Business Purpose: Define a standardized, self-contained capability
    that can be composed into workflows. Each skill takes input,
    processes it deterministically, and returns output.

    Implementations should:
    1. Define clear input_schema (what the skill accepts)
    2. Define clear output_schema (what the skill returns)
    3. Implement execute() with deterministic logic
    4. Document any external dependencies
    5. Handle errors gracefully

    Example skills:
    - SearchSkill: Query code/documentation
    - SQLSkill: Query databases
    - ReportSkill: Generate formatted reports
    - CodeAnalysisSkill: Analyze code structure
    - LLMSkill: Call LLM for reasoning

    Example usage:
        skill = SearchSkill(search_engine)
        result = await skill.execute({
            "query": "authentication flow",
            "limit": 10
        })
        print(result)  # {"results": [...]}
    """

    def __init__(self, name: str, description: str):
        """
        Initialize skill.

        Args:
            name: Unique skill identifier (e.g., "search", "sql", "report")
            description: Human-readable description of what skill does
        """
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        Define input schema for this skill.

        Returns:
            Dict describing input parameters and their types
            Format: {"param_name": {"type": "string", "required": True}, ...}

        Example:
            {
                "query": {"type": "string", "required": True},
                "limit": {"type": "integer", "default": 10},
                "search_type": {"type": "string", "enum": ["keyword", "vector", "hybrid"]}
            }
        """
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Dict[str, Any]:
        """
        Define output schema for this skill.

        Returns:
            Dict describing what this skill returns
            Format: {"results": {"type": "array", ...}, ...}

        Example:
            {
                "results": {
                    "type": "array",
                    "items": {"type": "object"}
                }
            }
        """
        pass

    @property
    def required_config(self) -> List[str]:
        """
        List of required configuration keys.

        Returns:
            List of config keys that must be provided during initialization
            Example: ["database_connection", "api_key"]
        """
        return []

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the skill with given input.

        Business Purpose: Perform the actual work of the skill deterministically.
        This should not make random decisions - same input should always
        produce same output (unless external state changes, like database content).

        Args:
            input_data: Input parameters matching input_schema

        Returns:
            Output dict matching output_schema

        Raises:
            SkillExecutionError: If execution fails
        """
        pass

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input matches schema.

        Args:
            input_data: Input to validate

        Returns:
            True if input is valid

        Note: Default implementation is basic. Override for complex validation.
        """
        schema = self.input_schema
        for field_name, field_spec in schema.items():
            if field_spec.get("required", False):
                if field_name not in input_data:
                    return False
                if field_spec.get("type") == "string":
                    if not isinstance(input_data[field_name], str):
                        return False
                elif field_spec.get("type") == "integer":
                    if not isinstance(input_data[field_name], int):
                        return False

        return True

    def get_info(self) -> SkillInfo:
        """
        Get metadata about this skill.

        Returns:
            SkillInfo with name, description, schemas
        """
        return SkillInfo(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            required_config=self.required_config
        )

    def __repr__(self) -> str:
        return f"Skill(name={self.name})"


class SkillExecutionError(Exception):
    """Raised when skill execution fails"""
    pass


class SkillValidationError(Exception):
    """Raised when skill input validation fails"""
    pass
