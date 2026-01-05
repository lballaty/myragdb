# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/query_rewriter.py
# Description: Query rewriter using phi3 (port 8081) to optimize queries for Meilisearch and ChromaDB
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

import httpx


@dataclass
class QueryFilters:
    """
    Extracted filters from user query.

    Business Purpose: Provides structured filters for scoped search in Meilisearch,
    dramatically improving search speed by narrowing the search space before full-text search.

    Example:
        filters = QueryFilters(
            extension=[".py", ".js"],
            folder_name="src/auth"
        )
    """
    extension: List[str] = field(default_factory=list)  # File extensions (e.g., [".py", ".js"])
    folder_name: Optional[str] = None  # Specific folder name if mentioned


@dataclass
class RewrittenQuery:
    """
    Rewritten query optimized for hybrid search with extracted filters.

    Business Purpose: Transforms natural language queries into structured search format
    with clean keywords (Meilisearch), semantic intent (ChromaDB), and extracted filters
    for scoped searching.

    Example:
        original = "can you find that cleanup script in my Projects folder?"
        rewritten = RewrittenQuery(
            keywords="cleanup script",
            semantic_intent="scripts or code related to cleanup operations and maintenance tasks",
            filters=QueryFilters(extension=[".py", ".sh"], folder_name="Projects")
        )
    """
    keywords: str  # Optimized for Meilisearch (3-5 core terms, no noise)
    semantic_intent: str  # Optimized for ChromaDB (conceptual description)
    filters: QueryFilters  # Extracted filters for scoped search


