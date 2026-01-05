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
    repositories: []
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeSearch();
    initializeActivityMonitor();
    initializeReindex();
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
            if (tabName === 'stats') {
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

    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            indicator.classList.add('healthy');
            statusText.textContent = 'Service Healthy';
        } else {
            statusText.textContent = 'Service Degraded';
        }
    } catch (error) {
        statusText.textContent = 'Service Offline';
        addActivityLog('error', `Health check failed: ${error.message}`);
    }
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');

    searchButton.addEventListener('click', performSearch);

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

async function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    const searchType = document.getElementById('search-type').value;
    const limit = parseInt(document.getElementById('result-limit').value);
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

    try {
        const response = await fetch(`${API_BASE_URL}/search/${searchType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, limit })
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
                        ${result.bm25_score !== undefined ? `
                            <div class="score-detail">
                                BM25: ${(result.bm25_score * 100).toFixed(1)}% |
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
function initializeActivityMonitor() {
    document.getElementById('refresh-activity').addEventListener('click', renderActivityLog);
    document.getElementById('clear-activity').addEventListener('click', clearActivityLog);
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

// Statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();

        document.getElementById('stat-bm25').textContent = data.keyword_documents.toLocaleString();
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

        // Only disable reindex button if BOTH BM25 and Vector are indexing
        // This allows starting Vector while BM25 is running (and vice versa)
        const bm25Indexing = data.bm25?.is_indexing || false;
        const vectorIndexing = data.vector?.is_indexing || false;
        const bothIndexing = bm25Indexing && vectorIndexing;

        if (data.is_indexing) {
            indexingStatus.style.display = 'flex';
            reindexButton.disabled = bothIndexing;  // Only disable if both are running

            // Update status text based on what's indexing
            if (bothIndexing) {
                statusElement.textContent = 'Keyword + Vector Indexing...';
            } else if (bm25Indexing) {
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

// Repository Management
async function loadRepositories() {
    const repositoryList = document.getElementById('repository-list');

    try {
        const response = await fetch(`${API_BASE_URL}/repositories`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const repositories = await response.json();
        state.repositories = repositories;

        renderRepositories();
        addActivityLog('info', `Loaded ${repositories.length} repositories`);

    } catch (error) {
        repositoryList.innerHTML = `<div class="error">Failed to load repositories: ${error.message}</div>`;
        addActivityLog('error', `Failed to load repositories: ${error.message}`);
    }
}

function renderRepositories() {
    const repositoryList = document.getElementById('repository-list');

    if (state.repositories.length === 0) {
        repositoryList.innerHTML = '<div style="color: var(--text-muted);">No repositories configured</div>';
        return;
    }

    const reposHtml = state.repositories.map(repo => {
        const enabledClass = repo.enabled ? 'enabled' : 'disabled';
        const priorityClass = `priority-${repo.priority}`;

        // Format file count and size
        let fileCountBadge = '';
        if (repo.file_count !== null && repo.file_count !== undefined) {
            const sizeClass = repo.file_count > 10000 ? 'large' : repo.file_count > 1000 ? 'medium' : 'small';
            const formattedSize = formatBytes(repo.total_size_bytes);
            fileCountBadge = `<span class="repository-badge file-count ${sizeClass}">${repo.file_count.toLocaleString()} files (${formattedSize})</span>`;
        }

        return `
            <div class="repository-item">
                <input type="checkbox"
                       class="repo-checkbox"
                       value="${escapeHtml(repo.name)}"
                       id="repo-${escapeHtml(repo.name)}"
                       ${repo.enabled ? 'checked' : ''}>
                <label for="repo-${escapeHtml(repo.name)}" class="repository-info">
                    <div class="repository-name">${escapeHtml(repo.name)}</div>
                    <div class="repository-path">${escapeHtml(repo.path)}</div>
                    <div>
                        <span class="repository-badge ${enabledClass}">
                            ${repo.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                        <span class="repository-badge ${priorityClass}">
                            ${repo.priority.toUpperCase()}
                        </span>
                        ${fileCountBadge}
                    </div>
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
    const indexBM25 = document.getElementById('index-bm25').checked;
    const indexVector = document.getElementById('index-vector').checked;
    const isFullRebuild = document.getElementById('mode-full').checked;

    // Build index type description
    const indexTypes = [];
    if (indexBM25) indexTypes.push('Keyword (Meilisearch)');
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
        const indexBM25 = document.getElementById('index-bm25').checked;
        const indexVector = document.getElementById('index-vector').checked;
        const isFullRebuild = document.getElementById('mode-full').checked;

        // Build request body
        const requestBody = {
            repositories: selectedRepos.length === state.repositories.length ? null : selectedRepos,
            index_bm25: indexBM25,
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

// Auto-refresh health status and indexing progress every 2 seconds
setInterval(() => {
    checkHealthStatus();
    updateIndexingProgress();
}, 2000);
