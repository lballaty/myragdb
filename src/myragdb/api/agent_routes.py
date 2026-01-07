# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/agent_routes.py
# Description: FastAPI routes for agent orchestration endpoints
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from myragdb.agent.orchestration import AgentOrchestrator
from myragdb.agent.skills import SkillRegistry


# ==================== Request/Response Models ====================

class ExecuteRequestModel(BaseModel):
    """
    Request to execute a template-based request.

    Business Purpose: Provide a clean interface for executing pre-built
    workflow templates with parameter substitution.
    """
    request_type: str = Field(
        ...,
        description="Template type (e.g., 'code_search', 'code_review')",
        examples=["code_search"]
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for template substitution",
        example={"query": "authentication", "limit": 10}
    )
    execution_id: Optional[str] = Field(
        default=None,
        description="Optional execution tracking ID"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "request_type": "code_search",
                "parameters": {"query": "JWT authentication", "limit": 10},
                "execution_id": "exec_12345"
            }
        }


class WorkflowStepModel(BaseModel):
    """Single step in a workflow."""
    skill: str = Field(..., description="Skill name")
    id: Optional[str] = Field(None, description="Optional step ID")
    input: Dict[str, Any] = Field(default_factory=dict, description="Step input")
    description: Optional[str] = Field(None, description="Step description")


class ExecuteWorkflowModel(BaseModel):
    """
    Request to execute a custom workflow.

    Business Purpose: Allow direct execution of custom workflows for
    non-standard task execution.
    """
    name: str = Field(..., description="Workflow name")
    steps: List[WorkflowStepModel] = Field(..., description="Workflow steps")
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Initial execution context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "code_review_workflow",
                "steps": [
                    {
                        "skill": "search",
                        "id": "find_code",
                        "input": {"query": "authentication"}
                    }
                ]
            }
        }


class ExecutionResultModel(BaseModel):
    """
    Result from workflow execution.

    Business Purpose: Return structured execution results with step-by-step
    details for auditing and debugging.
    """
    execution_id: str
    workflow_name: str
    status: str = Field(..., description="completed, failed, or error")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    steps_completed: int
    total_steps: int
    step_details: List[Dict[str, Any]]


class TemplateInfoModel(BaseModel):
    """Information about a workflow template."""
    id: str = Field(..., description="Template ID")
    name: str
    description: str
    category: Optional[str] = None
    parameters: Dict[str, Any]
    step_count: int


class AvailableTemplatesModel(BaseModel):
    """List of available templates."""
    total: int
    templates: List[TemplateInfoModel]


