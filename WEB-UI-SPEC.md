# Universal Search Service - Web UI Specification

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/WEB-UI-SPEC.md
**Description:** Browser-based search interface for semantic code/documentation discovery
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-04  

---

## Executive Summary

The USS Web UI provides an intuitive, real-time search interface accessible through any modern browser. It offers advanced filtering, visual result presentation, and direct integration with development tools.

**Key Features:**
- Real-time search-as-you-type
- Visual repository/directory selection
- Syntax-highlighted code previews
- One-click VS Code integration
- Search history and favorites
- Responsive design (desktop/tablet)
- Dark mode support

**Technology Stack:**
- React 18 + TypeScript
- Tailwind CSS for styling
- Vite for build tooling
- React Query for data fetching
- Zustand for state management
- Monaco Editor for code preview

---

## Architecture

### Component Structure

```
src/
├── App.tsx                      # Main application
├── main.tsx                     # Entry point
│
├── pages/
│   ├── SearchPage.tsx           # Main search interface
│   ├── SettingsPage.tsx         # Configuration
│   ├── StatsPage.tsx            # Statistics dashboard
│   └── HistoryPage.tsx          # Search history
│
├── components/
│   ├── search/
│   │   ├── SearchBar.tsx        # Search input
│   │   ├── SearchFilters.tsx    # Repository/type filters
│   │   ├── SearchResults.tsx    # Results list
│   │   ├── ResultCard.tsx       # Individual result
│   │   └── ResultPreview.tsx    # Code preview pane
│   │
│   ├── repositories/
│   │   ├── RepositoryList.tsx   # Repository selection
│   │   ├── RepositoryCard.tsx   # Repository info card
│   │   └── DirectoryBrowser.tsx # Ad-hoc directory picker
│   │
│   ├── filters/
│   │   ├── FileTypeFilter.tsx   # File type checkboxes
│   │   ├── SearchTypeToggle.tsx # Hybrid/Keyword/Semantic
│   │   └── DateRangeFilter.tsx  # Date range picker
│   │
│   ├── layout/
│   │   ├── Header.tsx           # App header
│   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   └── Footer.tsx           # Status footer
│   │
│   └── common/
│       ├── Button.tsx           # Reusable button
│       ├── Input.tsx            # Reusable input
│       ├── Badge.tsx            # Status badges
│       ├── Tooltip.tsx          # Tooltips
│       └── Loading.tsx          # Loading spinner
│
├── hooks/
│   ├── useSearch.ts             # Search logic
│   ├── useRepositories.ts       # Repository management
│   ├── useSearchHistory.ts      # History tracking
│   └── useKeyboardShortcuts.ts  # Keyboard nav
│
├── services/
│   ├── api.ts                   # API client
│   ├── searchService.ts         # Search operations
│   ├── indexService.ts          # Index operations
│   └── configService.ts         # Configuration
│
├── stores/
│   ├── searchStore.ts           # Search state
│   ├── settingsStore.ts         # User settings
│   └── themeStore.ts            # Theme state
│
├── types/
│   ├── search.ts                # Search types
│   ├── repository.ts            # Repository types
│   └── api.ts                   # API response types
│
└── utils/
    ├── syntax-highlight.ts      # Code highlighting
    ├── date-format.ts           # Date formatting
    └── file-icons.ts            # File type icons
```

---

## Page Layouts

