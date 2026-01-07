# MyRAGDB User Manual

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/USER_MANUAL.md
**Description:** Complete user manual for MyRAGDB hybrid search system
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07
**Last Updated:** 2026-01-07
**Last Updated By:** Libor Ballaty <libor@arionetworks.com>

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Web UI Guide](#web-ui-guide)
4. [Search Features](#search-features)
5. [Repository Management](#repository-management)
6. [Indexing & Reindexing](#indexing--reindexing)
7. [MCP Integration](#mcp-integration)
8. [LLM Integration](#llm-integration)
9. [API Reference](#api-reference)
10. [Configuration](#configuration)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)

---

## Introduction

### What is MyRAGDB?

MyRAGDB is a **hybrid search system** that combines keyword search (via Meilisearch) with semantic vector search (via ChromaDB) to provide intelligent code and documentation discovery across multiple git repositories.

### Key Features

- **Hybrid Search**: Combines keyword matching with semantic understanding
- **Multi-Repository Support**: Index and search across unlimited repositories
- **Incremental Indexing**: Only reindex changed files for fast updates
- **MCP Integration**: Model Context Protocol middleware enables AI tools to search your codebase
- **LLM Integration**: Built-in support for local LLMs with function calling
- **Repository Discovery**: Automatically find git repositories in directories
- **Real-time Updates**: File watcher monitors changes (optional)
- **Web UI**: Modern, responsive interface with dark mode
- **REST API**: Full programmatic access for automation
- **Clone Detection**: Identifies duplicate repositories automatically

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│               AI Tools (Claude Code, etc.)                   │
│                   MCP Protocol Clients                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓ (MCP Protocol)
┌─────────────────────────────────────────────────────────────┐
│                  MCP HTTP Middleware                         │
│              (Port 8093 - Tool Access)                       │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌───────────────────┐              ┌─────────────────────────┐
│      Web UI       │              │   FastAPI Server        │
│ (HTML/CSS/JS)     │◄────────────►│  (Python REST API)      │
│  Port 3003        │              │    Port 3003            │
└───────────────────┘              └─────────────────────────┘
                                              │
                         ┌────────────────────┼────────────────┐
                         ↓                    ↓                ↓
                   ┌───────────┐      ┌───────────┐    ┌──────────┐
                   │Meilisearch│      │ ChromaDB  │    │  SQLite  │
                   │ Keyword   │      │  Vector   │    │ Metadata │
                   │  Search   │      │  Search   │    │ Tracking │
                   │ Port 7700 │      │           │    │          │
                   └───────────┘      └───────────┘    └──────────┘
```

---

## Getting Started

### Prerequisites

- **Python 3.8+** installed
- **Git** installed
- **macOS, Linux, or Windows** with WSL

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd myragdb
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Install Meilisearch:**

   **macOS:**
   ```bash
   brew install meilisearch
   ```

   **Linux:**
   ```bash
   curl -L https://install.meilisearch.com | sh
   ```

   **Windows:**
   Download from https://github.com/meilisearch/meilisearch/releases

### Quick Start

#### Option 1: macOS App Bundle (Easiest)

**Just double-click MyRAGDB.app!**

1. **First time**: Double-click `MyRAGDB.app` in the project folder
2. App starts all services and opens browser automatically
3. App stays in Dock while services are running
4. **To stop**: Right-click app in Dock → Quit (or use `./stop.sh`)
5. **To reopen UI**: Double-click app again (services stay running)

**Adding to Applications/Dock:**

- **Option 1 - Create Alias:**
  ```bash
  cd /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb
  ln -s "$(pwd)/MyRAGDB.app" ~/Applications/MyRAGDB.app
  ```

- **Option 2 - Copy to Applications:**
  ```bash
  cp -R MyRAGDB.app ~/Applications/
  ```

- **Option 3 - Drag and Drop:**
  - Open Finder, navigate to project folder
  - Drag `MyRAGDB.app` to Applications folder
  - Hold ⌥ Option to copy, ⌘ Command to create alias

- **Add to Dock:**
  1. Open the app once
  2. Right-click the icon in Dock
  3. Options → Keep in Dock

#### Option 2: Terminal Script

1. **Configure repositories:**

   Edit `config/repositories.yaml`:
   ```yaml
   repositories:
     - name: myproject
       path: /path/to/your/project
       enabled: true
       priority: high
   ```

2. **Start MyRAGDB:**
   ```bash
   ./start.sh
   ```

   This single command:
   - Starts Meilisearch (search engine)
   - Starts MyRAGDB API server on port 3003
   - Starts MCP HTTP Middleware (for LLM tool access)
   - Opens web UI in your browser automatically

   **What the start script does internally:**
   ```bash
   # Step 1: Start Meilisearch on port 7700
   meilisearch --db-path data/meilisearch \
     --master-key myragdb_dev_key_2026 \
     --http-addr 127.0.0.1:7700

   # Step 2: Activate venv and start API server on port 3003
   source venv/bin/activate
   python -m myragdb.api.server

   # Step 3: Start MCP middleware on port 8093
   python -m mcp_server.http_middleware
   ```

3. **Access Web UI:**

   - Browser opens automatically at http://localhost:3003
   - Or manually navigate to http://localhost:3003

4. **Index repositories:**

   Click "🔄 Reindex" in the Repositories section

5. **Stop MyRAGDB:**
   ```bash
   ./stop.sh
   ```

   Stops all services in reverse dependency order:
   - MCP Middleware → API Server → Meilisearch

---

## Web UI Guide

### Dashboard Overview

The main dashboard consists of four sections:

1. **Header** (top navigation and status)
2. **Search Panel** (main content area)
3. **Repositories Panel** (left sidebar)
4. **Activity Log** (right sidebar)
5. **LLM Manager** (bottom section)

### Header Elements

**Left Section:**
- **🔍 MyRAGDB** - Application logo/title
- **Version Badge** - Shows current version (e.g., v2026.01.07.2.50.0)
- **Repository Status Badge** - Shows repository loading/ready status
  - ⏳ Loading repositories... (gray)
  - ✅ X repositories ready (green)
- **LLM Status Badge** - Shows LLM running status
  - 🤖 No LLM Running (gray)
  - 🤖 [Model Name] Running (green)

**Center Section:**
- **📖 User Manual** - Opens this manual in a modal viewer
- **💬 LLM Chat Tester** - Link to LLM testing interface
- **Status Indicator** - Server health check
  - 🟢 Connected (green) - Server responsive
  - 🔴 Disconnected (red) - Server not responding
  - 🟡 Checking... (yellow) - Connection test in progress

**Startup/Stop Commands:**
Displays the actual commands to start/stop the system:
```
Start: /Users/.../myragdb/start.sh
Stop: /Users/.../myragdb/stop.sh
```

### Search Panel (Main Content)

#### Search Input Section

**Search Box:**
- Large text input field for search queries
- Placeholder text guides query format
- **Keyboard shortcut**: Press `Enter` to search
- Supports natural language and technical queries

**Search Mode Selector:**
Three radio button options:
- **🔀 Hybrid** (recommended)
  - Combines keyword + semantic search
  - Best for general queries
  - Default selection
- **🔤 Keyword**
  - Fast BM25 text matching
  - Best for exact terms/code
- **🧠 Vector**
  - Semantic similarity search
  - Best for conceptual queries

**Search Filters:**

1. **Repository Filter** (Multi-select dropdown)
   - Shows all configured repositories
   - Select one or more to narrow search
   - Unselect all to search across everything
   - Disabled repos shown grayed out with "(disabled)" label

2. **File Type Filter** (Multi-select dropdown)
   - Common extensions: .py, .js, .ts, .md, .dart, etc.
   - Select specific types to filter results
   - Leave empty to search all file types

3. **Result Limit Slider**
   - Range: 1-100 results
   - Default: 10 results
   - Drag slider or click track to adjust
   - Current value displayed below slider

**🔍 Search Button:**
- Large blue button
- Triggers search with current parameters
- Shows loading state during search
- Alternative to pressing Enter

#### Search Results Section

**Result Cards:**

Each result shows:

1. **File Header**
   - **File path** - Full path to file (clickable to copy)
   - **Repository name** - Which repo contains this file
   - **File type icon** - Visual indicator (.py, .md, etc.)

2. **Content Preview**
   - 3-5 lines of matching content
   - **Highlighted matches** - Search terms highlighted in yellow
   - Ellipsis (...) for truncated content

3. **Match Metadata**
   - **Score** - Relevance percentage (0-100%)
   - **Match type** - hybrid/keyword/vector
   - Color-coded score bar:
     - Green (90-100%) - Excellent match
     - Blue (70-89%) - Good match
     - Gray (<70%) - Moderate match

4. **Action Buttons**
   - **📋 Copy Path** - Copy file path to clipboard
   - **View Context** - Show more surrounding code

**Results Summary:**
- Shows "Found X results in Yms" above result list
- **Repository Search Scope**: Displays which repositories were searched
  - Format: "📚 Searched 34 repositories: repo1, repo2, repo3 and 31 more"
  - Shows first 3 repository names plus count of additional repositories
  - Helps verify that repository filters are working correctly
- **API Call Details** (Collapsible):
  - Click to expand and see exact API request
  - Shows endpoint (POST /search/hybrid, /search/keyword, or /search/semantic)
  - Shows complete request body with all filters
  - Useful for debugging and comparing with chat interface searches
- Empty state message if no results
- Pagination controls if > limit results

### Repositories Panel (Left Sidebar)

#### Panel Header

**🔄 Reindex Button:**
- Large button at top of panel
- Opens reindex modal
- Shows repository selection checklist
- Locked repos unchecked by default

**🔍 Scan for Repositories:**
- Button to discover new git repos
- Opens repository discovery interface
- Scans directories for git repositories

#### Repository Cards

Each card displays comprehensive information:

**Card Header:**
- Repository name (large, bold text)
- Repository path (small, gray text, truncated if long)

**Status Badges:**

1. **Priority Badge** (🔴/🟡/🟢)
   - 🔴 High Priority - Red background
   - 🟡 Medium Priority - Yellow background
   - 🟢 Low Priority - Green background
   - Affects search result ranking

2. **Enabled/Disabled Badge**
   - ✅ Enabled - Green background
   - ❌ Disabled - Gray background
   - Controls whether repo participates in indexing

3. **Lock Status Badge**
   - 🔒 Locked - Red background
   - 🔓 Unlocked - Green background
   - Prevents/allows reindexing

**File Statistics:**
- **📁 Available: X files (Y MB)** - Files on disk
- **✓ Indexed: Z files (N%)** - Files in search index
  - Green if > 0% indexed
  - Gray if 0% indexed
  - Percentage shows coverage

**Indexing Statistics Table:**
(If repository has been indexed)

Shows for each index type (keyword/vector):
- **Type** - keyword or vector
- **Files** - Count of indexed files
- **Time** - Last index time (seconds)
- **When** - Relative time (e.g., "2 hours ago")

**Action Buttons:**

1. **🔓 Unlock / 🔒 Lock**
   - Toggles exclusion status
   - Locked repos can't be reindexed
   - Protects production/stable repos

2. **🗑️ Remove from Config**
   - Removes repo from configuration
   - Does NOT delete files from disk
   - Confirmation dialog shown

3. **⚙️ Configure**
   - Opens configuration modal
   - Edit enabled status
   - Set priority level
   - Configure exclude patterns
   - Toggle lock status

4. **📄 README** (if available)
   - Opens README viewer modal
   - Renders markdown with syntax highlighting
   - Shows file path at bottom

### Activity Log (Right Sidebar)

#### Log Header

**Activity Log Title**
- Shows current log count
- Example: "Activity Log (45 entries)"

**Filter Buttons:**
- **All** - Show all log entries
- **✅ Success** - Show only successful operations
- **⚠️ Warning** - Show only warnings
- **❌ Error** - Show only errors
- **ℹ️ Info** - Show only informational messages

**Action Buttons:**
- **🗑️ Clear Log** - Remove all entries
- **📥 Export** - Download log as text file
- **⏸️ Auto-scroll** toggle - Enable/disable automatic scrolling

#### Log Entries

Each entry shows:

1. **Timestamp** - Precise time (HH:MM:SS)
2. **Icon** - Type indicator (✅⚠️❌ℹ️)
3. **Message** - Description of operation
4. **Details** - Additional context (expandable)

**Entry Color Coding:**
- Green border - Success
- Yellow border - Warning
- Red border - Error
- Blue border - Info

**Entry Actions:**
- Click to expand/collapse details
- Copy message to clipboard
- Filter by similar messages

### LLM Manager (Bottom Section)

#### LLM Table

**Table Columns:**

1. **Model**
   - Model filename
   - Full path shown on hover
   - Color-coded by status:
     - Green text - Running
     - Gray text - Stopped

2. **Size**
   - File size in GB/MB
   - Format: "4.2 GB"

3. **Status**
   - **🟢 Running** - Green badge
     - Shows process PID
     - Shows port number
   - **⚪ Stopped** - Gray badge
     - "Not started" message

4. **Mode**
   - Dropdown selector
   - Options:
     - **Basic** - No function calling
     - **Tools** - Function calling enabled (--jinja)
     - **Performance** - Parallel processing
     - **Extended** - 32k context
   - Disabled while LLM is running

5. **Actions**
   - **▶️ Start** button (when stopped)
     - Launches llama-server process
     - Changes to Stop button when running
   - **⏹️ Stop** button (when running)
     - Gracefully stops llama-server
     - Changes back to Start button
   - **🔄 Restart** button (when running)
     - Stop then start in one action

#### LLM Status Indicators

**Starting:**
- Button shows "Starting..."
- Spinner animation
- Status badge shows "⏳ Starting"

**Running:**
- Status badge shows port and PID
- Example: "🟢 Running on :57291 (PID: 12345)"
- Stop/Restart buttons enabled

**Stopping:**
- Button shows "Stopping..."
- Status badge shows "⏳ Stopping"

**Error:**
- Status badge shows "❌ Failed to start"
- Error message displayed below table
- Check logs link provided

#### LLM Configuration

**Auto-detected Models:**
- Scans `/Users/liborballaty/llms/` directory
- Finds all .gguf files
- Automatically populates table

**Model Path Format:**
```
/Users/username/llms/model-name/filename.gguf
```

**Supported Quantizations:**
- Q4_K_M - 4-bit (fastest, least accurate)
- Q5_K_M - 5-bit (balanced)
- Q6_K - 6-bit (good quality)
- Q8_0 - 8-bit (high quality, slower)

### Configure Repository Modal

Opens when clicking **⚙️ Configure** on a repository card.

**Modal Sections:**

1. **Status (Enabled/Disabled)**
   - Radio button toggle
   - ✅ Enabled - Repository active for indexing
   - ❌ Disabled - Repository ignored

2. **Priority**
   - Dropdown selector
   - 🔴 High Priority - Ranked first in results
   - 🟡 Medium Priority - Standard ranking
   - 🟢 Low Priority - Ranked last

3. **Protection (Locked/Unlocked)**
   - Radio button toggle
   - 🔓 Unlocked - Can be reindexed
   - 🔒 Locked - Protected from reindexing

4. **Exclude Patterns**
   - Multi-line textarea
   - One glob pattern per line
   - Example patterns shown as placeholder
   - Syntax: `**/directory/**`, `**/*.ext`

**Modal Actions:**
- **Cancel** - Close without saving
- **💾 Save Changes** - Apply configuration
  - Saves to config/repositories.yaml
  - Refreshes repository list
  - Shows success message in Activity Log

### User Manual Modal

Opens when clicking **📖 User Manual** in header.

**Modal Features:**
- Full-screen overlay
- Markdown rendering with syntax highlighting
- Table of contents with anchor links
- Smooth scrolling navigation
- **✕ Close** button (top-right)
- **ESC key** to close
- Scrollable content area

### Reindex Modal

Opens when clicking **🔄 Reindex** button.

**Modal Content:**

1. **Repository Selection Checklist**
   - Shows all repositories
   - Checkboxes for each repository
   - Locked repos unchecked by default
   - Shows estimated file counts

2. **Reindex Options**
   - **Force Full Reindex** checkbox
     - If unchecked: Incremental (only changed files)
     - If checked: Full reindex (all files)

3. **Warning Messages**
   - Shows if large number of files selected
   - Estimates processing time
   - Warns about locked repositories

**Modal Actions:**
- **Cancel** - Close without reindexing
- **Proceed** - Start reindexing
  - Background process starts
  - Progress shown in Activity Log
  - Notification when complete

---

## Search Features

### Hybrid Search (Recommended)

Combines keyword and vector search using **Reciprocal Rank Fusion (RRF)**.

**How it works:**
1. Runs keyword search (BM25 algorithm)
2. Runs vector search (cosine similarity)
3. Merges results using rank-based scoring
4. Returns top results sorted by combined score

**Best for:**
- General queries
- Mixed technical/natural language
- When you're not sure which search type to use

**Example:**
```
Query: "database connection pool settings"
```

### Keyword Search

Fast exact and fuzzy text matching using Meilisearch.

**Features:**
- Typo tolerance
- Prefix matching
- Stop word removal
- Custom ranking

**Best for:**
- Exact file/function names
- Specific error messages
- Code snippets
- Technical identifiers

**Example:**
```
Query: "DatabaseConnectionPool.getConnection()"
```

### Vector Search

Semantic similarity using sentence embeddings (all-MiniLM-L6-v2).

**Features:**
- Understands meaning, not just keywords
- Finds conceptually similar content
- Language-agnostic
- Context-aware

**Best for:**
- Concept exploration
- "How does X work?" questions
- Finding similar implementations
- Cross-language patterns

**Example:**
```
Query: "how is user authentication handled?"
```

### Search Result Details

Each result shows:
- **File path** (clickable)
- **Repository** name
- **Content preview** with highlighted matches
- **Match score** (relevance percentage)
- **File type** indicator

**Actions:**
- Click path to copy
- Hover for full context
- Filter by repository

---

## Repository Management

### Adding Repositories

**Method 1: Manual Configuration**

Edit `config/repositories.yaml`:

```yaml
repositories:
  - name: myproject
    path: /Users/username/projects/myproject
    enabled: true
    priority: medium
    excluded: false
    auto_reindex: true
    file_patterns:
      include:
        - "**/*.md"
        - "**/*.py"
      exclude:
        - "**/node_modules/**"
        - "**/.git/**"
```

**Method 2: Repository Discovery (Web UI)**

1. Click "🔍 Scan for Repositories"
2. Enter base directory path
3. Configure scan options:
   - **Max Depth**: How deep to search (1-5 levels)
   - **Exclude Patterns**: Directories to skip
4. Click "Scan Now"
5. Review discovered repositories
6. Select repositories to add
7. Click "Add Selected Repositories"

**Method 3: API**

```bash
curl -X POST "http://localhost:3002/repositories/add" \
  -H "Content-Type: application/json" \
  -d '{
    "directories": ["/path/to/scan"],
    "max_depth": 3,
    "auto_add": false
  }'
```

### Bulk Repository Actions

Apply actions to all repositories at once using the bulk action buttons:

**Available Bulk Actions:**
- **✅ Enable All**: Enable all repositories for indexing and searching
- **❌ Disable All**: Disable all repositories (stops indexing and searching)
- **🔓 Unlock All**: Unlock all repositories (allows reindexing)
- **🔒 Lock All**: Lock all repositories (prevents reindexing)

**How to Use:**
1. Navigate to the Repository Management tab
2. Click the desired bulk action button
3. Confirm the action when prompted
4. Wait for the "✓ Done!" confirmation
5. Repository list will refresh automatically

**Loading Indicators:**
- Buttons show a spinner and "Processing..." during execution
- Briefly displays "✓ Done!" on success
- Returns to normal state after completion

**Use Cases:**
- **Enable All**: After initial setup or when restoring full search capability
- **Disable All**: When troubleshooting or temporarily suspending all indexing
- **Unlock All**: Before running a full reindex across all repositories
- **Lock All**: To protect stable repositories from accidental reindexing

### Repository Configuration

Click **⚙️ Configure** on any repository card to edit:

**Status:**
- **✅ Enabled**: Repository is active for indexing/searching
- **❌ Disabled**: Repository is ignored

**Priority:**
- **🔴 High**: Results ranked first
- **🟡 Medium**: Standard ranking
- **🟢 Low**: Results ranked last

**Protection:**
- **🔓 Unlocked**: Can be reindexed
- **🔒 Locked**: Protected from reindexing

**Exclude Patterns:**

Glob patterns for files to skip during indexing:

```
**/node_modules/**
**/.git/**
**/venv/**
**/__pycache__/**
**/*.log
**/temp/**
```

**Pattern Syntax:**
- `**` matches any number of directories
- `*` matches any characters in a filename
- One pattern per line

### Removing Repositories

**Option 1: Web UI**

1. Click **🗑️ Remove from Config** on repository card
2. Confirm removal
3. Repository is removed from configuration
4. **Note**: Files on disk are NOT deleted

**Option 2: Manual**

Edit `config/repositories.yaml` and remove the repository entry.

**Option 3: API**

```bash
curl -X DELETE "http://localhost:3002/repositories/myproject"
```

---

## Indexing & Reindexing

### Initial Indexing

When you add a new repository:

1. Server scans directory for matching files
2. Files are indexed in both Meilisearch and ChromaDB
3. Metadata is stored in SQLite database
4. Progress shown in Activity Log

**Time estimates:**
- 1,000 files: ~2-5 minutes
- 10,000 files: ~20-50 minutes
- 50,000 files: ~2-4 hours

### Incremental Reindexing

Reindexing is **incremental** - only changed files are processed.

**Triggers:**
- Manual: Click "🔄 Reindex" button
- Automatic: File watcher detects changes (if enabled)
- API: POST to `/reindex` endpoint

**How it works:**
1. Compares file modification times with database
2. Only indexes files that changed since last index
3. Deletes entries for removed files
4. Updates metadata for modified files

**Example:**
```
Repository: 10,000 total files
Changed: 50 files
Time: ~30 seconds (vs 30 minutes full reindex)
```

### Reindex Options (Web UI)

1. Click "🔄 Reindex" button
2. Modal shows repository selection
3. Check repositories to reindex
4. **Locked repositories** are unchecked by default
5. Click "Proceed" to start

**Smart Features:**
- Shows estimated file counts
- Warns if large number of files
- Prevents accidental reindex of locked repos
- Runs incrementally by default

### File Watcher (Auto-Reindex)

Enable in repository configuration:

```yaml
repositories:
  - name: myproject
    auto_reindex: true  # Enable file watcher
```

**Behavior:**
- Watches for file changes in real-time
- Triggers reindex after 2 seconds of inactivity
- Only indexes changed files
- Works in background

**Performance:**
- Low CPU usage (~0.1%)
- Instant search result updates
- No manual reindexing needed

---

## MCP Integration

### What is MCP?

**MCP (Model Context Protocol)** is an open standard that enables AI tools like Claude Code to interact with external systems through a standardized interface. MyRAGDB implements MCP to allow AI assistants to search your codebase directly.

**Key Benefits:**
- AI tools can autonomously search your repositories
- No manual copy-pasting of code
- Real-time context retrieval during conversations
- Seamless integration with Claude Code and other MCP clients

### How MyRAGDB Uses MCP

MyRAGDB includes an **MCP HTTP Middleware** server that:
- Runs on **port 8093**
- Automatically starts with `./start.sh`
- Exposes MyRAGDB search functionality as MCP tools
- Translates MCP protocol requests to REST API calls

### Architecture

```
┌─────────────────┐
│   Claude Code   │ ← AI assistant
└────────┬────────┘
         │ (1) User asks: "Find authentication code"
         ↓
┌─────────────────┐
│  MCP Middleware │ ← Translates MCP → REST API
│   Port 8093     │
└────────┬────────┘
         │ (2) Calls /search endpoint
         ↓
┌─────────────────┐
│  FastAPI Server │ ← Performs hybrid search
│   Port 3003     │
└────────┬────────┘
         │ (3) Returns search results
         ↓
┌─────────────────┐
│   Claude Code   │ ← AI analyzes results and responds
└─────────────────┘
```

### Available MCP Tools

When Claude Code connects to MyRAGDB, it gains access to these tools:

#### 1. **myragdb_search**
Search across all indexed repositories using hybrid search.

**Parameters:**
- `query` (required): Search query text
- `mode` (optional): "hybrid", "keyword", or "vector" (default: hybrid)
- `limit` (optional): Maximum results (default: 10)

**Example:**
```
User: "Find all authentication functions"
Claude: [Uses myragdb_search tool with query="authentication functions"]
→ Returns relevant code files and implementations
```

#### 2. **myragdb_repositories**
List all indexed repositories with statistics.

**Example:**
```
User: "What repositories are indexed?"
Claude: [Uses myragdb_repositories tool]
→ Returns list with file counts, update times, priorities
```

### Setting Up MCP with Claude Code

The MCP middleware is **automatically started** by the `./start.sh` script. No additional configuration needed!

**Startup sequence:**
```bash
./start.sh

# Step 1: Start Meilisearch (port 7700)
# Step 2: Start MyRAGDB API (port 3003)
# Step 3: Start MCP Middleware (port 8093) ← Enables AI tool access
```

**Verify MCP is running:**
```bash
# Check if MCP middleware is active
lsof -i :8093

# Should show:
# COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# Python    12345 user   3u   IPv4  ...   TCP *:8093 (LISTEN)
```

### Using MCP with Claude Code

Once MyRAGDB is running, Claude Code can automatically discover and use the MCP tools:

**Example workflow:**

1. **Start MyRAGDB:**
   ```bash
   ./start.sh
   ```

2. **Ask Claude Code:**
   ```
   User: "Find all files that implement user authentication"

   Claude: Let me search your codebase for authentication implementations.
   [Automatically uses myragdb_search tool]

   Results:
   - src/auth/login.py (95% relevance)
   - src/auth/session.py (87% relevance)
   - tests/test_auth.py (76% relevance)

   I found 3 files related to authentication. The main implementation
   is in src/auth/login.py which handles user login, password hashing,
   and session creation.
   ```

3. **Claude Code has full context** without you copying code manually!

### MCP Configuration

The MCP middleware configuration is in `mcp_server/server.py`:

**Default settings:**
```python
# Port configuration
MCP_PORT = 8093

# API endpoint
API_BASE_URL = "http://localhost:3003"

# Tool definitions
tools = [
    {
        "name": "myragdb_search",
        "description": "Search code repositories",
        "parameters": {...}
    },
    {
        "name": "myragdb_repositories",
        "description": "List indexed repositories",
        "parameters": {...}
    }
]
```

### Troubleshooting MCP

#### MCP middleware not starting

**Check if port 8093 is already in use:**
```bash
lsof -i :8093
```

**Solution:** Kill the process or change MCP_PORT in config.

#### Claude Code can't connect to MCP

**Verify middleware is running:**
```bash
curl http://localhost:8093/health

# Should return: {"status": "healthy"}
```

**Check logs:**
```bash
tail -f /tmp/mcp_middleware.log
```

#### MCP tools not appearing in Claude Code

**Restart MyRAGDB completely:**
```bash
./stop.sh
./start.sh
```

**Check Claude Code MCP configuration:**
- Ensure MCP server URL is set to `http://localhost:8093`
- Verify no firewall blocking local connections

### MCP vs Direct API Access

**When to use MCP:**
- ✅ AI assistant needs autonomous search (Claude Code, etc.)
- ✅ Conversational context retrieval
- ✅ Multi-step reasoning with code search
- ✅ Tool-calling AI workflows

**When to use REST API directly:**
- ✅ Custom applications and scripts
- ✅ Web UI (already integrated)
- ✅ CI/CD pipelines
- ✅ Non-AI automation

Both methods access the same underlying search engine - choose based on your use case!

---

## LLM Integration

### Overview

MyRAGDB integrates local LLMs to provide AI-powered search assistance.

**Capabilities:**
- Function calling to search repositories
- Multi-step reasoning
- Code generation from search results
- Natural language queries

### Supported Models

Any GGUF model compatible with llama.cpp:

**Recommended:**
- **DeepSeek R1 Distill Qwen 32B**: Best reasoning
- **Mistral Small 3.2 24B**: Fast and accurate
- **Llama 3.1 8B**: Good balance
- **Qwen 2.5 Coder 7B**: Code-focused

### Installing Models

**Option 1: Hugging Face CLI**

```bash
huggingface-cli download \
  TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q8_0.gguf \
  --local-dir /Users/username/llms/
```

**Option 2: Manual Download**

1. Visit https://huggingface.co/models
2. Search for GGUF models
3. Download .gguf file
4. Place in `/Users/username/llms/` directory

### Adding Models to UI

Models are auto-detected from these directories:
- `/Users/liborballaty/llms/`
- Custom paths in configuration

**To add custom directory:**

Edit server code or configuration to include your path.

### Starting an LLM

1. Go to **LLM Manager** section
2. Find your model in the list
3. Select **Mode**:
   - **Basic**: No function calling
   - **Tools**: Function calling enabled (recommended)
   - **Performance**: Parallel processing
   - **Extended**: 32k context
4. Click **▶️ Start**
5. Wait for status to show "Running"

### Using LLM with Function Calling

**Example conversation:**

```
User: Search for authentication code in the user service

LLM: [Calls search_repositories function]
     Found 15 results about authentication in user_service.py

     The authentication is handled in authenticate_user() function
     which validates JWT tokens and checks user permissions...
```

**Function Available:**
- `search_repositories(query, repositories, limit)`

**LLM can:**
- Decide when to search
- Refine queries based on results
- Combine multiple searches
- Explain code found

### Performance Tuning

**GPU Acceleration:**

Edit startup script to add GPU layers:
```bash
llama-server --model model.gguf --n-gpu-layers 35
```

**Context Window:**
- Basic: 2048 tokens
- Extended: 32768 tokens

**Batch Size:**
- Default: 512
- High performance: 2048

---

## API Reference

### Base URL

```
http://localhost:3002
```

### Authentication

Currently no authentication required (local use only).

### Endpoints

#### Search

**POST /search**

Perform hybrid search across repositories.

```bash
curl -X POST "http://localhost:3002/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication",
    "mode": "hybrid",
    "repositories": ["myproject"],
    "file_types": [".py"],
    "limit": 10
  }'
```

**Response:**
```json
{
  "results": [
    {
      "file_path": "/path/to/file.py",
      "repository": "myproject",
      "content": "def authenticate_user(username, password)...",
      "score": 0.95,
      "match_type": "hybrid"
    }
  ],
  "total_results": 15,
  "search_time_ms": 234
}
```

#### Repositories

**GET /repositories**

List all configured repositories.

```bash
curl "http://localhost:3002/repositories"
```

**POST /repositories/add**

Add repositories via discovery.

```bash
curl -X POST "http://localhost:3002/repositories/add" \
  -H "Content-Type: application/json" \
  -d '{
    "directories": ["/Users/username/projects"],
    "max_depth": 3,
    "exclude_patterns": ["archive-*", "old-*"]
  }'
```

**PATCH /repositories/{repo_name}**

Update repository configuration.

```bash
curl -X PATCH "http://localhost:3002/repositories/myproject?enabled=true&priority=high" \
  -H "Content-Type: application/json"
```

**DELETE /repositories/{repo_name}**

Remove repository from configuration.

```bash
curl -X DELETE "http://localhost:3002/repositories/myproject"
```

#### Indexing

**POST /reindex**

Trigger incremental reindexing.

```bash
curl -X POST "http://localhost:3002/reindex" \
  -H "Content-Type: application/json" \
  -d '{
    "repositories": ["myproject"],
    "force": false
  }'
```

**GET /index/status**

Get indexing status and statistics.

```bash
curl "http://localhost:3002/index/status"
```

### Python Client

```python
from myragdb import SearchClient

# Initialize client
client = SearchClient(base_url="http://localhost:3002")

# Search
results = client.search(
    query="user authentication",
    mode="hybrid",
    repositories=["myproject"],
    limit=10
)

# Print results
for result in results:
    print(f"{result['file_path']}: {result['score']}")
```

---

## Configuration

### Repository Configuration

**File:** `config/repositories.yaml`

```yaml
repositories:
  - name: myproject              # Unique identifier
    path: /path/to/repo          # Absolute path to repository
    enabled: true                # Enable/disable indexing
    priority: high               # Search result ranking (high/medium/low)
    excluded: false              # Lock from reindexing
    auto_reindex: true           # Enable file watcher
    file_patterns:
      include:                   # Glob patterns to include
        - "**/*.md"
        - "**/*.py"
        - "**/*.ts"
        - "**/*.tsx"
      exclude:                   # Glob patterns to exclude
        - "**/node_modules/**"
        - "**/.git/**"
        - "**/venv/**"
        - "**/__pycache__/**"
        - "**/*.pyc"
```

### Search Configuration

**Keyword Search Weights:** 0.4
**Vector Search Weights:** 0.6

**Reciprocal Rank Fusion (RRF):**
```python
RRF_K = 60  # Constant for rank fusion algorithm
```

**Embedding Model:**
```
sentence-transformers/all-MiniLM-L6-v2
Dimensions: 384
```

### Server Configuration

**Port:** 3002
**Host:** 0.0.0.0
**CORS:** Enabled for all origins (local dev)

**Database Paths:**
- Metadata: `data/file_metadata.db`
- Meilisearch: `data/meilisearch/`
- ChromaDB: `data/chromadb/`

---

## Troubleshooting

### macOS App Bundle Issues

#### App won't start

**Check logs:**
```bash
./view-app-logs.sh
```

This shows:
- App bundle launcher log
- Server log
- Middleware log

**Common causes:**

1. **PATH issues** - Python or Meilisearch not found
   - Check app bundle log: `tail -f /tmp/myragdb_app_bundle.log`
   - Look for: `Python: /opt/homebrew/bin/python3`
   - Look for: `Meilisearch: /opt/homebrew/bin/meilisearch`
   - If "not found", verify installations:
     ```bash
     which python3
     which meilisearch
     brew install meilisearch  # if missing
     ```

2. **Permission denied** - App not executable
   ```bash
   chmod +x MyRAGDB.app/Contents/MacOS/MyRAGDB
   chmod +x start.sh
   chmod +x stop.sh
   ```

3. **Gatekeeper blocking** - macOS quarantine attribute
   ```bash
   xattr -d com.apple.quarantine MyRAGDB.app
   ```

#### Browser opens but page won't load

**Wait for services to start:**
- First launch takes 10-15 seconds
- Check app bundle log for "Server is ready on port 3003!"
- Look for "Opening web UI in browser..."

**Verify server is running:**
```bash
lsof -i :3003
# Should show Python process listening on port 3003
```

**Check for errors:**
```bash
tail -f /tmp/myragdb_server.log
```

#### Services won't stop

**Use Force Quit:**
1. Right-click app icon in Dock
2. Select "Force Quit"
3. App bundle cleanup automatically stops services

**Manual cleanup (if needed):**
```bash
./stop.sh

# If stop.sh fails:
pkill -f "python.*myragdb"
pkill -f meilisearch
rm -f .server.pid .middleware.pid .meilisearch.pid
```

#### App restarts services when reopened

This is normal behavior:
- **If services running**: Opens browser only
- **If services stopped**: Starts everything and opens browser

To verify:
```bash
lsof -i :3003  # Check if server running
```

#### Logs location

All logs are in `/tmp/`:
- `/tmp/myragdb_app_bundle.log` - App launcher
- `/tmp/myragdb_server.log` - API server
- `/tmp/mcp_middleware.log` - MCP middleware

**View all logs:**
```bash
./view-app-logs.sh
```

**Follow logs in real-time:**
```bash
tail -f /tmp/myragdb_app_bundle.log
tail -f /tmp/myragdb_server.log
tail -f /tmp/mcp_middleware.log
```

### Common Issues

#### Search returns no results

**Possible causes:**
1. Repositories not indexed yet
2. Query too specific
3. File type filter excluding results

**Solutions:**
1. Click "🔄 Reindex" to index repositories
2. Try broader search terms
3. Remove file type filters
4. Switch to "Hybrid" search mode

#### Indexing is slow

**Possible causes:**
1. Large number of files
2. Slow disk I/O
3. Resource constraints

**Solutions:**
1. Add exclude patterns for large directories
2. Close other applications
3. Use incremental reindexing
4. Increase system resources

#### LLM won't start

**Possible causes:**
1. Insufficient RAM
2. Model file corrupted
3. Port already in use

**Solutions:**
1. Use smaller quantized model (Q4_K_M instead of Q8_0)
2. Re-download model file
3. Stop other llama-server instances:
   ```bash
   pkill llama-server
   ```

#### Server won't start

**Possible causes:**
1. Port 3003 already in use
2. Meilisearch not running
3. Missing dependencies
4. Virtual environment not activated

**Solutions:**
1. **Use the stop script first:**
   ```bash
   ./stop.sh
   ```
   Then try starting again:
   ```bash
   ./start.sh
   ```

2. **Check for conflicting processes:**
   ```bash
   lsof -i :3003  # MyRAGDB API
   lsof -i :7700  # Meilisearch
   lsof -i :8093  # MCP Middleware
   ```

3. **Check logs for errors:**
   ```bash
   tail -f /tmp/myragdb_server.log       # API server logs
   tail -f /tmp/meilisearch.log          # Meilisearch logs
   tail -f /tmp/mcp_middleware.log       # MCP middleware logs
   ```

4. **Manual cleanup (if stop.sh fails):**
   ```bash
   # Kill processes on specific ports
   kill $(lsof -ti:3003)  # API server
   kill $(lsof -ti:7700)  # Meilisearch
   kill $(lsof -ti:8093)  # MCP middleware
   ```

5. **Reinstall dependencies:**
   ```bash
   source venv/bin/activate
   pip install -e .
   ```

### Error Messages

#### "Repository path does not exist"

**Solution:** Update path in `config/repositories.yaml` with correct absolute path.

#### "Failed to connect to Meilisearch"

**Solution:** Start Meilisearch:
```bash
meilisearch --http-addr 127.0.0.1:7700
```

#### "Database is locked"

**Solution:** Close other instances accessing the database:
```bash
pkill python
```

Then restart server.

### Logs

**Server logs:** Check terminal output
**Activity log:** View in Web UI
**Debug mode:** Set environment variable:

```bash
export DEBUG=1
python -m myragdb.api.server
```

---

## Best Practices

### Repository Organization

**Do:**
- Group related projects in same directory
- Use descriptive repository names
- Set appropriate priorities
- Lock production repositories

**Don't:**
- Index system directories (/, /usr/, etc.)
- Mix unrelated projects
- Enable auto-reindex on large repos
- Index temporary directories

### Search Optimization

**For best results:**
1. Start with hybrid search
2. Use specific technical terms
3. Include file extensions when known
4. Filter by repository for focused results
5. Use vector search for concepts
6. Use keyword search for exact matches

**Query tips:**
```
Good: "JWT token validation middleware"
Better: "JWT token validation .js"
Best: "JWT token validation middleware authentication.js"
```

### Indexing Strategy

**Initial setup:**
1. Add all repositories disabled
2. Enable and index one at a time
3. Verify results before adding more
4. Set priorities based on usage
5. Lock stable repositories

**Maintenance:**
1. Reindex monthly for stable repos
2. Enable auto-reindex for active development
3. Remove archived/old repositories
4. Update exclude patterns as needed

### Performance Optimization

**For large codebases (50k+ files):**
1. Aggressive exclude patterns
2. Disable auto-reindex
3. Schedule reindexing during off-hours
4. Use keyword search when possible
5. Filter by repository/file type

**For fast searches:**
1. Enable result caching
2. Use specific queries
3. Limit result count
4. Filter by known repositories

### Security

**Important notes:**
- MyRAGDB is designed for **local use only**
- No authentication/authorization by default
- All repositories are searchable by anyone with access
- Do not expose port 3002 to internet
- Keep sensitive repos excluded or disabled

**For production use:**
1. Add authentication middleware
2. Implement repository-level permissions
3. Use HTTPS/TLS
4. Add rate limiting
5. Audit search logs

---

## Appendix

### Keyboard Shortcuts

**Web UI:**
- `Ctrl/Cmd + K`: Focus search box
- `Enter`: Execute search
- `Esc`: Close modals

### File Type Extensions

**Supported by default:**
- Code: .py, .js, .ts, .tsx, .jsx, .java, .go, .rs, .c, .cpp, .h
- Docs: .md, .txt, .rst, .adoc
- Config: .json, .yaml, .yml, .toml, .xml
- Web: .html, .css, .scss, .vue
- Mobile: .dart, .swift, .kt

### Glossary

- **BM25**: Best Match 25, ranking function for keyword search
- **ChromaDB**: Vector database for embeddings
- **GGUF**: File format for quantized LLM models
- **Incremental Indexing**: Only index changed files
- **Meilisearch**: Fast, typo-tolerant search engine
- **RRF**: Reciprocal Rank Fusion, algorithm for combining search results
- **Vector Embedding**: Numerical representation of text meaning

### Additional Resources

- **Architecture Documentation**: `docs/myragdb-SYSTEM_ARCHITECTURE.md`
- **API Specification**: `docs/universal-search-service-spec.md`
- **Web UI Specification**: `docs/WEB-UI-SPEC.md`
- **GitHub Issues**: https://github.com/your-org/myragdb/issues

---

## Support

For questions or issues:
- **Email**: libor@arionetworks.com
- **Documentation**: `docs/` directory
- **Logs**: Check Activity Log in Web UI

---

*Last updated: 2026-01-07*
