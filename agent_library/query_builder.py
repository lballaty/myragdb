# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/agent_library/query_builder.py
# Description: Fluent query builder for constructing search queries programmatically
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class QueryBuilder:
    """
    Fluent query builder for MyRAGDB searches.

    Business Purpose: Provides an intuitive, chainable API for LLMs and agents
    to construct complex search queries without dealing with raw dictionaries.

    Example:
        # Simple search
        query = QueryBuilder().search("authentication").build()

        # Complex filtered search
        query = (QueryBuilder()
            .search("database migration")
            .in_repositories(["xLLMArionComply", "RepoTools"])
            .only_file_types([".py", ".sql"])
            .with_min_score(0.5)
            .limit_to(20)
            .semantic()
            .build())
    """

    _query: str = ""
    _search_type: str = "hybrid"
    _repositories: Optional[List[str]] = None
    _file_types: Optional[List[str]] = None
    _extension_filter: Optional[str] = None
    _folder_filter: Optional[str] = None
    _min_score: float = 0.0
    _limit: int = 10

    def search(self, query: str) -> 'QueryBuilder':
        """
        Set the search query.

        Args:
            query: Natural language or keyword search query

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("how to implement JWT tokens")
        """
        self._query = query
        return self

    def hybrid(self) -> 'QueryBuilder':
        """
        Use hybrid search (keyword + semantic).

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("login").hybrid()
        """
        self._search_type = "hybrid"
        return self

    def keyword(self) -> 'QueryBuilder':
        """
        Use keyword-only search (fast, exact matching).

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("def authenticate").keyword()
        """
        self._search_type = "keyword"
        return self

    def semantic(self) -> 'QueryBuilder':
        """
        Use semantic-only search (understanding meaning).

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("how users sign in").semantic()
        """
        self._search_type = "semantic"
        return self

    def in_repositories(self, repos: List[str]) -> 'QueryBuilder':
        """
        Filter to specific repositories.

        Args:
            repos: List of repository names

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("config").in_repositories(["xLLMArionComply"])
        """
        self._repositories = repos
        return self

    def in_repository(self, repo: str) -> 'QueryBuilder':
        """
        Filter to a single repository.

        Args:
            repo: Repository name

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("utils").in_repository("RepoTools")
        """
        self._repositories = [repo]
        return self

    def only_file_types(self, types: List[str]) -> 'QueryBuilder':
        """
        Filter to specific file types.

        Args:
            types: List of file extensions (e.g., [".py", ".md"])

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("migration").only_file_types([".py", ".sql"])
        """
        self._file_types = types
        return self

    def only_python(self) -> 'QueryBuilder':
        """Filter to Python files only."""
        self._file_types = [".py"]
        return self

    def only_markdown(self) -> 'QueryBuilder':
        """Filter to Markdown files only."""
        self._file_types = [".md"]
        return self

    def only_typescript(self) -> 'QueryBuilder':
        """Filter to TypeScript/JavaScript files only."""
        self._file_types = [".ts", ".tsx", ".js", ".jsx"]
        return self

    def only_documentation(self) -> 'QueryBuilder':
        """Filter to documentation files."""
        self._file_types = [".md", ".txt", ".rst", ".adoc"]
        return self

    def with_extension(self, extension: str) -> 'QueryBuilder':
        """
        Filter by file extension.

        Args:
            extension: File extension (e.g., ".py")

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("config").with_extension(".yaml")
        """
        self._extension_filter = extension
        return self

    def in_folder(self, folder: str) -> 'QueryBuilder':
        """
        Filter to specific folder path.

        Args:
            folder: Folder path (e.g., "src/components")

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("button").in_folder("src/components")
        """
        self._folder_filter = folder
        return self

    def with_min_score(self, score: float) -> 'QueryBuilder':
        """
        Set minimum relevance score threshold.

        Args:
            score: Minimum score (0.0 to 1.0)

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("auth").with_min_score(0.7)
        """
        self._min_score = max(0.0, min(1.0, score))
        return self

    def limit_to(self, limit: int) -> 'QueryBuilder':
        """
        Set maximum number of results.

        Args:
            limit: Maximum results (1-100)

        Returns:
            Self for chaining

        Example:
            QueryBuilder().search("test").limit_to(50)
        """
        self._limit = max(1, min(100, limit))
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build the final query payload.

        Returns:
            Dictionary ready to pass to SearchClient

        Example:
            query = QueryBuilder().search("login").build()
            results = client.search(**query)
        """
        if not self._query:
            raise ValueError("Query text is required. Use .search('query text')")

        payload = {
            "query": self._query,
            "search_type": self._search_type,
            "limit": self._limit,
            "min_score": self._min_score
        }

        if self._repositories:
            payload["repositories"] = self._repositories

        if self._file_types:
            payload["file_types"] = self._file_types

        if self._extension_filter:
            payload["extension_filter"] = self._extension_filter

        if self._folder_filter:
            payload["folder_filter"] = self._folder_filter

        return payload

    def to_string(self) -> str:
        """
        Get human-readable representation of query.

        Returns:
            String description of the query

        Example:
            qb = QueryBuilder().search("auth").in_repository("MyApp").only_python()
            print(qb.to_string())
            # Output: "Search: 'auth' [hybrid] in MyApp (*.py) - max 10 results"
        """
        parts = [f"Search: '{self._query}'"]
        parts.append(f"[{self._search_type}]")

        if self._repositories:
            parts.append(f"in {', '.join(self._repositories)}")

        filters = []
        if self._file_types:
            filters.append(f"*{','.join(self._file_types)}")
        if self._extension_filter:
            filters.append(f"*{self._extension_filter}")
        if self._folder_filter:
            filters.append(f"folder:{self._folder_filter}")

        if filters:
            parts.append(f"({', '.join(filters)})")

        if self._min_score > 0:
            parts.append(f"min_score≥{self._min_score}")

        parts.append(f"- max {self._limit} results")

        return " ".join(parts)

    def __str__(self) -> str:
        """String representation."""
        return self.to_string()


# Convenience factory functions for common patterns

def find_in_code(query: str) -> QueryBuilder:
    """
    Find something in code files (Python, TypeScript, etc.).

    Example:
        query = find_in_code("authentication").build()
    """
    return (QueryBuilder()
            .search(query)
            .only_file_types([".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java"]))


def find_in_docs(query: str) -> QueryBuilder:
    """
    Find something in documentation.

    Example:
        query = find_in_docs("API usage").build()
    """
    return (QueryBuilder()
            .search(query)
            .only_documentation())


def find_pattern(pattern: str) -> QueryBuilder:
    """
    Find code pattern with exact keyword matching.

    Example:
        query = find_pattern("def authenticate").build()
    """
    return (QueryBuilder()
            .search(pattern)
            .keyword())


def understand_concept(concept: str) -> QueryBuilder:
    """
    Understand a concept using semantic search.

    Example:
        query = understand_concept("how users log in").build()
    """
    return (QueryBuilder()
            .search(concept)
            .semantic())
