# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/registry.py
# Description: Registry and discovery for available skills
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Dict, List, Optional

from myragdb.agent.skills.base import Skill, SkillInfo


class SkillRegistry:
    """
    Central registry for discovering and managing available skills.

    Business Purpose: Enable dynamic skill discovery, composition validation,
    and lifecycle management. Allows new skills to be registered without
    modifying other code.

    Example usage:
        registry = SkillRegistry()

        # Register skills
        registry.register_skill(SearchSkill())
        registry.register_skill(SQLSkill())

        # Get specific skill
        skill = registry.get("search")

        # List all available
        all_skills = registry.list_available()

        # Validate workflow composition
        is_valid = registry.validate_composition(workflow_steps)
    """

    def __init__(self):
        """Initialize skill registry"""
        self.skills: Dict[str, Skill] = {}
        self._skill_cache: Dict[str, SkillInfo] = {}

    def register_skill(self, skill: Skill) -> None:
        """
        Register a new skill.

        Args:
            skill: Skill instance to register

        Raises:
            ValueError: If skill with same name already registered
        """
        if skill.name in self.skills:
            raise ValueError(f"Skill '{skill.name}' already registered")

        self.skills[skill.name] = skill
        # Invalidate cache
        self._skill_cache.pop(skill.name, None)

    def unregister_skill(self, skill_name: str) -> None:
        """
        Unregister a skill.

        Args:
            skill_name: Name of skill to unregister
        """
        if skill_name in self.skills:
            del self.skills[skill_name]
            self._skill_cache.pop(skill_name, None)

    def get(self, skill_name: str) -> Optional[Skill]:
        """
        Get a skill by name.

        Args:
            skill_name: Name of skill to retrieve

        Returns:
            Skill instance, or None if not found
        """
        return self.skills.get(skill_name)

    def list_available(self) -> List[SkillInfo]:
        """
        List all available skills with metadata.

        Returns:
            List of SkillInfo objects for all registered skills
        """
        return [skill.get_info() for skill in self.skills.values()]

    def list_names(self) -> List[str]:
        """
        List names of all available skills.

        Returns:
            List of skill names
        """
        return list(self.skills.keys())

    def has_skill(self, skill_name: str) -> bool:
        """
        Check if a skill is registered.

        Args:
            skill_name: Name of skill to check

        Returns:
            True if skill registered, False otherwise
        """
        return skill_name in self.skills

    def validate_composition(self, workflow_steps: List[Dict]) -> bool:
        """
        Validate that workflow steps form a valid skill chain.

        Business Purpose: Ensure that:
        1. All skills exist
        2. Output of one step is compatible with input of next
        3. Workflow is composable

        Args:
            workflow_steps: List of workflow step dicts
                Each step: {"skill": "skill_name", "input": {...}}

        Returns:
            True if composition is valid, False otherwise

        Note: Basic validation - can be extended with schema checking
        """
        for step in workflow_steps:
            skill_name = step.get("skill")

            # Check skill exists
            if not self.has_skill(skill_name):
                print(f"Skill '{skill_name}' not found in registry")
                return False

            # Additional validation could check:
            # - Input schema matches provided input
            # - Output from previous step matches input of this step
            # - Output schemas are compatible

        return True

    def get_skill_info(self, skill_name: str) -> Optional[SkillInfo]:
        """
        Get metadata about a specific skill.

        Args:
            skill_name: Name of skill

        Returns:
            SkillInfo with input/output schemas, or None if not found
        """
        if skill_name not in self.skills:
            return None

        if skill_name not in self._skill_cache:
            self._skill_cache[skill_name] = self.skills[skill_name].get_info()

        return self._skill_cache[skill_name]

    def clear(self) -> None:
        """Clear all registered skills"""
        self.skills.clear()
        self._skill_cache.clear()

    def __repr__(self) -> str:
        return f"SkillRegistry({len(self.skills)} skills)"
