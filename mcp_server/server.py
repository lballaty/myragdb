# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/server.py
# Description: MCP (Model Context Protocol) server for MyRAGDB
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

"""
MCP Server for MyRAGDB.

Business Purpose: Exposes MyRAGDB search capabilities through the Model Context Protocol,
making it natively accessible to Claude, Claude Code, and other MCP-compatible LLMs.

The MCP protocol allows LLMs to discover and use tools, prompts, and resources through
a standardized interface.

Example Usage:
    # Start the MCP server
    python -m mcp_server.server

    # Or use uv (if installed)
    uvx mcp_server

    # Claude Code will automatically discover the server if configured in:
    # ~/.config/claude-code/mcp_servers.json
"""

import asyncio
import sys
from typing import Any, Optional
import httpx

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)


# MyRAGDB service configuration
MYRAGDB_URL = "http://localhost:3003"  # Default MyRAGDB server
TIMEOUT = 30.0


# Initialize MCP server
app = Server("myragdb")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available tools for MCP clients.

    Business Purpose: Tells Claude what search capabilities are available.
    """
    return [
        Tool(
            name="search_codebase",
            description=(
                "Search across all indexed codebases using hybrid keyword + semantic search. "
                "Finds relevant code, documentation, and files based on natural language queries. "
                "Best for: discovering implementation patterns, finding where features are implemented, "
                "locating documentation, understanding how things work across projects."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (e.g., 'how is authentication implemented', 'JWT token validation')"
                    },
                    "repositories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Filter to specific repositories by name (e.g., ['xLLMArionComply'])"
                    },
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Filter by file extensions (e.g., ['.py', '.md', '.ts'])"
                    },
                    "folder_filter": {
                        "type": "string",
                        "description": "Optional: Filter to specific folder path (e.g., 'src/components')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 10, max: 100)",
                        "default": 10
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum relevance score 0.0-1.0 (default: 0.0)",
                        "default": 0.0
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_semantic",
            description=(
                "Semantic-only search for understanding concepts and meaning. "
                "Finds documents conceptually similar to your query even if they don't use the same keywords. "
                "Best for: understanding how a concept works, finding related implementations, "
                "discovering alternative approaches."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query describing what you want to understand (e.g., 'how do users authenticate')"
                    },
                    "repositories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Filter to specific repositories"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_keyword",
            description=(
                "Keyword-only search for exact matches. Fast and precise for finding specific code patterns, "
                "function names, class names, or exact text. "
                "Best for: finding where specific function is defined, locating exact error messages, "
                "finding configuration values."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keyword query with exact terms to match (e.g., 'def authenticate', 'class UserModel')"
                    },
                    "repositories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Filter to specific repositories"
                    },
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Filter by file extensions"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_index_stats",
            description=(
                "Get statistics about indexed repositories and documents. "
                "Shows what codebases are available, how many files are indexed, and index health."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_repositories",
            description=(
                "List all available repositories that can be searched. "
                "Shows repository names, paths, and whether they are enabled."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="trigger_reindex",
            description=(
                "Trigger re-indexing of one or more repositories. "
                "Use this to update the search index after code changes. "
                "Supports incremental indexing (only re-indexes changed files)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repositories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of repository names to reindex. If empty, reindexes all enabled repositories."
                    },
                    "force_full": {
                        "type": "boolean",
                        "description": "Force full reindex instead of incremental (default: false)",
                        "default": False
                    },
                    "index_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["keyword", "vector", "both"]},
                        "description": "Which indexes to rebuild: 'keyword', 'vector', or 'both' (default: ['both'])",
                        "default": ["both"]
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="discover_repositories",
            description=(
                "Scan filesystem for new Git repositories. "
                "Discovers repositories under a specified path that aren't yet indexed. "
                "Useful for finding new projects to add to the search index."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root_path": {
                        "type": "string",
                        "description": "Base directory to scan for repositories (e.g., '/Users/username/Projects')"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum directory depth to search (default: 3)",
                        "default": 3
                    }
                },
                "required": ["root_path"]
            }
        ),
        Tool(
            name="add_repositories",
            description=(
                "Add new repositories to the search index. "
                "Takes a list of repository paths and adds them to the configuration, "
                "then starts indexing them."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repository_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of absolute paths to Git repositories to add"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Priority level for these repositories (affects search ranking)",
                        "default": "medium"
                    }
                },
                "required": ["repository_paths"]
            }
        ),
        Tool(
            name="enable_repository",
            description=(
                "Enable a disabled/locked repository. "
                "Unlocked repositories will be included in searches and can be re-indexed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "Name of repository to enable"
                    }
                },
                "required": ["repository_name"]
            }
        ),
        Tool(
            name="disable_repository",
            description=(
                "Disable/lock a repository. "
                "Disabled repositories are excluded from searches and won't be re-indexed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "Name of repository to disable"
                    }
                },
                "required": ["repository_name"]
            }
        ),
        Tool(
            name="remove_repository",
            description=(
                "Remove a repository from the search index. "
                "Removes it from configuration and deletes its indexed data. "
                "Does NOT delete the repository files themselves."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "Name of repository to remove"
                    }
                },
                "required": ["repository_name"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Execute tool calls from MCP clients.

    Business Purpose: Handles actual search requests from Claude and returns results.
    """

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            if name == "search_codebase":
                return await _search_hybrid(client, arguments)

            elif name == "search_semantic":
                return await _search_semantic(client, arguments)

            elif name == "search_keyword":
                return await _search_keyword(client, arguments)

            elif name == "get_index_stats":
                return await _get_stats(client)

            elif name == "list_repositories":
                return await _list_repositories(client)

            elif name == "trigger_reindex":
                return await _trigger_reindex(client, arguments)

            elif name == "discover_repositories":
                return await _discover_repositories(client, arguments)

            elif name == "add_repositories":
                return await _add_repositories(client, arguments)

            elif name == "enable_repository":
                return await _enable_repository(client, arguments)

            elif name == "disable_repository":
                return await _disable_repository(client, arguments)

            elif name == "remove_repository":
                return await _remove_repository(client, arguments)

            else:
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]

        except httpx.HTTPError as e:
            return [TextContent(
                type="text",
                text=f"Error calling MyRAGDB: {str(e)}\n\nIs the MyRAGDB server running? Start with: python -m myragdb.api.server"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Unexpected error: {str(e)}"
            )]


