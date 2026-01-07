# Non-Repository Directories - UI Design

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/DIRECTORIES_UI_DESIGN.md
**Description:** Visual and interaction design for directory management and search filtering
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Settings Page - Directories Tab

### Page Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚙️ Settings                                          [Back to Search] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┬────────────────────────────────────────────────┐  │
│  │             │                                                 │  │
│  │ Navigation  │  Directories                                   │  │
│  │             │                                                 │  │
│  │ › Repos     │  ┌──────────────────────────────────────────┐  │  │
│  │ › Directories   │ ~/projects/documentation                    │  │  │
│  │   General   │  │ Name: Documentation           [Edit]    │  │  │
│  │   Search    │  │ Path: /Users/user/projects/documentation    │  │  │
│  │   Advanced  │  │ Status: ✅ Enabled • 2,341 files indexed │  │  │
│  │             │  │ Last indexed: 1 hour ago                  │  │  │
│  │             │  │ Size: 845 MB                              │  │  │
│  │             │  │                                           │  │  │
│  │             │  │ [Reindex] [Disable] [Remove]             │  │  │
│  │             │  └──────────────────────────────────────────┘  │  │
│  │             │                                                 │  │
│  │             │  ┌──────────────────────────────────────────┐  │  │
│  │             │  │ ~/archive/research                           │  │  │
│  │             │  │ Name: Research Archive       [Edit]     │  │  │
│  │             │  │ Path: /Users/user/archive/research          │  │  │
│  │             │  │ Status: ⏸️  Disabled • 0 files searched   │  │  │
│  │             │  │ Last indexed: 3 days ago                  │  │  │
│  │             │  │ Size: 1.2 GB                              │  │  │
│  │             │  │                                           │  │  │
│  │             │  │ [Reindex] [Enable] [Remove]              │  │  │
│  │             │  └──────────────────────────────────────────┘  │  │
│  │             │                                                 │  │
│  │             │  ┌──────────────────────────────────────────┐  │  │
│  │             │  │ ~/Downloads/shared-docs                      │  │  │
│  │             │  │ Name: Shared Docs            [Edit]     │  │  │
│  │             │  │ Path: /Users/user/Downloads/shared-docs     │  │  │
│  │             │  │ Status: ✅ Enabled • 456 files indexed   │  │  │
│  │             │  │ Last indexed: 30 minutes ago               │  │  │
│  │             │  │ Size: 234 MB                              │  │  │
│  │             │  │                                           │  │  │
│  │             │  │ [Reindex] [Disable] [Remove]             │  │  │
│  │             │  └──────────────────────────────────────────┘  │  │
│  │             │                                                 │  │
│  │             │  [+ Add New Directory]                          │  │
│  │             │                                                 │  │
│  └─────────────┴────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Directory Card Component

#### Collapsed State
```
┌────────────────────────────────────────────────────┐
│ 📁 ~/projects/documentation         [Edit][Show▼]  │
│    Documentation • ✅ Enabled • 1h ago             │
└────────────────────────────────────────────────────┘
```

#### Expanded State
```
┌──────────────────────────────────────────────────────────┐
│ 📁 ~/projects/documentation         [Edit][Hide▲]      │
│    Documentation • ✅ Enabled • 1 hour ago              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Path:        /Users/user/projects/documentation        │
│ Size:        845 MB                                    │
│ Files:       2,341 indexed                             │
│ Created:     Jan 2, 2025                               │
│ Last Index:  Jan 7, 2025 at 2:30 PM                    │
│                                                          │
│ Indexing Status                                          │
│ ├─ Keyword Index:   ✅ Complete (2,341 files)          │
│ └─ Vector Index:    ✅ Complete (2,341 files)          │
│                                                          │
│ Actions:                                                │
│ [Reindex] [Reindex Full] [Disable] [Edit] [Remove]    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Add Directory Dialog

```
┌──────────────────────────────────────────────────┐
│ Add New Directory              [✕]               │
├──────────────────────────────────────────────────┤
│                                                  │
│ Directory Path *                                 │
│ ┌──────────────────────────────────────────────┐│
│ │ /Users/user/projects/__________ [Browse...] ││
│ └──────────────────────────────────────────────┘│
│                                                  │
│ Display Name *                                   │
│ ┌──────────────────────────────────────────────┐│
│ │ My Documentation Project___________________  ││
│ └──────────────────────────────────────────────┘│
│                                                  │
│ Notes (optional)                                 │
│ ┌──────────────────────────────────────────────┐│
│ │ Shared team documentation and guides         ││
│ │                                              ││
│ │                                              ││
│ └──────────────────────────────────────────────┘│
│                                                  │
│ ☑ Enable this directory for search               │
│                                                  │
│ [Cancel]  [Add Directory]                       │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Directory Browser (Tree Picker)

