// File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/static/js/admin.js
// Description: Admin panel functionality for Meilisearch management
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-06-15

let meilisearchStatusRefreshInterval = null;

// Initialize admin panel when tab is selected
function initAdminPanel() {
    refreshMeilisearchStatus();
    refreshMeilisearchLogs();

    // Set up auto-refresh every 10 seconds
    if (meilisearchStatusRefreshInterval) {
        clearInterval(meilisearchStatusRefreshInterval);
    }
    meilisearchStatusRefreshInterval = setInterval(refreshMeilisearchStatus, 10000);
}

// Clean up when leaving admin tab
function cleanupAdminPanel() {
    if (meilisearchStatusRefreshInterval) {
        clearInterval(meilisearchStatusRefreshInterval);
        meilisearchStatusRefreshInterval = null;
    }
}

// Refresh Meilisearch status
async function refreshMeilisearchStatus() {
    try {
        const response = await fetch('/api/v1/meilisearch/status');
        const status = await response.json();

        updateMeilisearchStatusDisplay(status);
    } catch (error) {
        console.error('Error fetching Meilisearch status:', error);
        showMeilisearchStatusMessage(
            'Failed to check Meilisearch status: ' + error.message,
            'error'
        );
    }
}

// Update Meilisearch status display
function updateMeilisearchStatusDisplay(status) {
    const statusDisplay = document.getElementById('meili-status-text');
    const startButton = document.getElementById('meili-start-button');
    const stopButton = document.getElementById('meili-stop-button');
    const docCountRow = document.getElementById('meili-doc-count-row');
    const uptimeRow = document.getElementById('meili-uptime-row');
    const versionRow = document.getElementById('meili-version-row');

    // Update status text with indicator
    if (status.is_running) {
        statusDisplay.innerHTML = '<span class="status-indicator running"></span>Running';
        if (startButton) startButton.style.display = 'none';
        if (stopButton) stopButton.style.display = 'inline-block';

        // Show additional info rows
        docCountRow.style.display = 'flex';
        uptimeRow.style.display = 'flex';
        versionRow.style.display = 'flex';

        // Update values
        const docCountEl = document.getElementById('meili-doc-count');
        if (docCountEl && status.document_count !== null) {
            docCountEl.textContent = status.document_count.toLocaleString();
        }

        const uptimeEl = document.getElementById('meili-uptime');
        if (uptimeEl && status.uptime_seconds !== null) {
            uptimeEl.textContent = formatUptime(status.uptime_seconds);
        }

        const versionEl = document.getElementById('meili-version');
        if (versionEl && status.version) {
            versionEl.textContent = status.version;
        }
    } else {
        statusDisplay.innerHTML = '<span class="status-indicator stopped"></span>Stopped';
        if (startButton) startButton.style.display = 'inline-block';
        if (stopButton) stopButton.style.display = 'none';

        // Hide additional info rows
        docCountRow.style.display = 'none';
        uptimeRow.style.display = 'none';
        versionRow.style.display = 'none';
    }

    // Clear any error message if status is OK
    if (status.status !== 'error') {
        const messageEl = document.getElementById('meili-status-message');
        if (messageEl) messageEl.style.display = 'none';
    }
}

