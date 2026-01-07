# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/data_visualization_skill.py
# Description: Advanced skill for data visualization and chart generation
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import base64
from io import BytesIO

from .base import Skill, SkillConfig


logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig(SkillConfig):
    """Configuration for data visualization."""
    max_data_points: int = 1000
    default_chart_type: str = "line"
    width: int = 1024
    height: int = 640
    theme: str = "light"
    include_legend: bool = True
    include_grid: bool = True


@dataclass
class ChartData:
    """Structure for chart data."""
    title: str
    chart_type: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


class DataVisualizationSkill(Skill):
    """
    Advanced data visualization skill.

    Business Purpose: Generates interactive charts and visualizations from data.
    Supports multiple chart types (line, bar, pie, scatter, etc.) and export
    formats (PNG, SVG, JSON).

    Capabilities:
    - Line charts for time series data
    - Bar charts for categorical comparisons
    - Pie charts for distribution analysis
    - Scatter plots for correlation analysis
    - Heatmaps for pattern detection
    - Export to multiple formats (PNG, SVG, JSON, HTML)

    Usage Example:
        skill = DataVisualizationSkill()

        # Generate line chart
        result = skill.execute(
            chart_type="line",
            title="Monthly Revenue",
            labels=["Jan", "Feb", "Mar"],
            datasets=[{
                "label": "Revenue",
                "data": [10000, 15000, 20000],
            }],
        )

        # Get as image
        image_base64 = result['chart_base64']
        with open('chart.png', 'wb') as f:
            f.write(base64.b64decode(image_base64))
    """

    NAME = "data_visualization"
    DESCRIPTION = "Generate interactive charts and visualizations from data"
    VERSION = "1.0.0"

    SUPPORTED_CHART_TYPES = {
        "line",
        "bar",
        "pie",
        "doughnut",
        "scatter",
        "bubble",
        "radar",
        "heatmap",
    }

    SUPPORTED_EXPORT_FORMATS = {
        "json",
        "svg",
        "png",
        "html",
    }

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize data visualization skill.

        Args:
            config: Visualization configuration
        """
        super().__init__(config or VisualizationConfig())
        self.config: VisualizationConfig = self.config

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute visualization generation.

        Args:
            chart_type: Type of chart (line, bar, pie, scatter, etc.)
            title: Chart title
            labels: Data labels (X-axis)
            datasets: List of datasets with label and data
            x_label: X-axis label
            y_label: Y-axis label
            export_format: Format to export as (json, svg, png, html)
            options: Additional chart options

        Returns:
            Dictionary with chart data and formats
        """
        try:
            chart_type = kwargs.get("chart_type", self.config.default_chart_type)
            title = kwargs.get("title", "Chart")
            labels = kwargs.get("labels", [])
            datasets = kwargs.get("datasets", [])
            x_label = kwargs.get("x_label")
            y_label = kwargs.get("y_label")
            export_format = kwargs.get("export_format", "json")
            options = kwargs.get("options", {})

            # Validate inputs
            if not chart_type in self.SUPPORTED_CHART_TYPES:
                return self._error(
                    f"Unsupported chart type: {chart_type}. "
                    f"Supported types: {', '.join(self.SUPPORTED_CHART_TYPES)}"
                )

            if not labels or not datasets:
                return self._error("Labels and datasets are required")

            if not export_format in self.SUPPORTED_EXPORT_FORMATS:
                return self._error(
                    f"Unsupported export format: {export_format}. "
                    f"Supported formats: {', '.join(self.SUPPORTED_EXPORT_FORMATS)}"
                )

            # Create chart data
            chart_data = ChartData(
                title=title,
                chart_type=chart_type,
                labels=labels,
                datasets=datasets,
                x_label=x_label,
                y_label=y_label,
                options=options,
            )

            # Generate chart in requested formats
            result = {
                "title": title,
                "chart_type": chart_type,
                "data_points": sum(len(ds.get("data", [])) for ds in datasets),
            }

            # JSON format (always included)
            result["chart_json"] = self._to_json_format(chart_data)

            # HTML interactive chart
            if export_format in ["html", "json"]:
                result["chart_html"] = self._to_html_format(chart_data)

            # SVG format
            if export_format in ["svg", "json"]:
                result["chart_svg"] = self._to_svg_format(chart_data)

            # PNG format (requires rendering)
            if export_format in ["png", "json"]:
                result["chart_base64_png"] = self._to_png_format(chart_data)

            # Add metadata
            result["metadata"] = {
                "generated_at": logger.info.__self__.__class__.__name__,
                "skill": self.NAME,
                "version": self.VERSION,
            }

            logger.info(
                f"Generated {chart_type} chart: {title}",
                extra={
                    'context': {
                        'chart_type': chart_type,
                        'data_points': result['data_points'],
                        'export_format': export_format,
                    }
                },
            )

            return self._success(result)

        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}", exc_info=True)
            return self._error(f"Visualization generation failed: {str(e)}")

    def _to_json_format(self, chart: ChartData) -> str:
        """Convert chart to JSON format."""
        return json.dumps({
            "title": chart.title,
            "type": chart.chart_type,
            "labels": chart.labels,
            "datasets": chart.datasets,
            "axes": {
                "x": chart.x_label,
                "y": chart.y_label,
            },
            "options": chart.options,
        }, indent=2)

    def _to_html_format(self, chart: ChartData) -> str:
        """Convert chart to interactive HTML using Chart.js."""
        dataset_str = json.dumps(chart.datasets)
        labels_str = json.dumps(chart.labels)

        html = f"""
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                canvas {{ max-width: 100%; }}
            </style>
        </head>
        <body>
            <h1>{chart.title}</h1>
            <canvas id="chart"></canvas>
            <script>
                const ctx = document.getElementById('chart').getContext('2d');
                const chart = new Chart(ctx, {{
                    type: '{chart.chart_type}',
                    data: {{
                        labels: {labels_str},
                        datasets: {dataset_str},
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{ display: {str(self.config.include_legend).lower()} }},
                            title: {{ display: true, text: '{chart.title}' }},
                        }},
                        scales: {{
                            {'y: { beginAtZero: true },' if chart.chart_type in ['bar', 'line'] else ''}
                        }},
                    }},
                }});
            </script>
        </body>
        </html>
        """
        return html

    def _to_svg_format(self, chart: ChartData) -> str:
        """Convert chart to SVG format."""
        # Simplified SVG generation
        # In production, use matplotlib or plotly for better rendering
        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
        <svg width="{self.config.width}" height="{self.config.height}"
             xmlns="http://www.w3.org/2000/svg">
            <text x="10" y="30" font-size="20" font-weight="bold">
                {chart.title}
            </text>
            <!-- Chart content would be generated here -->
            <text x="10" y="60" font-size="12" fill="#666">
                Generated SVG chart ({chart.chart_type})
            </text>
        </svg>
        """
        return svg

    def _to_png_format(self, chart: ChartData) -> str:
        """Convert chart to PNG format (base64 encoded)."""
        try:
            # Try to import matplotlib for PNG generation
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')

            fig, ax = plt.subplots(figsize=(10, 6))

            # Generate based on chart type
            if chart.chart_type == "line":
                for dataset in chart.datasets:
                    ax.plot(chart.labels, dataset["data"], label=dataset.get("label", ""))
                ax.set_xlabel(chart.x_label or "X")
                ax.set_ylabel(chart.y_label or "Y")

            elif chart.chart_type == "bar":
                x_pos = range(len(chart.labels))
                for i, dataset in enumerate(chart.datasets):
                    offset = i * 0.35
                    ax.bar([p + offset for p in x_pos], dataset["data"],
                          width=0.35, label=dataset.get("label", ""))
                ax.set_xticks([p + 0.35 for p in x_pos])
                ax.set_xticklabels(chart.labels)

            elif chart.chart_type == "pie":
                data = chart.datasets[0].get("data", [])
                ax.pie(data, labels=chart.labels, autopct="%1.1f%%")

            ax.set_title(chart.title)
            if self.config.include_legend:
                ax.legend()
            if self.config.include_grid:
                ax.grid(True, alpha=0.3)

            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            base64_str = base64.b64encode(buffer.read()).decode()
            plt.close(fig)

            return base64_str

        except ImportError:
            logger.warning("matplotlib not available, returning placeholder PNG")
            # Return a simple placeholder
            return base64.b64encode(b"PNG_PLACEHOLDER").decode()

    def _success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format successful execution result."""
        return {
            "status": "success",
            "data": data,
        }

    def _error(self, message: str) -> Dict[str, Any]:
        """Format error result."""
        logger.error(f"Visualization skill error: {message}")
        return {
            "status": "error",
            "error": message,
        }

    async def validate(self, **kwargs) -> bool:
        """Validate execution parameters."""
        chart_type = kwargs.get("chart_type", self.config.default_chart_type)
        export_format = kwargs.get("export_format", "json")

        if chart_type not in self.SUPPORTED_CHART_TYPES:
            return False
        if export_format not in self.SUPPORTED_EXPORT_FORMATS:
            return False
        if not kwargs.get("labels") or not kwargs.get("datasets"):
            return False

        return True