```
┌────────────────────────────────────────────┐
│ Select Directory                    [✕]    │
├────────────────────────────────────────────┤
│                                            │
│ Search: [________] [🔍 Find]               │
│                                            │
│ ▼ Users                                    │
│   ▼ user                                   │
│     ▼ projects                             │
│       ▼ GitHubProjectsDocuments            │
│         ○ xLLMArionComply                  │
│         ○ RepoDot                          │
│       ○ mysite                             │
│       ▶ archive                            │
│     ▼ Documents                            │
│       ○ Personal Notes                     │
│       ○ Research Papers                    │
│     ▼ Downloads                            │
│       ○ shared-docs  ← (can select here)   │
│                                            │
│ Recent:                                    │
│ • /Users/user/Documents/Research           │
│ • /Users/user/Downloads/shared-docs        │
│                                            │
│ [Bookmarks ▼]  [Cancel]  [Select]         │
│                                            │
└────────────────────────────────────────────┘
```

---

## Search Page - Filters Integration

### Filters Panel (New State)

```
┌──────────────────────┐
│      FILTERS         │
├──────────────────────┤
│                      │
│ REPOSITORIES         │
│ ☑ xLLMArionComply    │
│ ☑ RepoDot            │
│ ☐ ArionNetworks      │
│                      │
│ [Select All] [None]  │
│                      │
├──────────────────────┤
│                      │
│ DIRECTORIES          │ ← NEW SECTION
│ ▼ Documentation      │
│   ☑ My Docs (2.3K)   │
│   ☑ Research (456)   │
│   ☐ Archive (0)      │
│                      │
│ ▶ Downloads          │
│   ☑ shared-docs (23) │
│                      │
│ [Select All] [None]  │
│                      │
├──────────────────────┤
│                      │
│ FILE TYPES           │
│ ☑ .md                │
│ ☑ .py                │
│ ☑ .ts                │
│ ☐ .dart              │
│                      │
├──────────────────────┤
│                      │
│ SEARCH MODE          │
│ ● Hybrid             │
│ ○ Keyword            │
│ ○ Semantic           │
│                      │
└──────────────────────┘
```

### Hierarchical Directory Display

The directories section shows:
- **Group by Parent:** Directories organized by top-level folder
- **Collapsible:** Click to expand/collapse groups
- **File Count:** Shows how many indexed files in each
- **Status Indicator:** ✓ for enabled, ✗ for disabled

Example:
```
▼ Project Directories (3,541 files)
  ☑ xLLMArionComply/docs     (2,341 files)
  ☑ RepoDot/documentation    (1,200 files)

▼ Personal (1,256 files)
  ☑ Research Archive         (890 files)
  ☐ Old Projects (disabled)  (366 files)

▶ External (0 files)
  (collapsed)
```

### Search Results with Source Information

