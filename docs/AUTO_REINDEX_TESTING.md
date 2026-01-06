# Auto-Reindex Feature Testing Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/AUTO_REINDEX_TESTING.md
**Description:** Manual testing procedures for automatic file change detection and reindexing
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-06

---

## Overview

This document describes how to manually test the automatic file change detection and incremental reindexing feature.

## Prerequisites

1. MyRAGDB server running: `python -m myragdb.api.server`
2. At least one repository enabled in `config/repositories.yaml`
3. Repository must have `auto_reindex: true` (default)
4. Repository must be initially indexed

---

## Test 1: Verify Watcher Status

### Objective
Confirm that file system watchers are active for enabled repositories.

### Steps

1. Start the server:
   ```bash
   python -m myragdb.api.server
   ```

2. Check logs for watcher startup:
   ```
   INFO Repository watchers started successfully
   INFO Started watching repository repository=myragdb path=/path/to/myragdb extensions=['.py', '.md', ...]
   ```

3. Call the watcher status API:
   ```bash
   curl http://localhost:3002/watcher/status
   ```

### Expected Result

```json
{
  "watchers": [
    {
      "repository": "myragdb",
      "status": "active",
      "pending_changes": 0,
      "path": "/Users/.../myragdb",
      "debounce_seconds": 5
    }
  ],
  "total_watchers": 1,
  "total_pending_changes": 0
}
```

---

## Test 2: File Creation Detection

### Objective
Verify that creating a new file triggers automatic reindexing.

### Steps

1. Ensure repository is indexed and watcher is active

2. Create a new test file in the watched repository:
   ```bash
   echo "# Test Document\n\nThis is a test for automatic reindexing." > /path/to/myragdb/test_auto_reindex.md
   ```

3. Wait 6 seconds (debounce period is 5 seconds)

4. Check server logs for:
   ```
   INFO Auto-reindex triggered repository=myragdb file_count=1
   INFO Automatic reindex triggered by file changes repository=myragdb file_count=1
   ```

5. Verify keyword indexing started:
   ```
   INFO Starting keyword indexing...
   ```

6. Wait for indexing to complete

7. Search for content from the new file:
   ```bash
   curl -X POST http://localhost:3002/search/hybrid \
        -H "Content-Type: application/json" \
        -d '{"query": "test for automatic reindexing", "limit": 5}'
   ```

### Expected Result

- Logs show auto-reindex triggered
- Search results include the newly created file
- File appears in search results with correct content

---

## Test 3: File Modification Detection

### Objective
Verify that modifying an existing file triggers reindexing.

### Steps

1. Modify an existing indexed file:
   ```bash
   echo "\n\n## New Section About Automatic Reindexing\n\nThis section was added to test auto-reindex on file modifications." >> /path/to/myragdb/README.md
   ```

2. Wait 6 seconds

3. Check logs for auto-reindex trigger

4. Search for new content:
   ```bash
   curl -X POST http://localhost:3002/search/hybrid \
        -H "Content-Type: application/json" \
        -d '{"query": "New Section About Automatic Reindexing", "limit": 5}'
   ```

### Expected Result

- Auto-reindex triggered in logs
- Search results show updated content from README.md
- New section appears in search results

---

## Test 4: Multiple Rapid Changes (Debouncing)

### Objective
Verify that multiple rapid file changes are batched into a single reindex operation.

### Steps

1. Create multiple files rapidly:
   ```bash
   for i in {1..5}; do
       echo "# Test File $i" > /path/to/myragdb/test_file_$i.md
       sleep 0.5
   done
   ```

2. Wait 6 seconds

3. Check logs

### Expected Result

- Only ONE auto-reindex trigger appears in logs
- Log shows `file_count=5` (all files batched together)
- All 5 files are indexed in single operation

---

## Test 5: Excluded Files Not Triggering Reindex

### Objective
Verify that changes to excluded files (like node_modules) do NOT trigger reindexing.

### Steps

1. Create file in excluded directory:
   ```bash
   mkdir -p /path/to/myragdb/node_modules/test
   echo "test" > /path/to/myragdb/node_modules/test/index.js
   ```

2. Wait 6 seconds

3. Check logs

### Expected Result

- NO auto-reindex trigger in logs
- Watcher correctly ignores excluded paths

---

## Test 6: File Extension Filtering

### Objective
Verify that only configured file extensions trigger reindexing.

### Steps

1. Create file with non-watched extension:
   ```bash
   echo "test" > /path/to/myragdb/test.xyz
   ```

2. Wait 6 seconds

3. Check logs

4. Create file with watched extension:
   ```bash
   echo "# Test" > /path/to/myragdb/test_watched.md
   ```

5. Wait 6 seconds

6. Check logs

### Expected Result

- `.xyz` file does NOT trigger reindex
- `.md` file DOES trigger reindex

---

## Test 7: Toggle Auto-Reindex Off

