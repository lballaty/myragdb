# Directory Browser Feature Design
**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/DIRECTORY-BROWSER-DESIGN.md
**Description:** Design specification for interactive directory browser UI component
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Overview

The Directory Browser is a modal-based UI component that allows users to browse the filesystem and select directories to add to MyRAGDB. This design integrates seamlessly with the existing Directories tab.

---

## User Experience Flow

### 1. User Action
- User clicks the "📂 Browse" button in the Directories tab
- Modal dialog opens with directory browser interface

### 2. Browse Interface
- Start path: User's home directory (`~` or `/Users/username`)
- Display: File tree with expandable folders
- Select: User can click on any directory to select it
- Navigate: Breadcrumb trail shows current path
- Action: "Select This Directory" button confirms choice

### 3. Form Population
- Selected path auto-fills in the `#dir-path-input` field
- Focus returns to "Directory Name" field for quick form completion
- User can edit path manually if needed

### 4. Integration Points
```
┌─────────────────────────────────────────────┐
│ Directories Tab - Add Directory Form        │
├─────────────────────────────────────────────┤
│ [Path Input] [📂 Browse Button] ← CLICK HERE│
│ [Name Input] [Priority Select]              │
│ [Notes Input] [Add Button]                  │
└─────────────────────────────────────────────┘
         │
         └──► Opens Modal
             ┌──────────────────────────────┐
             │ Directory Browser Modal       │
             ├──────────────────────────────┤
             │ 🏠 /Users/username/...       │ (Breadcrumb)
             │                              │
             │ ├─ Documents ►               │
             │ ├─ Downloads                 │
             │ ├─ Projects ►                │
             │ │  ├─ myragdb               │
             │ │  └─ other                 │
             │ └─ (etc)                     │
             │                              │
             │ [Select This Directory] [X]  │
             └──────────────────────────────┘
```

---

## Component Architecture

### Backend API

#### New Endpoint: `GET /directories/browse`

**Purpose:** List directories at any filesystem path (not limited to existing indexed directories)

**Request Parameters:**
```python
{
    "path": "/Users/username/projects",  # Starting directory path
    "max_items": 50,                     # Max directories to show per level
    "max_depth": 1                       # Don't recurse by default
}
```

**Response:** `DirectoryBrowseInfo`
```json
{
    "path": "/Users/username/projects",
    "name": "projects",
    "is_directory": true,
    "parent_path": "/Users/username",
    "children": [
        {
            "path": "/Users/username/projects/myragdb",
            "name": "myragdb",
            "is_directory": true
        },
        {
            "path": "/Users/username/projects/other",
            "name": "other",
            "is_directory": true
        }
    ],
    "error": null
}
```

**Error Handling:**
- Permission denied: Include error message in response
- Invalid path: Return error in `error` field
- Path doesn't exist: Return empty children array

**Example Calls:**
```
GET /directories/browse?path=/Users/username
GET /directories/browse?path=/private/tmp&max_items=100
GET /directories/browse?path=/Users/username/Projects/myragdb
```

---

### Frontend Modal Component

#### HTML Structure (to be inserted in index.html)

```html
<!-- Directory Browser Modal -->
<div id="directory-browser-modal" class="modal" style="display: none;">
    <div class="modal-content directory-browser-modal">
        <div class="modal-header">
            <h2>📁 Browse Directory</h2>
            <button class="modal-close" onclick="closeBrowserModal()" title="Close">✕</button>
        </div>

        <div class="modal-body">
            <!-- Breadcrumb Navigation -->
            <div class="breadcrumb-nav">
                <button class="breadcrumb-item" onclick="navigateToHome()">
                    🏠 Home
                </button>
                <span class="breadcrumb-separator">/</span>
                <div id="breadcrumb-path" class="breadcrumb-path">
                    <!-- Dynamic breadcrumbs inserted here -->
                </div>
            </div>

            <!-- Path Input -->
            <div class="browser-path-input-container">
                <input
                    type="text"
                    id="browser-path-input"
                    class="browser-path-input"
                    placeholder="Enter path or navigate below"
                    onkeypress="handleBrowserPathKeypress(event)"
                >
            </div>

            <!-- Directory Tree -->
            <div class="directory-tree-container">
                <div id="directory-tree" class="directory-tree">
                    <div class="loading">Loading directories...</div>
                </div>
            </div>

            <!-- Current Selection Display -->
            <div class="browser-current-selection">
                <strong>Selected:</strong>
                <code id="browser-selected-path">/Users/username</code>
            </div>
        </div>

        <div class="modal-footer">
            <button id="browser-select-button" class="primary-button" onclick="confirmDirectorySelection()">
                ✓ Select This Directory
            </button>
            <button class="secondary-button" onclick="closeBrowserModal()">
                Cancel
            </button>
        </div>
    </div>
</div>
```

