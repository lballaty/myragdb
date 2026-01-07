# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/report_skill.py
# Description: Skill for generating formatted reports from search results
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import json
from typing import Any, Dict, List, Optional

from myragdb.agent.skills.base import Skill, SkillExecutionError


class ReportSkill(Skill):
    """
    Skill for generating formatted reports from search results and analysis data.

    Business Purpose: Enable agents to produce structured, human-readable reports
    from search results and analysis outputs. Supports multiple formats (markdown,
    JSON, plain text) for different consumption contexts.

    Input Schema:
    {
        "title": {
            "type": "string",
            "required": True,
            "description": "Report title"
        },
        "content": {
            "type": "array",
            "required": True,
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string"},
                    "data": {"type": "object"}
                }
            },
            "description": "Report sections with data"
        },
        "format": {
            "type": "string",
            "required": False,
            "default": "markdown",
            "enum": ["markdown", "json", "text"],
            "description": "Output format"
        },
        "include_metadata": {
            "type": "boolean",
            "required": False,
            "default": True,
            "description": "Include report metadata (timestamp, etc.)"
        }
    }

    Output Schema:
    {
        "report": {
            "type": "string",
            "description": "Formatted report content"
        },
        "format": {
            "type": "string",
            "description": "Report format used"
        },
        "sections": {
            "type": "integer",
            "description": "Number of sections in report"
        }
    }

    Example:
        skill = ReportSkill()
        result = await skill.execute({
            "title": "Authentication Implementation Review",
            "content": [
                {
                    "section": "Summary",
                    "data": {"text": "Found 15 authentication implementations..."}
                },
                {
                    "section": "Findings",
                    "data": {"items": ["Inconsistent token validation", "Missing error handling"]}
                }
            ],
            "format": "markdown"
        })
        print(result["report"])  # Formatted markdown report
    """

    def __init__(self):
        """Initialize ReportSkill."""
        super().__init__(
            name="report",
            description="Generate formatted reports from search results and analysis"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define input schema for report skill."""
        return {
            "title": {
                "type": "string",
                "required": True,
                "description": "Report title"
            },
            "content": {
                "type": "array",
                "required": True,
                "items": {
                    "type": "object",
                    "properties": {
                        "section": {"type": "string"},
                        "data": {"type": "object"}
                    }
                },
                "description": "Report sections with data"
            },
            "format": {
                "type": "string",
                "required": False,
                "default": "markdown",
                "enum": ["markdown", "json", "text"],
                "description": "Output format"
            },
            "include_metadata": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Include report metadata (timestamp, etc.)"
            }
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        """Define output schema for report skill."""
        return {
            "report": {
                "type": "string",
                "description": "Formatted report content"
            },
            "format": {
                "type": "string",
                "description": "Report format used"
            },
            "sections": {
                "type": "integer",
                "description": "Number of sections in report"
            }
        }

    @property
    def required_config(self) -> List[str]:
        """Report generation requires no external configuration."""
        return []

    def _format_markdown(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        include_metadata: bool
    ) -> str:
        """
        Format report as Markdown.

        Args:
            title: Report title
            sections: Report sections
            include_metadata: Whether to include metadata

        Returns:
            Formatted markdown report
        """
        lines = [f"# {title}\n"]

        if include_metadata:
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat()
            lines.append(f"**Generated:** {timestamp}\n")

        for section in sections:
            section_name = section.get("section", "Section")
            lines.append(f"## {section_name}\n")

            data = section.get("data", {})

            # Handle text data
            if "text" in data:
                lines.append(f"{data['text']}\n")

            # Handle items list
            if "items" in data:
                items = data["items"]
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            for key, value in item.items():
                                lines.append(f"- **{key}:** {value}")
                        else:
                            lines.append(f"- {item}")
                    lines.append("")

            # Handle key-value pairs
            if "pairs" in data:
                pairs = data["pairs"]
                if isinstance(pairs, dict):
                    for key, value in pairs.items():
                        lines.append(f"- **{key}:** {value}")
                    lines.append("")

            # Handle search results
            if "results" in data:
                results = data["results"]
                if isinstance(results, list):
                    for result in results:
                        if isinstance(result, dict):
                            path = result.get("file_path", "unknown")
                            repo = result.get("repository", "")
                            score = result.get("score", 0)
                            snippet = result.get("snippet", "")[:100]
                            lines.append(f"- [{path}]({path}) ({repo}) - Score: {score:.2f}")
                            if snippet:
                                lines.append(f"  > {snippet}...")
                        else:
                            lines.append(f"- {result}")
                    lines.append("")

        return "\n".join(lines)

    def _format_json(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        include_metadata: bool
    ) -> str:
        """
        Format report as JSON.

        Args:
            title: Report title
            sections: Report sections
            include_metadata: Whether to include metadata

        Returns:
            Formatted JSON report
        """
        report: Dict[str, Any] = {
            "title": title,
            "sections": sections
        }

        if include_metadata:
            from datetime import datetime
            report["generated"] = datetime.utcnow().isoformat()

        return json.dumps(report, indent=2)

    def _format_text(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        include_metadata: bool
    ) -> str:
        """
        Format report as plain text.

        Args:
            title: Report title
            sections: Report sections
            include_metadata: Whether to include metadata

        Returns:
            Formatted plain text report
        """
        lines = [title]
        lines.append("=" * len(title))
        lines.append("")

        if include_metadata:
            from datetime import datetime
            lines.append(f"Generated: {datetime.utcnow().isoformat()}")
            lines.append("")

        for section in sections:
            section_name = section.get("section", "Section")
            lines.append(section_name)
            lines.append("-" * len(section_name))

            data = section.get("data", {})

            # Handle text data
            if "text" in data:
                lines.append(data["text"])

            # Handle items list
            if "items" in data:
                items = data["items"]
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            for key, value in item.items():
                                lines.append(f"  {key}: {value}")
                        else:
                            lines.append(f"  - {item}")

            # Handle key-value pairs
            if "pairs" in data:
                pairs = data["pairs"]
                if isinstance(pairs, dict):
                    for key, value in pairs.items():
                        lines.append(f"  {key}: {value}")

            # Handle search results
            if "results" in data:
                results = data["results"]
                if isinstance(results, list):
                    for result in results:
                        if isinstance(result, dict):
                            path = result.get("file_path", "unknown")
                            score = result.get("score", 0)
                            lines.append(f"  {path} (Score: {score:.2f})")
                        else:
                            lines.append(f"  {result}")

            lines.append("")

        return "\n".join(lines)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute report generation.

        Business Purpose: Format results from search, analysis, and reasoning
        into readable reports for human consumption.

        Args:
            input_data: Input matching input_schema

        Returns:
            Dictionary with formatted report and metadata

        Raises:
            SkillExecutionError: If report generation fails
        """
        try:
            title = input_data.get("title")
            if not title:
                raise SkillExecutionError("Title is required")

            content = input_data.get("content")
            if not content:
                raise SkillExecutionError("Content is required")

            if not isinstance(content, list):
                raise SkillExecutionError("Content must be a list of sections")

            report_format = input_data.get("format", "markdown").lower()
            include_metadata = input_data.get("include_metadata", True)

            # Generate report
            if report_format == "markdown":
                report = self._format_markdown(title, content, include_metadata)
            elif report_format == "json":
                report = self._format_json(title, content, include_metadata)
            elif report_format == "text":
                report = self._format_text(title, content, include_metadata)
            else:
                raise SkillExecutionError(f"Unsupported format: {report_format}")

            return {
                "report": report,
                "format": report_format,
                "sections": len(content)
            }

        except Exception as e:
            if isinstance(e, SkillExecutionError):
                raise
            raise SkillExecutionError(f"Report generation failed: {str(e)}")
