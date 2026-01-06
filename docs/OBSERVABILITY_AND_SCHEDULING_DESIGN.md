# Observability and Scheduled Indexing Design

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/OBSERVABILITY_AND_SCHEDULING_DESIGN.md
**Description:** Design document for observability metrics tracking and scheduled indexing features
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-06
**Last Updated:** 2026-01-06
**Last Updated By:** Libor Ballaty <libor@arionetworks.com>

---

## Overview

This document describes the design and implementation of two major features:
1. **Observability Dashboard** - Real-time monitoring, metrics tracking, and error logging
2. **Scheduled Indexing** - Automated incremental indexing on configurable schedules

## Business Purpose

**Observability:**
- Monitor system health and performance in real-time
- Track and diagnose errors before they impact users
- Identify performance trends and bottlenecks
- Provide visibility into search and indexing operations
- Enable data-driven optimization decisions

**Scheduled Indexing:**
- Keep indexes up-to-date automatically without manual intervention
- Reduce index staleness for frequently-changing repositories
- Enable "set it and forget it" indexing workflows
- Support different schedules for different repository priorities

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Web UI (Frontend)                        │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ Observability Tab │  │ Repositories Tab (Enhanced)      │ │
│  │ - Charts.js      │  │ - Schedule Controls              │ │
│  │ - Metrics Cards  │  │ - Next Run Display               │ │
│  │ - Error Log      │  │ - Manual Trigger                 │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (server.py)                 │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ Observability API│  │ Scheduler API                    │ │
│  │ - /metrics       │  │ - /schedules                     │ │
│  │ - /errors        │  │ - /schedules/trigger             │ │
│  │ - /system-health │  │                                  │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
│           │                         │                        │
│           │                         ▼                        │
│           │             ┌────────────────────────┐           │
│           │             │ APScheduler            │           │
│           │             │ - Cron Jobs            │           │
│           │             │ - Job Management       │           │
│           │             └────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ observability.db │  │ schedules.db                     │ │
│  │ - search_metrics │  │ - indexing_schedules             │ │
│  │ - error_log      │  │ - schedule_history               │ │
│  │ - system_metrics │  │                                  │ │
│  │ - indexing_events│  │                                  │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1: Observability Dashboard

### 1.1 Database Schema

**File:** `src/myragdb/db/observability.py`

#### Table: `search_metrics`
Tracks all search queries for performance analysis.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| timestamp | INTEGER | Unix timestamp |
| query | TEXT | Search query text |
| search_type | TEXT | 'hybrid', 'keyword', or 'semantic' |
| latency_ms | REAL | Search duration in milliseconds |
| result_count | INTEGER | Number of results returned |
| repository_filter | TEXT | Repository filter if applied (NULL if all) |
| file_type_filter | TEXT | File type filter if applied |
| min_score | REAL | Minimum score threshold used |

**Purpose:** Analyze search performance, identify slow queries, track query patterns.

**Retention:** 90 days (configurable)

#### Table: `error_log`
Centralized error tracking for all system errors.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| timestamp | INTEGER | Unix timestamp |
| severity | TEXT | 'error', 'warning', 'critical' |
| error_type | TEXT | Exception class name |
| message | TEXT | Error message |
| stack_trace | TEXT | Full stack trace |
| context | TEXT | JSON context (endpoint, user action, etc.) |
| resolved | INTEGER | 0 = unresolved, 1 = resolved |

**Purpose:** Track errors for debugging, identify recurring issues, monitor error rates.

**Retention:** 90 days (configurable), critical errors kept indefinitely

#### Table: `system_metrics`
Time-series system health metrics.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| timestamp | INTEGER | Unix timestamp |
| metric_name | TEXT | Metric identifier (e.g., 'api_response_time_p95') |
| metric_value | REAL | Numeric value |
| metric_unit | TEXT | Unit of measurement (e.g., 'ms', 'bytes', 'count') |
| tags | TEXT | JSON tags for filtering (e.g., {"endpoint": "/search"}) |

**Purpose:** Track system performance over time, identify trends, detect anomalies.

**Retention:** 90 days (configurable), aggregated summaries kept longer

#### Table: `indexing_events`
Detailed indexing operation history.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| timestamp | INTEGER | Unix timestamp |
| repository | TEXT | Repository name |
| event_type | TEXT | 'start', 'complete', 'fail', 'skip' |
| index_type | TEXT | 'keyword' or 'vector' |
| duration_seconds | REAL | Operation duration (NULL for 'start') |
| files_processed | INTEGER | Number of files processed |
| files_skipped | INTEGER | Number of files skipped (incremental) |
| error_message | TEXT | Error details if failed |
| triggered_by | TEXT | 'manual', 'scheduled', 'api' |

**Purpose:** Track indexing history, diagnose failures, monitor automation effectiveness.

**Retention:** 365 days (configurable)

### 1.2 Backend Instrumentation

**File:** `src/myragdb/api/server.py`

#### Search Endpoint Instrumentation