class QueryRewriter:
    """
    Query rewriter using phi3 LLM (port 8081) for search optimization.

    Business Purpose: Transforms messy user queries into clean keyword and semantic
    descriptions, preventing noise words from polluting search rankings in both
    Meilisearch and ChromaDB.

    Architecture:
    - Uses phi3 on port 8081 (fast 8B model, ~1-2s response)
    - System prompt optimized for query transformation
    - Fallback to original query if LLM unavailable
    - n_ctx=32768 with Metal acceleration

    Example:
        rewriter = QueryRewriter(port=8081)

        # Messy user query
        original = "can you help me find where we handle user authentication"

        # Rewritten for search
        rewritten = await rewriter.rewrite(original)
        # keyword: "user authentication handler"
        # semantic: "code or documentation about user authentication logic and session handling"
    """

    SYSTEM_PROMPT = """You are a Search Optimization Engine. Your task is to transform a user's natural language request into a structured search schema for a dual-index (Meilisearch + ChromaDB) file system.

Output Format: You MUST return ONLY a valid JSON object. Do not include any introductory text, explanations, or markdown code blocks.

JSON Schema:
{
  "keywords": "3-5 space-separated terms for keyword matching",
  "semantic_intent": "A descriptive natural language sentence for vector search",
  "filters": {
    "extension": ["list", "of", "extensions"],
    "folder_name": "specific_folder_if_mentioned"
  }
}

Transformation Rules:

1. KEYWORDS (for Meilisearch exact matching):
   - Extract 3-5 core nouns, technical terms, or unique identifiers
   - Remove conversational fluff: "find," "where," "can you," "please," "the"
   - Keep: function names, file names, technical jargon
   - Format: space-separated terms (NOT a sentence)
   - Example: "can you find the python authentication module?" → "python authentication module"

2. SEMANTIC_INTENT (for ChromaDB vector search):
   - Expand the query into a descriptive natural language sentence
   - Add conceptual context about what type of content the user wants
   - Expand abbreviations (e.g., "auth" → "authentication")
   - Format: full sentence describing the intent
   - Example: "python auth module" → "code or documentation about Python authentication modules and user login systems"

3. FILTERS (extract from query):
   - extension: List of file extensions if mentioned (e.g., [".py", ".js", ".md"])
   - folder_name: Specific folder/directory if mentioned (e.g., "src", "Projects", "auth")
   - If not mentioned, use empty list [] for extension and null for folder_name

Examples:

Input: "Can you find that cleanup script in my Projects folder?"
Output:
{
  "keywords": "cleanup script Projects",
  "semantic_intent": "scripts or code related to cleanup operations and maintenance tasks in the Projects directory",
  "filters": {
    "extension": [".py", ".sh", ".bash"],
    "folder_name": "Projects"
  }
}

Input: "where is the JWT authentication implementation"
Output:
{
  "keywords": "JWT authentication implementation",
  "semantic_intent": "code or documentation about JWT authentication logic and token-based user authentication systems",
  "filters": {
    "extension": [],
    "folder_name": null
  }
}

Input: "find python files about database migrations"
Output:
{
  "keywords": "database migrations",
  "semantic_intent": "Python code or documentation about database schema migrations and version control",
  "filters": {
    "extension": [".py"],
    "folder_name": null
  }
}

Return ONLY the JSON object. No other text."""

    def __init__(self, host: str = "http://localhost", port: int = 8081):
        """
        Initialize query rewriter.

        Args:
            host: llama.cpp server host
            port: llama.cpp server port (default: 8081 for phi3)
        """
        self.base_url = f"{host}:{port}"
        self.completion_endpoint = f"{self.base_url}/v1/completions"

    async def rewrite(self, query: str, timeout: float = 5.0) -> RewrittenQuery:
        """
        Rewrite query for optimized hybrid search with filter extraction.

        Business Purpose: Transforms natural language queries into structured format
        with clean keywords (Meilisearch), semantic intent (ChromaDB), and extracted
        filters (extensions, folder names) for scoped searching.

        Args:
            query: Original user query (may contain noise words)
            timeout: Maximum seconds to wait for LLM response

        Returns:
            RewrittenQuery with keywords, semantic_intent, and filters

        Example:
            # Natural language query
            result = await rewriter.rewrite(
                "Can you find that cleanup script in my Projects folder?"
            )

            # Structured output
            print(result.keywords)           # "cleanup script Projects"
            print(result.semantic_intent)    # "scripts or code related to cleanup operations..."
            print(result.filters.extension)  # [".py", ".sh", ".bash"]
            print(result.filters.folder_name) # "Projects"
        """
        # Build prompt
        prompt = f"{self.SYSTEM_PROMPT}\n\nUser query: {query}\n\nJSON output:"

        # Request payload for llama.cpp
        payload = {
            "prompt": prompt,
            "temperature": 0.1,  # Low temperature for consistent output
            "max_tokens": 300,  # Increased for filter extraction
            "stop": ["\n\n", "User query:"],
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.completion_endpoint,
                    json=payload
                )
                response.raise_for_status()

                # Parse response
                data = response.json()
                completion_text = data.get("choices", [{}])[0].get("text", "")

                # Extract JSON from completion
                result = json.loads(completion_text.strip())

                # Parse filters
                filters_data = result.get("filters", {})
                filters = QueryFilters(
                    extension=filters_data.get("extension", []),
                    folder_name=filters_data.get("folder_name")
                )

                return RewrittenQuery(
                    keywords=result.get("keywords", query),  # Fallback to original
                    semantic_intent=result.get("semantic_intent", query),
                    filters=filters
                )

        except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"[QueryRewriter] Error rewriting query: {e}")
            print(f"[QueryRewriter] Falling back to original query")

            # Fallback: use original query with empty filters
            return RewrittenQuery(
                keywords=query,
                semantic_intent=query,
                filters=QueryFilters()
            )

    async def check_health(self) -> bool:
        """
        Check if phi3 model is available on port 8081.

        Returns:
            True if model is healthy and responding

        Example:
            if await rewriter.check_health():
                result = await rewriter.rewrite(query)
            else:
                print("phi3 not available, using original query")
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                # Try simple completion to verify model is loaded
                response = await client.post(
                    self.completion_endpoint,
                    json={"prompt": "test", "max_tokens": 1}
                )
                return response.status_code == 200
        except:
            return False