async def _search_hybrid(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Execute hybrid search."""
    payload = {
        "query": args["query"],
        "limit": args.get("limit", 10),
        "min_score": args.get("min_score", 0.0)
    }

    if "repositories" in args:
        payload["repositories"] = args["repositories"]
    if "file_types" in args:
        payload["file_types"] = args["file_types"]
    if "folder_filter" in args:
        payload["folder_filter"] = args["folder_filter"]

    response = await client.post(f"{MYRAGDB_URL}/search/hybrid", json=payload)
    response.raise_for_status()
    data = response.json()

    return _format_search_results(data, "Hybrid")


async def _search_semantic(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Execute semantic search."""
    payload = {
        "query": args["query"],
        "limit": args.get("limit", 10)
    }

    if "repositories" in args:
        payload["repositories"] = args["repositories"]

    response = await client.post(f"{MYRAGDB_URL}/search/semantic", json=payload)
    response.raise_for_status()
    data = response.json()

    return _format_search_results(data, "Semantic")


async def _search_keyword(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Execute keyword search."""
    payload = {
        "query": args["query"],
        "limit": args.get("limit", 10)
    }

    if "repositories" in args:
        payload["repositories"] = args["repositories"]
    if "file_types" in args:
        payload["file_types"] = args["file_types"]

    response = await client.post(f"{MYRAGDB_URL}/search/keyword", json=payload)
    response.raise_for_status()
    data = response.json()

    return _format_search_results(data, "Keyword")


async def _get_stats(client: httpx.AsyncClient) -> list[TextContent]:
    """Get index statistics."""
    response = await client.get(f"{MYRAGDB_URL}/stats")
    response.raise_for_status()
    data = response.json()

    output = "# MyRAGDB Index Statistics\n\n"
    output += f"**Keyword Documents:** {data.get('keyword_documents', 0):,}\n"
    output += f"**Vector Chunks:** {data.get('vector_chunks', 0):,}\n"
    output += f"**Repositories:** {data.get('repositories', 0)}\n"
    output += f"**Status:** {data.get('status', 'unknown')}\n"

    if "repositories_detail" in data:
        output += "\n## Repositories:\n"
        for repo in data["repositories_detail"]:
            output += f"- **{repo['name']}**: {repo.get('file_count', 0):,} files\n"

    return [TextContent(type="text", text=output)]


async def _list_repositories(client: httpx.AsyncClient) -> list[TextContent]:
    """List all repositories."""
    response = await client.get(f"{MYRAGDB_URL}/repositories")
    response.raise_for_status()
    repos = response.json()

    output = "# Available Repositories\n\n"

    for repo in repos:
        status = "✓ Enabled" if repo.get("enabled", False) else "✗ Disabled"
        if repo.get("excluded", False):
            status = "🔒 Locked"

        output += f"## {repo['name']}\n"
        output += f"- **Path:** {repo['path']}\n"
        output += f"- **Status:** {status}\n"
        output += f"- **Priority:** {repo.get('priority', 'medium')}\n"

        if "file_count" in repo:
            output += f"- **Files:** {repo['file_count']:,}\n"

        output += "\n"

    return [TextContent(type="text", text=output)]


async def _trigger_reindex(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Trigger repository reindexing."""
    payload = {
        "repositories": args.get("repositories", []),
        "force_full": args.get("force_full", False),
        "index_types": args.get("index_types", ["both"])
    }

    response = await client.post(f"{MYRAGDB_URL}/reindex", json=payload)
    response.raise_for_status()
    data = response.json()

    output = "# Reindex Started\n\n"
    output += f"**Status:** {data.get('status', 'unknown')}\n"
    output += f"**Message:** {data.get('message', '')}\n\n"

    repos = args.get("repositories", [])
    if repos:
        output += f"**Repositories:** {', '.join(repos)}\n"
    else:
        output += "**Repositories:** All enabled repositories\n"

    output += f"**Mode:** {'Full reindex' if args.get('force_full') else 'Incremental (changed files only)'}\n"
    output += f"**Indexes:** {', '.join(args.get('index_types', ['both']))}\n\n"

    output += "The indexing process is running in the background. "
    output += "Use `get_index_stats` to check progress.\n"

    return [TextContent(type="text", text=output)]


async def _discover_repositories(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Discover new repositories."""
    payload = {
        "root_path": args["root_path"],
        "max_depth": args.get("max_depth", 3)
    }

    response = await client.post(f"{MYRAGDB_URL}/repositories/discover", json=payload)
    response.raise_for_status()
    data = response.json()

    discovered = data.get("repositories_found", [])
    count = len(discovered)

    output = f"# Repository Discovery: {args['root_path']}\n\n"
    output += f"Found {count} repository/repositories\n\n"

    if count == 0:
        output += "No new repositories found in this path.\n"
        return [TextContent(type="text", text=output)]

    for repo in discovered:
        is_new = repo.get("is_new", True)
        status = "🆕 New" if is_new else "✓ Already indexed"

        output += f"## {repo['name']}\n"
        output += f"**Path:** {repo['path']}\n"
        output += f"**Status:** {status}\n"

        if "file_count" in repo:
            output += f"**Files:** {repo['file_count']:,}\n"

        output += "\n"

    output += "\n**Next Steps:**\n"
    output += "- Use `add_repositories` tool to add new repositories to the index\n"
    output += "- Provide the repository paths from above\n"

    return [TextContent(type="text", text=output)]


async def _add_repositories(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Add new repositories."""
    payload = {
        "repositories": [
            {"path": path, "priority": args.get("priority", "medium")}
            for path in args["repository_paths"]
        ]
    }

    response = await client.post(f"{MYRAGDB_URL}/repositories/add-batch", json=payload)
    response.raise_for_status()
    data = response.json()

    added = data.get("added", [])
    failed = data.get("failed", [])

    output = "# Add Repositories\n\n"

    if added:
        output += f"**✓ Successfully added {len(added)} repository/repositories:**\n\n"
        for repo in added:
            output += f"- {repo['name']} ({repo['path']})\n"
        output += "\n"

    if failed:
        output += f"**✗ Failed to add {len(failed)} repository/repositories:**\n\n"
        for item in failed:
            output += f"- {item['path']}: {item.get('error', 'Unknown error')}\n"
        output += "\n"

    if added:
        output += "**Next Steps:**\n"
        output += "- Repositories have been added to configuration\n"
        output += "- Use `trigger_reindex` to start indexing them\n"

    return [TextContent(type="text", text=output)]


async def _enable_repository(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Enable a repository."""
    repo_name = args["repository_name"]

    response = await client.patch(
        f"{MYRAGDB_URL}/repositories/{repo_name}",
        json={"excluded": False}
    )
    response.raise_for_status()
    data = response.json()

    output = f"# Enable Repository\n\n"
    output += f"**✓ Repository '{repo_name}' has been enabled**\n\n"
    output += "This repository will now:\n"
    output += "- Be included in search results\n"
    output += "- Be available for re-indexing\n\n"
    output += "Use `trigger_reindex` to update its index if needed.\n"

    return [TextContent(type="text", text=output)]


async def _disable_repository(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Disable a repository."""
    repo_name = args["repository_name"]

    response = await client.patch(
        f"{MYRAGDB_URL}/repositories/{repo_name}",
        json={"excluded": True}
    )
    response.raise_for_status()
    data = response.json()

    output = f"# Disable Repository\n\n"
    output += f"**🔒 Repository '{repo_name}' has been disabled**\n\n"
    output += "This repository will now:\n"
    output += "- Be excluded from search results\n"
    output += "- Not be re-indexed automatically\n\n"
    output += "Its data remains in the index but won't be returned in searches.\n"

    return [TextContent(type="text", text=output)]


async def _remove_repository(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    """Remove a repository."""
    repo_name = args["repository_name"]

    response = await client.delete(f"{MYRAGDB_URL}/repositories/{repo_name}")
    response.raise_for_status()
    data = response.json()

    output = f"# Remove Repository\n\n"
    output += f"**✓ Repository '{repo_name}' has been removed**\n\n"
    output += "Actions taken:\n"
    output += "- Removed from configuration\n"
    output += "- Deleted from search indexes\n"
    output += "- Cleared metadata\n\n"
    output += "**Note:** The repository files on disk were NOT deleted.\n"

    return [TextContent(type="text", text=output)]


def _format_search_results(data: dict, search_type: str) -> list[TextContent]:
    """Format search results for MCP response."""
    results = data.get("results", [])
    query = data.get("query", "")
    count = len(results)

    if count == 0:
        return [TextContent(
            type="text",
            text=f"# {search_type} Search: '{query}'\n\nNo results found."
        )]

    output = f"# {search_type} Search: '{query}'\n\n"
    output += f"Found {count} result(s)\n\n"

    # Detect if query is asking for directories
    query_lower = query.lower()
    is_directory_query = any(keyword in query_lower for keyword in [
        'director', 'folder', 'path', 'locate all', 'find all', 'list all'
    ])

    # If asking for directories, show unique directories first
    if is_directory_query:
        from pathlib import Path
        directories = {}
        for result in results:
            file_path = result.get('file_path', '')
            if file_path:
                dir_path = str(Path(file_path).parent)
                if dir_path not in directories:
                    directories[dir_path] = {
                        'files': [],
                        'repository': result.get('repository', ''),
                        'relative_dir': str(Path(result.get('relative_path', '')).parent)
                    }
                directories[dir_path]['files'].append(result)

        output += f"## Directories Found ({len(directories)})\n\n"
        for dir_path, info in sorted(directories.items())[:10]:
            rel_dir = info['relative_dir']
            file_count = len(info['files'])
            repo = info['repository']
            output += f"- **{rel_dir}** ({repo}) - {file_count} file(s)\n"
            output += f"  - Full path: `{dir_path}`\n"

        output += "\n---\n\n"

    # Show detailed file results
    output += "## Detailed Results\n\n"
    for i, result in enumerate(results, 1):
        output += f"### {i}. {result['relative_path']}\n\n"
        output += f"**Repository:** {result['repository']}\n"
        output += f"**Score:** {result['score']:.3f}\n"
        output += f"**Type:** {result['file_type']}\n"

        if "keyword_score" in result and result["keyword_score"] is not None:
            output += f"**Keyword Score:** {result['keyword_score']:.3f}\n"
        if "vector_score" in result and result["vector_score"] is not None:
            output += f"**Vector Score:** {result['vector_score']:.3f}\n"

        output += f"\n**Snippet:**\n```\n{result['snippet']}\n```\n\n"
        output += f"**Full Path:** `{result['file_path']}`\n\n"
        output += "---\n\n"

    return [TextContent(type="text", text=output)]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