```python
@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    start_time = time.time()

    try:
        # ... existing search logic ...

        # Record successful search
        observability_db.record_search_metric(
            query=request.query,
            search_type=request.search_type.value,
            latency_ms=(time.time() - start_time) * 1000,
            result_count=len(results),
            repository_filter=request.repository_filter,
            file_type_filter=request.extension_filter,
            min_score=request.min_score
        )

        return response

    except Exception as e:
        # Record error
        observability_db.record_error(
            severity='error',
            error_type=type(e).__name__,
            message=str(e),
            stack_trace=traceback.format_exc(),
            context={'endpoint': '/search', 'request': request.dict()}
        )
        raise
```

#### Indexing Event Tracking

```python
async def _run_keyword_indexing(...):
    # Record start event
    observability_db.record_indexing_event(
        repository=repo.name,
        event_type='start',
        index_type='keyword',
        triggered_by='manual'  # or 'scheduled'
    )

    try:
        # ... indexing logic ...

        # Record completion
        observability_db.record_indexing_event(
            repository=repo.name,
            event_type='complete',
            index_type='keyword',
            duration_seconds=duration,
            files_processed=len(files),
            files_skipped=skipped_count,
            triggered_by='manual'
        )
    except Exception as e:
        # Record failure
        observability_db.record_indexing_event(
            repository=repo.name,
            event_type='fail',
            index_type='keyword',
            error_message=str(e),
            triggered_by='manual'
        )
        raise
```

#### System Metrics Collection

```python
# Background task to collect system metrics every 60 seconds
async def collect_system_metrics():
    while True:
        try:
            # API health
            observability_db.record_system_metric(
                'api_status', 1 if service_healthy else 0, 'boolean'
            )

            # Index sizes
            meili_size = get_meilisearch_index_size()
            chroma_size = get_chromadb_index_size()
            observability_db.record_system_metric(
                'index_size_keyword', meili_size, 'bytes'
            )
            observability_db.record_system_metric(
                'index_size_vector', chroma_size, 'bytes'
            )

            # Document counts
            observability_db.record_system_metric(
                'total_documents', get_total_document_count(), 'count'
            )

        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))

        await asyncio.sleep(60)
```

### 1.3 API Endpoints

**File:** `src/myragdb/api/server.py`

#### GET /api/observability/metrics

Returns time-series metrics data with filtering.

**Query Parameters:**
- `metric_names` (optional): Comma-separated metric names
- `start_time` (optional): Unix timestamp for range start
- `end_time` (optional): Unix timestamp for range end
- `interval` (optional): Aggregation interval ('1m', '5m', '1h', '1d')

**Response:**
```json
{
  "metrics": [
    {
      "name": "search_latency_p95",
      "data_points": [
        {"timestamp": 1704567600, "value": 245.3},
        {"timestamp": 1704571200, "value": 198.7}
      ],
      "unit": "ms"
    }
  ]
}
```

#### GET /api/observability/errors

Returns recent errors with filtering and pagination.

**Query Parameters:**
- `severity` (optional): Filter by severity
- `resolved` (optional): true/false/all
- `limit` (optional): Number of results (default 50)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "total": 23,
  "errors": [
    {
      "id": 123,
      "timestamp": 1704567890,
      "severity": "error",
      "error_type": "ConnectionError",
      "message": "Failed to connect to Meilisearch",
      "stack_trace": "...",
      "context": {"endpoint": "/search"},
      "resolved": false
    }
  ]
}
```

#### GET /api/observability/search-stats

Returns aggregated search performance statistics.

**Query Parameters:**
- `time_range` (optional): '1h', '24h', '7d', '30d' (default '24h')

**Response:**
```json
{
  "total_searches": 1234,
  "avg_latency_ms": 187.3,
  "p50_latency_ms": 145.2,
  "p95_latency_ms": 423.7,
  "p99_latency_ms": 892.1,
  "searches_by_type": {
    "hybrid": 856,
    "keyword": 234,
    "semantic": 144
  },
  "zero_result_rate": 0.07,
  "avg_results_per_query": 8.3
}
```

#### GET /api/observability/indexing-stats

Returns indexing performance and history.

**Query Parameters:**
- `repository` (optional): Filter by repository
- `time_range` (optional): '1h', '24h', '7d', '30d'

**Response:**
```json
{
  "total_indexing_runs": 45,
  "successful_runs": 43,
  "failed_runs": 2,
  "avg_duration_seconds": 23.4,
  "total_files_indexed": 12456,
  "recent_events": [
    {
      "timestamp": 1704567890,
      "repository": "myragdb",
      "event_type": "complete",
      "duration_seconds": 15.3,
      "files_processed": 91
    }
  ]
}
```

#### GET /api/observability/system-health

Returns current system health snapshot.

**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 345678,
  "services": {
    "meilisearch": {"status": "healthy", "response_time_ms": 12},
    "chromadb": {"status": "healthy", "response_time_ms": 8},
    "database": {"status": "healthy"}
  },
  "resources": {
    "index_size_total_mb": 234.5,
    "database_size_mb": 12.3,
    "total_documents": 45678
  },
  "current_metrics": {
    "active_searches": 3,
    "indexing_in_progress": false
  }
}
```

