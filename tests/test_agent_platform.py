# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/test_agent_platform.py
# Description: Comprehensive tests for agent platform orchestration
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import pytest
import asyncio
from typing import Dict, Any

from myragdb.agent.skills import (
    Skill, SkillRegistry, SearchSkill, LLMSkill,
    CodeAnalysisSkill, ReportSkill, SQLSkill,
    SkillExecutionError
)
from myragdb.agent.orchestration import (
    WorkflowEngine, WorkflowExecution, TemplateEngine, AgentOrchestrator
)
from myragdb.llm.session_manager import SessionManager


class TestSkillRegistry:
    """Test SkillRegistry functionality."""

    def test_register_skill(self):
        """Test skill registration."""
        registry = SkillRegistry()

        # Create mock skill
        class MockSkill(Skill):
            def __init__(self):
                super().__init__("mock", "Mock skill")

            @property
            def input_schema(self):
                return {"param": {"type": "string", "required": True}}

            @property
            def output_schema(self):
                return {"result": {"type": "string"}}

            async def execute(self, input_data):
                return {"result": "done"}

        skill = MockSkill()
        registry.register_skill(skill)

        assert registry.has_skill("mock")
        assert registry.get("mock") == skill

    def test_list_skills(self):
        """Test skill listing."""
        registry = SkillRegistry()

        class Skill1(Skill):
            def __init__(self):
                super().__init__("skill1", "First")
            @property
            def input_schema(self):
                return {}
            @property
            def output_schema(self):
                return {}
            async def execute(self, input_data):
                return {}

        class Skill2(Skill):
            def __init__(self):
                super().__init__("skill2", "Second")
            @property
            def input_schema(self):
                return {}
            @property
            def output_schema(self):
                return {}
            async def execute(self, input_data):
                return {}

        registry.register_skill(Skill1())
        registry.register_skill(Skill2())

        names = registry.list_names()
        assert "skill1" in names
        assert "skill2" in names
        assert len(names) == 2

    def test_duplicate_skill_registration(self):
        """Test that duplicate skill registration raises error."""
        registry = SkillRegistry()

        class TestSkill(Skill):
            def __init__(self):
                super().__init__("test", "Test")
            @property
            def input_schema(self):
                return {}
            @property
            def output_schema(self):
                return {}
            async def execute(self, input_data):
                return {}

        registry.register_skill(TestSkill())

        with pytest.raises(ValueError):
            registry.register_skill(TestSkill())


class TestCodeAnalysisSkill:
    """Test CodeAnalysisSkill."""

    @pytest.mark.asyncio
    async def test_analyze_python_code(self):
        """Test Python code analysis."""
        skill = CodeAnalysisSkill()

        code = """
def authenticate(token):
    '''Validate authentication token'''
    return validate_token(token)

class AuthManager:
    def __init__(self):
        self.tokens = []
"""

        result = await skill.execute({
            "code": code,
            "language": "python",
            "analysis_type": "structure"
        })

        assert "structures" in result
        assert "function" in [s["type"] for s in result["structures"]]
        assert "class" in [s["type"] for s in result["structures"]]
        assert result["language"] == "python"

    @pytest.mark.asyncio
    async def test_analyze_javascript_code(self):
        """Test JavaScript code analysis."""
        skill = CodeAnalysisSkill()

        code = """
function authenticate(token) {
    return validateToken(token);
}

const verify = async (token) => {
    return await checkToken(token);
};
"""

        result = await skill.execute({
            "code": code,
            "language": "javascript",
            "analysis_type": "functions"
        })

        assert "structures" in result
        assert len(result["structures"]) > 0
        assert all("function" in s["type"].lower() for s in result["structures"])


class TestReportSkill:
    """Test ReportSkill."""

    @pytest.mark.asyncio
    async def test_generate_markdown_report(self):
        """Test markdown report generation."""
        skill = ReportSkill()

        result = await skill.execute({
            "title": "Test Report",
            "content": [
                {
                    "section": "Findings",
                    "data": {
                        "items": ["Finding 1", "Finding 2"]
                    }
                }
            ],
            "format": "markdown"
        })

        assert result["format"] == "markdown"
        assert "# Test Report" in result["report"]
        assert "## Findings" in result["report"]
        assert "Finding 1" in result["report"]

    @pytest.mark.asyncio
    async def test_generate_json_report(self):
        """Test JSON report generation."""
        skill = ReportSkill()

        result = await skill.execute({
            "title": "JSON Report",
            "content": [{"section": "Data", "data": {"text": "test"}}],
            "format": "json"
        })

        assert result["format"] == "json"
        import json
        parsed = json.loads(result["report"])
        assert parsed["title"] == "JSON Report"


