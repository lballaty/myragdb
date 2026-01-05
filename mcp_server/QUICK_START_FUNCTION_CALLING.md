# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/QUICK_START_FUNCTION_CALLING.md
# Description: Simplest way to enable function calling for each model
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

# Quick Start: Function Calling by Model

**TL;DR:** Just add `--jinja` flag. Custom templates are optional.

---

## Qwen Models (RECOMMENDED - Best Function Calling)

### Models:
- Qwen 2.5 (all sizes)
- Qwen Coder 7B ✅ **BEST CHOICE**
- DeepSeek R1 Qwen 32B

### Command:
```bash
/opt/homebrew/bin/llama-server \
  -m /path/to/qwen-model.gguf \
  --host 127.0.0.1 \
  --port 8085 \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja
```

**That's it!** Qwen models have excellent built-in function calling templates.

---

## Llama 3.1 / 3.2 / 4 Models

### Models:
- Llama 3.1 8B
- Llama 4 Scout 17B

### Command:
```bash
/opt/homebrew/bin/llama-server \
  -m /path/to/llama-model.gguf \
  --host 127.0.0.1 \
  --port 8087 \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja
```

**Works great!** Llama 3.1+ has native function calling.

---

## Hermes 3 Models

### Models:
- Hermes 3 Llama 8B

### Command:
```bash
/opt/homebrew/bin/llama-server \
  -m /path/to/hermes-model.gguf \
  --host 127.0.0.1 \
  --port 8086 \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja
```

**Specifically trained for tool use.**

---

## Mistral Models

### Models:
- Mistral 7B
- Mistral Small 24B

### Command:
```bash
# Try with --jinja first
/opt/homebrew/bin/llama-server \
  -m /path/to/mistral-model.gguf \
  --host 127.0.0.1 \
  --port 8083 \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja
```

**Hit or miss.** Some Mistral models support function calling, some don't.

---

## Phi-3 Models

### Models:
- Phi-3 Mini

### Command:
```bash
# Limited function calling support
/opt/homebrew/bin/llama-server \
  -m /path/to/phi3-model.gguf \
  --host 127.0.0.1 \
  --port 8081 \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja
```

**Limited support.** Small model, basic tool use only.

---

## Testing Function Calling

After starting with `--jinja` flag:

1. **Open chat UI:**
   ```bash
   open /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/llm-chat-tester.html
   ```

2. **Select the model** (should show 🟢 green)

3. **Send test query:**
   ```
   Search for authentication code in my repositories
   ```

4. **Look for:**
   - 🔧 **Tool Call** message
   - 📊 **Tool Result** message
   - LLM response using the results

---

## Troubleshooting

### Model doesn't call the tool
**Try:**
1. Make prompt more explicit: "Use the search_codebase tool to find..."
2. Try a different model (Qwen Coder is most reliable)

### Error: "tools param requires --jinja flag"
**Solution:** Add `--jinja` to the launch command

### Error: "Failed to infer a tool call example"
**Not a problem!** This is just a warning. The model will still work.

---

## For llamacppmanager

**Simplest implementation:**

```python
def build_command(model_config):
    cmd = [
        "/opt/homebrew/bin/llama-server",
        "-m", model_config["path"],
        "--host", "127.0.0.1",
        "--port", str(model_config["port"]),
        "--ctx-size", "8192",
        "--n-gpu-layers", "999",
        "--jinja"  # ← Just add this!
    ]
    return cmd
```

**That's it!** No custom templates needed for most models.

---

## Summary

| Model Family | Command | Function Calling Quality |
|--------------|---------|--------------------------|
| Qwen (all) | `--jinja` | ⭐⭐⭐⭐⭐ Excellent |
| Llama 3.1+ | `--jinja` | ⭐⭐⭐⭐ Very Good |
| Hermes 3 | `--jinja` | ⭐⭐⭐⭐ Very Good |
| Mistral | `--jinja` | ⭐⭐⭐ Good (varies) |
| Phi-3 | `--jinja` | ⭐⭐ Limited |

**Recommendation:** Use Qwen Coder 7B (port 8085) for best results.

---

Questions: libor@arionetworks.com