### 1.4 Frontend UI

**Files:** `web-ui/index.html`, `web-ui/static/js/app.js`, `web-ui/static/js/charts.js` (NEW)

#### Tab Structure

New "Observability" tab added to navigation:
```html
<div class="tabs">
  <button id="search-tab" class="tab active">Search</button>
  <button id="repositories-tab" class="tab">Repositories</button>
  <button id="observability-tab" class="tab">Observability</button>
  <button id="activity-tab" class="tab">Activity Monitor</button>
</div>
```

#### Observability Tab Layout

```
┌─────────────────────────────────────────────────────────────┐
│ ⏱ Time Range: [1h][6h][24h][7d][30d][Custom] 🔄 Auto-refresh│
├─────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ Uptime   │ │ Searches │ │ Avg      │ │ Errors   │        │
│ │ 4d 5h    │ │ 1.2k     │ │ Latency  │ │ 3        │        │
│ │          │ │ /24h     │ │ 187ms    │ │ /24h     │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├─────────────────────────────────────────────────────────────┤
│ 📊 Search Latency Over Time (p50, p95, p99)                 │
│ [Line Chart]                                                 │
├─────────────────────────────────────────────────────────────┤
│ 📊 Indexing Performance                                      │
│ [Bar Chart: Files/sec by repository]                        │
├─────────────────────────────────────────────────────────────┤
│ ⚠️ Recent Errors                                             │
│ [Table with filter by severity, expandable stack traces]    │
└─────────────────────────────────────────────────────────────┘
```

#### Chart.js Integration

**File:** `web-ui/static/js/charts.js`

```javascript
// Wrapper functions for consistent chart styling
function createLineChart(canvasId, data, options) {
    return new Chart(document.getElementById(canvasId), {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...options
        }
    });
}

function createBarChart(canvasId, data, options) { ... }
function createPieChart(canvasId, data, options) { ... }
```

#### Auto-Refresh Implementation

```javascript
let observabilityRefreshInterval = null;

function startObservabilityAutoRefresh(intervalSeconds = 30) {
    if (observabilityRefreshInterval) {
        clearInterval(observabilityRefreshInterval);
    }

    observabilityRefreshInterval = setInterval(() => {
        if (isObservabilityTabActive()) {
            loadObservabilityData();
        }
    }, intervalSeconds * 1000);
}

function stopObservabilityAutoRefresh() {
    if (observabilityRefreshInterval) {
        clearInterval(observabilityRefreshInterval);
        observabilityRefreshInterval = null;
    }
}
```

---

## Part 2: Scheduled Indexing

### 2.1 Database Schema

**File:** `src/myragdb/db/schedules.py`

#### Table: `indexing_schedules`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| repository | TEXT UNIQUE | Repository name |
| enabled | INTEGER | 1 = enabled, 0 = disabled |
| schedule_type | TEXT | 'cron', 'interval' |
| schedule_expression | TEXT | Cron expression or interval (e.g., '0 2 * * *', 'every 6 hours') |
| index_keyword | INTEGER | 1 = index keyword, 0 = skip |
| index_vector | INTEGER | 1 = index vector, 0 = skip |
| last_run | INTEGER | Unix timestamp of last execution (NULL if never run) |
| next_run | INTEGER | Unix timestamp of next scheduled run |
| created_at | INTEGER | Unix timestamp when schedule created |
| updated_at | INTEGER | Unix timestamp when schedule last modified |

#### Table: `schedule_history`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| schedule_id | INTEGER | Foreign key to indexing_schedules |
| repository | TEXT | Repository name |
| started_at | INTEGER | Unix timestamp when started |
| completed_at | INTEGER | Unix timestamp when completed (NULL if failed/running) |
| status | TEXT | 'success', 'failed', 'running' |
| files_processed | INTEGER | Number of files indexed |
| duration_seconds | REAL | Total duration |
| error_message | TEXT | Error details if failed |

**Purpose:** Track schedule execution history for auditing and troubleshooting.

**Retention:** 180 days (configurable)

### 2.2 Scheduler Implementation

**File:** `src/myragdb/scheduler/indexing_scheduler.py`

Uses **APScheduler** (Advanced Python Scheduler) for job management.

#### Core Components

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

