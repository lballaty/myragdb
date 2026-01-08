# MyRAGDB Comprehensive UI Testing Guide

**File:** `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/UI_TESTING_GUIDE.md`
**Description:** Complete guide to UI element and component interaction testing
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-08

---

## Overview

The MyRAGDB UI Testing Suite provides **comprehensive coverage of all user interface elements** including:

- **Interactive Elements** - Inputs, buttons, dropdowns, checkboxes, radio buttons
- **Display Components** - Lists, tables, cards, panels, modals
- **Form Handling** - Validation, submission, error display
- **Component Workflows** - Search, filtering, state changes
- **User Interactions** - Hover, focus, click, keyboard navigation
- **Accessibility** - ARIA labels, keyboard navigation, screen reader support
- **Responsive Design** - Mobile, tablet, desktop viewport testing
- **State Management** - Selection, data binding, error recovery

---

## Test Files

### ui-elements.spec.ts
**Complete UI element testing - all interactive components**

Tests cover:
- **Text Inputs** - Search, filtering, parameter inputs, character limits
- **Buttons** - Click actions, disabled states, hover effects, keyboard activation
- **Dropdowns** - Selection, option display, value management
- **Checkboxes** - Toggle states, multi-selection
- **Radio Buttons** - Single selection, mutual exclusivity
- **Lists & Tables** - Item display, selection, rendering
- **Cards & Panels** - Content display, interaction
- **Modals** - Opening, closing, form handling, backdrop
- **Forms** - Validation, submission, field focus
- **Alerts** - Display, dismissal, messaging
- **Loading States** - Progress bars, spinners, indicators
- **Accessibility** - ARIA labels, keyboard navigation, focus management

**Run:**
```bash
npm test -- --grep "@ui @elements"
```

### ui-component-interactions.spec.ts
**Complex component workflows and state management**

Tests cover:
- **Search Workflow** - Input, submission, result display, filtering, clearing
- **Repository Management** - List display, enable/disable, settings, statistics
- **Directory Management** - Add, list, toggle, settings, file counts, indexing status
- **Form Validation** - Required fields, validation feedback, error display, reset
- **Modal Lifecycle** - Open, close, focus trap, form handling
- **Selection State** - Item selection, state maintenance, state persistence
- **Data Binding** - UI updates on data change, reactive rendering
- **Error Handling** - Error messages, recovery, error dismissal
- **Responsive Layout** - Mobile, tablet, desktop adaptation

**Run:**
```bash
npm test -- --grep "@ui @interactions"
```

### ui-chat.spec.ts
**Comprehensive dashboard and chat interface testing - ALL TABS AND CONFIGURATIONS**

Tests cover:

**Main Dashboard (index.html) - 6 Tabs:**
- **Search Tab** - Search input, buttons, results display, filtering, clearing
- **Activity Monitor Tab** - UI Activity & Server Logs sub-tabs, log clearing, filtering
- **Repositories Tab** - List display, enable/disable toggles, settings, delete, file counts, index status
- **Directories Tab** - List display, add, enable/disable, settings, delete, file counts, indexing status
- **Observability Tab** - Statistics display, database metrics, Recent Errors table, Indexing Events table
- **LLM Manager Tab** - 3 Provider tabs (Google Gemini, OpenAI, Anthropic), API key input, model selection, test connection, configuration persistence

**Dedicated Chat Tester Page (llm-chat-tester.html):**
- **Model Selection** - Dropdown, connection status, test button, provider switching
- **Chat Interface** - Message input field, send button, clear chat, input clearing after send
- **Message Display** - User/assistant/system message roles, message bubbles, labels, timestamps
- **Message Formatting** - Code blocks, JSON formatting, tool call display, tool results
- **Token Management** - Token counter accuracy, context window display, max tokens limit, compress context
- **Tool Features** - Tool call visualization, function arguments display, tool results presentation
- **Status & Errors** - Connection status, error messages, error recovery, status updates
- **Responsive Design** - Mobile (375x667), tablet (768x1024), desktop (1920x1080)
- **Accessibility** - ARIA labels, semantic HTML, keyboard navigation, focus management, color contrast
- **State Management** - Chat history persistence, selected model persistence, configuration persistence
- **Complete Workflows** - Tab navigation flow, model selection + connection flow, message input flow