// Format uptime duration
function formatUptime(seconds) {
    if (!seconds) return '-';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Start Meilisearch
async function startMeilisearch() {
    try {
        const startButton = document.getElementById('meili-start-button');
        startButton.disabled = true;
        startButton.textContent = '⏳ Starting...';

        showMeilisearchStatusMessage('Starting Meilisearch...', 'info');

        const response = await fetch('/api/v1/meilisearch/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wait_for_ready: true, timeout_seconds: 30 })
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            showMeilisearchStatusMessage('✓ Meilisearch started successfully', 'success');
            // Refresh status after a short delay
            setTimeout(refreshMeilisearchStatus, 1000);
        } else {
            showMeilisearchStatusMessage(
                'Error: ' + (result.message || 'Failed to start Meilisearch'),
                'error'
            );
        }
    } catch (error) {
        console.error('Error starting Meilisearch:', error);
        showMeilisearchStatusMessage(
            'Failed to start Meilisearch: ' + error.message,
            'error'
        );
    } finally {
        const startButton = document.getElementById('meili-start-button');
        startButton.disabled = false;
        startButton.textContent = '▶️ Start Meilisearch';
    }
}

// Stop Meilisearch
async function stopMeilisearch() {
    try {
        const stopButton = document.getElementById('meili-stop-button');
        stopButton.disabled = true;
        stopButton.textContent = '⏳ Stopping...';

        showMeilisearchStatusMessage('Stopping Meilisearch...', 'info');

        const response = await fetch('/api/v1/meilisearch/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            showMeilisearchStatusMessage('✓ Meilisearch stopped successfully', 'success');
            // Refresh status after a short delay
            setTimeout(refreshMeilisearchStatus, 1000);
        } else {
            showMeilisearchStatusMessage(
                'Error: ' + (result.message || 'Failed to stop Meilisearch'),
                'error'
            );
        }
    } catch (error) {
        console.error('Error stopping Meilisearch:', error);
        showMeilisearchStatusMessage(
            'Failed to stop Meilisearch: ' + error.message,
            'error'
        );
    } finally {
        const stopButton = document.getElementById('meili-stop-button');
        stopButton.disabled = false;
        stopButton.textContent = '⏹️ Stop Meilisearch';
    }
}

// Refresh Meilisearch logs
async function refreshMeilisearchLogs() {
    try {
        const response = await fetch('/api/v1/meilisearch/logs?lines=50');
        const logsData = await response.json();

        updateMeilisearchLogsDisplay(logsData.lines);
    } catch (error) {
        console.error('Error fetching Meilisearch logs:', error);
        updateMeilisearchLogsDisplay(['Error loading logs: ' + error.message]);
    }
}

// Update Meilisearch logs display
function updateMeilisearchLogsDisplay(lines) {
    const logsContainer = document.getElementById('meilisearch-logs');

    if (!lines || lines.length === 0) {
        logsContainer.innerHTML = '<p class="logs-loading">No logs available</p>';
        return;
    }

    const logsHTML = lines.map(line => {
        let logClass = 'log-line';

        // Classify log lines by content
        if (line.includes('[ERROR]') || line.includes('error') || line.includes('Error')) {
            logClass += ' error';
        } else if (line.includes('[WARN]') || line.includes('warning') || line.includes('Warning')) {
            logClass += ' warning';
        } else if (line.includes('[INFO]') || line.includes('info') || line.includes('Info')) {
            logClass += ' info';
        } else if (line.includes('[SUCCESS]') || line.includes('success') || line.includes('Success')) {
            logClass += ' success';
        }

        return `<div class="${logClass}">${escapeHtml(line)}</div>`;
    }).join('');

    logsContainer.innerHTML = logsHTML;

    // Auto-scroll to bottom
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Show status message
function showMeilisearchStatusMessage(message, type = 'info') {
    const messageEl = document.getElementById('meili-status-message');
    if (!messageEl) return;

    messageEl.textContent = message;
    messageEl.className = `status-message ${type}`;
    messageEl.style.display = 'block';

    // Auto-hide success/info messages after 5 seconds
    if (type !== 'error') {
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 5000);
    }
}

// Helper function to escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Tab click handler
document.addEventListener('DOMContentLoaded', () => {
    // Find admin tab button and add click handler
    const adminTabButton = document.querySelector('[data-tab="admin"]');
    if (adminTabButton) {
        adminTabButton.addEventListener('click', () => {
            // The main tab switching is handled by app.js
            // We just need to initialize when the tab becomes visible
            setTimeout(initAdminPanel, 100);
        });
    }

    // Also check if admin tab is already visible
    const adminTab = document.getElementById('admin-tab');
    if (adminTab && !adminTab.style.display === 'none') {
        initAdminPanel();
    }
});