class IndexingScheduler:
    """
    Manages scheduled indexing jobs.

    Business Purpose: Automates incremental indexing to keep
    repositories up-to-date without manual intervention.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.schedule_db = ScheduleDatabase()

    def start(self):
        """Start the scheduler and load all enabled schedules."""
        self.scheduler.start()
        self._load_all_schedules()

    def _load_all_schedules(self):
        """Load schedules from database and register jobs."""
        schedules = self.schedule_db.get_all_enabled_schedules()
        for schedule in schedules:
            self._register_job(schedule)

    def _register_job(self, schedule):
        """Register a single indexing job with APScheduler."""
        job_id = f"index_{schedule['repository']}"

        if schedule['schedule_type'] == 'cron':
            trigger = CronTrigger.from_crontab(schedule['schedule_expression'])
        else:
            # Parse interval (e.g., "every 6 hours")
            trigger = self._parse_interval(schedule['schedule_expression'])

        self.scheduler.add_job(
            self._run_scheduled_index,
            trigger=trigger,
            id=job_id,
            args=[schedule],
            replace_existing=True
        )

    async def _run_scheduled_index(self, schedule):
        """Execute a scheduled indexing job."""
        # Record start in history
        history_id = self.schedule_db.record_schedule_run_start(
            schedule['id'], schedule['repository']
        )

        try:
            # Trigger indexing via API (reuse existing logic)
            await trigger_reindex_internal(
                repositories=[schedule['repository']],
                index_keyword=schedule['index_keyword'],
                index_vector=schedule['index_vector'],
                full_rebuild=False  # Always incremental for scheduled jobs
            )

            # Record success
            self.schedule_db.record_schedule_run_complete(
                history_id,
                status='success',
                files_processed=files_count,
                duration_seconds=duration
            )

            # Update next_run timestamp
            self.schedule_db.update_next_run(schedule['id'])

        except Exception as e:
            # Record failure
            self.schedule_db.record_schedule_run_complete(
                history_id,
                status='failed',
                error_message=str(e)
            )

            # Log to observability
            observability_db.record_error(
                severity='error',
                error_type='ScheduledIndexingFailed',
                message=f"Scheduled indexing failed for {schedule['repository']}",
                context={'schedule_id': schedule['id']}
            )
```

#### Schedule Parsing

```python
def _parse_interval(self, expression: str) -> IntervalTrigger:
    """
    Parse interval expressions like:
    - 'every 6 hours'
    - 'every 30 minutes'
    - 'every 1 day'
    """
    # Implementation details...
```

#### Integration with FastAPI Lifecycle

```python
# In src/myragdb/api/server.py

scheduler = None

@app.on_event("startup")
async def startup_event():
    global scheduler
    scheduler = IndexingScheduler()
    scheduler.start()
    logger.info("Indexing scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    if scheduler:
        scheduler.shutdown()
        logger.info("Indexing scheduler stopped")
```

### 2.3 API Endpoints

**File:** `src/myragdb/api/server.py`

#### GET /api/schedules

Get all indexing schedules.

**Response:**
```json
{
  "schedules": [
    {
      "id": 1,
      "repository": "myragdb",
      "enabled": true,
      "schedule_type": "cron",
      "schedule_expression": "0 2 * * *",
      "index_keyword": true,
      "index_vector": true,
      "last_run": 1704502800,
      "next_run": 1704589200,
      "human_readable": "Daily at 2:00 AM"
    }
  ]
}
```

#### POST /api/schedules

Create or update a schedule.

**Request:**
```json
{
  "repository": "myragdb",
  "enabled": true,
  "schedule_type": "cron",
  "schedule_expression": "0 2 * * *",
  "index_keyword": true,
  "index_vector": true
}
```

**Response:**
```json
{
  "status": "success",
  "schedule_id": 1,
  "next_run": 1704589200,
  "message": "Schedule created/updated successfully"
}
```

#### DELETE /api/schedules/{repository}

Delete a schedule.

**Response:**
```json
{
  "status": "success",
  "message": "Schedule deleted for repository: myragdb"
}
```

#### POST /api/schedules/{repository}/trigger

Manually trigger a scheduled job (run now).

**Response:**
```json
{
  "status": "started",
  "message": "Indexing triggered for myragdb"
}
```

#### GET /api/schedules/{repository}/history

Get execution history for a schedule.

**Query Parameters:**
- `limit` (optional): Number of records (default 50)

**Response:**
```json
{
  "history": [
    {
      "started_at": 1704502800,
      "completed_at": 1704502845,
      "status": "success",
      "files_processed": 91,
      "duration_seconds": 45.3
    },
    {
      "started_at": 1704416400,
      "completed_at": null,
      "status": "failed",
      "error_message": "Connection timeout"
    }
  ]
}
```

### 2.4 Frontend UI (Repositories Tab Enhancement)

**File:** `web-ui/index.html`, `web-ui/static/js/app.js`

#### Schedule Controls Section

Add new section to Repositories tab:

```html
<div id="schedule-section" class="section">
    <h3>⏰ Indexing Schedules</h3>

    <!-- Global schedule toggle -->
    <div class="schedule-global-controls">
        <label>
            <input type="checkbox" id="scheduler-enabled">
            Enable Automatic Scheduling
        </label>
        <button id="view-schedule-history">View History</button>
    </div>

    <!-- Per-repository schedule configuration -->
    <div id="repository-schedules">
        <!-- Populated dynamically -->
    </div>
</div>
```

#### Repository Card Enhancement

Add schedule indicator to each repository card:

```html
<div class="repository-schedule">
    <span class="schedule-status">
        ⏰ Daily at 2:00 AM
        <span class="next-run">Next: in 4h 23m</span>
    </span>
    <button class="btn-configure-schedule">Configure</button>
</div>
```

#### Schedule Configuration Modal

```html
<div id="schedule-modal" class="modal">
    <h3>Configure Schedule: <span id="schedule-repo-name"></span></h3>

    <label>
        <input type="checkbox" id="schedule-enabled-checkbox">
        Enable Schedule
    </label>

    <label>
        Schedule Type:
        <select id="schedule-type">
            <option value="preset">Preset</option>
            <option value="cron">Custom (Cron)</option>
        </select>
    </label>

    <!-- Preset options -->
    <div id="preset-options">
        <select id="schedule-preset">
            <option value="0 2 * * *">Daily at 2:00 AM</option>
            <option value="0 */6 * * *">Every 6 hours</option>
            <option value="0 */12 * * *">Every 12 hours</option>
            <option value="0 0 * * 0">Weekly (Sunday)</option>
        </select>
    </div>

    <!-- Custom cron -->
    <div id="cron-options" style="display: none;">
        <input type="text" id="cron-expression" placeholder="0 2 * * *">
        <span class="cron-help">Format: minute hour day month weekday</span>
    </div>

    <label>
        <input type="checkbox" id="schedule-index-keyword" checked>
        Index Keyword
    </label>

    <label>
        <input type="checkbox" id="schedule-index-vector" checked>
        Index Vector
    </label>

    <div class="modal-buttons">
        <button id="schedule-save">Save Schedule</button>
        <button id="schedule-cancel">Cancel</button>
    </div>
</div>
```

#### JavaScript Functions

```javascript
async function loadSchedules() {
    const response = await fetch(`${API_BASE_URL}/api/schedules`);
    const data = await response.json();
    state.schedules = data.schedules;
    renderScheduleIndicators();
}

async function saveSchedule(repository, scheduleConfig) {
    const response = await fetch(`${API_BASE_URL}/api/schedules`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            repository,
            ...scheduleConfig
        })
    });

    if (response.ok) {
        addActivityLog('success', `Schedule updated for ${repository}`);
        loadSchedules();
    }
}

function renderScheduleIndicators() {
    // Add schedule status to each repository card
    state.schedules.forEach(schedule => {
        const card = document.querySelector(`[data-repo="${schedule.repository}"]`);
        if (card) {
            const nextRunText = formatNextRunTime(schedule.next_run);
            card.querySelector('.schedule-status').innerHTML = `
                ⏰ ${schedule.human_readable}
                <span class="next-run">Next: ${nextRunText}</span>
            `;
        }
    });
}

function formatNextRunTime(unixTimestamp) {
    const now = Date.now() / 1000;
    const diff = unixTimestamp - now;

    if (diff < 0) return 'Overdue';
    if (diff < 3600) return `in ${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `in ${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
    return `in ${Math.floor(diff / 86400)}d ${Math.floor((diff % 86400) / 3600)}h`;
}
```

---

## Data Retention and Cleanup

### Automatic Cleanup Jobs

**File:** `src/myragdb/scheduler/cleanup_jobs.py`

```python
class DataCleanupScheduler:
    """
    Manages automatic cleanup of old metrics and logs.

    Business Purpose: Prevent database bloat while retaining
    meaningful historical data for trend analysis.
    """

    def __init__(self, observability_db, schedule_db):
        self.observability_db = observability_db
        self.schedule_db = schedule_db

    def schedule_cleanup_jobs(self, scheduler):
        # Run daily at 3 AM
        scheduler.add_job(
            self.cleanup_old_data,
            CronTrigger(hour=3, minute=0),
            id='cleanup_old_data'
        )

    def cleanup_old_data(self):
        """Remove data older than retention periods."""
        now = time.time()

        # Search metrics: 90 days
        cutoff_search = now - (90 * 86400)
        self.observability_db.delete_old_search_metrics(cutoff_search)

        # Error logs: 90 days (keep critical errors indefinitely)
        cutoff_errors = now - (90 * 86400)
        self.observability_db.delete_old_errors(cutoff_errors, keep_critical=True)

        # System metrics: 90 days (aggregate to hourly averages after 30 days)
        cutoff_aggregate = now - (30 * 86400)
        self.observability_db.aggregate_old_system_metrics(cutoff_aggregate)

        cutoff_delete = now - (90 * 86400)
        self.observability_db.delete_old_system_metrics(cutoff_delete)

        # Schedule history: 180 days
        cutoff_schedule = now - (180 * 86400)
        self.schedule_db.delete_old_schedule_history(cutoff_schedule)

        logger.info("Data cleanup completed")
```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Observability
OBSERVABILITY_ENABLED=true
OBSERVABILITY_RETENTION_DAYS=90
OBSERVABILITY_METRICS_INTERVAL_SECONDS=60

# Scheduling
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=UTC
```

### Configuration File

**File:** `config/observability.yaml` (NEW)

```yaml
observability:
  enabled: true
  retention:
    search_metrics_days: 90
    error_logs_days: 90
    system_metrics_days: 90
    indexing_events_days: 365
  metrics_collection:
    interval_seconds: 60
  auto_refresh:
    default_interval_seconds: 30
    min_interval_seconds: 5

scheduling:
  enabled: true
  timezone: "UTC"
  max_concurrent_jobs: 3
  retry_failed_jobs: true
  retry_max_attempts: 3
```

---

## Performance Considerations

### Database Indexing

Create indexes for common query patterns:

```sql
-- observability.db
CREATE INDEX idx_search_metrics_timestamp ON search_metrics(timestamp);
CREATE INDEX idx_error_log_timestamp ON error_log(timestamp);
CREATE INDEX idx_error_log_severity ON error_log(severity);
CREATE INDEX idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp);
CREATE INDEX idx_indexing_events_repo_timestamp ON indexing_events(repository, timestamp);

-- schedules.db
CREATE INDEX idx_schedules_enabled ON indexing_schedules(enabled);
CREATE INDEX idx_schedule_history_schedule_id ON schedule_history(schedule_id);
CREATE INDEX idx_schedule_history_started_at ON schedule_history(started_at);
```

### Query Optimization

- Use time-based partitioning for large metric tables
- Aggregate old data to reduce granularity (hourly instead of per-minute)
- Implement caching for frequently accessed dashboard data
- Use async queries to prevent blocking the UI

### Resource Limits

- Limit concurrent scheduled indexing jobs to prevent resource exhaustion
- Implement rate limiting on observability API endpoints
- Set maximum result limits for historical data queries

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_observability.py`

- Test database schema creation
- Test metric recording functions
- Test data retention/cleanup
- Test API endpoint responses

**File:** `tests/test_scheduler.py`

- Test schedule parsing (cron, intervals)
- Test job registration/removal
- Test schedule execution
- Test failure handling and retries

### Integration Tests

- Test end-to-end scheduled indexing flow
- Test observability data collection during real indexing
- Test API error tracking
- Test metric aggregation and cleanup

### Manual Testing Checklist

- [ ] Observability tab loads without errors
- [ ] Charts render correctly with real data
- [ ] Time range selector works
- [ ] Error log displays and filters correctly
- [ ] Auto-refresh updates data
- [ ] Schedule creation/modification works
- [ ] Scheduled jobs execute at correct times
- [ ] Manual job triggering works
- [ ] Schedule history displays correctly
- [ ] Data cleanup runs without errors

---

## Migration Path

### Phase 1: Observability Infrastructure
1. Create observability database and tables
2. Add instrumentation to existing code
3. Create API endpoints
4. Test data collection

### Phase 2: Observability UI
1. Add Chart.js library
2. Create observability tab UI
3. Implement charts and metrics display
4. Test with real data

### Phase 3: Scheduler Backend
1. Create schedules database
2. Implement scheduler with APScheduler
3. Create schedule API endpoints
4. Test job execution

### Phase 4: Scheduler UI
1. Add schedule controls to repositories tab
2. Implement schedule configuration modal
3. Add schedule indicators to repository cards
4. Test end-to-end workflow

### Phase 5: Production Hardening
1. Implement data retention and cleanup
2. Add comprehensive error handling
3. Performance optimization
4. Documentation updates

---

## Security Considerations

### API Security

- All observability endpoints require authentication (if auth is implemented)
- Rate limiting on metric collection to prevent abuse
- Input validation on schedule expressions to prevent injection attacks
- Sanitize error messages to avoid leaking sensitive information

### Data Privacy

- Redact sensitive information from logged errors (passwords, tokens)
- Implement role-based access to error logs
- Anonymize search queries if they contain PII

### Scheduler Security

- Validate cron expressions before registration
- Prevent schedule conflicts (max concurrent jobs)
- Implement job timeout to prevent runaway processes
- Log all schedule modifications for auditing

---

## Future Enhancements

### Observability

- [ ] Alerting system (email/webhook on error thresholds)
- [ ] Anomaly detection for performance metrics
- [ ] Custom dashboard builder
- [ ] Export metrics to external monitoring systems (Prometheus, Datadog)
- [ ] Distributed tracing for search queries
- [ ] User analytics (if multi-user system)

### Scheduling

- [ ] Schedule templates (save and reuse configurations)
- [ ] Bulk schedule management (apply to multiple repos)
- [ ] Schedule dependencies (index repo A before repo B)
- [ ] Smart scheduling (auto-adjust based on repository activity)
- [ ] Pause/resume functionality
- [ ] Schedule version history

---

## Part 3: Automatic Change Detection and Incremental Reindexing

### 3.1 Overview

**Business Purpose:**
Automatically detect file changes in indexed repositories and trigger incremental reindexing without manual intervention. This ensures search results are always up-to-date without requiring scheduled jobs or manual reindexing.

**Key Differences from Scheduled Indexing:**
- **Scheduled Indexing**: Runs at predetermined times (cron-based)
- **Change Detection**: Runs immediately when file changes are detected (event-driven)

### 3.2 Architecture

Uses **watchdog** library for cross-platform file system event monitoring.

```
┌─────────────────────────────────────────────────────────────┐
│                  File System Watcher                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  watchdog.observers.Observer                         │   │
│  │  - Monitors repository directories                   │   │
│  │  - Detects file create/modify/delete/move events     │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Event Handler (RepositoryEventHandler)              │   │
│  │  - Filters events by file type (.py, .md, .ts, etc.) │   │
│  │  - Debounces rapid changes (wait 5s after last event)│   │
│  │  - Queues changed files for reindexing               │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Reindex Queue                                       │   │
│  │  - Batches multiple file changes                     │   │
│  │  - Triggers incremental reindexing after debounce    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│             Incremental Indexer (Existing)                   │
│  - Indexes only changed files                                │
│  - Updates Meilisearch and ChromaDB                          │
│  - Records indexing event in observability.db                │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Implementation

**File:** `src/myragdb/watcher/repository_watcher.py`

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
from pathlib import Path

class RepositoryEventHandler(FileSystemEventHandler):
    """
    Handles file system events for a single repository.

    Business Purpose: Automatically detect file changes to keep
    search indexes up-to-date without manual intervention.
    """

    def __init__(self, repository_name, repository_path, file_extensions, debounce_seconds=5):
        self.repository_name = repository_name
        self.repository_path = Path(repository_path)
        self.file_extensions = set(file_extensions)  # e.g., {'.py', '.md', '.ts'}
        self.debounce_seconds = debounce_seconds

        # Track pending changes
        self.pending_changes = set()  # Set of file paths
        self.debounce_timer = None
        self.lock = threading.Lock()

    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should trigger reindexing."""
        path = Path(file_path)

        # Check extension
        if path.suffix not in self.file_extensions:
            return False

        # Exclude patterns (same as indexing exclusions)
        exclude_patterns = [
            '**/node_modules/**',
            '**/.git/**',
            '**/venv/**',
            '**/archive-*/**',
            '**/*.lock',
            '**/__pycache__/**',
            '**/data/**',
            '**/.meilisearch/**'
        ]

        for pattern in exclude_patterns:
            if path.match(pattern):
                return False

        return True

    def on_created(self, event):
        """Handle file creation."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change(event.src_path, 'created')

    def on_modified(self, event):
        """Handle file modification."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change(event.src_path, 'modified')

    def on_deleted(self, event):
        """Handle file deletion."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change(event.src_path, 'deleted')

    def on_moved(self, event):
        """Handle file move/rename."""
        if not event.is_directory:
            if self._should_process_file(event.src_path):
                self._queue_change(event.src_path, 'deleted')
            if self._should_process_file(event.dest_path):
                self._queue_change(event.dest_path, 'created')

    def _queue_change(self, file_path: str, event_type: str):
        """Queue a file change for reindexing with debouncing."""
        with self.lock:
            self.pending_changes.add((file_path, event_type))

            # Cancel existing timer
            if self.debounce_timer:
                self.debounce_timer.cancel()

            # Start new timer
            self.debounce_timer = threading.Timer(
                self.debounce_seconds,
                self._trigger_reindex
            )
            self.debounce_timer.start()

    def _trigger_reindex(self):
        """Trigger incremental reindexing for pending changes."""
        with self.lock:
            if not self.pending_changes:
                return

            # Get unique file paths (ignore event type for now)
            changed_files = {path for path, _ in self.pending_changes}

            logger.info(
                f"Auto-reindex triggered for {self.repository_name}",
                file_count=len(changed_files),
                files=list(changed_files)[:10]  # Log first 10
            )

            # Clear pending changes
            self.pending_changes.clear()

        # Trigger async reindexing (call existing indexing logic)
        try:
            asyncio.run_coroutine_threadsafe(
                trigger_incremental_reindex(
                    repository=self.repository_name,
                    changed_files=list(changed_files)
                ),
                get_event_loop()
            )
        except Exception as e:
            logger.error(
                f"Auto-reindex failed for {self.repository_name}",
                error=str(e)
            )


class RepositoryWatcherManager:
    """
    Manages file system watchers for multiple repositories.

    Business Purpose: Coordinates automatic change detection across
    all indexed repositories with centralized lifecycle management.
    """

    def __init__(self, file_metadata_db):
        self.file_metadata_db = file_metadata_db
        self.observers = {}  # repo_name -> Observer
        self.handlers = {}   # repo_name -> RepositoryEventHandler

    def start_watching(self, repository_name: str, repository_path: str,
                       file_extensions: list):
        """Start watching a repository for changes."""
        if repository_name in self.observers:
            logger.warning(f"Already watching {repository_name}")
            return

        # Create event handler
        handler = RepositoryEventHandler(
            repository_name=repository_name,
            repository_path=repository_path,
            file_extensions=file_extensions,
            debounce_seconds=5
        )

        # Create observer
        observer = Observer()
        observer.schedule(handler, repository_path, recursive=True)
        observer.start()

        self.observers[repository_name] = observer
        self.handlers[repository_name] = handler

        logger.info(f"Started watching repository: {repository_name}")

    def stop_watching(self, repository_name: str):
        """Stop watching a repository."""
        if repository_name not in self.observers:
            return

        observer = self.observers[repository_name]
        observer.stop()
        observer.join(timeout=5)

        del self.observers[repository_name]
        del self.handlers[repository_name]

        logger.info(f"Stopped watching repository: {repository_name}")

    def start_all_enabled_repositories(self):
        """Start watching all enabled and indexed repositories."""
        repos = self.file_metadata_db.get_all_repositories()

        for repo in repos:
            if repo['enabled'] and repo['is_indexed']:
                self.start_watching(
                    repository_name=repo['name'],
                    repository_path=repo['path'],
                    file_extensions=['.py', '.md', '.ts', '.tsx', '.dart', '.js']
                )

    def stop_all(self):
        """Stop all watchers."""
        repo_names = list(self.observers.keys())
        for repo_name in repo_names:
            self.stop_watching(repo_name)
```

### 3.4 Integration with FastAPI Server

**File:** `src/myragdb/api/server.py`

```python
from myragdb.watcher.repository_watcher import RepositoryWatcherManager

watcher_manager = None

@app.on_event("startup")
async def startup_event():
    global watcher_manager

    # Start repository watcher
    watcher_manager = RepositoryWatcherManager(file_metadata_db)
    watcher_manager.start_all_enabled_repositories()
    logger.info("Repository watcher started")

    # ... existing scheduler startup ...

@app.on_event("shutdown")
async def shutdown_event():
    if watcher_manager:
        watcher_manager.stop_all()
        logger.info("Repository watcher stopped")

    # ... existing scheduler shutdown ...
```

### 3.5 Configuration

**File:** `config/observability.yaml` (add section)

```yaml
change_detection:
  enabled: true
  debounce_seconds: 5  # Wait 5 seconds after last change before reindexing
  file_extensions:
    - .py
    - .md
    - .ts
    - .tsx
    - .dart
    - .js
  exclude_patterns:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/venv/**"
    - "**/archive-*/**"
    - "**/*.lock"
    - "**/__pycache__/**"
```

### 3.6 Database Updates

**File:** `src/myragdb/db/file_metadata.py` (add method)

```python
def set_auto_reindex_enabled(self, repository: str, enabled: bool):
    """Enable or disable automatic reindexing for a repository."""
    with self._get_connection() as conn:
        conn.execute(
            "UPDATE repositories SET auto_reindex = ? WHERE name = ?",
            (1 if enabled else 0, repository)
        )
```

**Schema migration:**

```sql
ALTER TABLE repositories ADD COLUMN auto_reindex INTEGER DEFAULT 1;
```

### 3.7 API Endpoints

**File:** `src/myragdb/api/server.py`

#### POST /api/repositories/{repository}/auto-reindex

Enable or disable automatic reindexing for a repository.

**Request:**
```json
{
  "enabled": true
}
```

**Response:**
```json
{
  "status": "success",
  "repository": "myragdb",
  "auto_reindex_enabled": true,
  "watcher_status": "active"
}
```

#### GET /api/watcher/status

Get status of all active watchers.

**Response:**
```json
{
  "watchers": [
    {
      "repository": "myragdb",
      "status": "active",
      "path": "/Users/..../myragdb",
      "watching_since": 1704567890,
      "pending_changes": 0
    }
  ]
}
```

### 3.8 Frontend UI

**File:** `web-ui/index.html` (add to repository card)

```html
<div class="repository-auto-reindex">
    <label>
        <input type="checkbox" class="auto-reindex-toggle" data-repo="{{repo.name}}" checked>
        🔄 Auto-reindex on changes
    </label>
    <span class="watcher-status active">Watching</span>
</div>
```

**File:** `web-ui/static/js/app.js`

```javascript
async function toggleAutoReindex(repository, enabled) {
    const response = await fetch(
        `${API_BASE_URL}/api/repositories/${repository}/auto-reindex`,
        {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ enabled })
        }
    );

    if (response.ok) {
        const data = await response.json();
        addActivityLog(
            'info',
            `Auto-reindex ${enabled ? 'enabled' : 'disabled'} for ${repository}`
        );
        updateWatcherStatus(repository, data.watcher_status);
    }
}

function updateWatcherStatus(repository, status) {
    const card = document.querySelector(`[data-repo="${repository}"]`);
    const statusEl = card.querySelector('.watcher-status');
    statusEl.textContent = status === 'active' ? 'Watching' : 'Stopped';
    statusEl.className = `watcher-status ${status}`;
}
```

### 3.9 Performance Considerations

**Debouncing:**
- Default 5-second debounce prevents excessive reindexing during rapid edits
- Configurable per repository if needed

**Resource Limits:**
- Only watch enabled and indexed repositories
- Exclude large directories (node_modules, .git, etc.)
- Batch multiple changes into single reindex operation

**Event Filtering:**
- Only monitor relevant file types
- Ignore temporary files, build artifacts
- Skip hidden files and directories

### 3.10 Testing Strategy

**Manual Testing:**
1. Enable auto-reindex for a repository
2. Edit a file in the repository
3. Wait 5 seconds
4. Verify reindexing triggered
5. Search for updated content
6. Verify search results reflect changes

**Edge Cases:**
- Rapid consecutive edits (verify debouncing works)
- Large file changes (performance)
- File deletions (verify removal from index)
- File renames (verify old entry deleted, new entry added)

---

## Questions for Review

Questions: libor@arionetworks.com