#### CSS Styling

```css
/* Modal Overlay */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
}

.modal.active {
    display: flex;
}

/* Modal Content */
.modal-content {
    background: var(--bg-secondary);
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    max-width: 700px;
    width: 90%;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
    margin: 0;
    font-size: 1.4em;
    color: var(--text-primary);
}

.modal-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 1.5em;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-close:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
}

/* Modal Body */
.modal-body {
    flex: 1;
    padding: 20px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

/* Breadcrumb Navigation */
.breadcrumb-nav {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 10px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    font-size: 0.9em;
}

.breadcrumb-item {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--text-secondary);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}

.breadcrumb-item:hover {
    background: rgba(255, 255, 255, 0.15);
    color: var(--text-primary);
}

.breadcrumb-path {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
}

.breadcrumb-separator {
    color: var(--text-secondary);
    opacity: 0.5;
}

/* Path Input */
.browser-path-input-container {
    display: flex;
}

.browser-path-input {
    flex: 1;
    padding: 10px 12px;
    background: var(--input-bg);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
    font-family: monospace;
    font-size: 0.9em;
}

.browser-path-input:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

/* Directory Tree */
.directory-tree-container {
    flex: 1;
    overflow-y: auto;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.2);
}

.directory-tree {
    padding: 8px;
}

.tree-item {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    cursor: pointer;
    transition: background 0.2s;
    border-radius: 6px;
    margin-bottom: 4px;
}

.tree-item:hover {
    background: rgba(255, 255, 255, 0.1);
}

.tree-item.selected {
    background: rgba(16, 185, 129, 0.3);
    border-left: 3px solid var(--accent-color);
}

.tree-item-toggle {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: var(--text-secondary);
    margin-right: 8px;
}

.tree-item-toggle.expanded::before {
    content: "▼";
}

.tree-item-toggle.collapsed::before {
    content: "▶";
}

.tree-item-icon {
    margin-right: 8px;
    font-size: 1.1em;
}

.tree-item-name {
    flex: 1;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.tree-item.disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.tree-item.disabled:hover {
    background: transparent;
}

.tree-children {
    margin-left: 20px;
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    padding-left: 8px;
}

.tree-children.hidden {
    display: none;
}

.loading {
    text-align: center;
    color: var(--text-secondary);
    padding: 20px;
}

/* Current Selection */
.browser-current-selection {
    padding: 12px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 6px;
    font-size: 0.9em;
}

.browser-current-selection code {
    display: block;
    background: rgba(0, 0, 0, 0.2);
    padding: 8px;
    border-radius: 4px;
    margin-top: 6px;
    font-family: monospace;
    color: var(--text-primary);
    word-break: break-all;
}

/* Modal Footer */
.modal-footer {
    display: flex;
    gap: 12px;
    padding: 20px;
    border-top: 1px solid var(--border-color);
    justify-content: flex-end;
}

.modal-footer button {
    min-width: 120px;
}
```

---

### JavaScript Functions

#### Core Functions

```javascript
// Open directory browser modal
function openBrowserModal() {
    const modal = document.getElementById('directory-browser-modal');
    modal.style.display = 'flex';

    // Start from home directory
    const homeDir = '/Users/' + getCurrentUsername();
    browsePath(homeDir);
}

// Close directory browser modal
function closeBrowserModal() {
    const modal = document.getElementById('directory-browser-modal');
    modal.style.display = 'none';
}

// Navigate to home directory
function navigateToHome() {
    const homeDir = '/Users/' + getCurrentUsername();
    browsePath(homeDir);
}

// Browse to a specific path
async function browsePath(path) {
    const treeContainer = document.getElementById('directory-tree');
    const pathInput = document.getElementById('browser-path-input');
    const selectedPath = document.getElementById('browser-selected-path');

    // Update path input
    pathInput.value = path;
    selectedPath.textContent = path;

    // Show loading
    treeContainer.innerHTML = '<div class="loading">Loading directories...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/directories/browse?path=${encodeURIComponent(path)}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Update breadcrumbs
        updateBreadcrumbs(path);

        // Render directory tree
        if (data.children && data.children.length > 0) {
            const html = data.children
                .map(child => renderTreeItem(child))
                .join('');
            treeContainer.innerHTML = html;
        } else {
            treeContainer.innerHTML = '<div style="padding: 20px; color: var(--text-secondary); text-align: center;">No subdirectories found</div>';
        }

    } catch (error) {
        treeContainer.innerHTML = `<div class="error">Error loading directory: ${error.message}</div>`;
        addActivityLog('error', `Failed to browse directory ${path}: ${error.message}`);
    }
}

// Render a single tree item
function renderTreeItem(item) {
    return `
        <div class="tree-item" onclick="browsePath('${item.path}')">
            <div class="tree-item-icon">📁</div>
            <div class="tree-item-name">${escapeHtml(item.name)}</div>
        </div>
    `;
}

// Update breadcrumb navigation
function updateBreadcrumbs(path) {
    const breadcrumbPath = document.getElementById('breadcrumb-path');
    const parts = path.split('/').filter(p => p);

    const breadcrumbs = parts.map((part, idx) => {
        const fullPath = '/' + parts.slice(0, idx + 1).join('/');
        return `
            <button class="breadcrumb-item" onclick="browsePath('${fullPath}')">
                ${escapeHtml(part)}
            </button>
        `;
    }).join(`<span class="breadcrumb-separator">/</span>`);

    breadcrumbPath.innerHTML = breadcrumbs;
}

// Confirm directory selection
function confirmDirectorySelection() {
    const pathInput = document.getElementById('browser-path-input');
    const selectedPath = pathInput.value.trim();

    if (!selectedPath) {
        addActivityLog('warn', 'Please select a valid directory path');
        return;
    }

    // Fill in the directory form
    document.getElementById('dir-path-input').value = selectedPath;

    // Close modal
    closeBrowserModal();

    // Focus on directory name field
    document.getElementById('dir-name-input').focus();

    addActivityLog('info', `Selected directory: ${selectedPath}`);
}

// Handle Enter key in path input
function handleBrowserPathKeypress(event) {
    if (event.key === 'Enter') {
        const path = event.target.value.trim();
        if (path) {
            browsePath(path);
        }
    }
}

// Get current username (for home directory)
function getCurrentUsername() {
    // This is a placeholder - actual implementation depends on OS
    // For testing: return hardcoded username from config
    return 'liborballaty';
}
```

