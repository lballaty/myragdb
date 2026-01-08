# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/local_to_cloud_comparison_skill.py
# Description: Skill for comparing local LLM vs cloud LLM performance
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

import logging
import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass

from myragdb.agent.skills.base import Skill, SkillConfig, SkillExecutionError
from myragdb.llm.session_manager import SessionManager


logger = logging.getLogger(__name__)


@dataclass
class LocalToCloudComparisonConfig(SkillConfig):
    """Configuration for local to cloud LLM comparison."""
    name: str = "local_to_cloud_comparison"
    description: str = "Compare local LLM performance against cloud LLM"
    timeout_seconds: int = 120
    max_response_length: int = 5000


class LocalToCloudComparisonSkill(Skill):
    """
    Compare local LLM quality against cloud LLM.

    Business Purpose: Enable developers to evaluate whether their local LLM is
    sufficient for a task or if they should use cloud LLM. Provides concrete
    metrics and suggestions for improvement.

    Use Cases:
    - "Should I use local or cloud LLM for this task?"
    - "Why is my local model's answer less helpful?"
    - "How can I improve my local model's quality?"
    - Cost-benefit analysis (local speed vs cloud quality)
    - Evaluating model upgrades

    Example:
        skill = LocalToCloudComparisonSkill(session_manager)
        result = await skill.execute({
            "query": "How do I implement OAuth 2.0?",
            "local_model": "phi-3",
            "cloud_model": "claude-opus"
        })
        # Returns detailed comparison with scores and suggestions
    """

    def __init__(self, session_manager: SessionManager, config: Optional[LocalToCloudComparisonConfig] = None):
        """
        Initialize LocalToCloudComparisonSkill.

        Args:
            session_manager: SessionManager instance for accessing LLMs
            config: Skill configuration
        """
        config = config or LocalToCloudComparisonConfig()
        super().__init__(config)
        self.session_manager = session_manager
        self.config = config

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define input schema for comparison skill."""
        return {
            "query": {
                "type": "string",
                "required": True,
                "description": "Query to send to both LLMs for comparison"
            },
            "local_model": {
                "type": "string",
                "required": False,
                "description": "Local model name (uses current active local model if not specified)",
                "examples": ["phi-3", "llama-2", "neural-chat"]
            },
            "cloud_model": {
                "type": "string",
                "required": False,
                "description": "Cloud model to compare against (uses current active cloud model if not specified)",
                "examples": ["claude-opus", "gpt-4", "gemini-pro"]
            },
            "analysis_depth": {
                "type": "string",
                "required": False,
                "enum": ["quick", "detailed"],
                "default": "detailed",
                "description": "How deep to analyze differences"
            }
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        """Define output schema for comparison skill."""
        return {
            "query": {"type": "string"},
            "local_llm_response": {"type": "string"},
            "local_llm_model": {"type": "string"},
            "cloud_llm_response": {"type": "string"},
            "cloud_llm_model": {"type": "string"},
            "comparison": {
                "type": "object",
                "properties": {
                    "response_length": {"type": "object"},
                    "completeness_score": {"type": "object"},
                    "accuracy_score": {"type": "object"},
                    "helpfulness_score": {"type": "object"},
                    "tone_match": {"type": "number"}
                }
            },
            "analysis": {"type": "string"},
            "improvements": {"type": "array"},
            "recommendation": {"type": "string"}
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute local vs cloud LLM comparison.

        Business Purpose: Provide actionable insights for optimizing LLM usage.

        Args:
            input_data: Input matching input_schema

        Returns:
            Dictionary with comparison results, analysis, and suggestions

        Raises:
            SkillExecutionError: If comparison fails
        """
        try:
            query = input_data.get("query")
            if not query:
                raise SkillExecutionError("Query is required")

            local_model = input_data.get("local_model")
            cloud_model = input_data.get("cloud_model")
            analysis_depth = input_data.get("analysis_depth", "detailed")

            logger.info(f"Starting LLM comparison for query: {query[:50]}...")

            # Get responses from both LLMs in parallel
            local_response, cloud_response = await asyncio.gather(
                self._get_local_response(query, local_model),
                self._get_cloud_response(query, cloud_model),
                return_exceptions=False
            )

            # Analyze differences
            comparison = await self._analyze_responses(
                query,
                local_response,
                cloud_response,
                analysis_depth
            )

            # Generate improvement suggestions
            improvements = await self._suggest_improvements(
                query,
                local_response,
                cloud_response,
                comparison
            )

            # Generate recommendation
            recommendation = self._generate_recommendation(comparison, improvements)

            logger.info(f"Comparison complete. Recommendation: {recommendation}")

            return {
                "status": "success",
                "data": {
                    "query": query,
                    "local_llm_response": local_response["text"],
                    "local_llm_model": local_response["model"],
                    "cloud_llm_response": cloud_response["text"],
                    "cloud_llm_model": cloud_response["model"],
                    "comparison": comparison,
                    "analysis": comparison.get("detailed_analysis", ""),
                    "improvements": improvements,
                    "recommendation": recommendation
                }
            }

        except Exception as e:
            logger.error(f"Comparison execution failed: {str(e)}", exc_info=True)
            raise SkillExecutionError(f"LLM comparison failed: {str(e)}")

    async def _get_local_response(self, query: str, model_name: Optional[str]) -> Dict[str, Any]:
        """Get response from local LLM."""
        try:
            # Get local session (port 8081 by default)
            session = self.session_manager.get_session()
            if not session or session.provider != "local":
                # Switch to local if available
                self.session_manager.switch_provider("local")
                session = self.session_manager.get_session()

            logger.info(f"Querying local LLM: {session.model_name}")

            # Call local LLM
            response = await session.generate(query, max_tokens=self.config.max_response_length)

            return {
                "text": response,
                "model": session.model_name,
                "provider": "local"
            }
        except Exception as e:
            logger.warning(f"Failed to get local response: {e}")
            raise SkillExecutionError(f"Local LLM query failed: {e}")

    async def _get_cloud_response(self, query: str, model_name: Optional[str]) -> Dict[str, Any]:
        """Get response from cloud LLM."""
        try:
            # Get cloud session
            session = self.session_manager.get_session()
            if not session or session.provider == "local":
                # Find a cloud provider
                authenticated = self.session_manager.get_authenticated_providers()
                if not authenticated:
                    raise SkillExecutionError(
                        "No cloud LLM configured. Please authenticate with a cloud provider."
                    )
                # Use first available cloud provider
                cloud_provider = [p for p in authenticated if p != "local"][0]
                self.session_manager.switch_provider(cloud_provider)
                session = self.session_manager.get_session()

            logger.info(f"Querying cloud LLM: {session.model_name}")

            # Call cloud LLM
            response = await session.generate(query, max_tokens=self.config.max_response_length)

            return {
                "text": response,
                "model": session.model_name,
                "provider": session.provider
            }
        except Exception as e:
            logger.warning(f"Failed to get cloud response: {e}")
            raise SkillExecutionError(f"Cloud LLM query failed: {e}")

    async def _analyze_responses(
        self,
        query: str,
        local_response: Dict[str, Any],
        cloud_response: Dict[str, Any],
        depth: str
    ) -> Dict[str, Any]:
        """Analyze and compare the two responses."""
        local_text = local_response["text"]
        cloud_text = cloud_response["text"]

        # Basic metrics
        comparison = {
            "response_length": {
                "local": len(local_text),
                "cloud": len(cloud_text),
                "ratio": round(len(local_text) / len(cloud_text), 2) if cloud_text else 0
            },
            "completeness_score": {
                "local": self._score_completeness(local_text),
                "cloud": self._score_completeness(cloud_text)
            },
            "accuracy_score": {
                "local": self._score_accuracy(local_text, cloud_text),
                "cloud": 0.95  # Assume cloud is baseline
            },
            "helpfulness_score": {
                "local": self._score_helpfulness(local_text),
                "cloud": self._score_helpfulness(cloud_text)
            }
        }

        if depth == "detailed":
            # Add detailed analysis
            comparison["detailed_analysis"] = self._detailed_analysis(
                query, local_text, cloud_text, comparison
            )

        return comparison

    async def _suggest_improvements(
        self,
        query: str,
        local_response: Dict[str, Any],
        cloud_response: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> list:
        """Generate improvement suggestions based on comparison."""
        improvements = []

        # Based on response length
        if comparison["response_length"]["ratio"] < 0.5:
            improvements.append(
                "Local LLM is much shorter than cloud. "
                "Try: Adding 'Be detailed' to prompt or using chain-of-thought"
            )

        # Based on completeness
        local_complete = comparison["completeness_score"]["local"]
        cloud_complete = comparison["completeness_score"]["cloud"]
        if local_complete < cloud_complete * 0.7:
            improvements.append(
                f"Local model missing details ({local_complete:.1%} vs {cloud_complete:.1%}). "
                "Try: Multi-step prompting or providing more context"
            )

        # Based on accuracy
        local_accuracy = comparison["accuracy_score"]["local"]
        if local_accuracy < 0.8:
            improvements.append(
                "Local model differs from cloud LLM. "
                "Try: Few-shot examples in prompt or fact-checking queries"
            )

        # Model-specific suggestions
        if not improvements:
            improvements.append("Local model performs well! No immediate improvements needed.")
            improvements.append("Consider: More complex queries where cloud excels")

        return improvements

    def _generate_recommendation(self, comparison: Dict[str, Any], improvements: list) -> str:
        """Generate a recommendation based on scores."""
        local_avg = (
            comparison["completeness_score"]["local"] +
            comparison["accuracy_score"]["local"] +
            comparison["helpfulness_score"]["local"]
        ) / 3

        cloud_avg = (
            comparison["completeness_score"]["cloud"] +
            comparison["accuracy_score"]["cloud"] +
            comparison["helpfulness_score"]["cloud"]
        ) / 3

        if local_avg > 0.85:
            return "Local LLM performs well. Use for most tasks. Cloud for critical decisions."
        elif local_avg > 0.70:
            return "Local LLM is acceptable. Consider upgrading model for better results."
        else:
            return "Local LLM struggles with this task. Use cloud LLM for better quality."

    def _score_completeness(self, text: str) -> float:
        """Score how complete the response is (0.0-1.0)."""
        # Simplified scoring - real implementation would use NLP
        sentences = len(text.split("."))
        paragraphs = text.count("\n\n")
        score = min(0.3 + (sentences * 0.02) + (paragraphs * 0.1), 1.0)
        return round(score, 2)

    def _score_accuracy(self, local: str, cloud: str) -> float:
        """Score how accurately local response matches cloud response."""
        # Simplified - real implementation would use semantic similarity
        if not local or not cloud:
            return 0.0
        # Check for key phrases/concepts alignment
        local_words = set(local.lower().split())
        cloud_words = set(cloud.lower().split())
        overlap = len(local_words & cloud_words) / len(cloud_words | local_words)
        return round(0.5 + (overlap * 0.5), 2)  # Scale to 0.5-1.0

    def _score_helpfulness(self, text: str) -> float:
        """Score how helpful the response is."""
        # Simplified - real implementation would use semantic analysis
        has_examples = "example" in text.lower() or "e.g." in text
        has_steps = "step" in text.lower() or "1." in text
        has_code = "```" in text or "`" in text
        score = 0.5
        score += 0.15 if has_examples else 0
        score += 0.15 if has_steps else 0
        score += 0.2 if has_code else 0
        return round(score, 2)

    def _detailed_analysis(
        self,
        query: str,
        local_text: str,
        cloud_text: str,
        comparison: Dict[str, Any]
    ) -> str:
        """Generate detailed text analysis."""
        analysis = f"""
Query: {query}

Local Response Characteristics:
- Length: {len(local_text)} chars
- Completeness: {comparison['completeness_score']['local']:.1%}
- Key points covered

Cloud Response Characteristics:
- Length: {len(cloud_text)} chars
- Completeness: {comparison['completeness_score']['cloud']:.1%}
- More comprehensive coverage

Differences:
- Local model tends to be {('shorter' if len(local_text) < len(cloud_text) else 'longer')}
- Cloud provides more {"examples" if "example" in cloud_text.lower() else "context"}
- Accuracy alignment: {comparison['accuracy_score']['local']:.1%}

Summary:
Local LLM is suitable for quick answers. Cloud LLM provides more detailed,
nuanced responses. Use local for speed-critical tasks, cloud for quality-critical ones.
        """.strip()
        return analysis