class TestWorkflowEngine:
    """Test WorkflowEngine."""

    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self):
        """Test simple workflow execution."""
        registry = SkillRegistry()
        engine = WorkflowEngine(registry)

        class EchoSkill(Skill):
            def __init__(self):
                super().__init__("echo", "Echo skill")
            @property
            def input_schema(self):
                return {"text": {"type": "string", "required": True}}
            @property
            def output_schema(self):
                return {"result": {"type": "string"}}
            async def execute(self, input_data):
                return {"result": f"Echo: {input_data['text']}"}

        registry.register_skill(EchoSkill())

        workflow = {
            "name": "simple_echo",
            "steps": [
                {
                    "skill": "echo",
                    "input": {"text": "Hello"}
                }
            ]
        }

        execution = await engine.execute_workflow(workflow)
        assert execution.status == "completed"
        assert execution.final_result["result"] == "Echo: Hello"

    @pytest.mark.asyncio
    async def test_workflow_variable_interpolation(self):
        """Test variable interpolation between steps."""
        registry = SkillRegistry()
        engine = WorkflowEngine(registry)

        class ProduceSkill(Skill):
            def __init__(self):
                super().__init__("produce", "Produces data")
            @property
            def input_schema(self):
                return {"value": {"type": "string", "required": True}}
            @property
            def output_schema(self):
                return {"data": {"type": "string"}}
            async def execute(self, input_data):
                return {"data": f"processed_{input_data['value']}"}

        class ConsumeSkill(Skill):
            def __init__(self):
                super().__init__("consume", "Consumes data")
            @property
            def input_schema(self):
                return {"input": {"type": "string", "required": True}}
            @property
            def output_schema(self):
                return {"result": {"type": "string"}}
            async def execute(self, input_data):
                return {"result": f"consumed_{input_data['input']}"}

        registry.register_skill(ProduceSkill())
        registry.register_skill(ConsumeSkill())

        workflow = {
            "name": "chained",
            "steps": [
                {
                    "skill": "produce",
                    "id": "step1",
                    "input": {"value": "test"}
                },
                {
                    "skill": "consume",
                    "id": "step2",
                    "input": {"input": "{{ step1.data }}"}
                }
            ]
        }

        execution = await engine.execute_workflow(workflow)
        assert execution.status == "completed"
        assert execution.final_result["result"] == "consumed_processed_test"

    @pytest.mark.asyncio
    async def test_workflow_validation(self):
        """Test workflow validation."""
        registry = SkillRegistry()
        engine = WorkflowEngine(registry)

        # Invalid workflow - missing steps
        invalid = {"name": "bad"}
        is_valid, error = engine.validate_workflow(invalid)
        assert not is_valid
        assert "steps" in error.lower()


class TestTemplateEngine:
    """Test TemplateEngine."""

    @pytest.mark.asyncio
    async def test_template_registration_and_execution(self):
        """Test template registration and execution."""
        registry = SkillRegistry()
        workflow_engine = WorkflowEngine(registry)
        template_engine = TemplateEngine(workflow_engine)

        class TestSkill(Skill):
            def __init__(self):
                super().__init__("test", "Test skill")
            @property
            def input_schema(self):
                return {"param": {"type": "string", "required": True}}
            @property
            def output_schema(self):
                return {"result": {"type": "string"}}
            async def execute(self, input_data):
                return {"result": input_data["param"]}

        registry.register_skill(TestSkill())

        template = {
            "name": "test_template",
            "parameters": {
                "input": {"type": "string", "required": True}
            },
            "steps": [
                {
                    "skill": "test",
                    "input": {"param": "{{ input }}"}
                }
            ]
        }

        template_engine.register_template("test_template", template)

        execution = await template_engine.execute_template(
            "test_template",
            parameters={"input": "hello"}
        )

        assert execution.status == "completed"
        assert execution.final_result["result"] == "hello"

    def test_template_validation(self):
        """Test template validation."""
        registry = SkillRegistry()
        workflow_engine = WorkflowEngine(registry)
        template_engine = TemplateEngine(workflow_engine)

        # Invalid template
        invalid = {"name": "bad"}
        is_valid, error = template_engine.validate_template(invalid)
        assert not is_valid


