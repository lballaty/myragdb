// File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/static/js/activity-monitor.js
// Description: Enhanced activity monitoring with filtering, export, and real-time updates
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

const ActivityMonitor = {
    activities: [],
    maxActivities: 500,
    filters: {
        type: [],
        severity: [],
        searchText: '',
        timeRange: 'all'
    },
    autoRefresh: true,
    refreshInterval: 5000,
    refreshTimer: null,

    /**
     * Initialize activity monitor
     */
    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
        this.loadActivities();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Filter listeners
        document.getElementById('activity-type-filter')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('activity-severity-filter')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('activity-search')?.addEventListener('input', (e) => {
            this.filters.searchText = e.target.value;
            this.applyFilters();
        });
        document.getElementById('activity-time-range')?.addEventListener('change', (e) => {
            this.filters.timeRange = e.target.value;
            this.applyFilters();
        });

        // Control listeners
        document.getElementById('activity-refresh-btn')?.addEventListener('click', () => this.refreshActivities());
        document.getElementById('activity-clear-btn')?.addEventListener('click', () => this.clearActivities());
        document.getElementById('activity-export-btn')?.addEventListener('click', () => this.exportActivities());
        document.getElementById('activity-auto-refresh-toggle')?.addEventListener('change', (e) => {
            this.autoRefresh = e.target.checked;
            if (this.autoRefresh) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });
    },

    /**
     * Add new activity
     */
    addActivity(type, message, severity = 'info', metadata = {}) {
        const activity = {
            id: Date.now() + Math.random(),
            timestamp: new Date().toLocaleTimeString(),
            timestampMs: Date.now(),
            type,
            message,
            severity,
            metadata
        };

        this.activities.unshift(activity);

        // Keep activities bounded
        if (this.activities.length > this.maxActivities) {
            this.activities = this.activities.slice(0, this.maxActivities);
        }

        // Auto-render if activity tab is active
        if (document.getElementById('activity-tab')?.classList.contains('active')) {
            this.applyFilters();
        }

        return activity;
    },

    /**
     * Load activities from storage/API
     */
    async loadActivities() {
        try {
            // Try to load from API first
            const response = await fetch('/api/v1/activities?limit=100');
            if (response.ok) {
                const data = await response.json();
                if (data.activities) {
                    this.activities = data.activities;
                }
            }
        } catch (error) {
            console.debug('Could not load activities from API:', error);
            // Fallback to local storage
            const stored = localStorage.getItem('activities');
            if (stored) {
                this.activities = JSON.parse(stored);
            }
        }
        this.applyFilters();
    },

    /**
     * Refresh activities from server
     */
    async refreshActivities() {
        await this.loadActivities();
        this.addActivity('system', 'Activities refreshed', 'info');
    },

    /**
     * Apply current filters and render
     */
    applyFilters() {
        const typeFilter = document.getElementById('activity-type-filter')?.value || '';
        const severityFilter = document.getElementById('activity-severity-filter')?.value || '';
        const timeRange = this.filters.timeRange;

        let filtered = this.activities;

        // Type filter
        if (typeFilter) {
            filtered = filtered.filter(a => a.type === typeFilter);
        }

        // Severity filter
        if (severityFilter) {
            filtered = filtered.filter(a => a.severity === severityFilter);
        }

        // Search filter
        if (this.filters.searchText) {
            const search = this.filters.searchText.toLowerCase();
            filtered = filtered.filter(a =>
                a.message.toLowerCase().includes(search) ||
                a.type.toLowerCase().includes(search)
            );
        }

        // Time range filter
        if (timeRange !== 'all') {
            const now = Date.now();
            const rangeMs = this.parseTimeRange(timeRange);
            filtered = filtered.filter(a => (now - a.timestampMs) <= rangeMs);
        }

        this.render(filtered);
    },

    /**
     * Parse time range string to milliseconds
     */
    parseTimeRange(range) {
        const ranges = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '24h': 24 * 60 * 60 * 1000
        };
        return ranges[range] || Infinity;
    },

    /**
     * Render activities
     */
    render(activities) {
        const container = document.getElementById('activity-log');
        if (!container) return;

        if (activities.length === 0) {
            container.innerHTML = '<div class="activity-empty">No activities match filters</div>';
            return;
        }

        const html = activities.map(activity => `
            <div class="activity-entry activity-${activity.severity}">
                <div class="activity-header">
                    <span class="activity-timestamp">${activity.timestamp}</span>
                    <span class="activity-type-badge">${this.getSeverityEmoji(activity.severity)} ${activity.type.toUpperCase()}</span>
                    <span class="activity-severity-badge severity-${activity.severity}">${activity.severity}</span>
                </div>
                <div class="activity-message">${this.escapeHtml(activity.message)}</div>
                ${Object.keys(activity.metadata || {}).length > 0 ?
                    `<div class="activity-metadata">${JSON.stringify(activity.metadata)}</div>` : ''}
            </div>
        `).join('');

        container.innerHTML = html;
    },

    /**
     * Get emoji for severity level
     */
    getSeverityEmoji(severity) {
        const emojis = {
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅',
            'system': '⚙️'
        };
        return emojis[severity] || 'ℹ️';
    },

    /**
     * Clear all activities
     */
    clearActivities() {
        if (confirm('Clear all activities?')) {
            this.activities = [];
            localStorage.removeItem('activities');
            this.render([]);
            this.addActivity('system', 'Activities cleared', 'info');
        }
    },

    /**
     * Export activities as JSON
     */
    exportActivities() {
        const data = JSON.stringify(this.activities, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `activities-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        this.addActivity('system', 'Activities exported', 'success');
    },

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        if (this.refreshTimer) clearInterval(this.refreshTimer);
        this.refreshTimer = setInterval(() => this.refreshActivities(), this.refreshInterval);
    },

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    },

    /**
     * Escape HTML special characters
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
};

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ActivityMonitor.init());
} else {
    ActivityMonitor.init();
}
