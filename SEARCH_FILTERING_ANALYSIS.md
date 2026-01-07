# Search Logic Filtering Analysis

## 1. HYBRID SEARCH METHOD STRUCTURE

### File: `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/search/hybrid_search.py`
### Lines: 182-207

Current method signature:
```python
async def hybrid_search(
    self,
    query: str,
    limit: int = 10,
    rewrite_query: bool = True,
    repository_filter: Optional[str] = None,
    folder_filter: Optional[str] = None,
    extension_filter: Optional[str] = None
) -> List[HybridSearchResult]:
```

**Note:** `directory_filter` parameter is MISSING and should be added here.

---

## 2. MEILISEARCH FILTER STRING CONSTRUCTION

### File: `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/meilisearch_indexer.py`
### Lines: 434-446

**Current Implementation:**
```python
try:
    # Build filter expression
    filters = []
    if folder_filter:
        # Exact match on folder_name
        filters.append(f'folder_name = "{folder_filter}"')
    if extension_filter:
        filters.append(f'extension = "{extension_filter}"')
    if repository_filter:
        filters.append(f'repository = "{repository_filter}"')

    filter_str = ' AND '.join(filters) if filters else None
```

**Pattern Analysis:**
- Uses list of filter strings
- Joins with ` AND ` operator
- Format: `attribute = "value"` for exact matches
- Result is None if no filters, otherwise joined string

**WHERE TO ADD DIRECTORY FILTERING:**
After line 443 (after `repository_filter` check), add:
```python
if directory_path_filter:
    filters.append(f'directory_path = "{directory_path_filter}"')
```

---

## 3. CHROMADB WHERE CLAUSE CONSTRUCTION

### File: `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/search/hybrid_search.py`
### Lines: 256-265 (fetch_chromadb function)

**Current Implementation:**
```python
async def fetch_chromadb() -> tuple[List[str], List[float]]:
    """Fetch semantic results from ChromaDB."""
    try:
        # Build where clause for repository filter
        where_clause = None
        if repository_filter:
            where_clause = {"repository": repository_filter}

        results = self.vector.collection.query(
            query_texts=[semantic_intent],
            n_results=fetch_limit,
            where=where_clause
        )
```

**Pattern Analysis:**
- ChromaDB uses Python dict for where clause (not string)
- Only supports single condition currently
- Format: `{"attribute": "value"}` for exact matches
- Supports metadata filtering based on what's in collection

**Problem:** Current implementation can only handle ONE filter (repository)
**Solution needed:** Convert to support multiple conditions

**ChromaDB where clause syntax for multiple conditions:**
```python
where_clause = {
    "$and": [
        {"repository": "MyProject"},
        {"source_type": "repository"}
    ]
}
```

---

## 4. MEILISEARCH SEARCH METHOD SIGNATURE

### File: `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/meilisearch_indexer.py`
### Lines: 392-399

**Current Implementation:**
```python
def search(
    self,
    query: str,
    limit: int = 10,
    folder_filter: Optional[str] = None,
    extension_filter: Optional[str] = None,
    repository_filter: Optional[str] = None
) -> List[MeilisearchResult]:
```

**Missing parameter:** `directory_path_filter` should be added here

---

## 5. MEILISEARCH FILTERABLE ATTRIBUTES

### File: `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/meilisearch_indexer.py`
### Lines: 133-145

**Current Configuration:**
```python
# Filterable attributes (lookup table - exact matches)
self.index.update_filterable_attributes([
    'file_path',      # Full absolute path
    'relative_path',  # Relative path from repo root
    'directory_path', # Full parent directory path
    'extension',      # File type (.py, .md, .js, etc.)
    'last_modified',  # Timestamp for incremental indexing
    'size',           # File size in bytes
    'repository',     # Repository name (for backward compatibility)
    'source_type',    # Source type: 'repository' or 'directory'
    'source_id',      # Source ID: repository name or directory ID
    'folder_name'     # Folder name (also searchable)
])
```

**Good News:** `directory_path` is ALREADY a filterable attribute (line 137)!

---

## 6. MEILISEARCH DOCUMENT STRUCTURE

### File: `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/meilisearch_indexer.py`
### Lines: 218-232

