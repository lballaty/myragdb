# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/test_mcp_tools.py
# Description: Test script simulating MCP tool calls for MyRAGDB
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

"""
Test script to verify MCP server tools work correctly.
Simulates how Claude Code and other LLMs would call the MCP tools.
"""

import asyncio
import sys
import httpx
import json

# Add project root to path
sys.path.insert(0, '/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb')

MYRAGDB_URL = "http://localhost:3003"
TIMEOUT = 30.0


async def test_search_codebase_tool():
    """Test the search_codebase tool (hybrid search)."""
    print("\n" + "="*60)
    print("Testing: search_codebase (Hybrid Search)")
    print("="*60)

    tool_args = {
        "query": "authentication flow JWT token",
        "limit": 5,
        "min_score": 0.0
    }

    print(f"\nTool Arguments: {json.dumps(tool_args, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{MYRAGDB_URL}/search/hybrid",
                json=tool_args
            )
            result = response.json()

            if response.status_code == 200:
                results = result.get('results', [])
                print(f"\n✓ Search successful! Found {len(results)} results")

                if results:
                    print("\nTop 3 Results:")
                    for i, res in enumerate(results[:3], 1):
                        print(f"\n{i}. {res['file_path']}")
                        print(f"   Repository: {res['repository']}")
                        print(f"   Score: {res['score']:.4f}")
                        snippet = res.get('snippet', 'N/A')
                        print(f"   Snippet: {snippet[:100]}...")
                return True
            else:
                print(f"\n✗ Search failed with status {response.status_code}")
                print(f"   Response: {result}")
                return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


async def test_search_semantic_tool():
    """Test the search_semantic tool."""
    print("\n" + "="*60)
    print("Testing: search_semantic (Semantic-Only Search)")
    print("="*60)

    tool_args = {
        "query": "how to validate user credentials and create session",
        "limit": 3
    }

    print(f"\nTool Arguments: {json.dumps(tool_args, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{MYRAGDB_URL}/search/semantic",
                json=tool_args
            )
            result = response.json()

            if response.status_code == 200:
                results = result.get('results', [])
                print(f"\n✓ Semantic search successful! Found {len(results)} results")
                return True
            else:
                print(f"\n✗ Semantic search failed")
                return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


async def test_list_repositories_tool():
    """Test the list_repositories tool."""
    print("\n" + "="*60)
    print("Testing: list_repositories")
    print("="*60)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{MYRAGDB_URL}/repositories")
            repos = response.json()

            if response.status_code == 200:
                print(f"\n✓ Found {len(repos)} repositories:")
                for repo in repos:
                    print(f"\n  - {repo.get('name', 'Unknown')}")
                    print(f"    Path: {repo.get('path', 'N/A')}")
                    print(f"    Enabled: {repo.get('enabled', False)}")
                return True
            else:
                print(f"\n✗ List repositories failed")
                return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


async def test_get_index_stats_tool():
    """Test the get_index_stats tool."""
    print("\n" + "="*60)
    print("Testing: get_index_stats")
    print("="*60)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{MYRAGDB_URL}/stats")
            stats = response.json()

            if response.status_code == 200:
                print(f"\n✓ Index Statistics:")
                print(f"   Total Files: {stats.get('total_files', 0)}")
                print(f"   Total Repos: {stats.get('total_repositories', 0)}")

                if 'repositories' in stats:
                    print("\n   Per-Repository Stats:")
                    for repo_name, repo_stats in stats['repositories'].items():
                        print(f"     {repo_name}: {repo_stats.get('file_count', 0)} files")

                return True
            else:
                print(f"\n✗ Get stats failed")
                return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


async def test_discover_repositories_tool():
    """Test the discover_repositories tool."""
    print("\n" + "="*60)
    print("Testing: discover_repositories")
    print("="*60)

    tool_args = {
        "root_path": "/Users/liborballaty/LocalProjects/GitHubProjectsDocuments",
        "max_depth": 2
    }

    print(f"\nTool Arguments: {json.dumps(tool_args, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{MYRAGDB_URL}/repositories/discover",
                json=tool_args
            )
            result = response.json()

            if response.status_code == 200:
                repos_found = result.get('repositories_found', [])
                print(f"\n✓ Discovered {len(repos_found)} repositories")
                if repos_found:
                    print("\nFirst 3 discovered:")
                    for repo in repos_found[:3]:
                        print(f"  - {repo}")
                return True
            else:
                print(f"\n✗ Discover failed: {result}")
                return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


async def test_trigger_reindex_tool():
    """Test the trigger_reindex tool."""
    print("\n" + "="*60)
    print("Testing: trigger_reindex")
    print("="*60)

    tool_args = {
        "repositories": [],  # Empty = all repos
        "full_reindex": False  # Incremental only
    }

    print(f"\nTool Arguments: {json.dumps(tool_args, indent=2)}")
    print("(This will trigger an incremental reindex of all repositories)")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{MYRAGDB_URL}/reindex",
                json=tool_args
            )
            result = response.json()

            if response.status_code == 200:
                print(f"\n✓ Reindex triggered successfully")
                print(f"   Status: {result.get('status', 'unknown')}")
                print(f"   Message: {result.get('message', 'N/A')}")
                return True
            else:
                print(f"\n✗ Reindex failed: {result}")
                return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


async def main():
    """Run all MCP tool tests."""
    print("="*60)
    print("MCP Tools Test Suite")
    print("="*60)
    print("\nTesting MyRAGDB MCP server tools as Claude Code would use them")

    results = []

    # Test each tool
    results.append(("search_codebase", await test_search_codebase_tool()))
    results.append(("search_semantic", await test_search_semantic_tool()))
    results.append(("list_repositories", await test_list_repositories_tool()))
    results.append(("get_index_stats", await test_get_index_stats_tool()))
    results.append(("discover_repositories", await test_discover_repositories_tool()))
    results.append(("trigger_reindex", await test_trigger_reindex_tool()))

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for tool_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {tool_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All MCP tools are working correctly!")
        print("\nYou can now:")
        print("1. Restart Claude Code to load the MCP server configuration")
        print("2. Ask Claude: 'Search for authentication in my codebases'")
        print("3. Claude will automatically use the search_codebase tool")
    else:
        print(f"\n✗ Some tests failed. Please review the errors above.")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