### Search Page (Main Interface)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔍 Universal Search                    [History] [Stats] [Settings] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Search: authentication flow_____________________ [🔍 Search] │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────┬─────────────────────────────────────────────────┐  │
│  │            │                                                  │  │
│  │ Filters    │  Results (7 found in 234ms)                     │  │
│  │            │                                                  │  │
│  │ Repos:     │  ┌──────────────────────────────────────────┐  │  │
│  │ ☑ xLLM...  │  │ 📄 docs/auth-flow.md        Score: 0.95  │  │  │
│  │ ☑ RepoDot  │  │    xLLMArionComply • 2 days ago          │  │  │
│  │ ☐ Arion... │  │                                           │  │  │
│  │            │  │    ...JWT tokens are validated using     │  │  │
│  │ Types:     │  │    Supabase authentication...            │  │  │
│  │ ☑ .md      │  │                                           │  │  │
│  │ ☑ .py      │  │    [📂 Open] [📋 Copy] [👁️ Preview]      │  │  │
│  │ ☑ .ts      │  └──────────────────────────────────────────┘  │  │
│  │ ☐ .dart    │                                                  │  │
│  │            │  ┌──────────────────────────────────────────┐  │  │
│  │ Mode:      │  │ 📄 backend/auth.py          Score: 0.87  │  │  │
│  │ ● Hybrid   │  │    RepoDot • 1 week ago                  │  │  │
│  │ ○ Keyword  │  │                                           │  │  │
│  │ ○ Semantic │  │    async def authenticate_user(token):   │  │  │
│  │            │  │        """Validate JWT..."""              │  │  │
│  │ [+ Add     │  │                                           │  │  │
│  │  Directory]│  │    [📂 Open] [📋 Copy] [👁️ Preview]      │  │  │
│  │            │  └──────────────────────────────────────────┘  │  │
│  └────────────┴─────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Settings Page

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚙️ Settings                                          [Back to Search] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┬────────────────────────────────────────────────┐  │
│  │             │                                                 │  │
│  │ Navigation  │  Repositories                                   │  │
│  │             │                                                 │  │
│  │ › Repos     │  ┌──────────────────────────────────────────┐  │  │
│  │   General   │  │ xLLMArionComply                  [Edit]  │  │  │
│  │   Search    │  │ Path: ~/LocalProjects/...                │  │  │
│  │   Advanced  │  │ Status: ✅ Enabled • 4,521 files indexed │  │  │
│  │             │  │ Last indexed: 2 hours ago                │  │  │
│  │             │  │                                           │  │  │
│  │             │  │ [Reindex] [Disable] [Remove]             │  │  │
│  │             │  └──────────────────────────────────────────┘  │  │
│  │             │                                                 │  │
│  │             │  ┌──────────────────────────────────────────┐  │  │
│  │             │  │ RepoDot                          [Edit]  │  │  │
│  │             │  │ Path: ~/LocalProjects/...                │  │  │
│  │             │  │ Status: ✅ Enabled • 1,234 files indexed │  │  │
│  │             │  │ Last indexed: 1 day ago                  │  │  │
│  │             │  │                                           │  │  │
│  │             │  │ [Reindex] [Disable] [Remove]             │  │  │
│  │             │  └──────────────────────────────────────────┘  │  │
│  │             │                                                 │  │
│  │             │  [+ Add Repository]                             │  │
│  │             │                                                 │  │
│  └─────────────┴────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Stats Page

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📊 Statistics                                        [Back to Search] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Overall Performance                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Total Searches (24h)    │ 342                                 │  │
│  │ Avg Search Time         │ 187ms                               │  │
│  │ Cache Hit Rate          │ 67%                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Repository Status                                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Repository       │ Files │ Size   │ Last Indexed │ Status    │  │
│  ├──────────────────┼───────┼────────┼──────────────┼───────────│  │
│  │ xLLMArionComply  │ 4,521 │ 1.6 GB │ 2h ago       │ ✅ Healthy │  │
│  │ RepoDot          │ 1,234 │ 512 MB │ 1d ago       │ ✅ Healthy │  │
│  │ ArionNetworks    │ 0     │ 0 MB   │ Never        │ ⏸️ Disabled│  │
│  └──────────────────┴───────┴────────┴──────────────┴───────────┘  │
│                                                                      │
│  Search Performance (Last 7 Days)                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │     [Line Chart: Search Time Trend]                           │  │
│  │ 400ms │                                                        │  │
│  │ 300ms │        ╭─╮                                            │  │
│  │ 200ms │  ╭─────╯ ╰───╮                                        │  │
│  │ 100ms │──╯           ╰────────────                           │  │
│  │   0ms └──────────────────────────────────────                │  │
│  │        Mon  Tue  Wed  Thu  Fri  Sat  Sun                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### SearchBar Component

**Purpose:** Main search input with autocomplete

**Props:**
```typescript
interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  suggestions?: string[];
  isLoading?: boolean;
}
```

**Features:**
- Debounced input (300ms)
- Search-as-you-type option
- Recent search suggestions
- Keyboard shortcuts (Cmd+K to focus)
- Clear button
- Search button

**Example:**
```tsx
<SearchBar
  value={query}
  onChange={setQuery}
  onSearch={handleSearch}
  suggestions={recentSearches}
  isLoading={isSearching}
/>
```

---

### SearchResults Component

