# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/code_analysis_skill.py
# Description: Skill for analyzing code structure, dependencies, and patterns
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import ast
import re
from typing import Any, Dict, List, Optional

from myragdb.agent.skills.base import Skill, SkillExecutionError


class CodeAnalysisSkill(Skill):
    """
    Skill for analyzing code structure, extracting definitions, and finding patterns.

    Business Purpose: Enable agents to understand code organization by extracting
    function/class definitions, imports, and structural patterns without needing
    to parse raw code themselves. Supports multiple programming languages through
    regex-based extraction.

    Input Schema:
    {
        "code": {
            "type": "string",
            "required": True,
            "description": "Source code to analyze"
        },
        "language": {
            "type": "string",
            "required": False,
            "default": "python",
            "enum": ["python", "javascript", "typescript", "java", "go", "rust"],
            "description": "Programming language of the code"
        },
        "analysis_type": {
            "type": "string",
            "required": False,
            "default": "structure",
            "enum": ["structure", "imports", "functions", "classes", "patterns"],
            "description": "Type of analysis to perform"
        }
    }

    Output Schema:
    {
        "analysis_type": {
            "type": "string",
            "description": "Type of analysis performed"
        },
        "language": {
            "type": "string",
            "description": "Language of analyzed code"
        },
        "structures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "line": {"type": "integer"},
                    "description": {"type": "string"}
                }
            },
            "description": "Found structures (functions, classes, etc.)"
        },
        "imports": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Found import statements"
        },
        "patterns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Detected code patterns"
        },
        "complexity_estimate": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "Rough complexity estimate"
        }
    }

    Example:
        skill = CodeAnalysisSkill()
        result = await skill.execute({
            "code": "def authenticate(token):\n    return validate_token(token)",
            "language": "python",
            "analysis_type": "structure"
        })
        print(result["structures"])  # [{"name": "authenticate", "type": "function", ...}]
    """

    def __init__(self):
        """Initialize CodeAnalysisSkill."""
        super().__init__(
            name="code_analysis",
            description="Analyze code structure, dependencies, and patterns"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define input schema for code analysis skill."""
        return {
            "code": {
                "type": "string",
                "required": True,
                "description": "Source code to analyze"
            },
            "language": {
                "type": "string",
                "required": False,
                "default": "python",
                "enum": ["python", "javascript", "typescript", "java", "go", "rust"],
                "description": "Programming language of the code"
            },
            "analysis_type": {
                "type": "string",
                "required": False,
                "default": "structure",
                "enum": ["structure", "imports", "functions", "classes", "patterns"],
                "description": "Type of analysis to perform"
            }
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        """Define output schema for code analysis skill."""
        return {
            "analysis_type": {
                "type": "string",
                "description": "Type of analysis performed"
            },
            "language": {
                "type": "string",
                "description": "Language of analyzed code"
            },
            "structures": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "line": {"type": "integer"},
                        "description": {"type": "string"}
                    }
                },
                "description": "Found structures (functions, classes, etc.)"
            },
            "imports": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Found import statements"
            },
            "patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Detected code patterns"
            },
            "complexity_estimate": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Rough complexity estimate"
            }
        }

    @property
    def required_config(self) -> List[str]:
        """Code analysis requires no external configuration."""
        return []

    def _analyze_python(self, code: str) -> Dict[str, Any]:
        """
        Analyze Python code structure using AST.

        Args:
            code: Python source code

        Returns:
            Dictionary with analysis results
        """
        structures: List[Dict[str, Any]] = []
        imports: List[str] = []
        patterns: List[str] = []

        try:
            tree = ast.parse(code)

            # Extract top-level definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    structures.append({
                        "name": node.name,
                        "type": "function",
                        "line": node.lineno,
                        "description": ast.get_docstring(node) or ""
                    })
                elif isinstance(node, ast.AsyncFunctionDef):
                    structures.append({
                        "name": node.name,
                        "type": "async_function",
                        "line": node.lineno,
                        "description": ast.get_docstring(node) or ""
                    })
                elif isinstance(node, ast.ClassDef):
                    structures.append({
                        "name": node.name,
                        "type": "class",
                        "line": node.lineno,
                        "description": ast.get_docstring(node) or ""
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")

            # Detect patterns
            if "async def" in code:
                patterns.append("async_programming")
            if "class " in code and "@dataclass" in code:
                patterns.append("dataclass_pattern")
            if "try:" in code and "except" in code:
                patterns.append("exception_handling")
            if "with " in code:
                patterns.append("context_managers")
            if "lambda" in code:
                patterns.append("functional_programming")

            # Estimate complexity
            complexity = "low"
            if len(structures) > 10:
                complexity = "high"
            elif len(structures) > 5:
                complexity = "medium"

            return {
                "structures": structures,
                "imports": imports,
                "patterns": patterns,
                "complexity": complexity
            }

        except SyntaxError as e:
            raise SkillExecutionError(f"Python syntax error: {str(e)}")

    def _analyze_javascript_typescript(self, code: str) -> Dict[str, Any]:
        """
        Analyze JavaScript/TypeScript code using regex patterns.

        Args:
            code: JavaScript/TypeScript source code

        Returns:
            Dictionary with analysis results
        """
        structures: List[Dict[str, Any]] = []
        imports: List[str] = []
        patterns: List[str] = []

        # Function declarations
        func_pattern = r"(?:async\s+)?function\s+(\w+)\s*\("
        for match in re.finditer(func_pattern, code):
            line_num = code[:match.start()].count('\n') + 1
            structures.append({
                "name": match.group(1),
                "type": "function",
                "line": line_num,
                "description": ""
            })

        # Arrow functions (simplified)
        arrow_pattern = r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"
        for match in re.finditer(arrow_pattern, code):
            line_num = code[:match.start()].count('\n') + 1
            structures.append({
                "name": match.group(1),
                "type": "arrow_function",
                "line": line_num,
                "description": ""
            })

        # Class declarations
        class_pattern = r"class\s+(\w+)"
        for match in re.finditer(class_pattern, code):
            line_num = code[:match.start()].count('\n') + 1
            structures.append({
                "name": match.group(1),
                "type": "class",
                "line": line_num,
                "description": ""
            })

        # Import statements
        import_pattern = r"^import\s+.*from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(import_pattern, code, re.MULTILINE):
            imports.append(f"import from {match.group(1)}")

        require_pattern = r"(?:const|let|var)\s+\{?(\w+)\}?\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        for match in re.finditer(require_pattern, code):
            imports.append(f"require {match.group(2)}")

        # Detect patterns
        if "async" in code:
            patterns.append("async_programming")
        if "Promise" in code:
            patterns.append("promise_based")
        if "try" in code and "catch" in code:
            patterns.append("exception_handling")
        if "map(" in code or "filter(" in code or "reduce(" in code:
            patterns.append("functional_programming")
        if "class " in code:
            patterns.append("oop_pattern")

        # Estimate complexity
        complexity = "low"
        if len(structures) > 10:
            complexity = "high"
        elif len(structures) > 5:
            complexity = "medium"

        return {
            "structures": structures,
            "imports": imports,
            "patterns": patterns,
            "complexity": complexity
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code analysis.

        Business Purpose: Extract code structure and patterns to help agents
        understand code organization without manual parsing.

        Args:
            input_data: Input matching input_schema

        Returns:
            Dictionary with code analysis results

        Raises:
            SkillExecutionError: If analysis fails
        """
        try:
            code = input_data.get("code")
            if not code:
                raise SkillExecutionError("Code is required")

            language = input_data.get("language", "python").lower()
            analysis_type = input_data.get("analysis_type", "structure")

            # Perform language-specific analysis
            if language == "python":
                analysis = self._analyze_python(code)
            elif language in ["javascript", "typescript"]:
                analysis = self._analyze_javascript_typescript(code)
            else:
                # For unsupported languages, use regex-based extraction
                analysis = self._analyze_javascript_typescript(code)

            # Filter results based on analysis type
            result: Dict[str, Any] = {
                "analysis_type": analysis_type,
                "language": language,
                "structures": analysis.get("structures", []),
                "imports": analysis.get("imports", []),
                "patterns": analysis.get("patterns", []),
                "complexity_estimate": analysis.get("complexity", "low")
            }

            if analysis_type == "functions":
                result["structures"] = [s for s in analysis["structures"] if "function" in s["type"]]
            elif analysis_type == "classes":
                result["structures"] = [s for s in analysis["structures"] if s["type"] == "class"]

            return result

        except Exception as e:
            if isinstance(e, SkillExecutionError):
                raise
            raise SkillExecutionError(f"Code analysis failed: {str(e)}")
