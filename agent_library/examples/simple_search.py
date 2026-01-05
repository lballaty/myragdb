# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/agent_library/examples/simple_search.py
# Description: Example agent using MyRAGDB for code search
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

"""
Simple example showing how agents can use MyRAGDB to search code.

Business Purpose: Demonstrates basic agent integration pattern for
discovering relevant code and documentation.
"""

import sys
sys.path.insert(0, '/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb')

from agent_library.search_client import SearchClient


def main():
    """
    Example: Agent searching for authentication-related code.

    Business Purpose: Shows how an agent can discover implementation
    patterns across projects.
    """
    print("=== MyRAGDB Agent Example: Finding Authentication Code ===\n")

    # Initialize client
    client = SearchClient()

    # Check service health
    if not client.health_check():
        print("Error: MyRAGDB service is not running")
        print("Start it with: python -m myragdb.api.server")
        return

    # Example 1: Hybrid search
    print("1. Hybrid Search: 'JWT authentication'")
    print("-" * 50)
    results = client.search("JWT authentication", limit=3)

    if results:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.relative_path} ({result.repository})")
            print(f"   Score: {result.score:.3f}", end="")
            if result.keyword_score and result.vector_score:
                print(f" (Keyword: {result.keyword_score:.3f}, Vector: {result.vector_score:.3f})")
            else:
                print()
            print(f"   {result.snippet[:100]}...")
    else:
        print("No results found (index may be empty)")

    # Example 2: Semantic search
    print("\n\n2. Semantic Search: 'how do users log in'")
    print("-" * 50)
    results = client.search(
        "how do users log in",
        search_type="semantic",
        limit=3
    )

    if results:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.relative_path} ({result.repository})")
            print(f"   Score: {result.score:.3f}")
            print(f"   {result.snippet[:100]}...")
    else:
        print("No results found")

    # Example 3: Filtered search
    print("\n\n3. Filtered Search: Python files only")
    print("-" * 50)
    results = client.search(
        "database",
        file_types=[".py"],
        limit=3
    )

    if results:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.relative_path} ({result.repository})")
            print(f"   Score: {result.score:.3f}")
            print(f"   Type: {result.file_type}")
    else:
        print("No results found")

    # Show statistics
    print("\n\n=== Index Statistics ===")
    print("-" * 50)
    stats = client.get_stats()
    print(f"Keyword Documents: {stats.get('keyword_documents', 0)}")
    print(f"Vector Chunks: {stats.get('vector_chunks', 0)}")

    client.close()


if __name__ == "__main__":
    main()
