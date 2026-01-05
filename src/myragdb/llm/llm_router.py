# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/llm_router.py
# Description: LLM router for llama.cpp multi-port suite with health checks and fallback
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import httpx
from typing import Optional, Dict, Any, List
from enum import Enum


class LLMTaskType(Enum):
    """
    Task types for routing to appropriate LLM models.

    Business Purpose: Maps user intent to the best model for the job,
    optimizing for both speed and quality based on task complexity.

    Example:
        task_type = LLMTaskType.CODE_QUESTIONS
        # Routes to qwen-coder-7b on port 8085
    """
    QUERY_REWRITE = "query_rewrite"      # phi3 (port 8081) - fast query optimization
    CODE_QUESTIONS = "code_questions"     # qwen-coder-7b (port 8085) - code understanding
    FAST_SUMMARY = "fast_summary"         # hermes-3-8b (port 8086) - quick summaries
    REASONING = "reasoning"               # deepseek-r1-qwen-32b (port 8092) - complex RAG
    FALLBACK = "fallback"                 # llama-3.1-8b (port 8087) - general purpose


class LLMRouter:
    """
    LLM router for llama.cpp multi-port suite with intelligent health checking.

    Business Purpose: Routes requests to the best available model based on task type,
    with automatic fallback if primary model is unavailable. Ensures 99%+ uptime
    for RAG operations even if specific models are down.

    Architecture:
    - Port 8081: phi3 (query rewrite, fast summaries)
    - Port 8085: qwen-coder-7b (code questions)
    - Port 8086: hermes-3-8b (fast tasks)
    - Port 8087: llama-3.1-8b (fallback)
    - Port 8092: deepseek-r1-qwen-32b (complex reasoning)

    All models: n_ctx=32768, use_mmap=True, metal_enabled=True

    Example:
        router = LLMRouter()

        # Route code question to qwen-coder-7b
        response = await router.route_query(
            query="How does JWT authentication work in this codebase?",
            context=search_results,
            task_type=LLMTaskType.CODE_QUESTIONS
        )

        # If qwen-coder unavailable, automatically falls back to llama-3.1-8b
    """

    # Port mapping for each task type
    PORT_MAPPING: Dict[LLMTaskType, int] = {
        LLMTaskType.QUERY_REWRITE: 8081,      # phi3
        LLMTaskType.CODE_QUESTIONS: 8085,     # qwen-coder-7b
        LLMTaskType.FAST_SUMMARY: 8086,       # hermes-3-8b
        LLMTaskType.REASONING: 8092,          # deepseek-r1-qwen-32b
        LLMTaskType.FALLBACK: 8087,           # llama-3.1-8b
    }

    # Model names for logging
    MODEL_NAMES: Dict[int, str] = {
        8081: "phi3",
        8085: "qwen-coder-7b",
        8086: "hermes-3-8b",
        8087: "llama-3.1-8b",
        8092: "deepseek-r1-qwen-32b",
    }

    def __init__(self, host: str = "http://localhost"):
        """
        Initialize LLM router.

        Args:
            host: llama.cpp server host (default: localhost)
        """
        self.host = host
        self.health_cache: Dict[int, bool] = {}  # Cache health checks

    async def check_port_health(self, port: int, timeout: float = 2.0) -> bool:
        """
        Check if llama.cpp model is healthy on specified port.

        Business Purpose: Verifies model is loaded and responding before routing
        requests, preventing failed queries due to model unavailability.

        Args:
            port: Port number to check
            timeout: Maximum seconds to wait for response

        Returns:
            True if model is healthy and responding

        Example:
            if await router.check_port_health(8085):
                # qwen-coder-7b is ready
                response = await router.call_llm(8085, query, context)
            else:
                # Fall back to llama-3.1-8b
                response = await router.call_llm(8087, query, context)
        """
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Try simple completion to verify model is loaded
                response = await client.post(
                    f"{self.host}:{port}/v1/completions",
                    json={"prompt": "test", "max_tokens": 1}
                )
                healthy = response.status_code == 200
                self.health_cache[port] = healthy
                return healthy
        except Exception as e:
            print(f"[LLMRouter] Port {port} ({self.MODEL_NAMES.get(port, 'unknown')}) unhealthy: {e}")
            self.health_cache[port] = False
            return False

    async def get_healthy_port(self, task_type: LLMTaskType) -> int:
        """
        Get healthy port for task type with fallback logic.

        Business Purpose: Ensures request is always routed to a working model,
        even if primary model is down. Falls back to llama-3.1-8b if needed.

        Args:
            task_type: Type of task to route

        Returns:
            Port number of healthy model (primary or fallback)

        Example:
            port = await router.get_healthy_port(LLMTaskType.CODE_QUESTIONS)
            # Returns 8085 if qwen-coder healthy, else 8087 (fallback)
        """
        # Get primary port for task
        primary_port = self.PORT_MAPPING.get(task_type, self.PORT_MAPPING[LLMTaskType.FALLBACK])

        # Check if primary port is healthy
        if await self.check_port_health(primary_port):
            print(f"[LLMRouter] Routing {task_type.value} to {self.MODEL_NAMES.get(primary_port)} (port {primary_port})")
            return primary_port

        # Primary unhealthy, fall back to llama-3.1-8b
        fallback_port = self.PORT_MAPPING[LLMTaskType.FALLBACK]
        if await self.check_port_health(fallback_port):
            print(f"[LLMRouter] Primary model unavailable, falling back to {self.MODEL_NAMES.get(fallback_port)} (port {fallback_port})")
            return fallback_port

        # Both unhealthy - return primary and let error handling deal with it
        print(f"[LLMRouter] WARNING: All models unavailable, attempting primary port {primary_port}")
        return primary_port

    async def call_llm(
        self,
        port: int,
        query: str,
        context: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: float = 30.0
    ) -> str:
        """
        Call llama.cpp model on specified port.

        Business Purpose: Sends query + context to LLM and returns generated response
        for RAG operations. Handles completion API with proper error handling.

        Args:
            port: Port number of llama.cpp server
            query: User query
            context: Retrieved context from hybrid search (optional)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            timeout: Maximum seconds to wait for completion

        Returns:
            Generated response from LLM

        Example:
            response = await router.call_llm(
                port=8085,
                query="How does authentication work?",
                context=search_results_text,
                temperature=0.3,
                max_tokens=1000
            )
        """
        # Build prompt with context
        if context:
            prompt = f"""Context from codebase:
{context}

User question: {query}

Answer based on the context provided:"""
        else:
            prompt = query

        # Request payload
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop": ["\n\nUser question:", "\n\nContext:"],
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.host}:{port}/v1/completions",
                    json=payload
                )
                response.raise_for_status()

                # Extract completion text
                data = response.json()
                completion = data.get("choices", [{}])[0].get("text", "")
                return completion.strip()

        except Exception as e:
            print(f"[LLMRouter] Error calling LLM on port {port}: {e}")
            return f"Error: Failed to generate response from {self.MODEL_NAMES.get(port, 'model')}"

    async def route_query(
        self,
        query: str,
        context: str = "",
        task_type: LLMTaskType = LLMTaskType.REASONING,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: float = 30.0
    ) -> str:
        """
        Route query to appropriate LLM based on task type with automatic fallback.

        Business Purpose: Main entry point for RAG queries. Intelligently routes
        to best model for the task, handles health checks and fallback, returns
        generated response.

        Args:
            query: User query
            context: Retrieved context from hybrid search (optional)
            task_type: Type of task (determines model selection)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            timeout: Maximum seconds to wait for completion

        Returns:
            Generated response from LLM

        Example:
            # Code question → qwen-coder-7b
            response = await router.route_query(
                query="How does JWT auth work?",
                context=search_results,
                task_type=LLMTaskType.CODE_QUESTIONS
            )

            # Complex reasoning → deepseek-r1-qwen-32b
            response = await router.route_query(
                query="Compare authentication approaches in these files",
                context=multiple_files,
                task_type=LLMTaskType.REASONING
            )
        """
        # Get healthy port for task
        port = await self.get_healthy_port(task_type)

        # Call LLM
        response = await self.call_llm(
            port=port,
            query=query,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )

        return response

    async def get_all_health_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status of all configured LLM ports.

        Business Purpose: Provides monitoring and debugging information about
        which models are currently available.

        Returns:
            Dictionary mapping task types to health status

        Example:
            status = await router.get_all_health_status()
            # {
            #     "query_rewrite": {"port": 8081, "model": "phi3", "healthy": True},
            #     "code_questions": {"port": 8085, "model": "qwen-coder-7b", "healthy": False},
            #     ...
            # }
        """
        status = {}
        for task_type, port in self.PORT_MAPPING.items():
            healthy = await self.check_port_health(port)
            status[task_type.value] = {
                "port": port,
                "model": self.MODEL_NAMES.get(port, "unknown"),
                "healthy": healthy
            }
        return status
