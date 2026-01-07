// File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/static/js/app.js
// Description: MyRAGDB web UI application logic
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-04

const API_BASE_URL = 'http://localhost:3003';

// State management
const state = {
    searchHistory: [],
    activityLog: [],
    stats: {
        totalSearches: 0,
        responseTimes: []
    },
    repositories: [],
    discoveredRepos: [],
    discoveryFilters: {
        search: '',
        status: 'all',
        priority: 'all',
        createdAfter: '',
        createdBefore: '',
        modifiedAfter: '',
        modifiedBefore: ''
    },
    discoveryPagination: {
        currentPage: 1,
        pageSize: 20,
        totalPages: 1
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeSearch();
    initializeActivityMonitor();
    initializeReindex();
    initializeDiscovery();
    checkHealthStatus();
    updateIndexingProgress();
    loadStatistics();
    loadRepositories();
    loadFromLocalStorage();
    loadVersion();
});

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            // Update active states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');

            // Load tab-specific data
            if (tabName === 'repositories') {
                loadStatistics();
            } else if (tabName === 'activity') {
                renderActivityLog();
            }
        });
    });
}

// Health Status Check
async function checkHealthStatus() {
    const indicator = document.getElementById('status-indicator');
    const statusText = indicator.querySelector('.status-text');
    const restartButton = document.getElementById('restart-server-button');

    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        // Remove all status classes
        indicator.classList.remove('healthy', 'degraded', 'unhealthy', 'offline');

        if (data.status === 'healthy') {
            indicator.classList.add('healthy');
            statusText.textContent = 'Service Healthy';
            statusText.title = data.message || '';
            restartButton.style.display = 'none';
        } else if (data.status === 'degraded') {
            indicator.classList.add('degraded');
            statusText.textContent = 'Service Degraded';
            statusText.title = data.message || 'Some dependencies unavailable';
            restartButton.style.display = 'inline-block';
            addActivityLog('warning', `Health degraded: ${data.message}`);
        } else if (data.status === 'unhealthy') {
            indicator.classList.add('unhealthy');
            statusText.textContent = 'Service Unhealthy';
            statusText.title = data.message || 'Critical dependencies unavailable';
            restartButton.style.display = 'inline-block';
            addActivityLog('error', `Health unhealthy: ${data.message}`);
        } else {
            statusText.textContent = 'Service Unknown';
            restartButton.style.display = 'inline-block';
        }
    } catch (error) {
        indicator.classList.remove('healthy', 'degraded', 'unhealthy');
        indicator.classList.add('offline');
        statusText.textContent = 'Service Offline';
        statusText.title = 'Cannot connect to server';
        restartButton.style.display = 'none';
        addActivityLog('error', `Health check failed: ${error.message}`);
    }
}

// Server restart functionality
async function restartServer() {
    const restartButton = document.getElementById('restart-server-button');
    const originalText = restartButton.textContent;

    if (!confirm('Are you sure you want to restart the MyRAGDB server?')) {
        return;
    }

    try {
        restartButton.disabled = true;
        restartButton.textContent = '⏳ Restarting...';
        addActivityLog('info', 'Server restart initiated...');

        const response = await fetch(`${API_BASE_URL}/admin/restart`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Restart failed: ${response.status}`);
        }

        const data = await response.json();
        addActivityLog('success', `${data.message} (PID: ${data.pid})`);

        // Wait a bit for server to restart, then check health
        setTimeout(() => {
            addActivityLog('info', 'Waiting for server to come back online...');
            let attempts = 0;
            const maxAttempts = 15;

            const checkInterval = setInterval(async () => {
                attempts++;
                try {
                    const healthResponse = await fetch(`${API_BASE_URL}/health`);
                    if (healthResponse.ok) {
                        clearInterval(checkInterval);
                        addActivityLog('success', 'Server restart completed successfully');
                        restartButton.textContent = originalText;
                        restartButton.disabled = false;
                        await checkHealthStatus();
                    }
                } catch (e) {
                    if (attempts >= maxAttempts) {
                        clearInterval(checkInterval);
                        addActivityLog('error', 'Server did not come back online after restart');
                        restartButton.textContent = originalText;
                        restartButton.disabled = false;
                    }
                }
            }, 2000); // Check every 2 seconds
        }, 3000); // Wait 3 seconds before starting checks

    } catch (error) {
        addActivityLog('error', `Restart failed: ${error.message}`);
        restartButton.textContent = originalText;
        restartButton.disabled = false;
    }
}

// Initialize restart button
document.addEventListener('DOMContentLoaded', () => {
    const restartButton = document.getElementById('restart-server-button');
    if (restartButton) {
        restartButton.addEventListener('click', restartServer);
    }
});

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const toggleAdvanced = document.getElementById('toggle-advanced-filters');
    const advancedFilters = document.getElementById('advanced-filters');

    searchButton.addEventListener('click', performSearch);

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Toggle advanced filters
    if (toggleAdvanced) {
        toggleAdvanced.addEventListener('click', () => {
            const isVisible = advancedFilters.style.display !== 'none';
            advancedFilters.style.display = isVisible ? 'none' : 'block';
            toggleAdvanced.textContent = isVisible ? '🔽 Advanced Filters' : '🔼 Advanced Filters';
        });
    }
}

async function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    const searchType = document.getElementById('search-type').value;
    const limit = parseInt(document.getElementById('result-limit').value);
    const repositorySelect = document.getElementById('repository-filter');
    const selectedRepo = repositorySelect.value;
    const selectedRepos = selectedRepo ? [selectedRepo] : []; // Convert single selection to array for API
    const folderFilter = document.getElementById('folder-filter').value.trim();
    const extensionFilter = document.getElementById('extension-filter').value.trim();
    const resultsDiv = document.getElementById('search-results');
    const searchButton = document.getElementById('search-button');

    if (!query) {
        resultsDiv.innerHTML = '<div class="error">Please enter a search query</div>';
        return;
    }

    // Show loading state
    searchButton.disabled = true;
    searchButton.textContent = 'Searching...';
    resultsDiv.innerHTML = '<div class="loading">🔍 Searching...</div>';

    const startTime = performance.now();

    // Build request body with filters
    const requestBody = { query, limit };
    // Use repositories array if specific repos selected, otherwise omit (search all)
    if (selectedRepos.length > 0) {
        requestBody.repositories = selectedRepos;
    }
    if (folderFilter) requestBody.folder_filter = folderFilter;
    if (extensionFilter) requestBody.extension_filter = extensionFilter;

    try {
        const response = await fetch(`${API_BASE_URL}/search/${searchType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const responseTime = performance.now() - startTime;

        // Update stats
        state.stats.totalSearches++;
        state.stats.responseTimes.push(responseTime);

        // Add to activity log
        addActivityLog('search', `Query: "${query}" | Type: ${searchType} | Results: ${data.results.length} | Time: ${responseTime.toFixed(0)}ms`);

        // Render results
        renderSearchResults(data, responseTime);

        // Save to local storage
        saveToLocalStorage();

    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">❌ Search failed: ${error.message}</div>`;
        addActivityLog('error', `Search failed: ${error.message}`);
    } finally {
        searchButton.disabled = false;
        searchButton.textContent = 'Search';
    }
}

function renderSearchResults(data, responseTime) {
    const resultsDiv = document.getElementById('search-results');

    if (data.results.length === 0) {
        resultsDiv.innerHTML = '<div class="search-meta">No results found</div>';
        return;
    }

    const metaHtml = `
        <div class="search-meta">
            Found ${data.total_results} results in ${responseTime.toFixed(0)}ms
        </div>
    `;

    const resultsHtml = data.results.map((result, index) => {
        const scoreClass = getScoreClass(result.score);
        const scorePercent = (result.score * 100).toFixed(1);

        return `
            <div class="result-card">
                <div class="result-header">
                    <div class="result-path">${escapeHtml(result.relative_path)}</div>
                    <div class="result-score">
                        <div class="score-badge ${scoreClass}">${scorePercent}%</div>
                        ${result.keyword_score !== undefined ? `
                            <div class="score-detail">
                                Keyword: ${(result.keyword_score * 100).toFixed(1)}% |
                                Vec: ${(result.vector_score * 100).toFixed(1)}%
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="result-meta">
                    <span>📁 ${escapeHtml(result.repository)}</span>
                    <span>📄 ${escapeHtml(result.file_type)}</span>
                </div>
                <div class="result-snippet">${escapeHtml(result.snippet.substring(0, 300))}...</div>
            </div>
        `;
    }).join('');

    resultsDiv.innerHTML = metaHtml + resultsHtml;
}

function getScoreClass(score) {
    if (score >= 0.7) return 'score-high';
    if (score >= 0.4) return 'score-medium';
    return 'score-low';
}

// Activity Monitor
let currentActivityView = 'ui'; // 'ui' or 'server'

function initializeActivityMonitor() {
    document.getElementById('refresh-activity').addEventListener('click', () => {
        if (currentActivityView === 'ui') {
            renderActivityLog();
        } else {
            loadServerLogs();
        }
    });
    document.getElementById('clear-activity').addEventListener('click', clearActivityLog);

    // Tab switching
    document.getElementById('tab-ui-logs').addEventListener('click', () => switchActivityView('ui'));
    document.getElementById('tab-server-logs').addEventListener('click', () => switchActivityView('server'));

    // Server logs filters
    document.getElementById('log-level-select').addEventListener('change', loadServerLogs);
    document.getElementById('log-lines-select').addEventListener('change', loadServerLogs);
}

function switchActivityView(view) {
    currentActivityView = view;

    // Update tab buttons
    document.getElementById('tab-ui-logs').classList.toggle('active', view === 'ui');
    document.getElementById('tab-server-logs').classList.toggle('active', view === 'server');

    // Show/hide appropriate content
    document.getElementById('activity-log').style.display = view === 'ui' ? 'block' : 'none';
    document.getElementById('server-logs').style.display = view === 'server' ? 'block' : 'none';

    // Show/hide filter controls
    document.getElementById('log-level-filter').style.display = view === 'server' ? 'inline-block' : 'none';
    document.getElementById('log-lines-filter').style.display = view === 'server' ? 'inline-block' : 'none';

    // Update clear button behavior
    const clearButton = document.getElementById('clear-activity');
    clearButton.style.display = view === 'ui' ? 'inline-block' : 'none';

    // Load appropriate content
    if (view === 'ui') {
        renderActivityLog();
    } else {
        loadServerLogs();
    }
}

function addActivityLog(type, message) {
    const timestamp = new Date().toLocaleTimeString();
    state.activityLog.unshift({ timestamp, type, message });

    // Keep only last 100 entries
    if (state.activityLog.length > 100) {
        state.activityLog = state.activityLog.slice(0, 100);
    }

    // If activity tab is active, re-render
    if (document.getElementById('activity-tab').classList.contains('active')) {
        renderActivityLog();
    }

    saveToLocalStorage();
}

function renderActivityLog() {
    const logDiv = document.getElementById('activity-log');

    if (state.activityLog.length === 0) {
        logDiv.innerHTML = '<div style="color: #94a3b8;">No activity yet. Perform a search to see logs here.</div>';
        return;
    }

    const logsHtml = state.activityLog.map(entry => `
        <div class="activity-entry">
            <span class="activity-timestamp">${entry.timestamp}</span>
            <span class="activity-type ${entry.type}">${entry.type.toUpperCase()}</span>
            <span>${escapeHtml(entry.message)}</span>
        </div>
    `).join('');

    logDiv.innerHTML = logsHtml;
}

function clearActivityLog() {
    if (confirm('Clear all activity logs?')) {
        state.activityLog = [];
        renderActivityLog();
        saveToLocalStorage();
        addActivityLog('info', 'Activity log cleared');
    }
}

async function loadServerLogs() {
    const logsDiv = document.getElementById('server-logs');
    const level = document.getElementById('log-level-select').value;
    const lines = document.getElementById('log-lines-select').value;

    try {
        logsDiv.innerHTML = '<div style="color: #94a3b8;">Loading server logs...</div>';

        const params = new URLSearchParams({ lines });
        if (level) {
            params.append('level', level);
        }

        const response = await fetch(`${API_BASE_URL}/logs?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.logs && data.logs.length > 0) {
            const logsHtml = data.logs.map(logLine => {
                // Colorize log levels
                const coloredLine = logLine
                    .replace(/(ERROR)/g, '<span style="color: #ef4444; font-weight: bold;">$1</span>')
                    .replace(/(WARNING)/g, '<span style="color: #f59e0b; font-weight: bold;">$1</span>')
                    .replace(/(INFO)/g, '<span style="color: #10b981;">$1</span>');
                return `<div style="padding: 0.25rem 0; border-bottom: 1px solid #334155;">${coloredLine}</div>`;
            }).join('');

            const filterInfo = data.filtered_by ? ` (filtered by ${data.filtered_by})` : '';
            logsDiv.innerHTML = `
                <div style="color: #94a3b8; margin-bottom: 1rem; font-size: 0.9rem;">
                    Showing ${data.total} lines${filterInfo}
                </div>
                ${logsHtml}
            `;
        } else if (data.message) {
            logsDiv.innerHTML = `<div style="color: #94a3b8;">${escapeHtml(data.message)}</div>`;
        } else {
            logsDiv.innerHTML = '<div style="color: #94a3b8;">No logs available.</div>';
        }
    } catch (error) {
        logsDiv.innerHTML = `<div style="color: #ef4444;">Failed to load server logs: ${escapeHtml(error.message)}</div>`;
        console.error('Failed to load server logs:', error);
    }
}

// Statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();

        document.getElementById('stat-keyword').textContent = data.keyword_documents.toLocaleString();
        document.getElementById('stat-vector').textContent = data.vector_chunks.toLocaleString();
        document.getElementById('stat-searches').textContent = state.stats.totalSearches.toLocaleString();

        if (state.stats.responseTimes.length > 0) {
            const avgTime = state.stats.responseTimes.reduce((a, b) => a + b, 0) / state.stats.responseTimes.length;
            document.getElementById('stat-avg-time').textContent = `${avgTime.toFixed(0)}ms`;
        } else {
            document.getElementById('stat-avg-time').textContent = '-';
        }

        // Update indexing status
        const indexingStatus = document.getElementById('indexing-status');
        const reindexButton = document.getElementById('reindex-button');
        const statusElement = document.getElementById('stat-index-status');

        // Only disable reindex button if BOTH Keyword and Vector are indexing
        // This allows starting Vector while Keyword is running (and vice versa)
        const keywordIndexing = data.keyword?.is_indexing || false;
        const vectorIndexing = data.vector?.is_indexing || false;
        const bothIndexing = keywordIndexing && vectorIndexing;

        if (data.is_indexing) {
            indexingStatus.style.display = 'flex';
            reindexButton.disabled = bothIndexing;  // Only disable if both are running

            // Update status text based on what's indexing
            if (bothIndexing) {
                statusElement.textContent = 'Keyword + Vector Indexing...';
            } else if (keywordIndexing) {
                statusElement.textContent = 'Keyword Indexing... (Vector available)';
            } else if (vectorIndexing) {
                statusElement.textContent = 'Vector Indexing... (Keyword available)';
            } else {
                statusElement.textContent = 'Indexing...';
            }
            statusElement.style.color = '#f59e0b';
        } else {
            indexingStatus.style.display = 'none';
            reindexButton.disabled = false;
            statusElement.textContent = 'Ready';
            statusElement.style.color = '#10b981';
        }

        // Update last index time
        if (data.last_index_time) {
            const date = new Date(data.last_index_time);
            document.getElementById('stat-last-index').textContent = date.toLocaleString();
        } else {
            document.getElementById('stat-last-index').textContent = 'Never';
        }

        addActivityLog('info', `Statistics loaded: ${data.keyword_documents} docs, ${data.vector_chunks} chunks`);
    } catch (error) {
        addActivityLog('error', `Failed to load statistics: ${error.message}`);
    }
}