**Document structure includes:**
```python
return {
    'id': doc_id,
    'file_path': scanned_file.file_path,
    'file_name': file_path_obj.name,
    'folder_name': folder_name,
    'directory_path': str(file_path_obj.parent),  # <-- AVAILABLE FOR FILTERING
    'extension': scanned_file.file_type,
    'repository': scanned_file.repository_name,
    'source_type': source_type,
    'source_id': source_id,
    'relative_path': scanned_file.relative_path,
    'content': content_truncated,
    'last_modified': last_modified,
    'size': size
}
```

---

## 7. CHROMADB METADATA STRUCTURE

### File: `/Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/indexers/vector_indexer.py`
### Lines: 270-280

**Metadata stored includes:**
```python
metadata = {
    "file_path": scanned_file.file_path,
    "repository": scanned_file.repository_name,
    "source_type": source_type,
    "source_id": source_id,
    "file_type": scanned_file.file_type,
    "relative_path": scanned_file.relative_path,
    "chunk_index": i,
    "total_chunks": len(chunks)
}
```

**Problem:** `directory_path` is NOT stored in metadata!
**Solution:** Add it to ChromaDB metadata during indexing.

---

## 8. HYBRID SEARCH FLOW DIAGRAM

```
hybrid_search(query, repository_filter, folder_filter, extension_filter, [MISSING: directory_filter])
    |
    +-- Step 1: Query rewriting (optional)
    |
    +-- Step 2: Parallel execution
    |   |
    |   +-- fetch_meilisearch()
    |   |   └── meilisearch.search(
    |   |       query,
    |   |       repository_filter,
    |   |       folder_filter,
    |   |       extension_filter,
    |   |       [MISSING: directory_path_filter]
    |   |   )
    |   |
    |   +-- fetch_chromadb()
    |   |   └── collection.query(
    |   |       query,
    |   |       where={"repository": repository_filter}  # ONLY supports 1 condition!
    |   |   )
    |
    +-- Step 3: RRF fusion
    +-- Step 4: Build unified results
    +-- Step 5: Sort and return
```

---

## SUMMARY: WHERE TO ADD DIRECTORY FILTERING

### Changes Required:

1. **hybrid_search.py (line 188)**
   - Add `directory_path_filter: Optional[str] = None` parameter

2. **hybrid_search.py (line 240-246)** - fetch_meilisearch call
   ```python
   # Change from:
   results = self.meilisearch.search(
       query=keywords,
       limit=fetch_limit,
       repository_filter=repository_filter,
       folder_filter=folder_filter,
       extension_filter=extension_filter
   )
   
   # To:
   results = self.meilisearch.search(
       query=keywords,
       limit=fetch_limit,
       repository_filter=repository_filter,
       folder_filter=folder_filter,
       extension_filter=extension_filter,
       directory_path_filter=directory_path_filter  # ADD THIS
   )
   ```

3. **hybrid_search.py (line 257-264)** - fetch_chromadb where clause
   ```python
   # Change from:
   where_clause = None
   if repository_filter:
       where_clause = {"repository": repository_filter}
   
   # To:
   where_clause = None
   conditions = []
   if repository_filter:
       conditions.append({"repository": repository_filter})
   if directory_path_filter:
       conditions.append({"directory_path": directory_path_filter})
   
   if conditions:
       if len(conditions) == 1:
           where_clause = conditions[0]
       else:
           where_clause = {"$and": conditions}
   ```

4. **meilisearch_indexer.py (line 392-399)** - Add parameter to search()
   ```python
   def search(
       self,
       query: str,
       limit: int = 10,
       folder_filter: Optional[str] = None,
       extension_filter: Optional[str] = None,
       repository_filter: Optional[str] = None,
       directory_path_filter: Optional[str] = None  # ADD THIS
   ) -> List[MeilisearchResult]:
   ```

5. **meilisearch_indexer.py (line 436-445)** - Add to filter construction
   ```python
   # After line 443, add:
   if directory_path_filter:
       filters.append(f'directory_path = "{directory_path_filter}"')
   ```

6. **vector_indexer.py (line 270-280)** - Add directory_path to metadata
   ```python
   metadata = {
       "file_path": scanned_file.file_path,
       "repository": scanned_file.repository_name,
       "source_type": source_type,
       "source_id": source_id,
       "file_type": scanned_file.file_type,
       "relative_path": scanned_file.relative_path,
       "directory_path": directory_path,  # ADD THIS
       "chunk_index": i,
       "total_chunks": len(chunks)
   }
   ```