**Purpose:** Display search results with pagination

**Props:**
```typescript
interface SearchResultsProps {
  results: SearchResult[];
  isLoading: boolean;
  totalResults: number;
  searchTime: number;
  onResultClick: (result: SearchResult) => void;
  onPageChange: (page: number) => void;
  currentPage: number;
  pageSize: number;
}
```

**Features:**
- Virtualized scrolling (performance)
- Infinite scroll option
- Sort by relevance/date
- Result count indicator
- Loading skeleton
- Empty state

---

### ResultCard Component

**Purpose:** Individual search result display

**Props:**
```typescript
interface ResultCardProps {
  result: SearchResult;
  onClick: () => void;
  onOpenInEditor: () => void;
  onCopyPath: () => void;
  onPreview: () => void;
  highlighted?: boolean;
}
```

**Layout:**
```
┌──────────────────────────────────────────────────┐
│ 📄 docs/auth-flow.md                Score: 0.95  │
│    📦 xLLMArionComply • 📅 2 days ago            │
│    📏 Line 45                                     │
│                                                   │
│    ...JWT tokens are validated using Supabase   │
│    authentication. The flow begins with user     │
│    login and ends with session...                │
│                                                   │
│    [📂 Open in VS Code] [📋 Copy Path] [👁️ Preview]│
└──────────────────────────────────────────────────┘
```

**Features:**
- Syntax-highlighted snippet
- File type icon
- Repository badge
- Relative time display
- Score visualization (progress bar)
- Action buttons with tooltips
- Keyboard navigation (j/k to navigate)

---

### RepositoryList Component

**Purpose:** Repository selection with status

**Props:**
```typescript
interface RepositoryListProps {
  repositories: Repository[];
  selectedRepos: string[];
  onToggle: (repoName: string) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
}
```

**Features:**
- Checkbox selection
- Select all/none buttons
- File count display
- Index status indicator
- Last indexed timestamp
- Quick reindex button

---

### DirectoryBrowser Component

**Purpose:** Browse and select ad-hoc directories

**Props:**
```typescript
interface DirectoryBrowserProps {
  onSelect: (path: string) => void;
  currentPath?: string;
}
```

**Features:**
- Native file picker integration
- Recent directories list
- Bookmark directories
- Path autocomplete
- Validation (path exists)

---

### ResultPreview Component

**Purpose:** Full file preview with syntax highlighting

**Props:**
```typescript
interface ResultPreviewProps {
  filePath: string;
  lineNumber?: number;
  repository: string;
  onClose: () => void;
}
```

**Features:**
- Monaco Editor integration
- Syntax highlighting
- Line highlighting
- Scroll to line
- Read-only mode
- Copy code button
- Open in external editor

**Layout:**
```
┌──────────────────────────────────────────────────┐
│ 📄 docs/auth-flow.md                         [✕] │
├──────────────────────────────────────────────────┤
│  1  # Authentication Flow                        │
│  2                                               │
│  3  ## Overview                                  │
│ ...                                              │
│ 45  JWT tokens are validated using Supabase     │ ← Highlighted
│ 46  authentication. The flow begins with user   │
│ 47  login and ends with session creation.       │
│ ...                                              │
├──────────────────────────────────────────────────┤
│ [📂 Open in VS Code] [📋 Copy All] [⬇️ Download] │
└──────────────────────────────────────────────────┘
```

---

## State Management

### Search Store (Zustand)

