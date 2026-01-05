# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/LLAMACPP_MANAGER_MODES.md
# Description: Common llama-server launch modes for llamacppmanager
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

# llama-server Launch Modes for llamacppmanager

This document defines the most common server modes you should support in your llamacppmanager.

---

## Mode Definitions

### Mode 1: `basic`
**Description:** Basic chat mode without function calling
**Use Case:** Simple chat completions, legacy apps

```bash
/opt/homebrew/bin/llama-server \
  -m {{MODEL_PATH}} \
  --host 127.0.0.1 \
  --port {{PORT}} \
  --ctx-size 8192 \
  --n-gpu-layers 999
```

**Parameters:**
- `ctx-size`: Context window (default: 8192)
- `n-gpu-layers`: GPU offloading (999 = all layers)

---

### Mode 2: `tools` (Recommended Default)
**Description:** Function calling enabled with chat template
**Use Case:** AI agents, tool use, MyRAGDB integration

```bash
/opt/homebrew/bin/llama-server \
  -m {{MODEL_PATH}} \
  --host 127.0.0.1 \
  --port {{PORT}} \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja \
  --chat-template {{TEMPLATE_PATH}}
```

**Template Paths by Model Family:**
- Qwen models: `/Users/liborballaty/llms/templates/qwen-tools.jinja`
- Llama models: `/Users/liborballaty/llms/templates/llama-tools.jinja`
- Hermes models: `/Users/liborballaty/llms/templates/hermes-tools.jinja`

**Auto-detect template:** If template path not specified, use `--jinja` alone for models with built-in templates.

---

### Mode 3: `performance`
**Description:** Optimized for concurrent requests
**Use Case:** Production, multiple simultaneous users

```bash
/opt/homebrew/bin/llama-server \
  -m {{MODEL_PATH}} \
  --host 127.0.0.1 \
  --port {{PORT}} \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja \
  --chat-template {{TEMPLATE_PATH}} \
  --n-parallel 4 \
  --batch-size 512 \
  --ubatch-size 512
```

**Additional Parameters:**
- `n-parallel`: Number of parallel requests (default: 4)
- `batch-size`: Processing batch size (default: 512)
- `ubatch-size`: Micro-batch size (default: 512)

---

### Mode 4: `extended`
**Description:** Extended context window for long documents
**Use Case:** Document analysis, long conversations

```bash
/opt/homebrew/bin/llama-server \
  -m {{MODEL_PATH}} \
  --host 127.0.0.1 \
  --port {{PORT}} \
  --ctx-size 32768 \
  --n-gpu-layers 999 \
  --jinja \
  --chat-template {{TEMPLATE_PATH}} \
  --flash-attn
```

**Additional Parameters:**
- `ctx-size`: 32768 (4x larger than basic)
- `flash-attn`: Flash attention for faster long-context processing

---

## Model-Specific Recommendations

### Qwen Models (Qwen 2.5, Qwen Coder, DeepSeek R1 Qwen)
**Best Mode:** `tools`
**Template:** `/Users/liborballaty/llms/templates/qwen-tools.jinja`
**Reason:** Excellent function calling support, well-optimized

```bash
llama-server -m qwen-model.gguf --port 8085 --jinja \
  --chat-template /Users/liborballaty/llms/templates/qwen-tools.jinja
```

---

### Llama Models (Llama 3.1, Llama 4)
**Best Mode:** `tools`
**Template:** `/Users/liborballaty/llms/templates/llama-tools.jinja`
**Reason:** Native function calling support in Llama 3.1+

```bash
llama-server -m llama-model.gguf --port 8087 --jinja \
  --chat-template /Users/liborballaty/llms/templates/llama-tools.jinja
```

---

### Hermes 3
**Best Mode:** `tools`
**Template:** `/Users/liborballaty/llms/templates/hermes-tools.jinja`
**Reason:** Specifically trained for tool use

```bash
llama-server -m hermes-model.gguf --port 8086 --jinja \
  --chat-template /Users/liborballaty/llms/templates/hermes-tools.jinja
```

---

### Mistral Models
**Best Mode:** `basic` or `tools` (test both)
**Template:** Try `--jinja` alone first
**Reason:** Varies by version

```bash
# Try built-in template first
llama-server -m mistral-model.gguf --port 8083 --jinja

# If that doesn't work, use basic mode
llama-server -m mistral-model.gguf --port 8083
```

---

### Phi-3
**Best Mode:** `basic` (limited function calling)
**Reason:** Small model with limited tool use capabilities

```bash
llama-server -m phi3-model.gguf --port 8081 --jinja
```

---

## llamacppmanager Implementation Suggestions

### Configuration Format

