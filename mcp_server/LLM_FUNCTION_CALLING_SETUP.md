# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/mcp_server/LLM_FUNCTION_CALLING_SETUP.md
# Description: Guide for enabling function calling support in local LLMs
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

# Enabling Function Calling for Local LLMs

**Current Status:** Your LLMs are running with basic configurations and don't support function calling yet.

**Problem:** The error `tools param requires --jinja flag` means llama.cpp needs additional flags and chat templates to support OpenAI-compatible function calling.

---

## Quick Summary

To use MyRAGDB search tools with your local LLMs, you need to:

1. Add `--jinja` flag to llama-server command
2. Provide a compatible chat template file (`.jinja`)
3. Some models may also need `--chat-template` parameter

---

## Current LLM Launch Commands

Based on running processes, your LLMs are currently started with minimal arguments:

```bash
# Phi-3 (port 8081)
/opt/homebrew/bin/llama-server -m /Users/liborballaty/llms/phi3/Phi-3-mini-4k-instruct-fp16.gguf \
  --host 127.0.0.1 --port 8081

# Mistral 7B (port 8083)
/opt/homebrew/bin/llama-server -m /Users/liborballaty/llms/mistral7b/mistral-7b-instruct-v0.2.Q8_0.gguf \
  --host 127.0.0.1 --port 8083

# DeepSeek R1 Qwen 32B (port 8092)
/opt/homebrew/bin/llama-server -m /Users/liborballaty/llms/DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8092
```

---

## Required Changes for Function Calling

### Option 1: Add --jinja Flag (Easiest)

The simplest approach for models with built-in templates:

```bash
/opt/homebrew/bin/llama-server \
  -m /path/to/model.gguf \
  --host 127.0.0.1 \
  --port 8081 \
  --jinja
```

**Supported Models:**
- Qwen models (Qwen 2.5, Qwen Coder, DeepSeek R1 Qwen)
- Llama 3.1 and Llama 4
- Hermes 3
- Some Mistral models

### Option 2: Provide Custom Chat Template

For models without built-in templates or when you need more control:

```bash
/opt/homebrew/bin/llama-server \
  -m /path/to/model.gguf \
  --host 127.0.0.1 \
  --port 8081 \
  --jinja \
  --chat-template /path/to/template.jinja
```

---

## Recommended Chat Templates

### For Qwen Models (Best for Function Calling)

Create `/Users/liborballaty/llms/templates/qwen-tools.jinja`:

```jinja
{%- if messages[0]['role'] == 'system' -%}
    {%- set system_message = messages[0]['content'] -%}
    {%- set loop_messages = messages[1:] -%}
{%- else -%}
    {%- set loop_messages = messages -%}
{%- endif -%}
{%- if tools is defined -%}
    {{- '<|im_start|>system\n' }}
    {%- if system_message is defined -%}
        {{- system_message }}
    {%- endif -%}
    {{- "\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>" }}
    {%- for tool in tools %}
        {{- "\n" }}
        {{- tool | tojson }}
    {%- endfor %}
    {{- "\n</tools>\n\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{\"name\": <function-name>, \"arguments\": <args-json-object>}\n</tool_call><|im_end|>\n" }}
{%- else -%}
    {%- if system_message is defined -%}
        {{- '<|im_start|>system\n' + system_message + '<|im_end|>\n' }}
    {%- endif -%}
{%- endif -%}
{%- for message in loop_messages %}
    {%- if message['role'] == 'user' -%}
        {{- '<|im_start|>user\n' + message['content'] + '<|im_end|>\n' }}
    {%- elif message['role'] == 'assistant' -%}
        {{- '<|im_start|>assistant\n' + message['content'] + '<|im_end|>\n' }}
    {%- elif message['role'] == 'tool' -%}
        {{- '<|im_start|>user\n<tool_response>\n' + message['content'] + '\n</tool_response><|im_end|>\n' }}
    {%- endif -%}
{%- endfor -%}
{%- if add_generation_prompt -%}
    {{- '<|im_start|>assistant\n' }}
{%- endif -%}
```

### For Llama 3.1/3.2/4 Models

Create `/Users/liborballaty/llms/templates/llama-tools.jinja`:

```jinja
{%- if messages[0]['role'] == 'system' -%}
    {%- set system_message = messages[0]['content'] -%}
    {%- set loop_messages = messages[1:] -%}
{%- else -%}
    {%- set loop_messages = messages -%}
{%- endif -%}
{{- "<|start_header_id|>system<|end_header_id|>\n\n" }}
{%- if tools is defined %}
    {{- "Environment: ipython\n" }}
{%- endif %}
{%- if system_message is defined %}
    {{- system_message }}
{%- endif %}
{%- if tools is defined -%}
    {{- "\n\nYou have access to the following functions:\n\n" }}
    {%- for tool in tools %}
        {{- tool | tojson }}
        {{- "\n\n" }}
    {%- endfor %}
{%- endif %}
{{- "<|eot_id|>" }}
{%- for message in loop_messages %}
    {%- if message['role'] == 'user' -%}
        {{- '<|start_header_id|>user<|end_header_id|>\n\n' + message['content'] + '<|eot_id|>' }}
    {%- elif message['role'] == 'assistant' -%}
        {{- '<|start_header_id|>assistant<|end_header_id|>\n\n' + message['content'] + '<|eot_id|>' }}
    {%- elif message['role'] == 'tool' -%}
        {{- '<|start_header_id|>ipython<|end_header_id|>\n\n' + message['content'] + '<|eot_id|>' }}
    {%- endif -%}
{%- endfor -%}
{%- if add_generation_prompt -%}
    {{- '<|start_header_id|>assistant<|end_header_id|>\n\n' }}
{%- endif -%}
```

### For Hermes 3 Models

Create `/Users/liborballaty/llms/templates/hermes-tools.jinja`:

```jinja
{%- if messages[0]['role'] == 'system' -%}
    {%- set system_message = messages[0]['content'] -%}
    {%- set loop_messages = messages[1:] -%}
{%- else -%}
    {%- set loop_messages = messages -%}
{%- endif -%}
{{- "<|im_start|>system\n" }}
{%- if tools is defined %}
    {{- "You are a function calling AI model. You may call one or more functions to assist with the user query.\n\n" }}
    {{- "You have access to the following functions:\n" }}
    {%- for tool in tools %}
        {{- tool | tojson }}
        {{- "\n" }}
    {%- endfor %}
{%- endif %}
{%- if system_message is defined %}
    {{- system_message }}
{%- endif %}
{{- "<|im_end|>\n" }}
{%- for message in loop_messages %}
    {%- if message['role'] == 'user' -%}
        {{- '<|im_start|>user\n' + message['content'] + '<|im_end|>\n' }}
    {%- elif message['role'] == 'assistant' -%}
        {{- '<|im_start|>assistant\n' + message['content'] + '<|im_end|>\n' }}
    {%- elif message['role'] == 'tool' -%}
        {{- '<|im_start|>tool\n' + message['content'] + '<|im_end|>\n' }}
    {%- endif -%}
{%- endfor -%}
{%- if add_generation_prompt -%}
    {{- '<|im_start|>assistant\n' }}
{%- endif -%}
```

---

## Implementation Steps

### Step 1: Create Template Directory

```bash
mkdir -p /Users/liborballaty/llms/templates
```

### Step 2: Create Template Files

Save the appropriate template(s) from above into the templates directory.

### Step 3: Update LLM LaunchAgent Configurations

You need to locate and update the plist files or startup scripts that launch your LLMs.

**Find the configuration files:**

```bash
# Check if plist files exist
ls -l ~/Library/LaunchAgents/llms.*.plist

# Or check if there are startup scripts
find /Users/liborballaty/llms -name "*.sh" -type f | grep -E "(start|run|launch)"
```

### Step 4: Add --jinja Flag to Launch Commands

**For Qwen Models (ports 8084, 8085, 8092):**

```bash
/opt/homebrew/bin/llama-server \
  -m /Users/liborballaty/llms/DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8092 \
  --jinja \
  --chat-template /Users/liborballaty/llms/templates/qwen-tools.jinja \
  --ctx-size 8192 \
  --n-gpu-layers 999
```

**For Llama Models (ports 8087, 8088):**

```bash
/opt/homebrew/bin/llama-server \
  -m /path/to/llama-model.gguf \
  --host 127.0.0.1 \
  --port 8087 \
  --jinja \
  --chat-template /Users/liborballaty/llms/templates/llama-tools.jinja \
  --ctx-size 8192 \
  --n-gpu-layers 999
```

**For Hermes 3 (port 8086):**