```
Results (12 found in 234ms)

📄 Authentication Flow Guide
   📁 Documentation • 📅 2 days ago
   Score: 0.95 | Keyword: 0.92 | Vector: 0.97

   ...JWT tokens are validated using Supabase
   authentication. The flow begins with user
   login and ends with session creation...

   [📂 Open] [📋 Copy] [👁️ Preview]

📄 auth.py
   📦 xLLMArionComply • 📅 1 week ago
   Score: 0.87 | Keyword: 0.85 | Vector: 0.89

   async def authenticate_user(token: str):
       """Validate JWT and create session..."""

   [📂 Open] [📋 Copy] [👁️ Preview]

📄 setup-guide.md
   📁 Research Archive • 📅 3 days ago  ← Directory source
   Score: 0.81 | Keyword: 0.78 | Vector: 0.84

   ...To set up authentication for your
   application, follow these steps...

   [📂 Open] [📋 Copy] [👁️ Preview]
```

---

## Component Specifications

### DirectoriesPage.tsx
- Full page layout with sidebar navigation
- Displays DirectoryList component
- Add button at bottom
- Empty state message when no directories

### DirectoryCard.tsx
- Collapsible card showing directory info
- Displays: name, path, status, file count, size, timestamps
- Action buttons: Edit, Reindex, Disable/Enable, Remove
- Expandable details section with indexing stats

### DirectoryForm.tsx
- Modal form for adding/editing directories
- Fields: Path (with Browse button), Name, Notes, Enabled toggle
- Validation: Path must exist and be readable
- Browse button opens DirectoryBrowser (tree picker)

### DirectoryBrowser.tsx
- File system tree picker
- Search capability to filter directories
- Recent directories list
- Bookmarks support
- Single path selection

### SearchFilters.tsx (Modified)
- New DIRECTORIES section parallel to REPOSITORIES
- Hierarchical display (grouped by parent)
- Collapsible groups
- File count display
- Select All / Clear All buttons

---

## Interactions & User Flows

### Add Directory Flow
1. User clicks "[+ Add New Directory]"
2. Add Directory dialog opens
3. User clicks "Browse..." or types path
4. DirectoryBrowser modal opens
5. User selects directory from tree
6. Path fills in automatically
7. User enters name and optional notes
8. User clicks "Add Directory"
9. Directory is indexed
10. Dialog closes, directory appears in list

### Edit Directory Flow
1. User clicks "Edit" on a directory card
2. Directory Form dialog opens with current values
3. User modifies name/notes
4. User toggles enabled/disabled if needed
5. User clicks "Save Changes"
6. Dialog closes, card updates

### Search with Directory Filtering Flow
1. User types search query
2. Filters panel shows on left
3. User expands DIRECTORIES section if collapsed
4. User checks/unchecks specific directories
5. Search results update to include only selected directories
6. Results show source (repository or directory name)
7. User can click result to preview in separate pane

### Reindex Directory Flow
1. User clicks "Reindex" on directory card
2. Card shows reindexing progress bar
3. After completion, "Last indexed" timestamp updates
4. File count may change if files were added/removed

### Disable Directory Flow
1. User clicks "Disable" on directory card
2. Directory becomes grayed out, showing "Disabled"
3. Directory no longer appears in search filters
4. User can click "Enable" to re-activate

---

## Mobile Responsive Behavior

### Tablet (768px - 1199px)
- Filters sidebar becomes collapsible/hidden by default
- Directory cards displayed full width
- Modal dialogs remain readable
- Tree picker optimized for touch

### Mobile (< 768px)
- Single column layout
- Filters as bottom sheet or hidden behind button
- Directory cards full width
- Modal becomes full-screen
- Tree picker simplified (less nesting)

---

## State & Loading States

### Directory Card States
- **Loading:** Spinner, "Indexing..." message
- **Success:** ✅ checkmark, "Indexed X files"
- **Error:** ⚠️ icon, "Index failed" with error message
- **Disabled:** 🔒 icon, grayed out appearance

### Directory List States
- **Empty:** "No directories yet. [+ Add Directory]"
- **Loading:** Spinner, "Loading directories..."
- **Loaded:** Display all directory cards
- **Error:** "Failed to load directories. Retry?"

