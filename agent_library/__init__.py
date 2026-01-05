# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/agent_library/__init__.py
# Description: Agent library for LLM integration with MyRAGDB
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

"""
Agent Library for MyRAGDB.

Provides Python client and query builder for LLMs to search codebases.

Example:
    from agent_library import SearchClient, QueryBuilder

    client = SearchClient()
    query = QueryBuilder().search("authentication").in_repository("MyApp").build()
    results = client.search(**query)
"""

from agent_library.search_client import SearchClient, SearchResult, search
from agent_library.query_builder import (
    QueryBuilder,
    find_in_code,
    find_in_docs,
    find_pattern,
    understand_concept
)

__all__ = [
    "SearchClient",
    "SearchResult",
    "search",
    "QueryBuilder",
    "find_in_code",
    "find_in_docs",
    "find_pattern",
    "understand_concept"
]
