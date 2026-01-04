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
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeSearch();
    initializeActivityMonitor();
    checkHealthStatus();
    loadStatistics();
    loadFromLocalStorage();
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

        document.getElementById('stat-bm25').textContent = data.bm25_documents.toLocaleString();
        document.getElementById('stat-vector').textContent = data.vector_chunks.toLocaleString();
        document.getElementById('stat-searches').textContent = state.stats.totalSearches.toLocaleString();

        if (state.stats.responseTimes.length > 0) {
            const avgTime = state.stats.responseTimes.reduce((a, b) => a + b, 0) / state.stats.responseTimes.length;
            document.getElementById('stat-avg-time').textContent = `${avgTime.toFixed(0)}ms`;
        } else {
            document.getElementById('stat-avg-time').textContent = '-';
        }

        addActivityLog('info', `Statistics loaded: ${data.bm25_documents} docs, ${data.vector_chunks} chunks`);
    } catch (error) {
        addActivityLog('error', `Failed to load statistics: ${error.message}`);
    }
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

// Auto-refresh health status every 30 seconds
setInterval(checkHealthStatus, 30000);