**Run:**
```bash
npm test -- --grep "@chat"
```

**Run Dashboard Tests:**
```bash
npm test -- --grep "@dashboard"
```

**Run LLM Manager Tests:**
```bash
npm test -- --grep "@llm-manager"
```

---

## Running UI Tests

### All UI Element Tests
```bash
npm test -- --grep "@ui"
```

### UI Element Coverage
```bash
npm test -- --grep "@ui @elements"
```

### Component Interaction Tests
```bash
npm test -- --grep "@ui @interactions"
```

### Specific Component Tests

**Search functionality:**
```bash
npm test -- --grep "@ui.*@search"
```

**Repository management:**
```bash
npm test -- --grep "@ui.*@repository"
```

**Directory management:**
```bash
npm test -- --grep "@ui.*@directory"
```

**Form handling:**
```bash
npm test -- --grep "@ui.*@form"
```

**Modal dialogs:**
```bash
npm test -- --grep "@ui.*@modal"
```

**Accessibility:**
```bash
npm test -- --grep "@ui.*@a11y"
```

### By Interaction Type

**Input elements:**
```bash
npm test -- --grep "@ui.*@input"
```

**Buttons:**
```bash
npm test -- --grep "@ui.*@button"
```

**Dropdowns:**
```bash
npm test -- --grep "@ui.*@select"
```

**Checkboxes:**
```bash
npm test -- --grep "@ui.*@checkbox"
```

**Radio buttons:**
```bash
npm test -- --grep "@ui.*@radio"
```

**Lists:**
```bash
npm test -- --grep "@ui.*@list"
```

**State changes:**
```bash
npm test -- --grep "@ui.*@state"
```

---

## Test Categories

### Element Type
- `@input` - Text inputs, text areas
- `@button` - Buttons, clickable elements
- `@select` - Dropdowns, combobox, select
- `@checkbox` - Checkbox controls
- `@radio` - Radio button controls
- `@list` - Lists, list items
- `@table` - Tables, rows, cells
- `@card` - Card components
- `@modal` - Modal dialogs
- `@alert` - Alerts, notifications
- `@form` - Form elements and validation

### Interaction Type
- `@interaction` - User interaction test
- `@click` - Click action
- `@focus` - Focus state
- `@hover` - Hover state
- `@input` - Text input
- `@selection` - Item selection
- `@submission` - Form submission
- `@validation` - Input validation

### Feature Area
- `@search` - Search functionality
- `@repository` - Repository management
- `@directory` - Directory management
- `@workflow` - Multi-step workflows
- `@filter` - Filtering capabilities

### Properties
- `@display` - Display/rendering
- `@state` - State management
- `@error` - Error handling
- `@a11y` - Accessibility features
- `@responsive` - Responsive behavior

---

## What Gets Tested

### Text Input Elements
- ✅ Input field visibility and interaction
- ✅ Text entry and value capture
- ✅ Input clearing
- ✅ Rapid input handling
- ✅ Focus and blur events
- ✅ Character limit validation
- ✅ Placeholder text
- ✅ Input types (text, email, number, password, etc.)

### Button Elements
- ✅ Button visibility and clickability
- ✅ Click action execution
- ✅ Disabled state detection
- ✅ Hover state effects
- ✅ Keyboard activation (Enter key)
- ✅ Button text and labels
- ✅ Multiple button interaction

### Dropdown/Select Elements
- ✅ Dropdown visibility
- ✅ Option display
- ✅ Option selection
- ✅ Selected value display
- ✅ Multiple selection (if applicable)
- ✅ Keyboard navigation

### Checkbox Elements
- ✅ Checkbox visibility
- ✅ Toggle on/off
- ✅ Checked state
- ✅ Disabled state
- ✅ Label association
- ✅ Multiple checkboxes

### Radio Button Elements
- ✅ Radio button visibility
- ✅ Selection interaction
- ✅ Checked state
- ✅ Mutual exclusivity (same group)
- ✅ Disabled state
- ✅ Label association

