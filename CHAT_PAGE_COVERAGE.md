# MyRAGDB Chat Page - Test Coverage Specification

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/CHAT_PAGE_COVERAGE.md
**Description:** Complete specification of chat page tabs, sections, and interactive elements for comprehensive testing
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-08

---

## Overview

The MyRAGDB Chat Page provides LLM (Large Language Model) chat capabilities with multiple configuration options and interactive features. This document maps all tabs, configurations, and interactive elements that must be tested comprehensively.

---

## Main Dashboard Tabs (index.html)

The main dashboard has **6 tabs** (+ Chat Tester link):

### 1. Search Tab
- **Location:** Primary landing tab
- **Components:**
  - Search input field
  - Search button
  - Results display area
  - Filter options
  - Sort options
  - Result count display
  - Individual result cards with:
    - Title/filename
    - Score/relevance
    - Preview text
    - File path
    - Action buttons (open, copy, etc.)

### 2. Activity Monitor Tab
- **Location:** Second tab
- **Sub-tabs (Internal):**
  - **UI Activity Tab** (active by default)
    - Activity log display
    - Log level filtering
    - Timestamp display
    - Event type indicator
    - Clear logs button
    - Auto-refresh toggle
    - Log export button

  - **Server Logs Tab**
    - Server-side log display
    - Log streaming
    - Filter by severity
    - Search within logs
    - Log export functionality

### 3. Repositories Tab
- **Location:** Third tab
- **Components:**
  - Repository list display
  - Add repository button
  - For each repository:
    - Repository name/path
    - Enable/Disable toggle
    - Index status indicator
    - File count display
    - Index progress bar
    - Settings button (opens settings modal)
    - Delete button (with confirmation)
    - Index statistics:
      - Total files
      - Last indexed timestamp
      - Index size

### 4. Directories Tab
- **Location:** Fourth tab
- **Components:**
  - Directory list display
  - Add directory button (opens form modal)
  - For each directory:
    - Directory path
    - Enable/Disable toggle
    - File count display
    - Indexing status
    - Index progress bar
    - Settings button
    - Delete button (with confirmation)
    - Sub-directory tree view (if applicable)

### 5. Observability Tab
- **Location:** Fifth tab
- **Sub-sections:**
  - **Statistics Section**
    - Total files indexed
    - Total documents
    - Average relevance score
    - Database size
    - Index health status
    - Performance metrics

  - **Recent Errors Table**
    - Error timestamp
    - Error message
    - Affected component
    - Error severity level
    - Action/retry button
    - Error details expansion

  - **Indexing Events Table**
    - Event timestamp
    - File name/path
    - Event type (added, updated, deleted)
    - Status (success, failed, pending)
    - Processing duration
    - Index version

### 6. LLM Manager Tab
- **Location:** Sixth tab
- **Components:**
  - **Provider Selection Section**
    - Provider tabs (3 tabs):
      - **Google Gemini**
        - API Key input
        - Model selection dropdown
        - Connection status indicator
        - Test connection button
        - Configuration save button
        - Configuration validation feedback

      - **OpenAI ChatGPT**
        - API Key input
        - Model selection dropdown
        - Base URL input (optional)
        - Connection status indicator
        - Test connection button
        - Configuration save button
        - Configuration validation feedback

      - **Anthropic Claude**
        - API Key input
        - Model selection dropdown
        - Connection status indicator
        - Test connection button
        - Configuration save button
        - Configuration validation feedback

  - **Status Message Display**
    - Provider connection status
    - Last configuration update timestamp
    - Current active model info
    - Error messages for failed configurations

---

## Dedicated Chat Tester Page (llm-chat-tester.html)

A **separate page** dedicated to LLM chat testing with the following components:

### Controls Section
- **Model Selection Control**
  - Dropdown menu with available models
  - Model status indicator
  - Test connection button
  - Connection feedback

### Chat Interface
- **Model Information Display**
  - Selected model name
  - Port number
  - Context window size
  - Max tokens limit
  - Capabilities indicators

- **Token/Context Controls**
  - Total tokens used display
  - Tokens per message breakdown
  - Token percentage of limit
  - Context window status bar
  - Compress context button
  - Clear chat history button

- **Chat Container**
  - Message display area
  - Messages with roles:
    - **User messages** (styled differently)
      - User label indicator
      - Message content
      - Timestamp

    - **Assistant messages** (styled differently)
      - Assistant label indicator
      - Message content
      - Timestamp

    - **System messages** (styled differently)
      - System indicator
      - Status updates
      - Tool call information
      - Tool results display

  - Message features:
    - Code block formatting (if applicable)
    - JSON formatting for structured responses
    - Tool call visualization
    - Error messages with formatting

- **Message Input Area**
  - Text input field
    - Placeholder text
    - Multi-line support
    - Enter to send (Shift+Enter for new line)
  - Send button
    - Enabled/Disabled state based on input
    - Loading state during transmission
    - Error handling feedback

### Tool Calling Features
- **Tool Call Display**
  - Tool name visualization
  - Function arguments display
  - Argument JSON formatting

- **Tool Result Display**
  - Tool execution result
  - Result formatting
  - Error handling if tool fails

### Status Area
- **Connection Status**
  - Connected/Disconnected indicator
  - Current model display
  - Last action status
  - Error messages with formatting

### Advanced Features
- **Context Compression**
  - Summarize older messages
  - Token savings calculation
  - Preservation of recent context
  - Summary injection as system message

---

## Interactive Elements to Test

### All Tabs/Pages - Common Elements
- [ ] Tab buttons (click, active state, hover, disabled state)
- [ ] Page transitions between tabs
- [ ] Content persistence within tab
- [ ] Responsive behavior on mobile/tablet/desktop
- [ ] Keyboard navigation (Tab key through elements)
- [ ] Focus management
- [ ] ARIA labels and roles
- [ ] Error message display and formatting
- [ ] Success feedback/notifications