```json
{
  "models": [
    {
      "id": "qwen-coder-7b",
      "name": "Qwen Coder 7B",
      "path": "/Users/liborballaty/llms/qwen-coder-7b/model.gguf",
      "port": 8085,
      "mode": "tools",
      "template": "/Users/liborballaty/llms/templates/qwen-tools.jinja",
      "ctx_size": 8192,
      "gpu_layers": 999
    },
    {
      "id": "llama-3.1-8b",
      "name": "Llama 3.1 8B",
      "path": "/Users/liborballaty/llms/llama-3.1-8b/model.gguf",
      "port": 8087,
      "mode": "tools",
      "template": "/Users/liborballaty/llms/templates/llama-tools.jinja",
      "ctx_size": 8192,
      "gpu_layers": 999
    },
    {
      "id": "phi3",
      "name": "Phi-3",
      "path": "/Users/liborballaty/llms/phi3/Phi-3-mini-4k-instruct-fp16.gguf",
      "port": 8081,
      "mode": "basic",
      "ctx_size": 8192,
      "gpu_layers": 999
    }
  ]
}
```

### Mode Builder Function (Python)

```python
def build_llama_server_command(model_config):
    """Build llama-server command based on mode."""

    base_cmd = [
        "/opt/homebrew/bin/llama-server",
        "-m", model_config["path"],
        "--host", "127.0.0.1",
        "--port", str(model_config["port"]),
        "--ctx-size", str(model_config.get("ctx_size", 8192)),
        "--n-gpu-layers", str(model_config.get("gpu_layers", 999))
    ]

    mode = model_config.get("mode", "basic")

    if mode == "basic":
        # Basic mode - no additional flags
        pass

    elif mode == "tools":
        # Function calling mode
        base_cmd.extend(["--jinja"])
        if "template" in model_config:
            base_cmd.extend(["--chat-template", model_config["template"]])

    elif mode == "performance":
        # High performance mode
        base_cmd.extend([
            "--jinja",
            "--n-parallel", str(model_config.get("parallel", 4)),
            "--batch-size", str(model_config.get("batch_size", 512)),
            "--ubatch-size", str(model_config.get("ubatch_size", 512))
        ])
        if "template" in model_config:
            base_cmd.extend(["--chat-template", model_config["template"]])

    elif mode == "extended":
        # Extended context mode
        base_cmd.extend([
            "--jinja",
            "--flash-attn"
        ])
        if "template" in model_config:
            base_cmd.extend(["--chat-template", model_config["template"]])

    return base_cmd
```

### Mode Switcher API

Add an endpoint to your manager to switch modes dynamically:

```python
@app.post("/set-mode")
def set_mode(model: str, mode: str):
    """
    Change the launch mode for a model.

    Args:
        model: Model ID (e.g., "qwen-coder-7b")
        mode: One of: basic, tools, performance, extended
    """
    if model not in MODELS:
        raise HTTPException(400, "unknown model")

    if mode not in ["basic", "tools", "performance", "extended"]:
        raise HTTPException(400, "invalid mode")

    # Update config
    config = MODELS[model]
    config["mode"] = mode

    # Restart model with new mode
    stop(model)
    start(model)

    return {"ok": True, "model": model, "mode": mode}
```

---

## Priority Implementation Order

For your llamacppmanager, implement in this order:

1. **`tools` mode** (HIGHEST PRIORITY)
   - Required for MyRAGDB integration
   - Most requested feature
   - Works with Qwen, Llama 3.1+, Hermes 3

2. **`basic` mode** (Keep existing)
   - Backward compatibility
   - Fallback for models without function calling

3. **`performance` mode** (OPTIONAL)
   - For production deployments
   - Only if you need concurrent users

4. **`extended` mode** (OPTIONAL)
   - For specialized use cases
   - Document analysis, RAG systems

---

## Quick Start for MyRAGDB

To get your LLMs working with MyRAGDB immediately:

1. **Update one model** (recommend Qwen Coder 7B):
   ```bash
   # In your llamacppmanager, change port 8085 to:
   mode = "tools"
   template = "/Users/liborballaty/llms/templates/qwen-tools.jinja"
   ```

2. **Restart the model**

3. **Test in chat UI:**
   ```
   open /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/llm-chat-tester.html
   ```

4. **Send query:**
   ```
   Search for authentication code in my repositories
   ```

5. **Verify tool call:**
   - Chat UI shows 🔧 Tool Call
   - Middleware logs show 🔍 SEARCH REQUEST
   - Chat UI shows 📊 Tool Result

---

## Summary

**For your llamacppmanager, focus on:**

1. **Add `tools` mode** with `--jinja` and `--chat-template` support
2. **Keep `basic` mode** for backward compatibility
3. **Auto-detect** which template to use based on model family name
4. **Default to `tools` mode** for all new models

**This will make all your LLMs function-calling ready immediately.**

---

Questions: libor@arionetworks.com
