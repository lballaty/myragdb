# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/sql_skill.py
# Description: Skill for executing SQL queries against configured databases
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Any, Dict, List, Optional

from myragdb.agent.skills.base import Skill, SkillExecutionError


class SQLSkill(Skill):
    """
    Skill for executing SQL queries against configured databases.

    Business Purpose: Enable agents to query databases directly for real-time
    data retrieval, enabling combination of code search with live database
    queries for comprehensive analysis.

    Input Schema:
    {
        "query": {
            "type": "string",
            "required": True,
            "description": "SQL query to execute"
        },
        "database": {
            "type": "string",
            "required": False,
            "description": "Database name or connection string (uses default if not specified)"
        },
        "limit_rows": {
            "type": "integer",
            "required": False,
            "default": 100,
            "description": "Maximum number of rows to return"
        },
        "timeout_seconds": {
            "type": "integer",
            "required": False,
            "default": 30,
            "description": "Query timeout in seconds"
        }
    }

    Output Schema:
    {
        "rows": {
            "type": "array",
            "items": {
                "type": "object"
            },
            "description": "Query result rows"
        },
        "column_names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Result column names"
        },
        "row_count": {
            "type": "integer",
            "description": "Number of rows returned"
        },
        "execution_time_ms": {
            "type": "number",
            "description": "Query execution time in milliseconds"
        }
    }

    Example:
        skill = SQLSkill(db_connections)
        result = await skill.execute({
            "query": "SELECT * FROM users WHERE active = true LIMIT 10",
            "database": "production",
            "limit_rows": 10
        })
        print(result["rows"])  # Query results
    """

    def __init__(self, db_connections: Optional[Dict[str, Any]] = None):
        """
        Initialize SQLSkill.

        Args:
            db_connections: Optional dictionary mapping database names to
                          connection objects or configuration
        """
        super().__init__(
            name="sql",
            description="Execute SQL queries against configured databases"
        )
        self.db_connections = db_connections or {}

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define input schema for SQL skill."""
        return {
            "query": {
                "type": "string",
                "required": True,
                "description": "SQL query to execute"
            },
            "database": {
                "type": "string",
                "required": False,
                "description": "Database name or connection string (uses default if not specified)"
            },
            "limit_rows": {
                "type": "integer",
                "required": False,
                "default": 100,
                "description": "Maximum number of rows to return"
            },
            "timeout_seconds": {
                "type": "integer",
                "required": False,
                "default": 30,
                "description": "Query timeout in seconds"
            }
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        """Define output schema for SQL skill."""
        return {
            "rows": {
                "type": "array",
                "items": {
                    "type": "object"
                },
                "description": "Query result rows"
            },
            "column_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Result column names"
            },
            "row_count": {
                "type": "integer",
                "description": "Number of rows returned"
            },
            "execution_time_ms": {
                "type": "number",
                "description": "Query execution time in milliseconds"
            }
        }

    @property
    def required_config(self) -> List[str]:
        """
        List required configuration.

        Returns:
            List of required config keys for database connections
        """
        return ["database_connections"]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SQL query.

        Business Purpose: Allow agents to query live databases to combine
        code search results with real-time data for comprehensive analysis.

        Args:
            input_data: Input matching input_schema

        Returns:
            Dictionary with query results and metadata

        Raises:
            SkillExecutionError: If query execution fails or databases not configured
        """
        try:
            # Note: This is a placeholder implementation pending Phase 1C (authentication)
            # which will implement secure database connection management.
            # For now, raise informative error about missing configuration.

            if not self.db_connections:
                raise SkillExecutionError(
                    "No database connections configured. "
                    "Database connectivity requires Phase 1C (authentication) implementation."
                )

            query = input_data.get("query")
            if not query:
                raise SkillExecutionError("Query is required")

            database = input_data.get("database")
            limit_rows = input_data.get("limit_rows", 100)
            timeout_seconds = input_data.get("timeout_seconds", 30)

            # Validate query safety
            if not self._validate_query_safety(query):
                raise SkillExecutionError(
                    "Query failed safety validation. "
                    "Only SELECT queries are currently supported."
                )

            # Query execution would go here pending database integration
            # For now, return placeholder response
            raise SkillExecutionError(
                "SQL skill execution requires database connection implementation "
                "in Phase 1C. Current status: awaiting authentication framework."
            )

        except Exception as e:
            if isinstance(e, SkillExecutionError):
                raise
            raise SkillExecutionError(f"SQL execution failed: {str(e)}")

    def _validate_query_safety(self, query: str) -> bool:
        """
        Validate query for safety (prevent modification queries).

        Business Purpose: Ensure agents can only read data, not modify databases.

        Args:
            query: SQL query to validate

        Returns:
            True if query is safe to execute
        """
        query_upper = query.strip().upper()

        # Only allow SELECT queries
        if not query_upper.startswith("SELECT"):
            return False

        # Block known dangerous patterns
        dangerous_patterns = [
            "DROP ",
            "DELETE ",
            "UPDATE ",
            "INSERT ",
            "ALTER ",
            "TRUNCATE ",
            "CREATE ",
            "EXEC ",
            "EXECUTE ",
            ";DROP ",
            ";DELETE ",
            ";UPDATE ",
        ]

        for pattern in dangerous_patterns:
            if pattern in query_upper:
                return False

        return True