### Search Filter States
- **Uncollapsed:** Shows all directory options
- **Collapsed:** Shows "[+] X directories" button
- **All Selected:** "[▼] All X directories selected"
- **Some Selected:** "[▼] X of Y selected"
- **None Selected:** "[+] Add directories to search"

---

## Color & Visual Design

### Directory-Specific Colors
- **Primary Icon:** 📁 (folder emoji)
- **Status Badges:**
  - ✅ Green for "Enabled"
  - ⏸️ Gray for "Disabled"
  - 🔄 Blue for "Indexing"
  - ⚠️ Orange for "Error"

### Visual Hierarchy
- **Directory Name:** Large, bold
- **Path:** Small, monospace, gray
- **Status:** Medium, colored
- **Stats:** Small, gray

### Spacing & Layout
- Card padding: 16px
- Section margins: 24px
- Action buttons: 8px gap between them
- Icon-text gap: 8px

---

## Error Handling UI

### Invalid Path Error
```
┌──────────────────────────┐
│ ⚠️ Cannot add directory   │
│                          │
│ Path does not exist:    │
│ /Users/user/nonexistent  │
│                          │
│ [Try Again] [Cancel]     │
└──────────────────────────┘
```

### Permission Error
```
┌──────────────────────────────────────┐
│ ⚠️ Permission Denied                 │
│                                      │
│ Cannot read directory:               │
│ /Users/user/restricted               │
│                                      │
│ This directory may be protected by   │
│ system security policies.            │
│                                      │
│ [Dismiss]                            │
└──────────────────────────────────────┘
```

### Indexing Error
```
┌──────────────────────────────────────────┐
│ Directory: ~/projects/documentation      │
│ Status: ⚠️ Index failed                  │
│                                          │
│ Error: Could not read 3 files            │
│ Last attempt: 5 minutes ago              │
│                                          │
│ [Try Again] [Show Details] [Dismiss]    │
└──────────────────────────────────────────┘
```

---

## Keyboard & Accessibility

### Keyboard Shortcuts (Future)
- `Cmd+D` - Open Add Directory dialog
- `j/k` - Navigate directory list (if focused)
- `Enter` - Edit selected directory
- `Delete` - Remove directory (with confirmation)

### ARIA Labels
```typescript
<button aria-label="Add new directory">
  [+ Add Directory]
</button>

<section aria-label="Managed directories">
  {/* directory cards */}
</section>

<input aria-label="Search directories" />
```

### Focus Management
- Tab order: Add button → Directory cards → Edit buttons
- Focus indicators visible on all interactive elements
- Modal dialogs trap focus

---

## Search Results Enhancement

### Result Card Source Information
```
Current:
📄 docs/auth-flow.md
   📦 xLLMArionComply • 📅 2 days ago

New:
📄 docs/auth-flow.md
   📁 Documentation • 📅 2 days ago    ← Shows "Directory name"

or

📄 docs/auth-flow.md
   📦 xLLMArionComply • 📅 2 days ago  ← Still shows repo for repo files
```

### Filter Application Feedback
```
Before filtering by directory:
"12 results found in 234ms"
[Source icons: 📦 xLLMArionComply (8) | 📁 Documentation (4)]

After user selects only Documentation:
"4 results found in 98ms (filtered)"
[Source icons: 📁 Documentation (4) ▼]
```

---

## Performance Considerations

### Render Optimization
- Virtualize directory list if > 50 items
- Lazy-load directory stats on expand
- Debounce search input in tree picker
- Memoize directory card components

### Search Optimization
- Directory filter updates search in real-time
- Debounce with 300ms delay
- Show "Filtering..." status during update
- Cache search results client-side

---

## Design System Alignment

### Typography
- **Directory Names:** Headline 6 (500px+) / Headline 7 (<500px)
- **Path:** Caption
- **Status:** Body 2
- **Stats:** Caption

### Spacing Scale
- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px

### Component Reuse
- Use existing Button, Input, Modal components
- Create new DirectoryCard, DirectoryForm as composed components
- Apply existing color scheme and iconography

---

**Questions:** libor@arionetworks.com
