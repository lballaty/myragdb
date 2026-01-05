# Whoosh to Meilisearch Migration Fix Plan

## 1. Problem Summary

The project was migrated from the `Whoosh` library (for BM25 keyword search) to `Meilisearch`. However, the refactoring was incomplete, leaving the application in a broken state.

The core issues are:
- **Legacy Code Remains:** The file `src/myragdb/indexers/bm25_indexer.py` still contains the old, `Whoosh`-based implementation.
- **Incorrect Imports:** Critical files like `src/myragdb/cli.py` are still importing from the legacy `bm25_indexer.py` file.
- **Missing Dependency:** Because `Whoosh` is no longer the intended engine, it has been correctly removed from `requirements.txt`.
- **Resulting Error:** The combination of incorrect imports and the missing dependency causes a `ModuleNotFoundError: No module named 'whoosh'`, which makes the application's CLI and potentially other components unusable.

This prevents testing of the keyword search functionality and indicates a critical inconsistency in the codebase.

## 2. Proposed Solution

The solution is to **complete the migration** by systematically removing all remaining `Whoosh`-related code and artifacts and ensuring all parts of the application correctly use the new `MeilisearchIndexer`.

This will involve:
1.  Redirecting all imports to the correct Meilisearch module.
2.  Deleting the obsolete `Whoosh` implementation file.
3.  Performing a final cleanup to ensure no traces of `Whoosh` remain.

This will result in a clean, consistent, and runnable codebase that properly implements Meilisearch as the sole keyword search engine.

## 3. Step-by-Step Execution Plan

### Step 1: Correct All Incorrect Import Paths

The primary issue is that modules are still pointing to the legacy `bm25_indexer`. These must be updated to point to the correct `meilisearch_indexer`.

**Action:**
In the following files, find the incorrect import statement and replace it.

- **File:** `src/myragdb/cli.py`
  - **Line 14**
  - **Change from:**
    ```python
    from myragdb.indexers.bm25_indexer import MeilisearchIndexer
    ```
  - **Change to:**
    ```python
    from myragdb.indexers.meilisearch_indexer import MeilisearchIndexer
    ```

*(Note: A global search should be conducted to find any other files that might reference `bm25_indexer.py` and apply the same fix, but `cli.py` is the most critical one identified so far.)*

### Step 2: Delete the Obsolete `bm25_indexer.py` File

Once no other files depend on it, the legacy `bm25_indexer.py` file is redundant and a source of confusion. It should be deleted permanently.

**Action:**
Execute the following shell command to remove the file:
```sh
rm src/myragdb/indexers/bm25_indexer.py
```

### Step 3: Remove Alias in `meilisearch_indexer.py`

The file `src/myragdb/indexers/meilisearch_indexer.py` contains aliases for backward compatibility that are no longer needed and can cause confusion.

**Action:**
Remove the following lines from `src/myragdb/indexers/meilisearch_indexer.py`:

```python
# Alias for backward compatibility
BM25SearchResult = MeilisearchSearchResult
```
```python
# Alias for backward compatibility
BM25Indexer = MeilisearchIndexer
```

### Step 4: Verify `requirements.txt` is Clean

This is a verification step. Ensure that `whoosh` is not listed as a dependency.

**Action:**
Manually inspect `requirements.txt` and confirm there is no line containing `whoosh`.

### Step 5: Final Verification

After completing the steps above, verify that the application runs correctly and that the `whoosh` dependency is fully removed.

**Action:**
1.  Activate the virtual environment.
    ```sh
    source venv/bin/activate
    ```
2.  Run the CLI search command that was previously failing. This command should now execute successfully and return search results.
    ```sh
    python -m myragdb.cli search "Supabase" --type keyword
    ```
3.  Run a global search for the term "whoosh" to ensure no references remain in the codebase.
    ```sh
    grep -r "whoosh" .
    ```
    This command should return no results (or only results in this migration plan file).

By following this plan, the `Whoosh` to `Meilisearch` migration will be completed, resolving the current errors and stabilizing the codebase.