```typescript
interface SearchState {
  // Query state
  query: string;
  setQuery: (query: string) => void;
  
  // Results state
  results: SearchResult[];
  setResults: (results: SearchResult[]) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  
  // Filter state
  selectedRepos: string[];
  toggleRepo: (repo: string) => void;
  selectedFileTypes: string[];
  toggleFileType: (type: string) => void;
  searchType: 'hybrid' | 'keyword' | 'semantic';
  setSearchType: (type: SearchType) => void;
  
  // Pagination
  currentPage: number;
  setCurrentPage: (page: number) => void;
  pageSize: number;
  
  // Actions
  search: () => Promise<void>;
  clearResults: () => void;
  reset: () => void;
}

const useSearchStore = create<SearchState>((set, get) => ({
  query: '',
  setQuery: (query) => set({ query }),
  
  results: [],
  setResults: (results) => set({ results }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
  
  selectedRepos: [],
  toggleRepo: (repo) => set((state) => ({
    selectedRepos: state.selectedRepos.includes(repo)
      ? state.selectedRepos.filter(r => r !== repo)
      : [...state.selectedRepos, repo]
  })),
  
  selectedFileTypes: ['.md', '.py', '.ts'],
  toggleFileType: (type) => set((state) => ({
    selectedFileTypes: state.selectedFileTypes.includes(type)
      ? state.selectedFileTypes.filter(t => t !== type)
      : [...state.selectedFileTypes, type]
  })),
  
  searchType: 'hybrid',
  setSearchType: (type) => set({ searchType: type }),
  
  currentPage: 1,
  setCurrentPage: (page) => set({ currentPage: page }),
  pageSize: 10,
  
  search: async () => {
    const { query, selectedRepos, selectedFileTypes, searchType } = get();
    set({ isLoading: true });
    
    try {
      const results = await searchService.search({
        query,
        repositories: selectedRepos.length > 0 ? selectedRepos : undefined,
        file_types: selectedFileTypes,
        search_type: searchType,
      });
      
      set({ results: results.results, isLoading: false });
    } catch (error) {
      console.error('Search failed:', error);
      set({ isLoading: false });
    }
  },
  
  clearResults: () => set({ results: [], currentPage: 1 }),
  reset: () => set({
    query: '',
    results: [],
    currentPage: 1,
    isLoading: false,
  }),
}));
```

---

### Settings Store

```typescript
interface SettingsState {
  // UI Settings
  theme: 'light' | 'dark' | 'auto';
  setTheme: (theme: Theme) => void;
  
  compactMode: boolean;
  toggleCompactMode: () => void;
  
  // Search Settings
  searchAsYouType: boolean;
  toggleSearchAsYouType: () => void;
  
  defaultSearchType: SearchType;
  setDefaultSearchType: (type: SearchType) => void;
  
  resultsPerPage: number;
  setResultsPerPage: (count: number) => void;
  
  // Editor Integration
  preferredEditor: string;
  setPreferredEditor: (editor: string) => void;
  
  // Persistence
  saveSettings: () => void;
  loadSettings: () => void;
}
```

---

## API Integration

### API Client

```typescript
// services/api.ts

class APIClient {
  private baseURL: string;
  
  constructor(baseURL: string = 'http://localhost:3002') {
    this.baseURL = baseURL;
  }
  
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
  
  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
}

export const apiClient = new APIClient();
```

### Search Service

```typescript
// services/searchService.ts

export const searchService = {
  async search(params: SearchParams): Promise<SearchResponse> {
    return apiClient.post('/search/hybrid', params);
  },
  
  async getKeywordResults(params: SearchParams): Promise<SearchResponse> {
    return apiClient.post('/search/keyword', params);
  },
  
  async getSemanticResults(params: SearchParams): Promise<SearchResponse> {
    return apiClient.post('/search/semantic', params);
  },
};
```

### Index Service

```typescript
// services/indexService.ts

export const indexService = {
  async getStats(): Promise<IndexStats> {
    return apiClient.get('/stats');
  },
  
  async indexRepository(name: string, full: boolean = false): Promise<void> {
    return apiClient.post('/index/repository', {
      repository_name: name,
      full_reindex: full,
    });
  },
  
  async getRepositories(): Promise<Repository[]> {
    return apiClient.get('/repositories');
  },
};
```

---

## React Query Integration

### Search Hook

```typescript
// hooks/useSearch.ts

import { useQuery } from '@tanstack/react-query';

export const useSearch = (params: SearchParams) => {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => searchService.search(params),
    enabled: params.query.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
};
```

### Repositories Hook

```typescript
// hooks/useRepositories.ts

export const useRepositories = () => {
  return useQuery({
    queryKey: ['repositories'],
    queryFn: () => indexService.getRepositories(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};
```

### Stats Hook

```typescript
// hooks/useStats.ts

export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => indexService.getStats(),
    refetchInterval: 60 * 1000, // Refresh every minute
  });
};
```

---

## Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + K` | Focus search bar |
| `Cmd/Ctrl + /` | Toggle filters panel |
| `Cmd/Ctrl + ,` | Open settings |
| `Cmd/Ctrl + H` | View history |
| `Esc` | Clear search / Close preview |

### Search Results Shortcuts

