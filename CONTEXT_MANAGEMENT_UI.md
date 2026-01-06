# Context Management UI Implementation

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/CONTEXT_MANAGEMENT_UI.md
**Description:** Documentation for LLM Chat Tester context window management features
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-06

---

## Overview

Implemented real-time context window management in the LLM Chat Tester to provide visibility and control over token usage, preventing "request exceeds available context size" errors.

## Features Implemented

### 1. Context Size Display in Model Selector

**Location:** Model dropdown (web-ui/llm-chat-tester.html:356-361)

**What it shows:**
- Context size for each model in dropdown
- Format: "🟢 Llama 3.1 8B (32k ctx, port 8087)"

**Context sizes (verified from official specs):**
- Phi-3: 8k tokens
- All other models: 32k tokens

### 2. Real-Time Context Usage Indicator

**Location:** New context indicator bar (web-ui/llm-chat-tester.html:325-334)

**What it shows:**
- Current token usage vs. model's context size
- Format: "Context: 1,234 / 32,768 tokens (3.8%)"
- Visual progress bar with color gradient:
  - Green (0-50%): Safe
  - Yellow (50-80%): Moderate
  - Orange (80-90%): Warning
  - Red (90-100%): Critical

**When it appears:**
- Hidden initially (no chat messages)
- Appears after first message sent
- Updates after every message (user, assistant, tool calls)

### 3. Context Warning System

**Location:** Warning badge (web-ui/llm-chat-tester.html:330)

**Triggers:**
- **80% threshold:** "⚠️ Approaching limit" + Compress button appears
- **90% threshold:** "⚠️ Critical: Compress context now!"

### 4. Context Compression Feature

**Location:** Compress button (web-ui/llm-chat-tester.html:331-333)

**How it works:**
1. Keeps first message (system prompt)
2. Keeps last 2 messages (recent context)
3. Summarizes everything in between using the LLM
4. Replaces middle messages with summary
5. Shows token savings

**Example:**
```
Before: 15 messages, 28,000 tokens
After: 4 messages, 8,500 tokens
Saved: 19,500 tokens
```

**User experience:**
- Button appears at 80% usage
- Shows "⏳ Compressing..." during operation
- Displays success message with savings
- Re-enabled after completion

## Token Estimation

**Method:** Character-based estimation (web-ui/llm-chat-tester.html:392-399)

**Formula:**
```javascript
tokens = words × 1.3 + special_chars × 0.5 + message_overhead
```

**Accuracy:**
- Approximate (real tokenization varies by model)
- Conservative (slightly overestimates for safety)
- Good enough for warning thresholds

## Technical Implementation

### Key Functions

1. **estimateTokens(text)** - Estimates tokens for a text string
2. **calculateContextUsage()** - Sums tokens across entire chatHistory
3. **updateContextIndicator()** - Updates UI display after each message
4. **compressContext()** - Summarizes and compresses chat history

### Integration Points

Updated sections in sendMessage():
- After user message: `updateContextIndicator()` (line 651)
- After tool call: `updateContextIndicator()` (line 736)
- After assistant message: `updateContextIndicator()` (lines 753, 759)

Updated clearChat():
- Resets context indicator to hidden state (line 827)

## Usage

### Normal Flow
1. Select LLM from dropdown (see context size)
2. Start chatting
3. Context indicator appears showing usage
4. Monitor percentage as conversation grows

### When Approaching Limit
1. Warning appears at 80% usage
2. "Compress Context" button becomes available
3. Click to compress (automatic summarization)
4. Continue chatting with reduced context

### Manual Compression
- Available anytime at 80%+ usage
- Can be triggered multiple times
- Preserves conversation continuity

## Benefits

1. **Visibility:** Always know how much context is used
2. **Prevention:** Warning before hitting limits
3. **Control:** Manual compression when needed
4. **Continuity:** Keep chatting without restarting

## Testing

### Test Scenarios

1. **Basic Display:**
   - Open chat tester
   - Verify dropdown shows context sizes
   - Send message, verify indicator appears

2. **Token Counting:**
   - Send short message (verify low token count)
   - Send long message (verify higher count)
   - Use tool calling (verify tool tokens counted)

3. **Warning Threshold:**
   - Fill context to ~80% (verify warning appears)
   - Continue to 90% (verify critical warning)

4. **Compression:**
   - Build up 10+ messages
   - Click "Compress Context"
   - Verify summary created
   - Verify token count reduced

## Known Limitations

1. **Token estimation is approximate** - Different models tokenize differently
2. **Compression quality depends on LLM** - Summary quality varies by model
3. **First message assumption** - Assumes first message should always be kept
4. **Tool call handling** - Tool results compressed like regular messages

## Future Enhancements

Potential improvements:
1. Model-specific tokenizers for exact counts
2. Configurable compression strategy (keep last N messages)
3. Manual selection of messages to keep/compress
4. Context usage history chart
5. Export/import compressed conversations

---

Questions: libor@arionetworks.com