```bash
/opt/homebrew/bin/llama-server \
  -m /path/to/hermes-model.gguf \
  --host 127.0.0.1 \
  --port 8086 \
  --jinja \
  --chat-template /Users/liborballaty/llms/templates/hermes-tools.jinja \
  --ctx-size 8192 \
  --n-gpu-layers 999
```

**For Phi-3 (port 8081):**

Phi-3 has limited function calling support. Try:

```bash
/opt/homebrew/bin/llama-server \
  -m /Users/liborballaty/llms/phi3/Phi-3-mini-4k-instruct-fp16.gguf \
  --host 127.0.0.1 \
  --port 8081 \
  --jinja \
  --ctx-size 8192 \
  --n-gpu-layers 999
```

### Step 5: Restart LLMs

Use your controller to restart the LLMs:

```bash
# Example using curl (adjust API key if needed)
curl -X POST http://localhost:8090/stop?model=phi3 \
  -H "X-API-Key: choose-a-shared-key"

curl -X POST http://localhost:8090/start?model=phi3 \
  -H "X-API-Key: choose-a-shared-key"
```

Or use launchctl directly:

```bash
# Stop the LLM
launchctl bootout gui/$(id -u)/llms.phi3

# Start with new configuration
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/llms.phi3.plist
launchctl kickstart -k gui/$(id -u)/llms.phi3
```

---

## Testing Function Calling

After restarting an LLM with the new configuration:

1. **Open the chat UI:**
   ```bash
   open /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/llm-chat-tester.html
   ```

2. **Select the updated LLM** (it should show 🟢 green)

3. **Send a test query:**
   ```
   Search for authentication code in my repositories
   ```

4. **Expected behavior:**
   - Chat UI shows: 🔧 **Tool Call** with search_codebase and parameters
   - Middleware logs show: 🔍 **SEARCH REQUEST**
   - Chat UI shows: 📊 **Tool Result** with search results
   - LLM responds using the search results

---

## Recommended Models for Function Calling

Based on your available models, prioritize enabling function calling on:

1. **Qwen Coder 7B (port 8085)** - Best for code-related tasks
2. **Hermes 3 Llama 8B (port 8086)** - Designed for tool use
3. **Llama 3.1 8B (port 8087)** - Good general function calling
4. **DeepSeek R1 Qwen 32B (port 8092)** - Powerful reasoning + function calling
5. **Qwen 2.5 32B (port 8084)** - Excellent function calling support

---

## Troubleshooting

### Error: "tools param requires --jinja flag"
**Solution:** Add `--jinja` flag to the llama-server command

### Error: "chat template not found"
**Solution:** Add `--chat-template /path/to/template.jinja` parameter

### LLM doesn't call the tool
**Solutions:**
1. Verify `--jinja` flag is in the launch command
2. Check that the chat template file exists and is readable
3. Try a different model (Qwen Coder, Hermes 3, or Llama 3.1)
4. Make your prompt more explicit: "Use the search_codebase tool to find..."

### LLM restarts but function calling still doesn't work
**Solutions:**
1. Check the LLM logs: `/Users/liborballaty/llms/logs/{model}.log`
2. Verify the launch command includes all required flags
3. Test the template by sending a simple query
4. Try using the built-in template with just `--jinja` flag

---

## Alternative: Test Without Restarting

If you want to test without modifying your production LLM setup, start a temporary instance:

```bash
# Start Qwen Coder 7B on a different port with function calling enabled
/opt/homebrew/bin/llama-server \
  -m /path/to/qwen-coder-7b.gguf \
  --host 127.0.0.1 \
  --port 9999 \
  --jinja \
  --chat-template /Users/liborballaty/llms/templates/qwen-tools.jinja \
  --ctx-size 8192 \
  --n-gpu-layers 999
```

Then add it to the chat UI dropdown by modifying `llm-chat-tester.html`:

```javascript
const LLM_MODELS = [
    // ... existing models ...
    { id: 'qwen-coder-test', name: 'Qwen Coder 7B (Test)', port: 9999 }
];
```

---

## Next Steps

1. Create the templates directory and template files
2. Start with one LLM (recommend Qwen Coder 7B on port 8085)
3. Update its launch configuration with `--jinja` flag and template
4. Restart the LLM
5. Test in the chat UI
6. If successful, update other LLMs

---

Questions: libor@arionetworks.com