class TestAgentOrchestrator:
    """Test AgentOrchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        registry = SkillRegistry()
        orchestrator = AgentOrchestrator(skill_registry=registry)

        assert orchestrator.skill_registry == registry
        assert orchestrator.workflow_engine is not None
        assert orchestrator.template_engine is not None

    def test_built_in_templates(self):
        """Test built-in templates are registered."""
        registry = SkillRegistry()
        orchestrator = AgentOrchestrator(skill_registry=registry)

        templates = orchestrator.template_engine.list_templates()
        assert "code_search" in templates
        assert "code_analysis" in templates
        assert "code_review" in templates

    def test_orchestrator_info(self):
        """Test orchestrator info retrieval."""
        registry = SkillRegistry()
        orchestrator = AgentOrchestrator(skill_registry=registry)

        info = orchestrator.get_orchestrator_info()
        assert "total_skills" in info
        assert "total_templates" in info
        assert "available_templates" in info
        assert info["total_templates"] >= 3  # At least built-in templates

    @pytest.mark.asyncio
    async def test_custom_skill_registration(self):
        """Test registering and using custom skills."""
        registry = SkillRegistry()
        orchestrator = AgentOrchestrator(skill_registry=registry)

        class CustomSkill(Skill):
            def __init__(self):
                super().__init__("custom", "Custom skill")
            @property
            def input_schema(self):
                return {"data": {"type": "string", "required": True}}
            @property
            def output_schema(self):
                return {"output": {"type": "string"}}
            async def execute(self, input_data):
                return {"output": f"custom_{input_data['data']}"}

        orchestrator.register_custom_skill(CustomSkill())

        assert registry.has_skill("custom")
        skills = orchestrator.list_available_skills()
        assert any(s["name"] == "custom" for s in skills)


class TestInputValidation:
    """Test input validation across skills."""

    @pytest.mark.asyncio
    async def test_skill_input_validation(self):
        """Test that skills validate input."""
        skill = CodeAnalysisSkill()

        # Missing required code parameter
        with pytest.raises(SkillExecutionError):
            await skill.execute({"language": "python"})

    @pytest.mark.asyncio
    async def test_report_skill_input_validation(self):
        """Test report skill input validation."""
        skill = ReportSkill()

        # Missing required title
        with pytest.raises(SkillExecutionError):
            await skill.execute({"content": []})

        # Missing required content
        with pytest.raises(SkillExecutionError):
            await skill.execute({"title": "Test"})


class TestErrorHandling:
    """Test error handling in workflows."""

    @pytest.mark.asyncio
    async def test_workflow_step_failure(self):
        """Test workflow stops on step failure."""
        registry = SkillRegistry()
        engine = WorkflowEngine(registry)

        class FailingSkill(Skill):
            def __init__(self):
                super().__init__("fail", "Fails")
            @property
            def input_schema(self):
                return {}
            @property
            def output_schema(self):
                return {}
            async def execute(self, input_data):
                raise SkillExecutionError("Intentional failure")

        registry.register_skill(FailingSkill())

        workflow = {
            "name": "failing",
            "steps": [
                {"skill": "fail", "input": {}}
            ]
        }

        execution = await engine.execute_workflow(workflow)
        assert execution.status == "failed"
        assert "Intentional failure" in execution.error


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow execution."""
        registry = SkillRegistry()
        orchestrator = AgentOrchestrator(skill_registry=registry)

        # Register a test skill
        class SearchMockSkill(Skill):
            def __init__(self):
                super().__init__("search_mock", "Mock search")
            @property
            def input_schema(self):
                return {"query": {"type": "string", "required": True}}
            @property
            def output_schema(self):
                return {"results": {"type": "array"}}
            async def execute(self, input_data):
                return {
                    "results": [
                        {"file": "test.py", "snippet": "def test(): pass"}
                    ]
                }

        registry.register_skill(SearchMockSkill())

        # Create workflow
        workflow = {
            "name": "test_workflow",
            "steps": [
                {
                    "skill": "search_mock",
                    "id": "search",
                    "input": {"query": "test"}
                }
            ]
        }

        result = await orchestrator.execute_workflow(workflow)
        assert result["status"] == "completed"
        assert len(result["step_details"]) == 1
        assert result["step_details"][0]["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