### Lists and Tables
- ✅ List/table structure rendering
- ✅ List item display
- ✅ Item selection
- ✅ Table headers and data
- ✅ Row and cell rendering
- ✅ Item count
- ✅ Pagination (if applicable)

### Cards and Panels
- ✅ Card visibility
- ✅ Card content display
- ✅ Card interaction
- ✅ Card styling
- ✅ Multiple cards

### Modals and Dialogs
- ✅ Modal open/close
- ✅ Modal backdrop
- ✅ Focus trap (stays within modal)
- ✅ Close button functionality
- ✅ Form inside modal
- ✅ Modal animations

### Forms
- ✅ Form structure
- ✅ Input field validation
- ✅ Required field enforcement
- ✅ Validation message display
- ✅ Form submission
- ✅ Form reset
- ✅ Error state display

### Alerts and Notifications
- ✅ Alert visibility
- ✅ Alert message content
- ✅ Alert dismissal
- ✅ Multiple alert types (error, warning, info, success)
- ✅ Alert positioning

### Loading States
- ✅ Loading indicator visibility
- ✅ Progress bar display
- ✅ Loading spinner
- ✅ Loading state transitions
- ✅ Disable of inputs during loading

### Accessibility
- ✅ ARIA labels and descriptions
- ✅ Role attributes
- ✅ Keyboard navigation
- ✅ Tab order
- ✅ Focus management
- ✅ Alt text on images
- ✅ Color contrast (should be verified)
- ✅ Screen reader compatibility

### Responsive Design
- ✅ Mobile viewport (375x667)
- ✅ Tablet viewport (768x1024)
- ✅ Desktop viewport (1920x1080)
- ✅ Content visibility at all sizes
- ✅ Touch-friendly element sizing
- ✅ Responsive menu behavior

### Dashboard Components (Main Dashboard - index.html)
- ✅ Tab navigation (6 main tabs)
- ✅ Tab state persistence
- ✅ Search tab functionality
- ✅ Activity Monitor tab with sub-tabs (UI Activity, Server Logs)
- ✅ Repository Management (list, toggle, settings, delete)
- ✅ Directory Management (add, list, toggle, settings, delete)
- ✅ Observability metrics and tables
- ✅ LLM Manager with 3 provider tabs

### LLM Configuration Elements
- ✅ Google Gemini API configuration
- ✅ OpenAI ChatGPT API configuration
- ✅ Anthropic Claude API configuration
- ✅ API key input and validation
- ✅ Model selection dropdown
- ✅ Connection testing
- ✅ Configuration persistence
- ✅ Provider tab switching
- ✅ Status message display
- ✅ Error handling for invalid configurations

### Chat Tester Interface (llm-chat-tester.html)
- ✅ Model selection and dropdown
- ✅ Connection status indicator
- ✅ Chat message container
- ✅ User message formatting and display
- ✅ Assistant message formatting and display
- ✅ System message formatting and display
- ✅ Message labels with role indicators
- ✅ Message timestamps
- ✅ Code block formatting in messages
- ✅ JSON structure formatting
- ✅ Message input field with focus/blur
- ✅ Send button functionality
- ✅ Clear Chat button and confirmation
- ✅ Input clearing after message send
- ✅ Shift+Enter for new line support
- ✅ Enter to send message support

### Token and Context Management
- ✅ Token counter display
- ✅ Token count accuracy
- ✅ Context window status bar
- ✅ Max tokens limit display
- ✅ Context compression button
- ✅ Compression confirmation dialog
- ✅ Token savings calculation
- ✅ Context preservation after compression

### Tool Calling Features
- ✅ Tool call visualization
- ✅ Function name display
- ✅ Function arguments display
- ✅ Argument JSON formatting
- ✅ Tool execution status
- ✅ Tool result display
- ✅ Tool result formatting
- ✅ Error handling for failed tool calls

### Status and Connection Management
- ✅ Connected/Disconnected indicator
- ✅ Model status display
- ✅ Connection failure messages
- ✅ Error message formatting
- ✅ Status update display
- ✅ Action feedback
- ✅ Loading states during actions

---

## Complex Workflow Tests

