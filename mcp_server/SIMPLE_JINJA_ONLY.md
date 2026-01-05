# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/SIMPLE_JINJA_ONLY.md
# Description: Simplest instructions for enabling function calling - tested and verified
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

# Enable Function Calling: What Actually Works

**TESTED AND VERIFIED on 2026-01-05 with Qwen Coder 7B**

---

## The Solution (2 Flags)

Add these TWO flags to your llama-server command:

1. `--ctx-size 8192`
2. `--jinja`

**That's it. Nothing else needed.**

---

## Example Command

```bash
/opt/homebrew/bin/llama-server \
  -m /path/to/your-model.gguf \
  --host 127.0.0.1 \
  --port 8085 \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja
```

---

## Which Models

This works for:
- ✅ All Qwen models (Qwen 2.5, Qwen Coder, DeepSeek R1 Qwen)
- ✅ Llama 3.1 and Llama 4
- ✅ Hermes 3

Skip for now:
- ⏭️ Phi-3 (limited support)
- ⏭️ Mistral (inconsistent)

---

## Python Implementation

```python
def build_command(model_path, port):
    """Build llama-server command with function calling enabled."""
    return [
        "/opt/homebrew/bin/llama-server",
        "-m", model_path,
        "--host", "127.0.0.1",
        "--port", str(port),
        "--ctx-size", "8192",
        "--n-gpu-layers", "999",
        "--jinja"
    ]
```

---

## DO NOT

❌ Do NOT add `--chat-template /path/to/template.jinja`
❌ Do NOT create custom templates
❌ Do NOT implement "modes"
❌ Do NOT make this complicated

The built-in templates work perfectly.

---

## Verification

After starting the server, check the log output:

**Good (works):**
```
Chat format: Hermes 2 Pro
```

**Bad (doesn't work):**
```
Chat format: Generic
```

---

## Test

1. Start server with the two flags above
2. Send a query through the chat UI
3. Check middleware logs for `🔍 SEARCH REQUEST`
4. If you see the search request, function calling is working

---

## Real Example from Testing

**Command used:**
```bash
/opt/homebrew/bin/llama-server \
  -m /Users/liborballaty/llms/qwen-coder-7b/model.gguf \
  --host 127.0.0.1 \
  --port 8085 \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --jinja
```

**Result:**
- ✅ Chat format: Hermes 2 Pro (template loaded)
- ✅ Function calling worked
- ✅ Middleware logged search request
- ✅ 20 results returned in 344ms

---

## Summary

**For your LLM manager:**

1. Take existing llama-server command
2. Add `--ctx-size 8192`
3. Add `--jinja`
4. Done

**No modes. No templates. No complexity.**

---

Questions: libor@arionetworks.com
