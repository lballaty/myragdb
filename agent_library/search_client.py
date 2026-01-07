# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/agent_library/search_client.py
# Description: Python client library for AI agents to use MyRAGDB search
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import httpx


@dataclass
class SearchResult:
    """
    Search result from MyRAGDB.

    Business Purpose: Provides a clean, Pythonic interface to search results
    for agent code.

    Example:
        result = SearchResult(
            file_path="/path/to/file.py",
            repository="MyProject",
            score=0.89,
            snippet="def authenticate..."
        )
        print(f"Found: {result.relative_path} (score: {result.score})")
    """
    file_path: str
    repository: str
    relative_path: str
    score: float
    snippet: str
    file_type: str
    keyword_score: Optional[float] = None
    vector_score: Optional[float] = None

    def __str__(self) -> str:
        """String representation for easy display."""
        return f"{self.relative_path} ({self.repository}) - Score: {self.score:.3f}"


class SearchClient:
    """
    Client for MyRAGDB search service.

    Business Purpose: Provides simple Python API for AI agents to search
    across codebases. Handles HTTP communication and result parsing.

    Example:
        from agent_library import SearchClient

        client = SearchClient()
        results = client.search("how to authenticate users")

        for result in results:
            print(f"{result.relative_path}: {result.score}")
            print(f"  {result.snippet}")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3003",
        timeout: float = 30.0
    ):
        """
        Initialize search client.

        Args:
            base_url: URL of MyRAGDB service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "hybrid",
        repositories: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for documents.

        Business Purpose: Main search method for agents. Finds relevant
        code and documentation based on query.

        Args:
            query: Search query (natural language or keywords)
            limit: Maximum results to return
            search_type: "hybrid" (default), "keyword", or "semantic"
            repositories: Optional list of repository names to search
            file_types: Optional list of file extensions (e.g., [".py", ".md"])
            min_score: Minimum relevance score (0.0-1.0)

        Returns:
            List of SearchResult objects sorted by relevance

        Example:
            # Find authentication code
            results = client.search("JWT token validation", limit=5)

            # Search only Python files in specific repo
            results = client.search(
                "database migration",
                repositories=["xLLMArionComply"],
                file_types=[".py"]
            )

            # Semantic search
            results = client.search(
                "how do users log in",
                search_type="semantic"
            )
        """
        endpoint = f"{self.base_url}/search/{search_type}"

        payload = {
            "query": query,
            "limit": limit,
            "min_score": min_score
        }

        if repositories:
            payload["repositories"] = repositories

        if file_types:
            payload["file_types"] = file_types

        try:
            response = self.client.post(endpoint, json=payload)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data["results"]:
                result = SearchResult(
                    file_path=item["file_path"],
                    repository=item["repository"],
                    relative_path=item["relative_path"],
                    score=item["score"],
                    snippet=item["snippet"],
                    file_type=item["file_type"],
                    keyword_score=item.get("keyword_score"),
                    vector_score=item.get("vector_score")
                )
                results.append(result)

            return results

        except httpx.HTTPError as e:
            print(f"Error searching: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Business Purpose: Allows agents to check index health and size.

        Returns:
            Dictionary with statistics

        Example:
            stats = client.get_stats()
            print(f"Indexed documents: {stats['keyword_documents']}")
        """
        try:
            response = self.client.get(f"{self.base_url}/stats")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            print(f"Error getting stats: {e}")
            return {}

    def health_check(self) -> bool:
        """
        Check if service is healthy.

        Business Purpose: Allows agents to verify service is running
        before attempting searches.

        Returns:
            True if service is healthy, False otherwise

        Example:
            if client.health_check():
                results = client.search("my query")
            else:
                print("Search service is not available")
        """
        try:
            response = self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"

        except httpx.HTTPError:
            return False

    def close(self):
        """Close HTTP client connection."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function
def search(query: str, **kwargs) -> List[SearchResult]:
    """
    Quick search function for simple use cases.

    Business Purpose: Provides one-liner search for agent scripts.

    Args:
        query: Search query
        **kwargs: Additional arguments passed to SearchClient.search()

    Returns:
        List of SearchResult objects

    Example:
        from agent_library import search

        results = search("authentication flow")
        for r in results:
            print(r)
    """
    with SearchClient() as client:
        return client.search(query, **kwargs)
