# Whoosh to Meilisearch Migration Fix Plan

## MIGRATION STATUS: ✅ COMPLETED (2026-01-05)

All steps in this migration plan have been successfully executed. The application is now fully migrated to Meilisearch with all legacy Whoosh code removed.

**Verification:**
- CLI keyword search tested and working: `python -m myragdb.cli search "test" --type keyword`
- API key authentication configured correctly
- Method signatures standardized to `repository_filter`
- All imports corrected to use `meilisearch_indexer`

---

## 1. Problem Summary (RESOLVED)

The project was migrated from the `Whoosh` library (for BM25 keyword search) to `Meilisearch`. However, the refactoring was incomplete, leaving the application in a broken state.

The core issues were:
- **Legacy Code Remains:** ✅ FIXED - Deleted `src/myragdb/indexers/bm25_indexer.py`
- **Incorrect Imports:** ✅ FIXED - Updated `cli.py` and all documentation to import from `meilisearch_indexer`
- **Missing Dependency:** ✅ FIXED - Removed Whoosh from `setup.py` and `requirements.txt`
- **Resulting Error:** ✅ FIXED - No more `ModuleNotFoundError: No module named 'whoosh'`

Additional fixes applied:
- **API Key Configuration:** ✅ FIXED - MeilisearchIndexer now uses config defaults
- **Method Signatures:** ✅ FIXED - All search methods use `repository_filter` parameter

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

---

## Completion Summary

### Execution Date: 2026-01-05

All steps in this migration plan were successfully executed in two commits:

#### Commit 1: Legacy Code Removal (Version 2026.01.05.2.5.1)
**Files Modified:**
- `src/myragdb/cli.py` - Fixed import from bm25_indexer to meilisearch_indexer
- `MIGRATION_GUIDE.md` - Updated import examples
- `setup.py` - Removed Whoosh dependency
- `.claude/CLAUDE.md` - Updated technology stack reference

**Files Deleted:**
- `src/myragdb/indexers/bm25_indexer.py` - Removed obsolete Whoosh implementation

#### Commit 2: API Configuration Fix (Version 2026.01.05.2.5.2)
**Files Modified:**
- `src/myragdb/indexers/meilisearch_indexer.py`:
  - Changed import from `settings` to `app_settings`
  - Updated `__init__` to use config defaults for host, api_key, and index_name
- `src/myragdb/cli.py`:
  - Fixed method signatures: `repository` → `repository_filter` in all three search types

### Verification Results

✅ **All steps completed successfully:**
1. Import paths corrected in cli.py
2. Legacy bm25_indexer.py file deleted
3. Backward compatibility aliases removed (not needed)
4. requirements.txt verified clean (Whoosh not present)
5. Final verification passed:
   - CLI search command working: `python -m myragdb.cli search "test" --type keyword --limit 5`
   - Returns 5 results without errors
   - No ModuleNotFoundError
   - Meilisearch authentication working correctly

### Current Status

The MyRAGDB project is now fully migrated to Meilisearch with:
- Zero legacy Whoosh code remaining
- All imports corrected
- API authentication configured
- Method signatures standardized
- CLI tested and operational

**Next steps** are documented in MIGRATION_GUIDE.md items 9-12 (Hybrid search, LLM router, server updates, vector indexer ID updates).