// Repository Status Badge
function updateRepositoryBadge(status, count = 0) {
    const badge = document.getElementById('repo-status-badge');
    const icon = badge.querySelector('.repo-badge-icon');
    const text = badge.querySelector('.repo-badge-text');

    // Remove all status classes
    badge.classList.remove('repo-loading', 'repo-error', 'repo-loaded');

    switch(status) {
        case 'loading':
            badge.classList.add('repo-loading');
            icon.textContent = '⏳';
            text.textContent = 'Loading repositories...';
            break;
        case 'error':
            badge.classList.add('repo-error');
            icon.textContent = '❌';
            text.textContent = 'No repositories found';
            break;
        case 'loaded':
            badge.classList.add('repo-loaded');
            icon.textContent = '✅';
            text.textContent = `${count} ${count === 1 ? 'repository' : 'repositories'} available`;
            break;
    }
}

// Repository Management
async function loadRepositories() {
    const repositoryList = document.getElementById('repository-list');

    // Set loading state
    updateRepositoryBadge('loading');

    try {
        const response = await fetch(`${API_BASE_URL}/repositories`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const repositories = await response.json();
        state.repositories = repositories;

        renderRepositories();
        populateRepositoryFilter();

        // Update badge with success state (count only non-excluded repositories)
        const activeRepos = repositories.filter(r => !r.excluded);
        if (activeRepos.length === 0) {
            updateRepositoryBadge('error');
        } else {
            updateRepositoryBadge('loaded', activeRepos.length);
        }

        // Log repository names explicitly
        const repoNames = repositories.map(r => r.name).join(', ');
        addActivityLog('info', `Loaded ${repositories.length} ${repositories.length === 1 ? 'repository' : 'repositories'}: ${repoNames}`);

    } catch (error) {
        repositoryList.innerHTML = `<div class="error">Failed to load repositories: ${error.message}</div>`;
        addActivityLog('error', `Failed to load repositories: ${error.message}`);
        updateRepositoryBadge('error');
    }
}

function populateRepositoryFilter() {
    const filterSelect = document.getElementById('repository-filter');
    if (!filterSelect) return;

    // Keep the "All Repositories" option
    filterSelect.innerHTML = '<option value="">All Repositories</option>';

    // Sort repositories alphabetically by name
    const sortedRepos = [...state.repositories].sort((a, b) =>
        a.name.localeCompare(b.name)
    );

    // Add each repository as an option
    sortedRepos.forEach(repo => {
        const option = document.createElement('option');
        option.value = repo.name;
        option.textContent = `${repo.name} ${repo.enabled ? '' : '(disabled)'}`;
        option.disabled = !repo.enabled;
        filterSelect.appendChild(option);
    });

    addActivityLog('info', `Repository filter populated with ${state.repositories.length} options (alphabetically sorted)`);
}

function renderRepositories() {
    const repositoryList = document.getElementById('repository-list');

    if (state.repositories.length === 0) {
        repositoryList.innerHTML = '<div style="color: var(--text-muted);">No repositories configured</div>';
        return;
    }

    // Show ALL repos including excluded ones (but disabled)
    const reposHtml = state.repositories.map(repo => {
        const isExcluded = repo.excluded || false;
        const enabledClass = repo.enabled ? 'enabled' : 'disabled';
        const priorityClass = `priority-${repo.priority}`;
        const excludedClass = isExcluded ? 'excluded-repo' : '';

        // Debug logging for badge rendering
        console.log(`Rendering ${repo.name}: file_count=${repo.file_count}, has_stats=${!!(repo.indexing_stats && repo.indexing_stats.length)}`);

        // Calculate total indexed files from indexing_stats
        // Note: Don't sum across index types (would double-count files indexed in both)
        // Instead, take the max since files are indexed in both keyword and vector
        let totalIndexedFiles = 0;
        if (repo.indexing_stats && repo.indexing_stats.length > 0) {
            totalIndexedFiles = Math.max(...repo.indexing_stats.map(stat => stat.total_files_indexed || 0));
        }

        // Format file count badges - show both on-disk and indexed
        let fileCountBadge = '';
        if (repo.file_count !== null && repo.file_count !== undefined) {
            const formattedSize = formatBytes(repo.total_size_bytes);

            // Total files on disk badge
            fileCountBadge = `<span class="repository-badge file-count" title="Total files found on disk">${repo.file_count.toLocaleString()} files (${formattedSize})</span>`;

            // Indexed files badge (always show to indicate indexing status)
            const indexedPercent = repo.file_count > 0 ? ((totalIndexedFiles / repo.file_count) * 100).toFixed(0) : 0;
            fileCountBadge += ` <span class="repository-badge file-count" title="Files currently in search index">${totalIndexedFiles.toLocaleString()} indexed (${indexedPercent}%)</span>`;
        }

        // Format indexing time stats
        let indexingStatsBadges = '';
        if (repo.indexing_stats && repo.indexing_stats.length > 0) {
            const statsItems = repo.indexing_stats.map(stat => {
                const indexType = stat.index_type === 'keyword' ? 'Keyword' : 'Vector';

                // Show last reindex time if available, otherwise initial time
                const timeSeconds = stat.last_reindex_time_seconds !== null
                    ? stat.last_reindex_time_seconds
                    : stat.initial_index_time_seconds;

                if (timeSeconds === null || timeSeconds === 0) {
                    return ''; // No timing data yet
                }

                // Calculate rate: files per second
                const filesPerSec = stat.total_files_indexed / timeSeconds;

                // Format time with appropriate precision
                let timeDisplay;
                if (timeSeconds < 0.1) {
                    // For very fast operations, show milliseconds
                    timeDisplay = `${(timeSeconds * 1000).toFixed(0)}ms`;
                } else if (timeSeconds < 60) {
                    timeDisplay = `${timeSeconds.toFixed(1)}s`;
                } else {
                    const mins = Math.floor(timeSeconds / 60);
                    const secs = Math.floor(timeSeconds % 60);
                    timeDisplay = `${mins}m ${secs}s`;
                }

                return `<span class="repository-badge file-count" title="${stat.index_type} indexing: ${stat.total_files_indexed} files in ${timeDisplay} (${filesPerSec.toFixed(1)} files/sec)">${indexType}: ${timeDisplay}</span>`;
            }).filter(s => s !== '').join(' ');

            if (statsItems && statsItems.trim() !== '') {
                indexingStatsBadges = statsItems;
            }
        }

        // Excluded badge
        let excludedBadge = '';
        if (isExcluded) {
            excludedBadge = '<span class="repository-badge excluded" style="background-color: var(--status-warning); color: white;">🔒 LOCKED</span>';
        }

        return `
            <div class="repository-item ${excludedClass}">
                <input type="checkbox"
                       class="repo-checkbox"
                       value="${escapeHtml(repo.name)}"
                       id="repo-${escapeHtml(repo.name)}"
                       ${repo.enabled && !isExcluded ? 'checked' : ''}
                       ${isExcluded ? 'disabled' : ''}
                       title="${isExcluded ? 'This repository is locked. Click the lock button to unlock it before reindexing.' : ''}">
                <label for="repo-${escapeHtml(repo.name)}" class="repository-info">
                    <div class="repository-name">
                        ${escapeHtml(repo.name)}
                        <button class="readme-link" onclick="event.preventDefault(); event.stopPropagation(); openReadmeModal('${escapeHtml(repo.name)}');" title="View README">
                            README
                        </button>
                    </div>
                    <div class="repository-path">${escapeHtml(repo.path)}</div>
                    <div>
                        ${excludedBadge}
                        <span class="repository-badge ${enabledClass}">
                            ${repo.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                        <span class="repository-badge ${priorityClass}">
                            ${repo.priority.toUpperCase()}
                        </span>
                    </div>
                    ${fileCountBadge ? `<div>${fileCountBadge}</div>` : ''}
                    ${indexingStatsBadges ? `<div>${indexingStatsBadges}</div>` : ''}
                </label>
            </div>
        `;
    }).join('');

    repositoryList.innerHTML = reposHtml;
}

function getSelectedRepositories() {
    const checkboxes = document.querySelectorAll('.repo-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// Re-indexing
async function triggerReindex() {
    const selectedRepos = getSelectedRepositories();

    if (selectedRepos.length === 0) {
        alert('Please select at least one repository to re-index.');
        return;
    }

    const repoText = selectedRepos.length === state.repositories.length
        ? 'all repositories'
        : `${selectedRepos.length} selected repositor${selectedRepos.length === 1 ? 'y' : 'ies'}`;

    // Show confirmation modal
    showReindexModal(selectedRepos, repoText);
}

function showReindexModal(selectedRepos, repoText) {
    const modal = document.getElementById('reindex-modal');
    const modalMessage = document.getElementById('modal-message');
    const modalCancel = document.getElementById('modal-cancel');
    const modalConfirm = document.getElementById('modal-confirm');

    // Get selected options
    const indexKeyword = document.getElementById('index-keyword').checked;
    const indexVector = document.getElementById('index-vector').checked;
    const isFullRebuild = document.getElementById('mode-full').checked;

    // Build index type description
    const indexTypes = [];
    if (indexKeyword) indexTypes.push('Keyword (Meilisearch)');
    if (indexVector) indexTypes.push('Vector (semantic)');
    const indexTypeText = indexTypes.length > 0 ? indexTypes.join(' + ') : 'NONE';

    // Build mode description
    const modeText = isFullRebuild ? 'full rebuild' : 'incremental update';
    const modeDescription = isFullRebuild
        ? 'This will <strong>clear existing indexes</strong> and rebuild from scratch.'
        : 'This will update existing indexes with any new or modified files.';

    // Validation warning
    let warningHTML = '';
    if (indexTypes.length === 0) {
        warningHTML = '<div style="color: var(--danger-color); padding: 1rem; background: #fee2e2; border-radius: 6px; margin-bottom: 1rem;"><strong>⚠️ ERROR:</strong> You must select at least one index type (Keyword or Vector).</div>';
    }

    // Set modal message
    modalMessage.innerHTML = `
        ${warningHTML}
        <strong>You are about to ${modeText} ${repoText}.</strong><br><br>
        <strong>Index Types:</strong> ${indexTypeText}<br>
        <strong>Mode:</strong> ${modeText}<br><br>
        ${modeDescription}<br><br>
        <em>Note: This operation may take several minutes for large repositories.</em>
    `;

    // Disable confirm button if no index types selected
    modalConfirm.disabled = (indexTypes.length === 0);

    // Show modal
    modal.style.display = 'flex';

    // Set up event listeners
    const handleCancel = () => {
        modal.style.display = 'none';
        modalCancel.removeEventListener('click', handleCancel);
        modalConfirm.removeEventListener('click', handleConfirm);
    };

    const handleConfirm = () => {
        modal.style.display = 'none';
        modalCancel.removeEventListener('click', handleCancel);
        modalConfirm.removeEventListener('click', handleConfirm);
        executeReindex(selectedRepos);
    };

    modalCancel.addEventListener('click', handleCancel);
    modalConfirm.addEventListener('click', handleConfirm);
}

async function executeReindex(selectedRepos) {
    const reindexButton = document.getElementById('reindex-button');
    const indexingStatus = document.getElementById('indexing-status');

    try {
        reindexButton.disabled = true;
        indexingStatus.style.display = 'flex';

        // Get selected options
        const indexKeyword = document.getElementById('index-keyword').checked;
        const indexVector = document.getElementById('index-vector').checked;
        const isFullRebuild = document.getElementById('mode-full').checked;

        // Build request body
        const requestBody = {
            repositories: selectedRepos.length === state.repositories.length ? null : selectedRepos,
            index_keyword: indexKeyword,
            index_vector: indexVector,
            full_rebuild: isFullRebuild
        };

        const response = await fetch(`${API_BASE_URL}/reindex`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        addActivityLog('info', `Re-indexing ${data.repositories.join(', ')} started at ${new Date(data.started_at).toLocaleTimeString()}`);

        // Poll for completion every 5 seconds
        const pollInterval = setInterval(async () => {
            await loadStatistics();

            // Check if indexing is complete
            const statsResponse = await fetch(`${API_BASE_URL}/stats`);
            const statsData = await statsResponse.json();

            if (!statsData.is_indexing) {
                clearInterval(pollInterval);
                addActivityLog('info', 'Re-indexing completed successfully');
            }
        }, 5000);

    } catch (error) {
        indexingStatus.style.display = 'none';
        reindexButton.disabled = false;
        addActivityLog('error', `Re-indexing failed: ${error.message}`);
    }
}

function initializeReindex() {
    document.getElementById('reindex-button').addEventListener('click', triggerReindex);

    // Initialize "Select All" checkbox
    document.getElementById('select-all-repos').addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.repo-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = e.target.checked;
        });
    });
}