class SkillInfoModel(BaseModel):
    """Information about a skill."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_config: List[str]


class AvailableSkillsModel(BaseModel):
    """List of available skills."""
    total: int
    skills: List[SkillInfoModel]


class OrchestratorInfoModel(BaseModel):
    """Information about the orchestrator."""
    total_skills: int
    total_templates: int
    available_skills: List[str]
    available_templates: List[str]
    has_session_manager: bool
    has_search_engine: bool


class RegisterTemplateModel(BaseModel):
    """Request to register a template."""
    template_id: str = Field(..., description="Unique template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = None
    steps: List[WorkflowStepModel] = Field(..., description="Workflow steps")
    parameters: Optional[Dict[str, Any]] = None


class RegisterSkillModel(BaseModel):
    """Request to register a skill."""
    skill_name: str = Field(..., description="Skill name")
    # Note: Full skill registration would require actual skill class


# ==================== Router Setup ====================

def create_agent_routes(orchestrator: AgentOrchestrator) -> APIRouter:
    """
    Create FastAPI router for agent orchestration endpoints.

    Business Purpose: Provide REST API for agent platform functionality.

    Args:
        orchestrator: AgentOrchestrator instance

    Returns:
        FastAPI APIRouter with agent endpoints
    """
    router = APIRouter(prefix="/api/v1/agent", tags=["Agent Platform"])

    # ==================== Execution Endpoints ====================

    @router.post(
        "/execute",
        response_model=ExecutionResultModel,
        summary="Execute template-based request",
        description="Execute a pre-built workflow template with parameters"
    )
    async def execute_template_request(
        request: ExecuteRequestModel
    ) -> ExecutionResultModel:
        """
        Execute a template-based request.

        Business Purpose: Run pre-built workflows with parameter substitution
        for common patterns like code search and review.

        Args:
            request: Execution request with template type and parameters

        Returns:
            Execution result with status and step details

        Raises:
            HTTPException: If template not found or execution fails
        """
        try:
            result = await orchestrator.execute_request(
                request_type=request.request_type,
                parameters=request.parameters,
                execution_id=request.execution_id
            )
            return ExecutionResultModel(**result)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

    @router.post(
        "/execute-workflow",
        response_model=ExecutionResultModel,
        summary="Execute custom workflow",
        description="Execute a custom workflow with specified steps"
    )
    async def execute_custom_workflow(
        workflow: ExecuteWorkflowModel
    ) -> ExecutionResultModel:
        """
        Execute a custom workflow.

        Business Purpose: Allow flexible workflow execution for non-standard
        tasks or complex compositions.

        Args:
            workflow: Custom workflow definition

        Returns:
            Execution result with status and step details

        Raises:
            HTTPException: If workflow is invalid or execution fails
        """
        try:
            # Convert to dict format expected by orchestrator
            workflow_dict = {
                "name": workflow.name,
                "steps": [step.dict() for step in workflow.steps]
            }

            result = await orchestrator.execute_workflow(
                workflow=workflow_dict,
                context=workflow.context
            )
            return ExecutionResultModel(**result)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

    # ==================== Template Endpoints ====================

    @router.get(
        "/templates",
        response_model=AvailableTemplatesModel,
        summary="List available templates",
        description="Get list of all available workflow templates"
    )
    async def list_templates() -> AvailableTemplatesModel:
        """
        List available workflow templates.

        Returns:
            List of template information
        """
        templates = orchestrator.list_available_templates()
        return AvailableTemplatesModel(
            total=len(templates),
            templates=[TemplateInfoModel(**t) for t in templates]
        )

    @router.get(
        "/templates/{template_id}",
        response_model=TemplateInfoModel,
        summary="Get template information",
        description="Get detailed information about a specific template"
    )
    async def get_template_info(template_id: str) -> TemplateInfoModel:
        """
        Get information about a specific template.

        Args:
            template_id: Template identifier

        Returns:
            Template information

        Raises:
            HTTPException: If template not found
        """
        try:
            info = orchestrator.template_engine.get_template_info(template_id)
            return TemplateInfoModel(**info)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.post(
        "/templates",
        summary="Register custom template",
        description="Register a new workflow template"
    )
    async def register_template(template: RegisterTemplateModel) -> Dict[str, str]:
        """
        Register a custom workflow template.

        Args:
            template: Template definition

        Returns:
            Confirmation with template ID

        Raises:
            HTTPException: If template registration fails
        """
        try:
            template_dict = {
                "name": template.name,
                "description": template.description or "",
                "steps": [step.dict() for step in template.steps],
                "parameters": template.parameters or {}
            }

            orchestrator.template_engine.register_template(
                template.template_id,
                template_dict
            )

            return {
                "status": "success",
                "template_id": template.template_id,
                "message": f"Template '{template.template_id}' registered"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== Skill Endpoints ====================

    @router.get(
        "/skills",
        response_model=AvailableSkillsModel,
        summary="List available skills",
        description="Get list of all available skills"
    )
    async def list_skills() -> AvailableSkillsModel:
        """
        List all available skills.

        Returns:
            List of skill information
        """
        skills = orchestrator.list_available_skills()
        return AvailableSkillsModel(
            total=len(skills),
            skills=[SkillInfoModel(**s) for s in skills]
        )

    @router.get(
        "/skills/{skill_name}",
        summary="Get skill information",
        description="Get detailed information about a specific skill"
    )
    async def get_skill_info(skill_name: str) -> Dict[str, Any]:
        """
        Get information about a specific skill.

        Args:
            skill_name: Skill name

        Returns:
            Skill information

        Raises:
            HTTPException: If skill not found
        """
        skill = orchestrator.skill_registry.get(skill_name)
        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

        skill_info = skill.get_info()
        return {
            "name": skill_info.name,
            "description": skill_info.description,
            "input_schema": skill_info.input_schema,
            "output_schema": skill_info.output_schema,
            "required_config": skill_info.required_config
        }

    # ==================== Orchestrator Endpoints ====================

    @router.get(
        "/info",
        response_model=OrchestratorInfoModel,
        summary="Get orchestrator information",
        description="Get information about orchestrator capabilities"
    )
    async def get_orchestrator_info() -> OrchestratorInfoModel:
        """
        Get orchestrator information and capabilities.

        Returns:
            Orchestrator information
        """
        info = orchestrator.get_orchestrator_info()
        return OrchestratorInfoModel(**info)

    @router.get(
        "/health",
        summary="Health check",
        description="Check if agent platform is operational"
    )
    async def health_check() -> Dict[str, str]:
        """
        Health check for agent platform.

        Returns:
            Health status
        """
        return {
            "status": "healthy",
            "message": "Agent platform orchestrator is operational"
        }

    return router