### Input Elements (All Pages)
- [ ] Text inputs (fill, clear, focus, blur, validation)
- [ ] Select/dropdown menus (open, select option, display selected, keyboard nav)
- [ ] Buttons (click, hover, active, disabled states)
- [ ] Toggles (on/off states, visual feedback)
- [ ] Text areas (multi-line input, scrolling)
- [ ] Number inputs (increment, decrement, min/max validation)

### Display Elements (All Pages)
- [ ] Tables (header, rows, cells, data display)
- [ ] Lists (items, selection, hover states)
- [ ] Cards (title, description, metadata, actions)
- [ ] Progress bars (visual fill, percentage, color changes)
- [ ] Status indicators (color coding, icons, text labels)
- [ ] Modals (open, close, backdrop, form handling, focus trap)
- [ ] Notifications/Alerts (display, auto-dismiss, close button)

### Chat-Specific Elements
- [ ] Message bubbles (user vs assistant vs system styling)
- [ ] Message labels (role indicator)
- [ ] Message timestamps
- [ ] Code block display and formatting
- [ ] JSON structure formatting
- [ ] Token counter accuracy
- [ ] Context window progress visualization
- [ ] Message input field state changes
- [ ] Send button state changes (enabled/disabled/loading)
- [ ] Clear chat confirmation
- [ ] Compress context confirmation
- [ ] Tool call visualization
- [ ] Tool result display

### Configuration Elements (LLM Manager)
- [ ] API key input (masked, copy button if applicable)
- [ ] API key validation
- [ ] Model dropdown selection and display
- [ ] Connection test execution and feedback
- [ ] Save configuration button state
- [ ] Configuration persistence
- [ ] Error handling for invalid configs
- [ ] Provider tab switching
- [ ] Status message display and updates

### Accessibility Elements (All Pages)
- [ ] ARIA labels on all buttons
- [ ] ARIA labels on all inputs
- [ ] ARIA labels on interactive containers
- [ ] Role attributes on custom components
- [ ] Tab order (logical flow)
- [ ] Focus indicators visible
- [ ] Color contrast on all text
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Screen reader compatibility
- [ ] Alt text on images (if any)

### State Management Tests
- [ ] Selected model persists after tab switch
- [ ] Chat history persists within session
- [ ] Configuration saves persist across page reload
- [ ] Activity logs update in real-time
- [ ] Repository/directory list updates
- [ ] Message display updates live during streaming (if applicable)
- [ ] Error recovery and retry capability

### Performance Tests
- [ ] Tab switching responsiveness
- [ ] Message display performance with large chat history
- [ ] Search results display performance
- [ ] Repository list rendering with many repos
- [ ] Token calculation performance
- [ ] Context compression speed

### Error Handling Tests
- [ ] Invalid API key handling
- [ ] Connection timeout handling
- [ ] Network error display
- [ ] Invalid model selection
- [ ] Form validation errors
- [ ] Tool call failures
- [ ] Message send failures

---

## Test Coverage Matrix

### Index.html (Main Dashboard)

| Feature | Element | Test Count | Priority |
|---------|---------|-----------|----------|
| Search Tab | Input, Button, Results | 8 | High |
| Activity Monitor | Tabs, Logs, Filters | 6 | Medium |
| Repositories | List, Toggles, Settings | 10 | High |
| Directories | List, Toggles, Settings | 10 | High |
| Observability | Stats, Tables, Data | 8 | Medium |
| LLM Manager | Tabs, Inputs, Buttons | 12 | High |
| General | Navigation, Responsive, A11y | 8 | High |

**Total Tests for Main Dashboard: ~62 tests**

### llm-chat-tester.html (Chat Page)

| Feature | Element | Test Count | Priority |
|---------|---------|-----------|----------|
| Model Selection | Dropdown, Status, Test | 5 | High |
| Chat Display | Messages, Roles, Formatting | 8 | High |
| Message Input | Input field, Send button | 6 | High |
| Token Display | Counter, Percentage, Status | 5 | High |
| Tool Calling | Call display, Results | 4 | High |
| Compress Context | Button, Confirmation, Results | 3 | Medium |
| Clear Chat | Button, Confirmation, Reset | 2 | High |
| Error Handling | Error messages, Recovery | 5 | High |
| Accessibility | ARIA, Keyboard, Focus | 6 | High |
| State Management | Persistence, Updates | 4 | Medium |
| Responsive | Mobile, Tablet, Desktop | 3 | Medium |

**Total Tests for Chat Page: ~51 tests**

---

## Total Coverage

- **Main Dashboard Tests:** 62 tests
- **Chat Page Tests:** 51 tests
- **Total UI Tests:** 113 tests
- **All test files:** 200+ tests when combined with existing ui-elements.spec.ts and ui-component-interactions.spec.ts

---

## Test File Organization

Tests will be organized in two files:

1. **tests/e2e/ui-dashboard.spec.ts** - Main dashboard (index.html) comprehensive tests
2. **tests/e2e/ui-chat.spec.ts** - Chat tester page (llm-chat-tester.html) comprehensive tests

Both files will use:
- `@ui` tag for all tests
- `@chat` tag for chat-specific tests
- `@dashboard` tag for dashboard-specific tests
- `@fast` or `@slow` based on execution speed
- Feature tags: `@search`, `@repository`, `@directory`, `@observability`, `@llm-manager`, `@chat`
- Type tags: `@interaction`, `@input`, `@display`, `@state`, `@a11y`, `@responsive`, `@error`, `@performance`

---

**Last Updated:** 2026-01-08
**Status:** Coverage specification complete
**Next:** Create test files with 113+ test cases