| Shortcut | Action |
|----------|--------|
| `↑/↓` or `j/k` | Navigate results |
| `Enter` | Open selected result in editor |
| `Cmd/Ctrl + Enter` | Open preview |
| `c` | Copy file path |
| `o` | Open in VS Code |
| `p` | Toggle preview pane |
| `1-9` | Jump to result N |

### Filter Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + 1` | Toggle first repository |
| `Cmd/Ctrl + 2` | Toggle second repository |
| `Cmd/Ctrl + Shift + A` | Select all repos |
| `Cmd/Ctrl + Shift + N` | Clear all repos |

---

## Responsive Design

### Desktop (1200px+)

- Full three-column layout
- Filters sidebar (left)
- Results list (center)
- Preview pane (right, optional)

### Tablet (768px - 1199px)

- Two-column layout
- Collapsible filters sidebar
- Results list (main)
- Preview as modal overlay

### Mobile (< 768px)

- Single column layout
- Filters as bottom sheet
- Results full-width
- Preview full-screen modal

---

## Styling System

### Tailwind Configuration

```javascript
// tailwind.config.js

module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        score: {
          high: '#10b981',    // Green for 0.9+
          medium: '#f59e0b',  // Orange for 0.7-0.9
          low: '#6b7280',     // Gray for <0.7
        },
      },
      typography: {
        DEFAULT: {
          css: {
            code: {
              backgroundColor: '#f3f4f6',
              padding: '0.2em 0.4em',
              borderRadius: '0.25rem',
            },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
};
```

### Component Styles

```typescript
// Common button styles
const buttonStyles = {
  primary: "bg-primary-600 hover:bg-primary-700 text-white",
  secondary: "bg-gray-200 hover:bg-gray-300 text-gray-900",
  ghost: "hover:bg-gray-100 text-gray-700",
  danger: "bg-red-600 hover:bg-red-700 text-white",
};

// Result card styles
const resultCardStyles = `
  border border-gray-200 rounded-lg p-4 
  hover:shadow-md transition-shadow
  dark:border-gray-700 dark:bg-gray-800
`;

// Code snippet styles
const codeStyles = `
  font-mono text-sm bg-gray-50 p-3 rounded
  dark:bg-gray-900
`;
```

---

## Dark Mode

### Theme Toggle

```typescript
const ThemeToggle = () => {
  const { theme, setTheme } = useSettingsStore();
  
  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
    >
      {theme === 'dark' ? '🌞' : '🌙'}
    </button>
  );
};
```

### Color Scheme

**Light Mode:**
- Background: `#ffffff`
- Text: `#1f2937`
- Border: `#e5e7eb`
- Accent: `#3b82f6`

**Dark Mode:**
- Background: `#111827`
- Text: `#f9fafb`
- Border: `#374151`
- Accent: `#60a5fa`

---

## Performance Optimizations

### Code Splitting

```typescript
// Lazy load pages
const SearchPage = lazy(() => import('./pages/SearchPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const StatsPage = lazy(() => import('./pages/StatsPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));

// Routes with suspense
<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/" element={<SearchPage />} />
    <Route path="/settings" element={<SettingsPage />} />
    <Route path="/stats" element={<StatsPage />} />
    <Route path="/history" element={<HistoryPage />} />
  </Routes>
</Suspense>
```

### Virtualization

```typescript
// Virtualize long result lists
import { useVirtualizer } from '@tanstack/react-virtual';

const VirtualResultsList = ({ results }) => {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: results.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 150, // Estimated result card height
  });
  
  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <ResultCard result={results[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

### Debouncing

```typescript
// Debounce search input
const useDebounce = (value: string, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(handler);
  }, [value, delay]);
  
  return debouncedValue;
};