// Local Storage
function saveToLocalStorage() {
    try {
        localStorage.setItem('myragdb_state', JSON.stringify(state));
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
    }
}

function loadFromLocalStorage() {
    try {
        const saved = localStorage.getItem('myragdb_state');
        if (saved) {
            const loaded = JSON.parse(saved);
            state.activityLog = loaded.activityLog || [];
            state.stats = loaded.stats || { totalSearches: 0, responseTimes: [] };
        }
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatBytes(bytes) {
    if (bytes === null || bytes === undefined) return 'Unknown';
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Indexing Progress Update
async function updateIndexingProgress() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();

        const progressContainer = document.getElementById('indexing-progress');
        const headerText = document.getElementById('indexing-header-text');
        const detailText = document.getElementById('indexing-detail-text');
        const progressBarFill = document.getElementById('indexing-progress-bar-fill');

        if (data.is_indexing) {
            // Show progress indicator
            progressContainer.style.display = 'inline-flex';

            // Build header text with index types
            const indexTypes = data.index_types.join(' + ');
            headerText.textContent = `Indexing: ${indexTypes}`;

            // Build detail text
            let details = [];
            if (data.current_repository) {
                details.push(`Repository: ${data.current_repository} (${data.repositories_completed + 1}/${data.repositories_total})`);
            }
            if (data.current_phase) {
                details.push(`Phase: ${data.current_phase}`);
            }

            // Show progress using actual indexed document counts
            if (data.current_phase === 'Keyword') {
                details.push(`Keyword: ${data.keyword_documents.toLocaleString()} docs`);
            } else if (data.current_phase === 'Vector') {
                details.push(`Vector: ${data.vector_chunks.toLocaleString()} chunks`);
            }

            if (data.files_total > 0) {
                details.push(`Target: ${data.files_total.toLocaleString()} files`);
            }
            if (data.mode) {
                details.push(`Mode: ${data.mode === 'full_rebuild' ? 'Full Rebuild' : 'Incremental'}`);
            }
            detailText.textContent = details.join(' • ');

            // Update progress bar using actual document counts as rough estimate
            let progressPercent = 0;
            if (data.files_total > 0) {
                // Use actual indexed counts for progress estimation
                let indexedCount = 0;
                if (data.current_phase === 'Keyword') {
                    indexedCount = data.keyword_documents;
                } else if (data.current_phase === 'Vector') {
                    // Vector chunks can exceed file count, so cap at files_total
                    indexedCount = Math.min(data.vector_chunks, data.files_total);
                }
                progressPercent = (indexedCount / data.files_total) * 100;
            }
            progressBarFill.style.width = `${Math.min(100, progressPercent)}%`;
        } else {
            // Hide progress indicator
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('Failed to update indexing progress:', error);
    }
}

// Version Management
async function loadVersion() {
    try {
        const response = await fetch(`${API_BASE_URL}/version`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const versionBadge = document.getElementById('version-badge');
        if (versionBadge) {
            versionBadge.textContent = `v${data.version}`;
        }
    } catch (error) {
        console.error('Failed to load version:', error);
        const versionBadge = document.getElementById('version-badge');
        if (versionBadge) {
            versionBadge.textContent = 'v?.?.?';
        }
    }
}

// Repository Discovery Functions
function initializeDiscovery() {
    const scanButton = document.getElementById('scan-repositories-button');
    const addSelectedButton = document.getElementById('add-selected-button');
    const selectAllNewButton = document.getElementById('select-all-new-button');
    const selectAllVisibleButton = document.getElementById('select-all-visible-button');
    const filterSearch = document.getElementById('filter-repo-search');
    const filterStatus = document.getElementById('filter-repo-status');
    const filterPriority = document.getElementById('filter-repo-priority');
    const filterCreatedAfter = document.getElementById('filter-created-after');
    const filterCreatedBefore = document.getElementById('filter-created-before');
    const filterModifiedAfter = document.getElementById('filter-modified-after');
    const filterModifiedBefore = document.getElementById('filter-modified-before');
    const paginationPrev = document.getElementById('pagination-prev');
    const paginationNext = document.getElementById('pagination-next');

    if (scanButton) {
        scanButton.addEventListener('click', scanForRepositories);
    }

    if (addSelectedButton) {
        addSelectedButton.addEventListener('click', addSelectedRepositories);
    }

    if (selectAllNewButton) {
        selectAllNewButton.addEventListener('click', () => selectAllNew());
    }

    if (selectAllVisibleButton) {
        selectAllVisibleButton.addEventListener('click', () => selectAllVisible());
    }

    if (filterSearch) {
        filterSearch.addEventListener('input', () => {
            state.discoveryFilters.search = filterSearch.value;
            applyDiscoveryFilters();
        });
    }

    if (filterStatus) {
        filterStatus.addEventListener('change', () => {
            state.discoveryFilters.status = filterStatus.value;
            applyDiscoveryFilters();
        });
    }

    if (filterPriority) {
        filterPriority.addEventListener('change', () => {
            state.discoveryFilters.priority = filterPriority.value;
            applyDiscoveryFilters();
        });
    }

    if (filterCreatedAfter) {
        filterCreatedAfter.addEventListener('change', () => {
            state.discoveryFilters.createdAfter = filterCreatedAfter.value;
            applyDiscoveryFilters();
        });
    }

    if (filterCreatedBefore) {
        filterCreatedBefore.addEventListener('change', () => {
            state.discoveryFilters.createdBefore = filterCreatedBefore.value;
            applyDiscoveryFilters();
        });
    }

    if (filterModifiedAfter) {
        filterModifiedAfter.addEventListener('change', () => {
            state.discoveryFilters.modifiedAfter = filterModifiedAfter.value;
            applyDiscoveryFilters();
        });
    }

    if (filterModifiedBefore) {
        filterModifiedBefore.addEventListener('change', () => {
            state.discoveryFilters.modifiedBefore = filterModifiedBefore.value;
            applyDiscoveryFilters();
        });
    }

    if (paginationPrev) {
        paginationPrev.addEventListener('click', () => {
            if (state.discoveryPagination.currentPage > 1) {
                state.discoveryPagination.currentPage--;
                renderDiscoveredRepos();
            }
        });
    }

    if (paginationNext) {
        paginationNext.addEventListener('click', () => {
            if (state.discoveryPagination.currentPage < state.discoveryPagination.totalPages) {
                state.discoveryPagination.currentPage++;
                renderDiscoveredRepos();
            }
        });
    }
}

async function scanForRepositories() {
    const pathInput = document.getElementById('discovery-path');
    const depthSelect = document.getElementById('discovery-depth');
    const scanButton = document.getElementById('scan-repositories-button');
    const container = document.getElementById('discovered-repos-container');

    const rootPath = pathInput.value.trim();
    const maxDepth = parseInt(depthSelect.value);

    if (!rootPath) {
        container.innerHTML = '<div class="error">Please enter a root path to scan</div>';
        return;
    }

    try {
        scanButton.disabled = true;
        scanButton.textContent = '🔍 Scanning...';
        container.innerHTML = '<div class="loading">Scanning for repositories...</div>';

        const response = await fetch(`${API_BASE_URL}/repositories/discover`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                root_path: rootPath,
                max_depth: maxDepth
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        state.discoveredRepos = data.repositories || [];

        // Show filters and bulk actions
        document.getElementById('discovery-filters').style.display = 'grid';
        document.getElementById('discovery-bulk-actions').style.display = 'flex';
        document.getElementById('discovery-pagination').style.display = 'flex';

        // Update filter status options with counts
        const filterStatus = document.getElementById('filter-repo-status');
        filterStatus.innerHTML = `
            <option value="all">All Repositories (${data.total_found})</option>
            <option value="new">New Only (${data.new_repositories})</option>
            <option value="indexed">Already Indexed (${data.already_indexed})</option>
        `;

        // Reset pagination
        state.discoveryPagination.currentPage = 1;

        // Render results
        applyDiscoveryFilters();

        addActivityLog('info', `Discovered ${data.total_found} repositories (${data.new_repositories} new, ${data.already_indexed} already indexed)`);

    } catch (error) {
        container.innerHTML = `<div class="error">❌ Discovery failed: ${error.message}</div>`;
        addActivityLog('error', `Repository discovery failed: ${error.message}`);
    } finally {
        scanButton.disabled = false;
        scanButton.textContent = '🔍 Scan for Repositories';
    }
}

function applyDiscoveryFilters() {
    const { search, status, priority, createdAfter, createdBefore, modifiedAfter, modifiedBefore } = state.discoveryFilters;

    let filtered = state.discoveredRepos.filter(repo => {
        // Search filter
        if (search && !repo.name.toLowerCase().includes(search.toLowerCase()) &&
            !repo.path.toLowerCase().includes(search.toLowerCase())) {
            return false;
        }

        // Status filter
        if (status === 'new' && repo.is_already_indexed) return false;
        if (status === 'indexed' && !repo.is_already_indexed) return false;
        if (status === 'excluded' && !repo.excluded) return false;

        // Priority filter (for repos that have priority set)
        if (priority !== 'all' && repo.priority && repo.priority !== priority) {
            return false;
        }

        // Date filters
        if (repo.created_date) {
            const repoCreatedDate = new Date(repo.created_date).toISOString().split('T')[0];

            if (createdAfter && repoCreatedDate < createdAfter) {
                return false;
            }

            if (createdBefore && repoCreatedDate > createdBefore) {
                return false;
            }
        }

        if (repo.modified_date) {
            const repoModifiedDate = new Date(repo.modified_date).toISOString().split('T')[0];

            if (modifiedAfter && repoModifiedDate < modifiedAfter) {
                return false;
            }

            if (modifiedBefore && repoModifiedDate > modifiedBefore) {
                return false;
            }
        }

        return true;
    });

    // Calculate pagination
    state.discoveryPagination.totalPages = Math.ceil(filtered.length / state.discoveryPagination.pageSize);

    // Store filtered repos in state
    state.filteredDiscoveredRepos = filtered;

    renderDiscoveredRepos();
}

function renderDiscoveredRepos() {
    const container = document.getElementById('discovered-repos-container');
    const filtered = state.filteredDiscoveredRepos || state.discoveredRepos;
    const { currentPage, pageSize } = state.discoveryPagination;

    if (filtered.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">No repositories match the current filters.</div>';
        updatePaginationInfo(0, 0, 0);
        return;
    }

    // Build clone group map to count clones
    const cloneGroups = {};
    filtered.forEach(repo => {
        if (repo.clone_group) {
            if (!cloneGroups[repo.clone_group]) {
                cloneGroups[repo.clone_group] = [];
            }
            cloneGroups[repo.clone_group].push(repo);
        }
    });

    // Paginate
    const startIdx = (currentPage - 1) * pageSize;
    const endIdx = Math.min(startIdx + pageSize, filtered.length);
    const pageRepos = filtered.slice(startIdx, endIdx);

    const reposHtml = pageRepos.map(repo => {
        const isNew = !repo.is_already_indexed;
        const isExcluded = repo.excluded || false;

        // Badge logic
        let badgeClass = isNew ? 'new' : 'indexed';
        let badgeText = isNew ? 'NEW' : 'INDEXED';
        let excludedBadge = '';
        let cloneBadge = '';

        if (isExcluded) {
            excludedBadge = '<span class="badge excluded">🔒 EXCLUDED</span>';
        }

        // Clone detection
        if (repo.clone_group && cloneGroups[repo.clone_group]) {
            const cloneCount = cloneGroups[repo.clone_group].length;
            if (cloneCount > 1) {
                cloneBadge = `<span class="badge clone" title="${cloneCount} clones detected for ${repo.clone_group}">📋 ${cloneCount} CLONES</span>`;
            }
        }

        const checkboxHtml = `<input type="checkbox" class="repo-discovery-checkbox" ${isNew ? '' : 'disabled'} data-repo-path="${escapeHtml(repo.path)}">`;

        const priorityHtml = `
            <select class="repo-card-priority" data-repo-path="${escapeHtml(repo.path)}" ${isNew ? '' : ''}>
                <option value="high">High</option>
                <option value="medium" selected>Medium</option>
                <option value="low">Low</option>
            </select>
        `;

        let actionsHtml = '';
        if (isNew) {
            actionsHtml = `
                <button class="btn-small btn-add" onclick="addSingleRepository('${escapeHtml(repo.path)}')">➕ Add</button>
                <button class="btn-small btn-preview" onclick="previewRepository('${escapeHtml(repo.path)}')">👁️ Preview</button>
            `;
        } else {
            // For indexed repos: show lock/unlock toggle and remove button
            const lockButtonText = isExcluded ? '🔓 Unlock' : '🔒 Lock';
            const lockButtonClass = isExcluded ? 'btn-unlock' : 'btn-lock';
            const lockButtonTitle = isExcluded ? 'Unlock repository to allow re-indexing' : 'Lock repository to prevent re-indexing';
            actionsHtml = `
                <button class="btn-small ${lockButtonClass}" onclick="toggleRepositoryExcluded('${escapeHtml(repo.name)}', ${!isExcluded})" title="${lockButtonTitle}">${lockButtonText}</button>
                <button class="btn-small btn-remove" onclick="removeRepository('${escapeHtml(repo.name)}')'" title="Remove from configuration (does not delete files)">🗑️ Remove from Config</button>
                <button class="btn-small btn-configure" onclick="configureRepository('${escapeHtml(repo.name)}')">⚙️ Configure</button>
            `;
        }

        return `
            <div class="repo-card ${isNew ? '' : 'indexed'} ${isExcluded ? 'excluded' : ''}">
                <div class="repo-card-header">
                    ${checkboxHtml}
                    <div class="repo-card-info">
                        <div class="repo-card-name">
                            ${escapeHtml(repo.name)}
                            <button class="readme-link" onclick="event.stopPropagation(); openReadmeModal('${escapeHtml(repo.name)}');" title="View README">
                                README
                            </button>
                        </div>
                        <div class="repo-card-path">${escapeHtml(repo.path)}</div>
                        <div class="repo-card-badges">
                            <span class="badge ${badgeClass}">${badgeText}</span>
                            ${excludedBadge}
                            ${cloneBadge}
                            ${priorityHtml}
                        </div>
                        <div class="repo-card-actions">
                            ${actionsHtml}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = reposHtml;
    updatePaginationInfo(startIdx + 1, endIdx, filtered.length);
    updateAddSelectedButton();
}

function updatePaginationInfo(start, end, total) {
    const paginationInfo = document.getElementById('pagination-info');
    const prevButton = document.getElementById('pagination-prev');
    const nextButton = document.getElementById('pagination-next');

    if (paginationInfo) {
        paginationInfo.textContent = `Showing ${start}-${end} of ${total} repositories`;
    }

    if (prevButton) {
        prevButton.disabled = state.discoveryPagination.currentPage === 1;
    }

    if (nextButton) {
        nextButton.disabled = state.discoveryPagination.currentPage === state.discoveryPagination.totalPages;
    }
}

function selectAllNew() {
    const checkboxes = document.querySelectorAll('.repo-discovery-checkbox:not(:disabled)');
    checkboxes.forEach(cb => cb.checked = true);
    updateAddSelectedButton();
}

function selectAllVisible() {
    const checkboxes = document.querySelectorAll('.repo-discovery-checkbox');
    checkboxes.forEach(cb => {
        if (!cb.disabled) cb.checked = true;
    });
    updateAddSelectedButton();
}

function updateAddSelectedButton() {
    const addButton = document.getElementById('add-selected-button');
    const checkboxes = document.querySelectorAll('.repo-discovery-checkbox:checked:not(:disabled)');
    const count = checkboxes.length;

    if (addButton) {
        addButton.textContent = count > 0
            ? `➕ Add Selected to Config (${count} selected)`
            : `➕ Add Selected to Config`;
        addButton.disabled = count === 0;
    }

    // Add event listener for checkbox changes
    document.querySelectorAll('.repo-discovery-checkbox').forEach(checkbox => {
        checkbox.removeEventListener('change', updateAddSelectedButton);
        checkbox.addEventListener('change', updateAddSelectedButton);
    });
}

async function addSelectedRepositories() {
    const checkboxes = document.querySelectorAll('.repo-discovery-checkbox:checked:not(:disabled)');
    const repoPaths = Array.from(checkboxes).map(cb => cb.getAttribute('data-repo-path'));

    if (repoPaths.length === 0) {
        alert('Please select at least one repository to add.');
        return;
    }

    // Get priorities for each selected repo
    const reposWithPriority = repoPaths.map(path => {
        const prioritySelect = document.querySelector(`.repo-card-priority[data-repo-path="${path}"]`);
        return {
            path: path,
            priority: prioritySelect ? prioritySelect.value : 'medium'
        };
    });

    const defaultPriority = document.getElementById('default-priority-select').value;

    try {
        const addButton = document.getElementById('add-selected-button');
        addButton.disabled = true;
        addButton.textContent = '⏳ Adding...';

        const response = await fetch(`${API_BASE_URL}/repositories/add-batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repositories: repoPaths,
                priority: defaultPriority,
                enabled: true
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        addActivityLog('success', `${data.message}: ${data.added_count} added, ${data.skipped_count} skipped`);
        alert(`Successfully added ${data.added_count} repositories to configuration.\n${data.skipped_count} repositories were skipped (already exist).`);

        // Refresh the discovery scan to update "INDEXED" status
        await scanForRepositories();

        // Reload repositories list
        await loadRepositories();

    } catch (error) {
        addActivityLog('error', `Failed to add repositories: ${error.message}`);
        alert(`Failed to add repositories: ${error.message}`);
    }
}

async function addSingleRepository(path) {
    const prioritySelect = document.querySelector(`.repo-card-priority[data-repo-path="${path}"]`);
    const priority = prioritySelect ? prioritySelect.value : 'medium';

    try {
        const response = await fetch(`${API_BASE_URL}/repositories/add-batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repositories: [path],
                priority: priority,
                enabled: true
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        addActivityLog('success', `Repository added: ${path}`);
        alert('Repository successfully added to configuration!');

        // Refresh
        await scanForRepositories();
        await loadRepositories();

    } catch (error) {
        addActivityLog('error', `Failed to add repository: ${error.message}`);
        alert(`Failed to add repository: ${error.message}`);
    }
}

function previewRepository(path) {
    alert(`Preview functionality for: ${path}\n\nThis would show:\n- Number of files\n- File types distribution\n- Estimated index size`);
}

function triggerSingleReindex(repoName) {
    alert(`Re-index functionality for: ${repoName}\n\nThis would trigger re-indexing for this specific repository.`);
}

async function removeRepository(repoName) {
    if (!confirm(`Are you sure you want to remove "${repoName}" from configuration?\n\nThis will NOT delete any files on disk, only removes it from the indexing configuration.`)) {
        return;
    }

    try {
        const response = await fetch(`/repositories/${encodeURIComponent(repoName)}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            const result = await response.json();
            addActivityLog('info', `Repository "${repoName}" removed from configuration`);

            // Refresh discovery results to show updated status
            const scanButton = document.getElementById('scan-repositories-button');
            if (scanButton) {
                scanButton.click();
            }

            // Also refresh repositories list
            loadRepositories();
        } else {
            const error = await response.json();
            addActivityLog('error', `Failed to remove repository: ${error.detail || 'Unknown error'}`);
            alert(`Failed to remove repository: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        addActivityLog('error', `Failed to remove repository: ${error.message}`);
        alert(`Failed to remove repository: ${error.message}`);
    }
}

async function configureRepository(repoName) {
    // Find repository in either discovered repos or regular repos list
    let repo = state.discoveredRepos.find(r => r.name === repoName);
    if (!repo) {
        repo = state.repositories.find(r => r.name === repoName);
    }

    if (!repo) {
        alert(`Repository "${repoName}" not found`);
        return;
    }

    // Populate modal with current values
    document.getElementById('configure-repo-name').value = repoName;
    document.getElementById('configure-priority').value = repo.priority || 'medium';

    // Set enabled status
    if (repo.enabled) {
        document.getElementById('configure-enabled-yes').checked = true;
    } else {
        document.getElementById('configure-enabled-no').checked = true;
    }

    // Set excluded status
    const isExcluded = repo.excluded || false;
    if (isExcluded) {
        document.getElementById('configure-excluded-yes').checked = true;
    } else {
        document.getElementById('configure-excluded-no').checked = true;
    }

    // Set exclude patterns (join array into newline-separated string)
    const excludePatterns = repo.file_patterns?.exclude || [];
    document.getElementById('configure-exclude-patterns').value = excludePatterns.join('\n');

    // Show modal
    document.getElementById('configure-modal').style.display = 'flex';
}

function closeConfigureModal() {
    document.getElementById('configure-modal').style.display = 'none';
}

async function saveRepositoryConfiguration() {
    const repoName = document.getElementById('configure-repo-name').value;
    const priority = document.getElementById('configure-priority').value;
    const enabled = document.querySelector('input[name="enabled"]:checked').value === 'true';
    const excluded = document.querySelector('input[name="excluded"]:checked').value === 'true';

    // Get exclude patterns from textarea, split by newlines, filter empty lines, and join with commas
    const excludePatternsText = document.getElementById('configure-exclude-patterns').value;
    const excludePatterns = excludePatternsText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .join(',');

    try {
        // Build query params
        let url = `/repositories/${encodeURIComponent(repoName)}?priority=${priority}&enabled=${enabled}&excluded=${excluded}`;
        if (excludePatterns) {
            url += `&exclude_patterns=${encodeURIComponent(excludePatterns)}`;
        }

        const response = await fetch(url, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const result = await response.json();
            addActivityLog('success', `Repository "${repoName}" configuration updated`);

            // Close modal
            closeConfigureModal();

            // Refresh both discovered repos and regular repos lists
            const scanButton = document.getElementById('scan-repositories-button');
            if (scanButton) {
                scanButton.click();
            }
            loadRepositories();
        } else {
            const error = await response.json();
            addActivityLog('error', `Failed to update repository: ${error.detail || 'Unknown error'}`);
            alert(`Failed to update repository: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        addActivityLog('error', `Failed to update repository: ${error.message}`);
        alert(`Failed to update repository: ${error.message}`);
    }
}

async function toggleRepositoryExcluded(repoName, excludedValue) {
    try {
        const response = await fetch(`/repositories/${encodeURIComponent(repoName)}?excluded=${excludedValue}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const result = await response.json();
            addActivityLog('info', `Repository "${repoName}" ${excludedValue ? 'locked (excluded)' : 'unlocked'}`);

            // Refresh discovery results to show updated status
            const scanButton = document.getElementById('scan-repositories-button');
            if (scanButton) {
                scanButton.click();
            }

            // Also refresh repositories list
            loadRepositories();
        } else {
            const error = await response.json();
            addActivityLog('error', `Failed to update repository: ${error.detail || 'Unknown error'}`);
            alert(`Failed to update repository: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        addActivityLog('error', `Failed to update repository: ${error.message}`);
        alert(`Failed to update repository: ${error.message}`);
    }
}

// ============================================================================
// Bulk Repository Actions
// ============================================================================

async function bulkUpdateRepositories(action, actionName) {
    // Confirm action with user
    const confirmMessage = `Are you sure you want to ${actionName} ALL repositories?`;
    if (!confirm(confirmMessage)) {
        return;
    }

    try {
        const response = await fetch(`/repositories/bulk-update?action=${action}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const result = await response.json();
            addActivityLog('success', result.message);

            // Refresh both discovered repos and regular repos lists
            const scanButton = document.getElementById('scan-repositories-button');
            if (scanButton) {
                scanButton.click();
            }
            loadRepositories();
        } else {
            const error = await response.json();
            addActivityLog('error', `Failed to perform bulk update: ${error.detail || 'Unknown error'}`);
            alert(`Failed to perform bulk update: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        addActivityLog('error', `Failed to perform bulk update: ${error.message}`);
        alert(`Failed to perform bulk update: ${error.message}`);
    }
}

async function enableAllRepositories() {
    await bulkUpdateRepositories('enable_all', 'enable');
}

async function disableAllRepositories() {
    await bulkUpdateRepositories('disable_all', 'disable');
}

async function unlockAllRepositories() {
    await bulkUpdateRepositories('unlock_all', 'unlock');
}

async function lockAllRepositories() {
    await bulkUpdateRepositories('lock_all', 'lock');
}

// Make bulk action functions globally available
window.enableAllRepositories = enableAllRepositories;
window.disableAllRepositories = disableAllRepositories;
window.unlockAllRepositories = unlockAllRepositories;
window.lockAllRepositories = lockAllRepositories;

// ============================================================================
// LLM Manager
// ============================================================================

const MODE_DESCRIPTIONS = {
    basic: 'Standard chat mode (no function calling)',
    tools: 'Function calling enabled with --jinja',
    performance: 'Function calling + parallel processing',
    extended: 'Function calling + extended context (32k)'
};

async function loadLLMModels() {
    const container = document.getElementById('llm-models-grid');
    if (!container) return;

    // Show loading state immediately - UI renders instantly
    const loadingModels = [
        {"id": "qwen-coder-7b", "name": "Qwen Coder 7B", "port": 8085, "status": "checking", "category": "best"},
        {"id": "qwen2.5-32b", "name": "Qwen 2.5 32B Instruct", "port": 8084, "status": "checking", "category": "best"},
        {"id": "deepseek-r1-qwen-32b", "name": "DeepSeek R1 Qwen 32B", "port": 8092, "status": "checking", "category": "best"},
        {"id": "llama-3.1-8b", "name": "Llama 3.1 8B", "port": 8087, "status": "checking", "category": "best"},
        {"id": "llama-4-scout-17b", "name": "Llama 4 Scout 17B (Q3_K_S)", "port": 8088, "status": "checking", "category": "best"},
        {"id": "hermes-3-llama-8b", "name": "Hermes 3 Llama 8B", "port": 8086, "status": "checking", "category": "best"},
        {"id": "mistral-7b", "name": "Mistral 7B", "port": 8083, "status": "checking", "category": "limited"},
        {"id": "mistral-small-24b", "name": "Mistral Small 24B", "port": 8089, "status": "checking", "category": "limited"},
        {"id": "phi3", "name": "Phi-3", "port": 8081, "status": "checking", "category": "limited"},
        {"id": "smollm3", "name": "SmolLM3", "port": 8082, "status": "checking", "category": "limited"}
    ];

    renderLLMModels(loadingModels);

    // Fetch actual status in background
    try {
        const response = await fetch(`${API_BASE_URL}/llm/models`);
        if (!response.ok) {
            throw new Error('Failed to fetch LLM models');
        }

        const models = await response.json();
        renderLLMModels(models);
        addActivityLog('info', `Loaded ${models.length} LLM models`);
    } catch (error) {
        console.error('Error loading LLM models:', error);
        addActivityLog('error', `Failed to load LLM models: ${error.message}`);

        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">
                <p>Failed to load LLM models</p>
                <p style="font-size: 14px; margin-top: 8px;">${error.message}</p>
            </div>
        `;
    }
}

function renderLLMModels(models) {
    const container = document.getElementById('llm-models-grid');
    if (!container) return;

    if (models.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: rgba(255,255,255,0.6);">
                <p>No LLM models configured</p>
            </div>
        `;
        return;
    }

    container.innerHTML = models.map(model => createLLMModelCard(model)).join('');

    // Attach event listeners to all start/stop buttons
    models.forEach(model => {
        const startButton = document.getElementById(`llm-start-${model.id}`);
        const stopButton = document.getElementById(`llm-stop-${model.id}`);
        const modeSelect = document.getElementById(`llm-mode-${model.id}`);

        if (startButton) {
            startButton.addEventListener('click', () => startLLM(model.id));
        }

        if (stopButton) {
            stopButton.addEventListener('click', () => stopLLM(model.id));
        }

        if (modeSelect) {
            modeSelect.addEventListener('change', (e) => updateModeDescription(model.id, e.target.value));
        }
    });
}

function createLLMModelCard(model) {
    const isRunning = model.status === 'running';
    const isChecking = model.status === 'checking';
    const statusClass = isRunning ? 'running' : (isChecking ? 'checking' : 'stopped');

    let statusText = 'Stopped';
    if (isRunning) statusText = 'Running';
    if (isChecking) statusText = 'Checking...';

    return `
        <div class="llm-model-card ${statusClass}" id="llm-card-${model.id}">
            <div class="llm-model-header">
                <div class="llm-model-name">${model.name}</div>
                <div class="llm-model-category ${model.category}">${model.category}</div>
            </div>

            <div class="llm-model-info">
                <div class="llm-model-info-row">
                    <span class="llm-model-info-label">Port:</span>
                    <span class="llm-model-info-value">${model.port}</span>
                </div>
                <div class="llm-model-info-row">
                    <span class="llm-model-info-label">Status:</span>
                    <span class="llm-model-status ${statusClass}">
                        <span class="llm-model-status-dot"></span>
                        ${statusText}
                    </span>
                </div>
            </div>

            <div class="llm-mode-selector" id="llm-mode-selector-${model.id}" ${(isRunning || isChecking) ? 'style="display: none;"' : ''}>
                <label for="llm-mode-${model.id}">Mode:</label>
                <select id="llm-mode-${model.id}" ${isChecking ? 'disabled' : ''}>
                    <option value="basic">Basic</option>
                    <option value="tools" selected>Tools (Function Calling)</option>
                    <option value="performance">Performance</option>
                    <option value="extended">Extended Context</option>
                </select>
                <div class="llm-mode-info" id="llm-mode-info-${model.id}">
                    ${MODE_DESCRIPTIONS.tools}
                </div>
            </div>

            <div class="llm-model-actions">
                ${isChecking ? `
                    <button class="llm-start-button" disabled>
                        <span class="spinner" style="width: 14px; height: 14px; border-width: 2px; margin-right: 8px;"></span>
                        Checking status...
                    </button>
                ` : isRunning ? `
                    <button id="llm-stop-${model.id}" class="llm-stop-button">
                        🛑 Stop LLM
                    </button>
                ` : `
                    <button id="llm-start-${model.id}" class="llm-start-button">
                        🚀 Start LLM
                    </button>
                `}
            </div>

            <div id="llm-message-${model.id}" style="display: none;"></div>
        </div>
    `;
}

function updateModeDescription(modelId, mode) {
    const infoElement = document.getElementById(`llm-mode-info-${modelId}`);
    if (infoElement && MODE_DESCRIPTIONS[mode]) {
        infoElement.textContent = MODE_DESCRIPTIONS[mode];
    }
}

async function startLLM(modelId) {
    const button = document.getElementById(`llm-start-${modelId}`);
    const modeSelect = document.getElementById(`llm-mode-${modelId}`);
    const messageElement = document.getElementById(`llm-message-${modelId}`);
    const card = document.getElementById(`llm-card-${modelId}`);

    if (!button || !modeSelect || !messageElement || !card) return;

    const mode = modeSelect.value;

    // Disable button and show loading state
    button.disabled = true;
    button.innerHTML = '<span class="spinner" style="width: 14px; height: 14px; border-width: 2px; margin-right: 8px;"></span>Starting...';

    // Clear previous message
    messageElement.style.display = 'none';
    messageElement.className = '';

    addActivityLog('info', `Starting ${modelId} in ${mode} mode...`);

    try {
        const response = await fetch(`${API_BASE_URL}/llm/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_id: modelId,
                mode: mode
            })
        });

        const result = await response.json();

        if (result.status === 'success') {
            // Show success message
            messageElement.className = 'llm-model-message success';
            messageElement.textContent = result.message;
            messageElement.style.display = 'block';

            // Update card appearance
            card.classList.add('running');
            card.classList.remove('stopped');

            // Update button
            button.className = 'llm-start-button running';
            button.innerHTML = '✅ Running';
            button.disabled = false;

            // Update status in card
            const statusElement = card.querySelector('.llm-model-status');
            if (statusElement) {
                statusElement.className = 'llm-model-status running';
                statusElement.innerHTML = '<span class="llm-model-status-dot"></span>Running';
            }

            addActivityLog('success', `${modelId} started successfully in ${mode} mode`);

            // Update header LLM status badge immediately
            updateLLMStatusBadge();

            // Auto-hide success message after 5 seconds
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 5000);

        } else {
            // Show error message
            messageElement.className = 'llm-model-message error';
            messageElement.textContent = result.message;
            messageElement.style.display = 'block';

            // Re-enable button
            button.disabled = false;
            button.innerHTML = '🚀 Start LLM';

            addActivityLog('error', `Failed to start ${modelId}: ${result.message}`);
        }

    } catch (error) {
        console.error('Error starting LLM:', error);

        messageElement.className = 'llm-model-message error';
        messageElement.textContent = `Error: ${error.message}`;
        messageElement.style.display = 'block';

        button.disabled = false;
        button.innerHTML = '🚀 Start LLM';

        addActivityLog('error', `Error starting ${modelId}: ${error.message}`);
    }
}

async function stopLLM(modelId) {
    const button = document.getElementById(`llm-stop-${modelId}`);
    const messageElement = document.getElementById(`llm-message-${modelId}`);
    const card = document.getElementById(`llm-card-${modelId}`);

    if (!button || !messageElement || !card) return;

    // Disable button and show loading state
    button.disabled = true;
    button.innerHTML = '<span class="spinner" style="width: 14px; height: 14px; border-width: 2px; margin-right: 8px;"></span>Stopping...';

    // Clear previous message
    messageElement.style.display = 'none';
    messageElement.className = '';

    addActivityLog('info', `Stopping ${modelId}...`);

    try {
        const response = await fetch(`${API_BASE_URL}/llm/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_id: modelId
            })
        });

        const result = await response.json();

        if (result.status === 'success') {
            // Show success message
            messageElement.className = 'llm-model-message success';
            messageElement.textContent = result.message;
            messageElement.style.display = 'block';

            // Update card appearance
            card.classList.remove('running');
            card.classList.add('stopped');

            // Replace stop button with start button
            const actionsContainer = card.querySelector('.llm-model-actions');
            if (actionsContainer) {
                actionsContainer.innerHTML = `
                    <button id="llm-start-${modelId}" class="llm-start-button">
                        🚀 Start LLM
                    </button>
                `;

                // Re-attach event listener to new start button
                const newStartButton = document.getElementById(`llm-start-${modelId}`);
                if (newStartButton) {
                    newStartButton.addEventListener('click', () => startLLM(modelId));
                }
            }

            // Show mode selector again
            const modeSelector = document.getElementById(`llm-mode-selector-${modelId}`);
            if (modeSelector) {
                modeSelector.style.display = 'block';
            }

            // Update status in card
            const statusElement = card.querySelector('.llm-model-status');
            if (statusElement) {
                statusElement.className = 'llm-model-status stopped';
                statusElement.innerHTML = '<span class="llm-model-status-dot"></span>Stopped';
            }

            addActivityLog('success', `${modelId} stopped successfully`);

            // Update header LLM status badge immediately
            updateLLMStatusBadge();

            // Auto-hide success message after 5 seconds
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 5000);

        } else {
            // Show error message
            messageElement.className = 'llm-model-message error';
            messageElement.textContent = result.message;
            messageElement.style.display = 'block';

            // Re-enable button
            button.disabled = false;
            button.innerHTML = '🛑 Stop LLM';

            addActivityLog('error', `Failed to stop ${modelId}: ${result.message}`);
        }

    } catch (error) {
        console.error('Error stopping LLM:', error);

        messageElement.className = 'llm-model-message error';
        messageElement.textContent = `Error: ${error.message}`;
        messageElement.style.display = 'block';

        button.disabled = false;
        button.innerHTML = '🛑 Stop LLM';

        addActivityLog('error', `Error stopping ${modelId}: ${error.message}`);
    }
}

// Initialize LLM Manager when tab is shown
document.addEventListener('DOMContentLoaded', () => {
    const llmManagerTab = document.querySelector('[data-tab="llm-manager"]');
    if (llmManagerTab) {
        llmManagerTab.addEventListener('click', () => {
            loadLLMModels();
        });
    }

    // Make LLM status badge clickable to navigate to LLM Manager tab
    const llmStatusBadge = document.getElementById('llm-status-badge');
    if (llmStatusBadge) {
        llmStatusBadge.addEventListener('click', () => {
            // Switch to LLM Manager tab
            const llmTab = document.querySelector('[data-tab="llm-manager"]');
            if (llmTab) {
                llmTab.click();
            }
        });
    }
});

// Update LLM Status Badge
async function updateLLMStatusBadge() {
    const badge = document.getElementById('llm-status-badge');
    if (!badge) return;

    const icon = badge.querySelector('.llm-badge-icon');
    const text = badge.querySelector('.llm-badge-text');

    try {
        const response = await fetch(`${API_BASE_URL}/llm/models`);
        if (!response.ok) {
            // API not available or error
            badge.classList.remove('llm-running');
            badge.classList.add('llm-none');
            icon.textContent = '🤖';
            text.textContent = 'No LLM Running';
            return;
        }

        const models = await response.json();
        const runningModels = models.filter(m => m.status === 'running');

        if (runningModels.length === 0) {
            // No models running
            badge.classList.remove('llm-running');
            badge.classList.add('llm-none');
            icon.textContent = '🤖';
            text.textContent = 'No LLM Running';
        } else if (runningModels.length === 1) {
            // One model running
            badge.classList.remove('llm-none');
            badge.classList.add('llm-running');
            icon.textContent = '✨';
            text.textContent = `${runningModels[0].name} Running`;
            badge.title = `Port: ${runningModels[0].port}`;
        } else {
            // Multiple models running
            badge.classList.remove('llm-none');
            badge.classList.add('llm-running');
            icon.textContent = '✨';
            text.textContent = `${runningModels.length} LLMs Running`;
            const modelNames = runningModels.map(m => `${m.name} (${m.port})`).join(', ');
            badge.title = `Running: ${modelNames}`;
        }
    } catch (error) {
        // Error fetching LLM status - show as none running
        badge.classList.remove('llm-running');
        badge.classList.add('llm-none');
        icon.textContent = '🤖';
        text.textContent = 'No LLM Running';
    }
}

// Auto-refresh health status, indexing progress, and LLM status every 2 seconds
setInterval(() => {
    checkHealthStatus();
    updateIndexingProgress();
    updateLLMStatusBadge();
}, 2000);

// Initial LLM status check on page load
document.addEventListener('DOMContentLoaded', () => {
    updateLLMStatusBadge();
});

// ====================
// Observability Tab
// ====================

let observabilityCharts = {
    searchPerformance: null,
    searchType: null,
    errorRate: null,
    errorComponent: null
};

// Get time range in hours from selector
function getObservabilityTimeRange() {
    const selector = document.getElementById('obs-time-range');
    const value = selector.value;

    if (value === 'custom') {
        const startInput = document.getElementById('obs-start-time');
        const endInput = document.getElementById('obs-end-time');

        if (startInput.value && endInput.value) {
            const startTime = Math.floor(new Date(startInput.value).getTime() / 1000);
            const endTime = Math.floor(new Date(endInput.value).getTime() / 1000);
            return { start: startTime, end: endTime };
        }
    }

    const hours = parseInt(value);
    const endTime = Math.floor(Date.now() / 1000);
    const startTime = endTime - (hours * 3600);

    return { start: startTime, end: endTime };
}

// Format timestamp to readable date
function formatObservabilityTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}

// Load observability statistics
async function loadObservabilityStats() {
    try {
        const timeRange = getObservabilityTimeRange();
        const response = await fetch(`/observability/stats?start_time=${timeRange.start}&end_time=${timeRange.end}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Update stats cards - add null checks to prevent errors
        document.getElementById('obs-total-searches').textContent = data.search_stats.total_searches ? data.search_stats.total_searches.toLocaleString() : '0';
        document.getElementById('obs-avg-response-time').textContent = data.search_stats.avg_response_time_ms != null ? data.search_stats.avg_response_time_ms.toFixed(1) : '0.0';
        document.getElementById('obs-min-response-time').textContent = data.search_stats.min_response_time_ms != null ? `${data.search_stats.min_response_time_ms.toFixed(1)}ms` : '0.0ms';
        document.getElementById('obs-max-response-time').textContent = data.search_stats.max_response_time_ms != null ? data.search_stats.max_response_time_ms.toFixed(1) : '0.0';

        document.getElementById('obs-total-errors').textContent = data.error_stats.total_errors ? data.error_stats.total_errors.toLocaleString() : '0';
        document.getElementById('obs-critical-errors').textContent = data.error_stats.by_severity.CRITICAL || 0;
        document.getElementById('obs-error-errors').textContent = data.error_stats.by_severity.ERROR || 0;

        document.getElementById('obs-db-size').textContent = data.database_info.size_mb != null ? `${data.database_info.size_mb.toFixed(2)} MB` : '0.00 MB';
        document.getElementById('obs-total-rows').textContent = data.database_info.total_rows ? data.database_info.total_rows.toLocaleString() : '0';

        addActivityLog('info', 'Loaded observability statistics');
    } catch (error) {
        console.error('Failed to load observability stats:', error);
        addActivityLog('error', `Failed to load stats: ${error.message}`);
    }
}

// Load observability metrics and update charts
async function loadObservabilityMetrics() {
    try {
        const timeRange = getObservabilityTimeRange();

        const response = await fetch('/observability/metrics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                metric_type: 'all',
                start_time: timeRange.start,
                end_time: timeRange.end,
                limit: 1000
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Update charts
        updateSearchPerformanceChart(data.search_metrics || []);
        updateSearchTypeChart(data.search_metrics || []);
        updateErrorRateChart(data.error_logs || []);
        updateErrorComponentChart(data.error_logs || []);

        // Update tables
        updateErrorsTable(data.error_logs || []);
        updateIndexingEventsTable(data.indexing_events || []);

        logActivity('info', `Loaded ${data.total_count} observability metrics`, 'Observability');
    } catch (error) {
        console.error('Failed to load observability metrics:', error);
        logActivity('error', `Failed to load metrics: ${error.message}`, 'Observability');
    }
}

// Update search performance chart (line chart showing response times over time)
function updateSearchPerformanceChart(metrics) {
    const ctx = document.getElementById('obs-search-performance-chart');

    // Sort by timestamp
    metrics.sort((a, b) => a.timestamp - b.timestamp);

    // Group by hour and calculate average
    const hourlyData = {};
    metrics.forEach(m => {
        const hour = Math.floor(m.timestamp / 3600) * 3600;
        if (!hourlyData[hour]) {
            hourlyData[hour] = { sum: 0, count: 0 };
        }
        hourlyData[hour].sum += m.response_time_ms;
        hourlyData[hour].count += 1;
    });

    const labels = Object.keys(hourlyData).map(ts => {
        const date = new Date(parseInt(ts) * 1000);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });

    const data = Object.values(hourlyData).map(d => d.sum / d.count);

    if (observabilityCharts.searchPerformance) {
        observabilityCharts.searchPerformance.destroy();
    }

    observabilityCharts.searchPerformance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Avg Response Time (ms)',
                data: data,
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Response Time (ms)' } }
            }
        }
    });
}

// Update search type chart (pie chart showing distribution)
function updateSearchTypeChart(metrics) {
    const ctx = document.getElementById('obs-search-type-chart');

    const typeCounts = {};
    metrics.forEach(m => {
        typeCounts[m.search_type] = (typeCounts[m.search_type] || 0) + 1;
    });

    if (observabilityCharts.searchType) {
        observabilityCharts.searchType.destroy();
    }

    observabilityCharts.searchType = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(typeCounts),
            datasets: [{
                data: Object.values(typeCounts),
                backgroundColor: [
                    'rgb(99, 102, 241)',
                    'rgb(168, 85, 247)',
                    'rgb(236, 72, 153)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });
}

// Update error rate chart (line chart showing errors over time)
function updateErrorRateChart(errors) {
    const ctx = document.getElementById('obs-error-rate-chart');

    errors.sort((a, b) => a.timestamp - b.timestamp);

    // Group by hour
    const hourlyErrors = {};
    errors.forEach(e => {
        const hour = Math.floor(e.timestamp / 3600) * 3600;
        hourlyErrors[hour] = (hourlyErrors[hour] || 0) + 1;
    });

    const labels = Object.keys(hourlyErrors).map(ts => {
        const date = new Date(parseInt(ts) * 1000);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });

    const data = Object.values(hourlyErrors);

    if (observabilityCharts.errorRate) {
        observabilityCharts.errorRate.destroy();
    }

    observabilityCharts.errorRate = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Error Count',
                data: data,
                backgroundColor: 'rgba(239, 68, 68, 0.6)',
                borderColor: 'rgb(239, 68, 68)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
        }
    });
}

// Update error component chart (bar chart showing errors by component)
function updateErrorComponentChart(errors) {
    const ctx = document.getElementById('obs-error-component-chart');

    const componentCounts = {};
    errors.forEach(e => {
        componentCounts[e.component] = (componentCounts[e.component] || 0) + 1;
    });

    if (observabilityCharts.errorComponent) {
        observabilityCharts.errorComponent.destroy();
    }

    observabilityCharts.errorComponent = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(componentCounts),
            datasets: [{
                label: 'Error Count',
                data: Object.values(componentCounts),
                backgroundColor: 'rgba(245, 158, 11, 0.6)',
                borderColor: 'rgb(245, 158, 11)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
        }
    });
}

// Update errors table
function updateErrorsTable(errors) {
    const tbody = document.getElementById('obs-errors-tbody');

    if (errors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No errors found in selected time range</td></tr>';
        return;
    }

    // Show most recent errors first
    errors.sort((a, b) => b.timestamp - a.timestamp);
    const recentErrors = errors.slice(0, 50);

    tbody.innerHTML = recentErrors.map(error => `
        <tr>
            <td>${formatObservabilityTimestamp(error.timestamp)}</td>
            <td><span class="obs-severity-badge ${error.severity.toLowerCase()}">${error.severity}</span></td>
            <td>${error.component}</td>
            <td>${error.error_type}</td>
            <td style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${error.message}">${error.message}</td>
            <td>
                <div class="obs-error-actions">
                    <button class="obs-action-button" onclick="viewErrorDetails(${error.id})">View</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Update indexing events table
function updateIndexingEventsTable(events) {
    const tbody = document.getElementById('obs-indexing-tbody');

    if (events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No indexing events found in selected time range</td></tr>';
        return;
    }

    events.sort((a, b) => b.timestamp - a.timestamp);
    const recentEvents = events.slice(0, 50);

    tbody.innerHTML = recentEvents.map(event => {
        const metadata = event.metadata || {};
        const indexType = metadata.index_type || 'unknown';
        const duration = event.duration_seconds ? `${event.duration_seconds.toFixed(1)}s` : '-';

        return `
            <tr>
                <td>${formatObservabilityTimestamp(event.timestamp)}</td>
                <td>${event.repository}</td>
                <td>${indexType}</td>
                <td><span class="obs-status-badge ${event.status}">${event.status}</span></td>
                <td>${event.files_processed.toLocaleString()}</td>
                <td>${duration}</td>
            </tr>
        `;
    }).join('');
}

// View error details (modal or expansion)
function viewErrorDetails(errorId) {
    console.log('View error details:', errorId);
    // TODO: Implement error details modal
    alert(`Error ID: ${errorId}\nDetails modal not yet implemented`);
}

// Handle cleanup old data
async function handleObservabilityCleanup() {
    const retentionDays = parseInt(prompt('Enter number of days to retain data:', '30'));

    if (isNaN(retentionDays) || retentionDays < 1) {
        alert('Invalid retention days');
        return;
    }

    if (!confirm(`This will delete all observability data older than ${retentionDays} days. Continue?`)) {
        return;
    }

    try {
        const response = await fetch('/observability/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ retention_days: retentionDays })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const total = Object.values(data.records_deleted).reduce((a, b) => a + b, 0);

        alert(`Successfully deleted ${total} old records:\n` +
              `- Search metrics: ${data.records_deleted.search_metrics}\n` +
              `- Errors: ${data.records_deleted.error_log}\n` +
              `- System metrics: ${data.records_deleted.system_metrics}\n` +
              `- Indexing events: ${data.records_deleted.indexing_events}`);

        // Refresh data
        refreshObservabilityData();

        logActivity('info', `Cleaned up ${total} old observability records`, 'Observability');
    } catch (error) {
        console.error('Failed to cleanup data:', error);
        alert(`Failed to cleanup data: ${error.message}`);
        logActivity('error', `Cleanup failed: ${error.message}`, 'Observability');
    }
}

// Refresh all observability data
async function refreshObservabilityData() {
    await loadObservabilityStats();
    await loadObservabilityMetrics();
}

// Handle time range change
document.getElementById('obs-time-range')?.addEventListener('change', (e) => {
    const customRange = document.getElementById('obs-custom-range');
    if (e.target.value === 'custom') {
        customRange.style.display = 'flex';
    } else {
        customRange.style.display = 'none';
        refreshObservabilityData();
    }
});

// Handle custom time range changes
document.getElementById('obs-start-time')?.addEventListener('change', refreshObservabilityData);
document.getElementById('obs-end-time')?.addEventListener('change', refreshObservabilityData);

// Handle refresh button
document.getElementById('obs-refresh-button')?.addEventListener('click', refreshObservabilityData);

// Handle cleanup button
document.getElementById('obs-cleanup-button')?.addEventListener('click', handleObservabilityCleanup);

// Load observability data when tab becomes active
document.querySelector('[data-tab="observability"]')?.addEventListener('click', () => {
    // Small delay to ensure tab is visible
    setTimeout(() => {
        refreshObservabilityData();
    }, 100);
});

// ============================================================================
// README Viewer Functions
// ============================================================================

/**
 * Open README modal and fetch content for a repository.
 *
 * @param {string} repositoryName - Name of the repository
 */
async function openReadmeModal(repositoryName) {
    const modal = document.getElementById('readme-modal');
    const title = document.getElementById('readme-modal-title');
    const loading = document.getElementById('readme-loading');
    const error = document.getElementById('readme-error');
    const content = document.getElementById('readme-content');
    const filePath = document.getElementById('readme-file-path');

    // Show modal
    modal.style.display = 'flex';

    // Reset state
    title.textContent = `${repositoryName} README`;
    loading.style.display = 'flex';
    error.style.display = 'none';
    content.style.display = 'none';
    content.innerHTML = '';
    filePath.textContent = '';

    try {
        // Fetch README content
        const response = await fetch(`${API_BASE_URL}/repositories/${encodeURIComponent(repositoryName)}/readme`);
        const data = await response.json();

        loading.style.display = 'none';

        if (data.readme_found && data.content) {
            // Render markdown content using marked.js
            const htmlContent = marked.parse(data.content);
            content.innerHTML = htmlContent;
            content.style.display = 'block';
            filePath.textContent = data.readme_path || data.file_name || '';
        } else {
            // Show error
            error.style.display = 'block';
            document.getElementById('readme-error-message').textContent =
                data.error || 'README file not found for this repository.';
        }
    } catch (err) {
        console.error('Failed to fetch README:', err);
        loading.style.display = 'none';
        error.style.display = 'block';
        document.getElementById('readme-error-message').textContent =
            `Failed to load README: ${err.message}`;
    }
}

/**
 * Close the README modal.
 */
function closeReadmeModal() {
    const modal = document.getElementById('readme-modal');
    modal.style.display = 'none';
}

/**
 * Close modal when clicking outside the content area.
 */
document.getElementById('readme-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'readme-modal') {
        closeReadmeModal();
    }
});

/**
 * Close modal with Escape key.
 */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('readme-modal');
        if (modal && modal.style.display === 'flex') {
            closeReadmeModal();
        }
    }
});

// Make functions globally available
window.openReadmeModal = openReadmeModal;
window.closeReadmeModal = closeReadmeModal;

// ============================================================================
// User Manual
// ============================================================================

// Store original content for search
let originalManualContent = '';

async function openUserManual() {
    const modal = document.getElementById('user-manual-modal');
    const loadingDiv = document.getElementById('user-manual-loading');
    const errorDiv = document.getElementById('user-manual-error');
    const contentDiv = document.getElementById('user-manual-content');
    const searchInput = document.getElementById('manual-search-input');

    // Show modal and loading state
    modal.style.display = 'flex';
    loadingDiv.style.display = 'flex';
    errorDiv.style.display = 'none';
    contentDiv.style.display = 'none';

    // Clear search input
    if (searchInput) {
        searchInput.value = '';
        document.getElementById('manual-search-results').textContent = '';
    }

    try {
        // Fetch the user manual markdown file
        const response = await fetch('/docs/USER_MANUAL.md');

        if (!response.ok) {
            throw new Error(`Failed to load manual: ${response.statusText}`);
        }

        const markdown = await response.text();

        // Convert markdown to HTML using marked.js
        const html = marked.parse(markdown);

        // Store original content for search
        originalManualContent = html;

        // Display content
        contentDiv.innerHTML = html;
        loadingDiv.style.display = 'none';
        contentDiv.style.display = 'block';

        // Smooth scroll to top of content
        contentDiv.scrollTop = 0;

    } catch (error) {
        console.error('Error loading user manual:', error);
        loadingDiv.style.display = 'none';
        errorDiv.style.display = 'block';
        document.getElementById('user-manual-error-message').textContent =
            `Failed to load user manual: ${error.message}`;
    }
}

function closeUserManual() {
    const modal = document.getElementById('user-manual-modal');
    modal.style.display = 'none';
}

function searchManual() {
    const searchInput = document.getElementById('manual-search-input');
    const contentDiv = document.getElementById('user-manual-content');
    const resultsSpan = document.getElementById('manual-search-results');

    const query = searchInput.value.trim().toLowerCase();

    // If search is empty, restore original content
    if (!query) {
        contentDiv.innerHTML = originalManualContent;
        resultsSpan.textContent = '';
        return;
    }

    // Escape special regex characters
    const escapeRegex = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    // Create regex for case-insensitive search
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');

    // Replace content with highlighted version
    let highlightedContent = originalManualContent.replace(regex, '<mark>$1</mark>');
    contentDiv.innerHTML = highlightedContent;

    // Count matches
    const matches = contentDiv.querySelectorAll('mark');
    if (matches.length > 0) {
        resultsSpan.textContent = `${matches.length} match${matches.length !== 1 ? 'es' : ''} found`;
        resultsSpan.style.color = 'var(--accent-color)';

        // Scroll to first match
        matches[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
        matches[0].classList.add('current-match');
    } else {
        resultsSpan.textContent = 'No matches found';
        resultsSpan.style.color = 'var(--danger-color)';
    }
}

// Close manual on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('user-manual-modal');
        if (modal && modal.style.display === 'flex') {
            closeUserManual();
        }
    }
});

// Make functions globally available
window.openUserManual = openUserManual;
window.closeUserManual = closeUserManual;
window.searchManual = searchManual;