### Search Workflow
1. Find search input
2. Enter search term
3. Submit search
4. Verify results display
5. Apply filters
6. Change sort order
7. Clear search

### Repository Management Workflow
1. Display repository list
2. Count repositories
3. Click repository
4. Show details/highlight
5. Enable/disable toggle
6. Update settings
7. Display statistics

### Directory Management Workflow
1. Add new directory
2. Fill path input
3. Submit form
4. Verify directory added
5. Display directory list
6. Toggle enable/disable
7. Update settings

### Form Validation Workflow
1. Find form
2. Attempt submit without inputs
3. Verify validation messages
4. Fill required fields
5. Submit form
6. Verify success
7. Reset form

### Modal Workflow
1. Find modal trigger
2. Click trigger
3. Verify modal opens
4. Find form/content
5. Interact with elements
6. Submit or cancel
7. Verify modal closes

### Dashboard Tab Navigation Workflow
1. Load main dashboard (index.html)
2. Verify Search tab is active by default
3. Click Activity Monitor tab
4. Verify Activity Monitor content displays
5. Click Repositories tab
6. Verify Repository list displays
7. Click Directories tab
8. Verify Directory list displays
9. Click Observability tab
10. Verify Statistics and tables display
11. Click LLM Manager tab
12. Verify LLM configuration forms display
13. Switch between provider tabs (Gemini, OpenAI, Anthropic)

### LLM Manager Configuration Workflow
1. Navigate to LLM Manager tab
2. Select a provider tab (e.g., OpenAI)
3. Fill API key input
4. Select model from dropdown
5. Click Test Connection button
6. Verify connection status feedback
7. Click Save Configuration
8. Verify configuration persists
9. Switch to different provider
10. Repeat configuration steps
11. Verify all providers maintain separate configurations

### Chat Tester Session Workflow
1. Navigate to llm-chat-tester.html
2. Select model from dropdown
3. Verify connection status
4. Enter message in input field
5. Click Send or press Enter
6. Verify message appears as user message
7. Verify token counter updates
8. Type another message
9. Verify context window updates
10. Clear Chat when done
11. Verify chat history clears

### Tool Calling Workflow (if supported)
1. Send message that triggers tool call
2. Verify tool call is visualized
3. Verify function name is displayed
4. Verify arguments are shown
5. Wait for tool result
6. Verify result is formatted and displayed
7. Verify assistant response follows tool result

---

## Running Full UI Test Suite

### Quick UI Check (< 5 min)
Tests only critical UI elements:
```bash
npm test -- --grep "@ui @smoke"
```

### Fast UI Regression (15-20 min)
Tests all UI elements and interactions:
```bash
npm test -- --grep "@ui @fast"
```

### Complete UI Testing (30-45 min)
Tests all UI elements including slow interactions:
```bash
npm test -- --grep "@ui"
```

---

## Test Execution Examples

### Testing New UI Feature
```bash
# Test your new component
npm test -- --grep "@ui.*@[your-feature]"

# Example: Test new search feature
npm test -- --grep "@ui.*@search"
```

### Regression Before Merge
```bash
# Full UI regression
npm test -- --grep "@ui"

# Or with dashboard
npm run test:ui
```

### Continuous Integration
```bash
# Fast UI tests for every push
npm test -- --grep "@ui @fast"

# Full UI tests before merge
npm test -- --grep "@ui"
```

---

## Best Practices

### Writing UI Tests

1. **Use data-testid** for reliable element selection
   ```html
   <div data-testid="result">
     <button data-testid="expand">Expand</button>
   </div>
   ```

2. **Test user interactions** not implementation
   ```typescript
   // Good: User clicks button
   await button.click();

   // Bad: Testing internal state
   expect(component.state.open).toBe(true);
   ```

3. **Wait for elements explicitly**
   ```typescript
   // Good: Wait for element visibility
   await element.waitFor({ state: 'visible' });

   // Bad: Hard sleep
   await page.waitForTimeout(1000);
   ```

4. **Handle optional elements gracefully**
   ```typescript
   // Good: Check if element exists before interacting
   if (await element.isVisible()) {
     await element.click();
   }
   ```