// Usage
const SearchBar = () => {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  
  useEffect(() => {
    if (debouncedQuery) {
      performSearch(debouncedQuery);
    }
  }, [debouncedQuery]);
  
  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
};
```

---

## Error Handling

### Error Boundary

```typescript
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('UI Error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Something went wrong</h1>
            <p className="text-gray-600 mb-4">{this.state.error?.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

### API Error Handling

```typescript
const handleAPIError = (error: Error) => {
  if (error.message.includes('HTTP 500')) {
    toast.error('Server error. Please try again.');
  } else if (error.message.includes('HTTP 404')) {
    toast.error('Endpoint not found.');
  } else if (error.message.includes('Network')) {
    toast.error('Server is not running. Start with "uss server start"');
  } else {
    toast.error('An unexpected error occurred.');
  }
};
```

---

## Testing Strategy

### Unit Tests (Vitest)

```typescript
// components/SearchBar.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { SearchBar } from './SearchBar';

describe('SearchBar', () => {
  it('renders search input', () => {
    render(<SearchBar value="" onChange={() => {}} onSearch={() => {}} />);
    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
  });
  
  it('calls onChange when typing', () => {
    const handleChange = vi.fn();
    render(<SearchBar value="" onChange={handleChange} onSearch={() => {}} />);
    
    fireEvent.change(screen.getByPlaceholderText(/search/i), {
      target: { value: 'test query' },
    });
    
    expect(handleChange).toHaveBeenCalledWith('test query');
  });
  
  it('calls onSearch when Enter is pressed', () => {
    const handleSearch = vi.fn();
    render(<SearchBar value="query" onChange={() => {}} onSearch={handleSearch} />);
    
    fireEvent.keyDown(screen.getByPlaceholderText(/search/i), {
      key: 'Enter',
    });
    
    expect(handleSearch).toHaveBeenCalled();
  });
});
```

### Integration Tests

```typescript
// Search flow integration test

describe('Search Flow', () => {
  it('performs search and displays results', async () => {
    render(<App />);
    
    // Type query
    const searchInput = screen.getByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'authentication' } });
    
    // Click search
    fireEvent.click(screen.getByText(/search/i));
    
    // Wait for results
    await waitFor(() => {
      expect(screen.getByText(/results/i)).toBeInTheDocument();
    });
    
    // Verify result cards are displayed
    expect(screen.getAllByTestId('result-card')).toHaveLength(7);
  });
});
```

### E2E Tests (Playwright)

```typescript
// e2e/search.spec.ts

import { test, expect } from '@playwright/test';

test('search and open result', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Search
  await page.fill('[placeholder="Search..."]', 'authentication flow');
  await page.click('button:has-text("Search")');
  
  // Wait for results
  await page.waitForSelector('[data-testid="result-card"]');
  
  // Click first result
  await page.click('[data-testid="result-card"]:first-child');
  
  // Verify preview opened
  await expect(page.locator('[data-testid="preview-pane"]')).toBeVisible();
});
```

---

## Build and Deployment

### Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open browser at http://localhost:5173
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Output: dist/ directory
```

### Docker Deployment

```dockerfile
# Dockerfile

FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
# nginx.conf

server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:3002/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Accessibility

### ARIA Labels

```tsx
<button
  aria-label="Search"
  aria-keyshortcuts="Ctrl+K"
  onClick={handleSearch}
>
  🔍
</button>

<input
  type="search"
  aria-label="Search query"
  aria-describedby="search-hint"
/>

<div id="search-hint" className="sr-only">
  Press Enter to search, or Escape to clear
</div>
```

### Keyboard Navigation

- All interactive elements are keyboard accessible
- Focus indicators visible
- Tab order logical
- Skip to main content link

### Screen Reader Support

- Semantic HTML
- ARIA landmarks
- Live regions for dynamic content
- Descriptive labels

---

## Browser Support

### Target Browsers

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions

### Polyfills

```typescript
// main.tsx

// Polyfill for older browsers
import 'core-js/stable';
import 'regenerator-runtime/runtime';
```

---

## Analytics

### User Events to Track

```typescript
// Track search events
analytics.track('search_performed', {
  query: query,
  search_type: searchType,
  num_results: results.length,
  search_time_ms: searchTime,
});

// Track result interactions
analytics.track('result_opened', {
  file_path: result.file_path,
  repository: result.repository,
  rank: result.rank,
});

// Track feature usage
analytics.track('filter_toggled', {
  filter_type: 'repository',
  filter_value: repoName,
});
```

---

## Future Enhancements

### Phase 2 Features

1. **Collaborative Features**
   - Share search results via URL
   - Team search history
   - Shared saved searches

2. **Advanced Visualizations**
   - Code dependency graphs
   - File relationship maps
   - Search analytics dashboard

3. **AI Assistance**
   - Query suggestions
   - Result summarization
   - Auto-categorization

4. **Integrations**
   - Slack bot
   - GitHub integration
   - Jira linking

---

**End of Web UI Specification**

**Next: Create deployment guide with incremental adoption strategy**
