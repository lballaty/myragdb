# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/search_skill.py
# Description: Skill for querying hybrid search engine across indexed repositories
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import time
from typing import Any, Dict, List, Optional

from myragdb.agent.skills.base import Skill, SkillExecutionError
from myragdb.search.hybrid_search import HybridSearchEngine, HybridSearchResult


class SearchSkill(Skill):
    """
    Skill for querying the hybrid search engine across indexed repositories.

    Business Purpose: Enable agents to discover code and documentation by
    searching across all indexed repositories using both keyword matching
    and semantic understanding. Supports filtering by repositories and
    managed directories.

    Input Schema:
    {
        "query": {
            "type": "string",
            "required": True,
            "description": "Search query (natural language or keywords)"
        },
        "limit": {
            "type": "integer",
            "required": False,
            "default": 10,
            "description": "Maximum number of results to return"
        },
        "repository_filter": {
            "type": "string",
            "required": False,
            "description": "Optional repository name to filter results"
        },
        "directories": {
            "type": "array",
            "required": False,
            "items": {"type": "integer"},
            "description": "Optional list of directory IDs to search"
        },
        "folder_filter": {
            "type": "string",
            "required": False,
            "description": "Optional folder path to filter (e.g., 'src/components')"
        },
        "extension_filter": {
            "type": "string",
            "required": False,
            "description": "Optional file extension filter (e.g., '.py', '.ts')"
        },
        "rewrite_query": {
            "type": "boolean",
            "required": False,
            "default": True,
            "description": "Whether to use LLM query rewriting for optimization"
        }
    }

    Output Schema:
    {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "repository": {"type": "string"},
                    "relative_path": {"type": "string"},
                    "score": {"type": "number"},
                    "snippet": {"type": "string"},
                    "file_type": {"type": "string"}
                }
            },
            "description": "Search results sorted by relevance"
        },
        "total_results": {
            "type": "integer",
            "description": "Number of results returned"
        },
        "search_time_ms": {
            "type": "number",
            "description": "Search duration in milliseconds"
        }
    }

    Example:
        skill = SearchSkill(hybrid_search_engine)
        result = await skill.execute({
            "query": "authentication flow",
            "limit": 10,
            "repository_filter": "xLLMArionComply"
        })
        print(result)  # Returns top 10 results matching query
    """

    def __init__(self, search_engine: HybridSearchEngine):
        """
        Initialize SearchSkill.

        Args:
            search_engine: HybridSearchEngine instance for executing searches
        """
        super().__init__(
            name="search",
            description="Query hybrid search engine across indexed repositories"
        )
        self.search_engine = search_engine

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define input schema for search skill."""
        return {
            "query": {
                "type": "string",
                "required": True,
                "description": "Search query (natural language or keywords)"
            },
            "limit": {
                "type": "integer",
                "required": False,
                "default": 10,
                "description": "Maximum number of results to return"
            },
            "repository_filter": {
                "type": "string",
                "required": False,
                "description": "Optional repository name to filter results"
            },
            "directories": {
                "type": "array",
                "required": False,
                "items": {"type": "integer"},
                "description": "Optional list of directory IDs to search"
            },
            "folder_filter": {
                "type": "string",
                "required": False,
                "description": "Optional folder path to filter (e.g., 'src/components')"
            },
            "extension_filter": {
                "type": "string",
                "required": False,
                "description": "Optional file extension filter (e.g., '.py', '.ts')"
            },
            "rewrite_query": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Whether to use LLM query rewriting for optimization"
            }
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        """Define output schema for search skill."""
        return {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "repository": {"type": "string"},
                        "relative_path": {"type": "string"},
                        "score": {"type": "number"},
                        "snippet": {"type": "string"},
                        "file_type": {"type": "string"}
                    }
                },
                "description": "Search results sorted by relevance"
            },
            "total_results": {
                "type": "integer",
                "description": "Number of results returned"
            },
            "search_time_ms": {
                "type": "number",
                "description": "Search duration in milliseconds"
            }
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute search query.

        Business Purpose: Perform hybrid search combining keyword and semantic
        matching, returning relevant results with snippets for agent context.

        Args:
            input_data: Input matching input_schema

        Returns:
            Dictionary with results, count, and search duration

        Raises:
            SkillExecutionError: If search fails
        """
        try:
            # Extract input parameters
            query = input_data.get("query")
            if not query:
                raise SkillExecutionError("Query is required")

            limit = input_data.get("limit", 10)
            repository_filter = input_data.get("repository_filter")
            directories = input_data.get("directories")
            folder_filter = input_data.get("folder_filter")
            extension_filter = input_data.get("extension_filter")
            rewrite_query = input_data.get("rewrite_query", True)

            # Execute search
            start_time = time.time()

            results: List[HybridSearchResult] = await self.search_engine.hybrid_search(
                query=query,
                limit=limit,
                rewrite_query=rewrite_query,
                repository_filter=repository_filter,
                folder_filter=folder_filter,
                extension_filter=extension_filter,
                directories=directories
            )

            search_time_ms = (time.time() - start_time) * 1000

            # Format results for agent consumption
            formatted_results = [
                {
                    "file_path": result.file_path,
                    "repository": result.repository,
                    "relative_path": result.relative_path,
                    "score": float(result.rrf_score),
                    "snippet": result.snippet,
                    "file_type": result.file_path.split(".")[-1] if "." in result.file_path else "unknown",
                    "keyword_score": float(result.keyword_score),
                    "semantic_distance": float(result.semantic_distance)
                }
                for result in results
            ]

            return {
                "results": formatted_results,
                "total_results": len(formatted_results),
                "search_time_ms": round(search_time_ms, 2)
            }

        except Exception as e:
            raise SkillExecutionError(f"Search execution failed: {str(e)}")