---

## Implementation Checklist

- [ ] Add `DirectoryBrowseInfo` model to `models.py`
- [ ] Implement `GET /directories/browse` endpoint in `directories.py`
- [ ] Add HTML modal structure to `index.html`
- [ ] Add CSS styling to `styles.css`
- [ ] Add JavaScript functions to `app.js`
- [ ] Wire browse button to `openBrowserModal()`
- [ ] Test modal opening/closing
- [ ] Test directory navigation
- [ ] Test path selection
- [ ] Test form population
- [ ] Test error handling
- [ ] Test with actual filesystem paths
- [ ] Update user manual with browse feature

---

## Error Handling Strategy

### Scenario: Permission Denied
```
GET /directories/browse?path=/root
Response: {
    "error": "Permission denied: /root",
    "path": "/root",
    "children": null
}
UI: Display error message, allow manual path entry
```

### Scenario: Invalid Path
```
GET /directories/browse?path=/nonexistent
Response: {
    "error": "Path not found: /nonexistent",
    "path": "/nonexistent",
    "children": []
}
UI: Show helpful message, suggest home directory
```

### Scenario: Network Error
```
UI: Show generic error message
Allow user to manually type path and proceed
```

---

## Security Considerations

1. **Path Validation:**
   - Only allow absolute paths
   - Reject paths with `..` or other traversal attempts
   - Symlink handling (optional: block or follow)

2. **Performance:**
   - Limit max items to 100 per directory
   - Limit depth to prevent expensive operations
   - Cache results for common paths

3. **User Privacy:**
   - Only show directories user has permission to read
   - Don't expose sensitive paths (if desired)

---

## Testing Plan

### Unit Tests
- [ ] Path validation
- [ ] Permission checking
- [ ] Directory discovery
- [ ] Response formatting

### Integration Tests
- [ ] Browse home directory
- [ ] Navigate to subdirectories
- [ ] Select directory
- [ ] Form population
- [ ] Error handling

### E2E Tests
- [ ] Open modal
- [ ] Browse filesystem
- [ ] Select directory
- [ ] Complete add directory flow
- [ ] Verify directory added to list

---

## User Manual Entry

### Browsing Directories

The Directory Browser allows you to visually navigate your filesystem and select directories to index.

**How to Use:**

1. Click the **📂 Browse** button in the "Add Directory" section
2. The Directory Browser modal will open, starting at your home directory
3. Click on any folder to navigate into it
4. Use the breadcrumb trail at the top to navigate back
5. Click **✓ Select This Directory** to confirm your choice
6. The path will be auto-filled in the form
7. Complete the form and click **Add Directory**

**Tips:**
- You can also type a path directly into the path input field and press Enter
- The breadcrumb buttons provide quick navigation
- Click the home button to return to your home directory

---

## Testing Success Criteria

- ✅ Browse button opens modal
- ✅ Can navigate directory tree
- ✅ Breadcrumbs display correctly
- ✅ Can select directory
- ✅ Path auto-fills in form
- ✅ Modal closes properly
- ✅ Error handling works
- ✅ No JavaScript console errors

