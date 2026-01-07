# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/llm_skill.py
# Description: Skill for calling LLM for reasoning, analysis, and summarization
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Any, Dict, Optional

from myragdb.agent.skills.base import Skill, SkillExecutionError
from myragdb.llm.session_manager import SessionManager


class LLMSkill(Skill):
    """
    Skill for calling the active LLM for reasoning, analysis, and summarization.

    Business Purpose: Enable agents to leverage LLM capabilities for complex
    reasoning tasks that require semantic understanding, multi-step analysis,
    or creative problem-solving. Uses the currently active LLM session which
    could be local or cloud-based.

    Input Schema:
    {
        "prompt": {
            "type": "string",
            "required": True,
            "description": "Prompt to send to the LLM"
        },
        "max_tokens": {
            "type": "integer",
            "required": False,
            "default": 1000,
            "description": "Maximum tokens to generate"
        },
        "temperature": {
            "type": "number",
            "required": False,
            "default": 0.7,
            "description": "Temperature for randomness (0.0-1.0)"
        },
        "stream": {
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "Whether to stream response tokens"
        }
    }

    Output Schema:
    {
        "response": {
            "type": "string",
            "description": "LLM response text"
        },
        "model": {
            "type": "string",
            "description": "Model ID that generated response"
        },
        "tokens_used": {
            "type": "integer",
            "description": "Approximate tokens used"
        }
    }

    Example:
        skill = LLMSkill(session_manager)
        result = await skill.execute({
            "prompt": "Summarize the authentication flow described in these files",
            "max_tokens": 500,
            "temperature": 0.5
        })
        print(result["response"])  # LLM summary
    """

    def __init__(self, session_manager: SessionManager):
        """
        Initialize LLMSkill.

        Args:
            session_manager: SessionManager instance for accessing active LLM
        """
        super().__init__(
            name="llm",
            description="Call active LLM for reasoning, analysis, and summarization"
        )
        self.session_manager = session_manager

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define input schema for LLM skill."""
        return {
            "prompt": {
                "type": "string",
                "required": True,
                "description": "Prompt to send to the LLM"
            },
            "max_tokens": {
                "type": "integer",
                "required": False,
                "default": 1000,
                "description": "Maximum tokens to generate"
            },
            "temperature": {
                "type": "number",
                "required": False,
                "default": 0.7,
                "description": "Temperature for randomness (0.0-1.0)"
            },
            "stream": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Whether to stream response tokens"
            }
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        """Define output schema for LLM skill."""
        return {
            "response": {
                "type": "string",
                "description": "LLM response text"
            },
            "model": {
                "type": "string",
                "description": "Model ID that generated response"
            },
            "tokens_used": {
                "type": "integer",
                "description": "Approximate tokens used"
            }
        }

    @property
    def required_config(self) -> list:
        """
        List required configuration.

        Returns:
            List of required config keys
        """
        return []

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LLM call for reasoning/analysis.

        Business Purpose: Provide semantic understanding and reasoning capabilities
        to agents by delegating to the active LLM (local or cloud).

        Args:
            input_data: Input matching input_schema

        Returns:
            Dictionary with response text, model ID, and token estimate

        Raises:
            SkillExecutionError: If no active LLM session or execution fails
        """
        try:
            # Get active session
            session = self.session_manager.get_active_session()
            if not session:
                raise SkillExecutionError(
                    "No active LLM session. Switch to a cloud LLM or start a local model."
                )

            # Extract parameters
            prompt = input_data.get("prompt")
            if not prompt:
                raise SkillExecutionError("Prompt is required")

            max_tokens = input_data.get("max_tokens", 1000)
            temperature = input_data.get("temperature", 0.7)
            stream = input_data.get("stream", False)

            # Validate parameters
            if not 0.0 <= temperature <= 1.0:
                raise SkillExecutionError("Temperature must be between 0.0 and 1.0")
            if max_tokens < 1 or max_tokens > 10000:
                raise SkillExecutionError("Max tokens must be between 1 and 10000")

            # Call LLM based on provider
            if session.provider_type.value == "local":
                # For local LLMs, would integrate with local model provider
                # For now, return placeholder indicating local integration needed
                raise SkillExecutionError(
                    "Local LLM integration not yet implemented in skill layer"
                )
            else:
                # Cloud provider - get provider instance
                provider = session.provider_manager.get_provider(session.provider_type.value)
                if not provider:
                    raise SkillExecutionError(
                        f"Provider {session.provider_type.value} not available"
                    )

                # Generate response
                response = await provider.generate(
                    prompt=prompt,
                    model_id=session.model_id,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                # Estimate tokens (roughly 1.3 tokens per word)
                estimated_tokens = int((len(prompt.split()) + len(response.split())) * 1.3)

                return {
                    "response": response,
                    "model": session.model_id,
                    "tokens_used": estimated_tokens
                }

        except Exception as e:
            if isinstance(e, SkillExecutionError):
                raise
            raise SkillExecutionError(f"LLM execution failed: {str(e)}")