5. **Use meaningful assertions**
   ```typescript
   // Good: Clear assertion
   expect(await input.inputValue()).toBe('test');

   // Bad: Vague assertion
   expect(input).toBeTruthy();
   ```

### Maintaining UI Tests

1. Update selectors when UI changes
2. Add data-testid to components (not relying on CSS classes)
3. Keep tests independent and reusable
4. Mock external services if needed
5. Document complex test scenarios
6. Review flaky tests regularly

---

## Debugging UI Tests

### Run with Browser Visible
```bash
npm test -- --headed
```

### Debug Mode with Inspector
```bash
npm test -- --debug
```

### Slow Motion (easier to watch)
```bash
npm test -- --headed --slow-mo=1000
```

### Single Test File
```bash
npm test tests/e2e/ui-elements.spec.ts
```

### Single Test
```bash
npm test -- --grep "should accept search input text"
```

---

## Accessibility Testing

### Keyboard Navigation
```typescript
test('should navigate with keyboard', async ({ page }) => {
  await page.keyboard.press('Tab');
  const focused = await page.evaluate(() => document.activeElement?.id);
  expect(focused).toBe('expected-id');
});
```

### ARIA Attributes
```typescript
test('should have aria labels', async ({ page }) => {
  const label = await page.getAttribute('[role="button"]', 'aria-label');
  expect(label).toBeTruthy();
});
```

### Screen Reader Compatibility
- Test with semantic HTML
- Verify ARIA roles and labels
- Check alt text on images
- Ensure heading hierarchy

---

## Performance Considerations

### Test Timeout
- Default: 30 seconds per test
- Increase for slow operations: `test.setTimeout(60000)`
- Decrease for fast assertions: `test.setTimeout(5000)`

### Test Parallelization
- Default: Sequential execution (safer)
- Parallel: `npm test -- --workers=2` (faster but may conflict)

### Resource Usage
- Watch for memory leaks
- Close resources in afterEach
- Use test fixtures for setup/teardown

---

## Continuous Integration

### GitHub Actions Example
```yaml
- name: Run UI Tests
  run: npm test -- --grep "@ui"

- name: Upload Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: ui-test-results
    path: tests/test-results/
```

---

## Results and Reporting

### View Test Report
```bash
npx playwright show-report
```

### JSON Results
```bash
cat tests/test-results/results.json | jq .
```

### Failed Tests Only
```bash
grep "failing" tests/test-results/results.json
```

---

## Common Issues

### Element Not Found
```
Error: locator.click: Target page, context or browser has been closed
```
- Wait for element: `await element.waitFor()`
- Check element visibility: `await element.isVisible()`
- Verify selector is correct

### Timeout Waiting for Element
```
Error: Timeout 30000ms exceeded
```
- Element doesn't exist on page
- Increase timeout: `test.setTimeout(60000)`
- Add debug logs to see page state

### Form Validation Fails
- Fill all required fields
- Verify field types match
- Check for client-side validation

### Modal Won't Open
- Verify trigger button exists
- Add wait after click: `await page.waitForTimeout(500)`
- Check for modal existence before interaction

---

## References

- [Playwright Documentation](https://playwright.dev)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Accessibility](https://webaim.org/)
- [UI Component Best Practices](./ui-elements.spec.ts)
- [Interaction Tests](./ui-component-interactions.spec.ts)

---

## Summary

This comprehensive UI testing suite ensures:

✅ **All interactive elements tested** - Inputs, buttons, dropdowns, etc.
✅ **Complete workflows covered** - Search, management, forms
✅ **Accessibility verified** - ARIA, keyboard, labels
✅ **Responsive design checked** - Mobile, tablet, desktop
✅ **Error handling validated** - Error messages, recovery
✅ **State management tested** - Selection, data binding, updates
✅ **User workflows verified** - Multi-step scenarios

**Get started:**
```bash
npm test -- --grep "@ui @elements"   # Run element tests
npm test -- --grep "@ui @interactions" # Run interaction tests
npm test -- --grep "@ui"              # Run all UI tests
npm run test:ui                        # Open interactive dashboard
```

---

**Last Updated:** 2026-01-08
**Status:** Complete and comprehensive
