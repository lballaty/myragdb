# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/test_mcp.py
# Description: Test script for MCP server functionality
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

"""
Test script to verify MCP server functionality.
Tests tool discovery, API connectivity, and tool execution.
"""

import asyncio
import sys
import httpx

# Add project root to path
sys.path.insert(0, '/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb')

from mcp_server.server import app

async def test_api_connectivity():
    """Test that MyRAGDB API is accessible."""
    print("\n=== Testing API Connectivity ===")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:3003/health")
            print(f"✓ API Health: {response.json()}")

            response = await client.get("http://localhost:3003/repositories")
            repos = response.json()
            print(f"✓ Found {len(repos)} repositories")
            for i, repo in enumerate(repos):
                if i >= 3:
                    break
                print(f"  - {repo.get('name', 'Unknown')}: {repo.get('status', 'N/A')}")

            return True
    except Exception as e:
        print(f"✗ API connectivity failed: {e}")
        return False

async def test_search_tools():
    """Test search functionality through MCP."""
    print("\n=== Testing Search Tools ===")

    # Test hybrid search
    print("\n1. Testing hybrid search...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:3003/search/hybrid",
                json={
                    "query": "authentication",
                    "limit": 3
                }
            )
            result = response.json()
            results = result.get('results', [])
            print(f"✓ Hybrid search returned {len(results)} results")
            if results:
                print(f"  Top result: {results[0]['file_path']} (score: {results[0]['score']:.3f})")
    except Exception as e:
        print(f"✗ Hybrid search failed: {e}")

    # Test semantic search
    print("\n2. Testing semantic search...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:3003/search/semantic",
                json={
                    "query": "user authentication flow",
                    "limit": 3
                }
            )
            result = response.json()
            results = result.get('results', [])
            print(f"✓ Semantic search returned {len(results)} results")
    except Exception as e:
        print(f"✗ Semantic search failed: {e}")

    # Test keyword search
    print("\n3. Testing keyword search...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:3003/search/keyword",
                json={
                    "query": "authentication",
                    "limit": 3
                }
            )
            result = response.json()
            results = result.get('results', [])
            print(f"✓ Keyword search returned {len(results)} results")
    except Exception as e:
        print(f"✗ Keyword search failed: {e}")

async def test_repository_tools():
    """Test repository management functionality."""
    print("\n=== Testing Repository Management ===")

    # List repositories
    print("\n1. Testing list repositories...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:3003/repositories")
            repos = response.json()
            print(f"✓ Listed {len(repos)} repositories")

            # Show repository details
            for repo in repos:
                print(f"  - {repo.get('name', 'Unknown')}:")
                print(f"    Path: {repo.get('path', 'N/A')}")
                print(f"    Status: {repo.get('status', 'N/A')}")
                print(f"    Enabled: {repo.get('enabled', False)}")
    except Exception as e:
        print(f"✗ List repositories failed: {e}")

async def test_index_stats():
    """Test index statistics retrieval."""
    print("\n=== Testing Index Statistics ===")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:3003/stats")
            stats = response.json()
            print(f"✓ Retrieved index statistics:")
            print(f"  Total files indexed: {stats.get('total_files', 0)}")
            print(f"  Total repositories: {stats.get('total_repositories', 0)}")
            if 'repositories' in stats:
                for repo_name, repo_stats in stats['repositories'].items():
                    print(f"  {repo_name}: {repo_stats.get('file_count', 0)} files")
    except Exception as e:
        print(f"✗ Get stats failed: {e}")

async def main():
    """Run all MCP server tests."""
    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)

    # Test API connectivity first
    if not await test_api_connectivity():
        print("\n✗ Cannot proceed - MyRAGDB API is not accessible")
        print("  Make sure the API server is running:")
        print("  python -m myragdb.api.server")
        return

    # Run tests
    await test_search_tools()
    await test_repository_tools()
    await test_index_stats()

    print("\n" + "=" * 60)
    print("MCP Server Test Complete")
    print("=" * 60)
    print("\n✓ MCP server is ready for use with Claude Code, ChatGPT CLI, and Gemini CLI")
    print("\nNext steps:")
    print("1. Restart your CLI tool to load the MCP server configuration")
    print("2. Try asking: 'Search for authentication in my codebases'")
    print("3. The LLM should automatically use the search_codebase tool")

if __name__ == "__main__":
    asyncio.run(main())
