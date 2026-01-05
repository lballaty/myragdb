# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/health_check.py
# Description: Infrastructure health check for Meilisearch, ChromaDB, and all LLM endpoints
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-04

import asyncio
import httpx
import chromadb
import psutil
import sys
from typing import Dict, List, Tuple
from datetime import datetime


# LLM port mapping
LLM_PORTS: Dict[int, str] = {
    8081: "phi3",
    8082: "smollm3",
    8083: "mistral",
    8084: "qwen2.5-32b",
    8085: "qwen-coder-7b",
    8086: "hermes-3-8b",
    8087: "llama-3.1-8b",
    8088: "llama-4-scout-17b",
    8089: "mistral-small-24b",
    8092: "deepseek-r1-32b"
}


async def check_meilisearch(host: str = "http://localhost:7700") -> Tuple[bool, str]:
    """
    Check Meilisearch health status.

    Returns:
        Tuple of (is_healthy, status_message)
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{host}/health")

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")

                if status == "available":
                    return True, f"✅ Meilisearch: Online (status: {status})"
                else:
                    return False, f"⚠️  Meilisearch: Degraded (status: {status})"
            else:
                return False, f"❌ Meilisearch: HTTP {response.status_code}"

    except httpx.ConnectError:
        return False, "❌ Meilisearch: Connection refused (not running?)"
    except Exception as e:
        return False, f"❌ Meilisearch: Error - {str(e)[:50]}"


async def check_chromadb(host: str = "localhost", port: int = 8000) -> Tuple[bool, str]:
    """
    Check ChromaDB health status.

    Returns:
        Tuple of (is_healthy, status_message)
    """
    try:
        # Try HTTP client first
        client = chromadb.HttpClient(host=host, port=port)
        heartbeat = client.heartbeat()

        # Heartbeat returns nanoseconds since epoch
        if heartbeat > 0:
            return True, f"✅ ChromaDB: Online (heartbeat: {heartbeat}ns)"
        else:
            return False, "⚠️  ChromaDB: Heartbeat returned 0"

    except Exception as e:
        # Try local persistent client as fallback
        try:
            client = chromadb.PersistentClient(path="./data/chromadb")
            heartbeat = client.heartbeat()
            if heartbeat > 0:
                return True, f"✅ ChromaDB: Online (local mode, heartbeat: {heartbeat}ns)"
            else:
                return False, "⚠️  ChromaDB: Local heartbeat returned 0"
        except Exception as e2:
            return False, f"❌ ChromaDB: Error - {str(e)[:50]}"


async def check_llm_endpoint(port: int, model_name: str) -> Tuple[bool, str, str]:
    """
    Check LLM endpoint health and verify model.

    Returns:
        Tuple of (is_healthy, status_message, actual_model_name)
    """
    base_url = f"http://localhost:{port}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # First, try to get model info
            models_response = await client.get(f"{base_url}/v1/models")

            if models_response.status_code == 200:
                models_data = models_response.json()

                # Extract model name from response
                actual_model = "unknown"
                if "data" in models_data and len(models_data["data"]) > 0:
                    actual_model = models_data["data"][0].get("id", "unknown")
                elif "model" in models_data:
                    actual_model = models_data["model"]

                # Now test with a minimal completion
                completion_response = await client.post(
                    f"{base_url}/v1/completions",
                    json={
                        "prompt": "say ok",
                        "max_tokens": 1,
                        "temperature": 0.0
                    }
                )

                if completion_response.status_code == 200:
                    return True, f"✅ LLM {model_name} (:{port}): Online - Model: {actual_model}", actual_model
                else:
                    return False, f"⚠️  LLM {model_name} (:{port}): Model loaded but completions failing (HTTP {completion_response.status_code})", actual_model
            else:
                return False, f"❌ LLM {model_name} (:{port}): HTTP {models_response.status_code}", "unknown"

    except httpx.ConnectError:
        return False, f"❌ LLM {model_name} (:{port}): Connection refused (not running?)", "unknown"
    except httpx.ReadTimeout:
        return False, f"⚠️  LLM {model_name} (:{port}): Timeout (model loading?)", "unknown"
    except Exception as e:
        return False, f"❌ LLM {model_name} (:{port}): Error - {str(e)[:50]}", "unknown"


def get_system_resources() -> Dict[str, any]:
    """
    Get current system resource usage (M4 Max baseline).

    Returns:
        Dictionary with memory and CPU stats
    """
    # Memory stats
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024 ** 3)
    memory_used_gb = memory.used / (1024 ** 3)
    memory_percent = memory.percent

    # CPU stats
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()

    # Process stats (current Python process)
    process = psutil.Process()
    process_memory_mb = process.memory_info().rss / (1024 ** 2)

    return {
        "total_memory_gb": round(memory_gb, 2),
        "used_memory_gb": round(memory_used_gb, 2),
        "memory_percent": round(memory_percent, 1),
        "available_memory_gb": round((memory.total - memory.used) / (1024 ** 3), 2),
        "cpu_percent": round(cpu_percent, 1),
        "cpu_count": cpu_count,
        "process_memory_mb": round(process_memory_mb, 2)
    }


async def run_full_diagnostics():
    """
    Run complete infrastructure health check.
    """
    print("=" * 80)
    print("MyRAGDB Infrastructure Health Check")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # System Resources
    print("📊 M4 Max System Resources (Baseline)")
    print("-" * 80)
    resources = get_system_resources()
    print(f"Total Memory:     {resources['total_memory_gb']} GB")
    print(f"Used Memory:      {resources['used_memory_gb']} GB ({resources['memory_percent']}%)")
    print(f"Available Memory: {resources['available_memory_gb']} GB")
    print(f"CPU Load:         {resources['cpu_percent']}% ({resources['cpu_count']} cores)")
    print(f"Process Memory:   {resources['process_memory_mb']} MB")
    print()

    # Database Checks
    print("🗄️  Database Connectivity")
    print("-" * 80)

    # Meilisearch
    meili_healthy, meili_msg = await check_meilisearch()
    print(meili_msg)

    # ChromaDB
    chroma_healthy, chroma_msg = await check_chromadb()
    print(chroma_msg)
    print()

    # LLM Endpoint Checks
    print("🤖 LLM Endpoint Verification (10 Models)")
    print("-" * 80)

    llm_tasks = [
        check_llm_endpoint(port, name)
        for port, name in LLM_PORTS.items()
    ]

    llm_results = await asyncio.gather(*llm_tasks)

    online_count = 0
    offline_count = 0
    model_mappings = []

    for (healthy, msg, actual_model), (port, expected_model) in zip(llm_results, LLM_PORTS.items()):
        print(msg)
        if healthy:
            online_count += 1
            model_mappings.append((port, expected_model, actual_model))
        else:
            offline_count += 1

    print()

    # Summary
    print("=" * 80)
    print("📈 Health Check Summary")
    print("-" * 80)
    print(f"Meilisearch:      {'✅ Online' if meili_healthy else '❌ Offline'}")
    print(f"ChromaDB:         {'✅ Online' if chroma_healthy else '❌ Offline'}")
    print(f"LLM Endpoints:    {online_count}/10 Online, {offline_count}/10 Offline")
    print()

    # Model Port Mapping Table
    if model_mappings:
        print("🔗 Verified Model Port Mappings")
        print("-" * 80)
        print(f"{'Port':<8} {'Expected Model':<25} {'Actual Model':<30}")
        print("-" * 80)
        for port, expected, actual in model_mappings:
            match_indicator = "✓" if expected.lower() in actual.lower() or actual.lower() in expected.lower() else "?"
            print(f"{port:<8} {expected:<25} {actual:<30} {match_indicator}")
        print()

    # Overall Status
    total_services = 2 + 10  # Meilisearch + ChromaDB + 10 LLMs
    online_services = (1 if meili_healthy else 0) + (1 if chroma_healthy else 0) + online_count

    print("=" * 80)
    if online_services == total_services:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print(f"   {online_services}/{total_services} services online")
        return 0
    elif online_services >= total_services * 0.5:
        print("⚠️  PARTIAL SYSTEM AVAILABILITY")
        print(f"   {online_services}/{total_services} services online")
        return 1
    else:
        print("❌ CRITICAL: MAJORITY OF SERVICES OFFLINE")
        print(f"   {online_services}/{total_services} services online")
        return 2


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_full_diagnostics())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Health check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error during health check: {e}")
        sys.exit(1)
