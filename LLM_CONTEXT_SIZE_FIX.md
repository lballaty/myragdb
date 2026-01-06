# LLM Context Size Fix

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/LLM_CONTEXT_SIZE_FIX.md
**Description:** Documentation for fixing "request exceeds available context size" error
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-06

---

## Problem

When using the LLM Chat Tester with Llama 3.1 8B, users encountered error:
```
request exceeds the available context size. try increasing the context size or enable context shift
```

## Root Cause

The LLM startup script `/Users/liborballaty/llms/restart-with-function-calling.sh` was launching all models with only **8192 tokens** context size:

```bash
# Line 102 - OLD (WRONG)
--ctx-size 8192
```

According to MyRAGDB documentation (MIGRATION_GUIDE.md, llm/llm_router.py), all models should use **32768 tokens** (32k) for extended context to handle larger prompts with search results.

## Solution

Updated **two** LLM startup scripts to use 32k context:

### 1. `/Users/liborballaty/llms/restart-with-function-calling.sh`
Line 102:
```bash
# OLD: --ctx-size 8192
# NEW: --ctx-size 32768
```

### 2. `/Users/liborballaty/llms/restart-llm-interactive.sh`
Lines 118, 122, 126:
```bash
# All modes now use --ctx-size 32768 (was 8192)
# Modes affected: basic, tools, performance, extended
```

## Verification

Restarted Llama 3.1 8B server:
```bash
/Users/liborballaty/llms/restart-with-function-calling.sh llama-3.1-8b
```

Verified running configuration:
```bash
ps aux | grep "llama-server" | grep "8087"
# Shows: --ctx-size 32768 ✅
```

## Impact

Context size allocation based on **verified official specifications**:

### Models with 32k Context (Changed: 8k → 32k)
- **Llama 3.1 8B** (port 8087) - Native: 128k ✅
- **Hermes 3 Llama 8B** (port 8086) - Native: 128k ✅
- **Qwen Coder 7B** (port 8085) - Default: 32k, Max: 128k ✅
- **Qwen 2.5 32B** (port 8084) - Default: 32k, Max: 128k ✅
- **DeepSeek R1 Qwen 32B** (port 8092) - Native: 128k ✅
- **Mistral 7B v0.2** (port 8083) - Native: 32k ✅
- **Mistral Small 24B** (port 8089) - Native: 32k+ ✅
- **SmolLM3** (port 8082) - Trained: 64k, Max: 128k ✅

### Models with 8k Context (Unchanged - At Safe Limit)
- **Phi-3-mini-4k** (port 8081) - Native: 4k, staying at 8k (2x scaling)

All updated models now align with MyRAGDB's 32k requirement while respecting native capabilities.

## Testing

After restarting Llama 3.1 8B, the "request exceeds available context size" error should no longer occur in the LLM Chat Tester.

---

Questions: libor@arionetworks.com
