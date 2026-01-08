# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/__init__.py
# Description: Agent skills module
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from myragdb.agent.skills.base import Skill, SkillExecutionError, SkillInfo, SkillValidationError
from myragdb.agent.skills.registry import SkillRegistry

# Built-in skills
from myragdb.agent.skills.search_skill import SearchSkill
from myragdb.agent.skills.llm_skill import LLMSkill
from myragdb.agent.skills.code_analysis_skill import CodeAnalysisSkill
from myragdb.agent.skills.report_skill import ReportSkill
from myragdb.agent.skills.sql_skill import SQLSkill

# Advanced skills (conditionally imported to handle missing dependencies)
try:
    from myragdb.agent.skills.data_visualization_skill import DataVisualizationSkill
    _HAS_VISUALIZATION = True
except (ImportError, AttributeError):
    DataVisualizationSkill = None
    _HAS_VISUALIZATION = False

try:
    from myragdb.agent.skills.code_generation_skill import CodeGenerationSkill
    _HAS_CODE_GENERATION = True
except (ImportError, AttributeError):
    CodeGenerationSkill = None
    _HAS_CODE_GENERATION = False

try:
    from myragdb.agent.skills.slack_integration_skill import SlackIntegrationSkill
    _HAS_SLACK = True
except (ImportError, AttributeError):
    SlackIntegrationSkill = None
    _HAS_SLACK = False

try:
    from myragdb.agent.skills.webhook_integration_skill import WebhookIntegrationSkill
    _HAS_WEBHOOK = True
except (ImportError, AttributeError):
    WebhookIntegrationSkill = None
    _HAS_WEBHOOK = False

__all__ = [
    # Base
    "Skill",
    "SkillInfo",
    "SkillExecutionError",
    "SkillValidationError",
    "SkillRegistry",
    # Built-in skills
    "SearchSkill",
    "LLMSkill",
    "CodeAnalysisSkill",
    "ReportSkill",
    "SQLSkill",
]

# Add advanced skills to __all__ if they loaded successfully
if _HAS_VISUALIZATION:
    __all__.append("DataVisualizationSkill")
if _HAS_CODE_GENERATION:
    __all__.append("CodeGenerationSkill")
if _HAS_SLACK:
    __all__.append("SlackIntegrationSkill")
if _HAS_WEBHOOK:
    __all__.append("WebhookIntegrationSkill")