### Objective
Verify that disabling auto-reindex stops the watcher.

### Steps

1. Disable auto-reindex via API:
   ```bash
   curl -X POST http://localhost:3002/repositories/myragdb/auto-reindex \
        -H "Content-Type: application/json" \
        -d '{"enabled": false}'
   ```

2. Expected response:
   ```json
   {
     "status": "success",
     "repository": "myragdb",
     "auto_reindex_enabled": false,
     "watcher_status": "stopped",
     "message": "Auto-reindex disabled for repository myragdb"
   }
   ```

3. Verify watcher stopped:
   ```bash
   curl http://localhost:3002/watcher/status
   ```

4. Create a new file:
   ```bash
   echo "test" > /path/to/myragdb/test_disabled.md
   ```

5. Wait 6 seconds

6. Check logs

### Expected Result

- Watcher status shows 0 active watchers
- New file creation does NOT trigger reindex
- No auto-reindex logs appear

---

## Test 8: Toggle Auto-Reindex Back On

### Objective
Verify that re-enabling auto-reindex starts the watcher.

### Steps

1. Enable auto-reindex via API:
   ```bash
   curl -X POST http://localhost:3002/repositories/myragdb/auto-reindex \
        -H "Content-Type: application/json" \
        -d '{"enabled": true}'
   ```

2. Verify watcher status shows 1 active watcher

3. Create a new file to confirm watching works:
   ```bash
   echo "# Watcher Re-enabled Test" > /path/to/myragdb/test_reenabled.md
   ```

4. Wait 6 seconds

5. Check logs

### Expected Result

- Watcher status shows 1 active watcher
- File creation triggers auto-reindex
- Indexing completes successfully

---

## Test 9: Server Restart Persistence

### Objective
Verify that watchers correctly restart after server restart.

### Steps

1. Stop the server (Ctrl+C)

2. Restart the server:
   ```bash
   python -m myragdb.api.server
   ```

3. Check logs for watcher initialization

4. Check watcher status:
   ```bash
   curl http://localhost:3002/watcher/status
   ```

5. Create a file to verify watching:
   ```bash
   echo "# Post-restart Test" > /path/to/myragdb/test_restart.md
   ```

6. Wait 6 seconds

7. Check logs

### Expected Result

- Server logs show "Repository watchers started successfully"
- Watcher status shows active watchers
- File creation triggers auto-reindex

---

## Test 10: File Deletion Detection

### Objective
Verify that file deletions are detected and trigger reindexing.

### Steps

1. Create a test file:
   ```bash
   echo "# Temporary Test File" > /path/to/myragdb/temp_test.md
   ```

2. Wait for initial reindex (6 seconds)

3. Delete the file:
   ```bash
   rm /path/to/myragdb/temp_test.md
   ```

4. Wait 6 seconds

5. Check logs

6. Search for deleted file content:
   ```bash
   curl -X POST http://localhost:3002/search/hybrid \
        -H "Content-Type: application/json" \
        -d '{"query": "Temporary Test File", "limit": 5}'
   ```

### Expected Result

- Deletion triggers auto-reindex in logs
- Search results do NOT include deleted file
- File removed from index

---

## Troubleshooting

### Watcher Not Starting

**Symptom:** No watchers shown in status, no startup logs

**Possible Causes:**
1. Repository `enabled: false` in config
2. Repository `auto_reindex: false` in config
3. Repository path doesn't exist

**Solution:**
- Check `config/repositories.yaml`
- Ensure repository is enabled and auto_reindex is true
- Verify path exists

### Auto-Reindex Not Triggering

**Symptom:** Files change but no reindex happens

**Possible Causes:**
1. Watcher not active (check status)
2. File extension not in watched list
3. File in excluded directory
4. Debounce period not elapsed

**Solution:**
- Check `/watcher/status` endpoint
- Verify file extension is in repository's include patterns
- Wait full 6 seconds after file change
- Check server logs for errors

### Excessive Reindexing

**Symptom:** Reindexing triggered too frequently

**Possible Causes:**
1. IDE or build tools creating many temporary files
2. Debounce period too short

**Solution:**
- Add problematic directories to exclude patterns
- Increase debounce_seconds in watcher initialization
- Disable auto-reindex for frequently-changing repos

---

## Performance Notes

- **Debounce Period:** Default 5 seconds provides good balance between responsiveness and resource usage
- **File Extensions:** Limiting watched extensions reduces unnecessary events
- **Exclude Patterns:** Comprehensive exclusions prevent indexing build artifacts
- **Incremental Indexing:** Only changed files are reindexed, not entire repository

---

## Next Steps

Once manual testing passes:

1. Add automated integration tests
2. Add observability metrics for auto-reindex operations
3. Consider configurable debounce per repository
4. Add UI toggle for auto-reindex in web interface

---

Questions: libor@arionetworks.com
