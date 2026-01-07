// File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/static/js/observability.js
// Description: Enhanced observability and monitoring dashboard with alerts and thresholds
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

const Observability = {
    charts: {},
    metrics: {},
    alerts: [],
    thresholds: {
        responseTimeWarning: 1000,      // ms
        responseTimeError: 2000,        // ms
        errorRateWarning: 0.05,         // 5%
        errorRateError: 0.10,           // 10%
        cpuWarning: 80,                 // %
        memoryWarning: 85               // %
    },
    autoRefresh: true,
    refreshInterval: 10000,
    refreshTimer: null,

    /**
     * Initialize observability dashboard
     */
    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
        this.loadMetrics();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        document.getElementById('obs-refresh-button')?.addEventListener('click', () => this.refresh());
        document.getElementById('obs-cleanup-button')?.addEventListener('click', () => this.cleanup());
        document.getElementById('obs-time-range')?.addEventListener('change', (e) => {
            if (e.target.value === 'custom') {
                document.getElementById('obs-custom-range').style.display = 'block';
            } else {
                document.getElementById('obs-custom-range').style.display = 'none';
                this.loadMetrics();
            }
        });
        document.getElementById('obs-auto-refresh-toggle')?.addEventListener('change', (e) => {
            this.autoRefresh = e.target.checked;
            if (this.autoRefresh) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });
        document.getElementById('obs-export-btn')?.addEventListener('click', () => this.exportMetrics());
    },

    /**
     * Get time range in milliseconds
     */
    getTimeRange() {
        const select = document.getElementById('obs-time-range');
        const hours = parseInt(select?.value || '24');
        return hours * 60 * 60 * 1000;
    },

    /**
     * Load metrics from server
     */
    async loadMetrics() {
        try {
            const timeRange = this.getTimeRange();
            const response = await fetch(`/api/v1/observability/metrics?time_range=${timeRange}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            this.metrics = data;
            this.renderMetrics();
            this.updateCharts();
            this.checkAlerts();
        } catch (error) {
            console.error('Failed to load observability metrics:', error);
            this.addAlert('error', 'Failed to load observability metrics', error.message);
        }
    },

    /**
     * Render metrics summary cards
     */
    renderMetrics() {
        const m = this.metrics;

        // Total searches
        this.updateStat('obs-total-searches', m.total_searches || 0);
        this.updateStat('obs-avg-response-time', Math.round(m.avg_response_time_ms || 0));

        // Errors
        this.updateStat('obs-total-errors', m.total_errors || 0);
        this.updateStat('obs-critical-errors', m.critical_errors || 0);
        this.updateStat('obs-error-errors', m.error_count || 0);

        // Database
        this.updateStat('obs-db-size', this.formatBytes(m.database_size_bytes || 0));
        this.updateStat('obs-total-rows', m.total_records || 0);

        // Performance
        this.updateStat('obs-min-response-time', Math.round(m.min_response_time_ms || 0));
        this.updateStat('obs-max-response-time', Math.round(m.max_response_time_ms || 0));

        // System
        this.updateStat('obs-cpu-usage', `${m.cpu_usage || 0}%`);
        this.updateStat('obs-memory-usage', `${m.memory_usage || 0}%`);
        this.updateStat('obs-disk-usage', `${m.disk_usage || 0}%`);
    },

    /**
     * Update a stat element
     */
    updateStat(elementId, value) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = value;
            el.style.opacity = '1';
        }
    },

    /**
     * Update charts
     */
    updateCharts() {
        this.updateSearchPerformanceChart();
        this.updateSearchTypeChart();
        this.updateErrorRateChart();
        this.updateSystemHealthChart();
    },

    /**
     * Update search performance chart
     */
    updateSearchPerformanceChart() {
        const data = this.metrics.search_performance_timeline || [];
        if (!data.length) return;

        const ctx = document.getElementById('obs-search-performance-chart');
        if (!ctx) return;

        if (this.charts.searchPerformance) {
            this.charts.searchPerformance.destroy();
        }

        this.charts.searchPerformance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
                datasets: [{
                    label: 'Response Time (ms)',
                    data: data.map(d => d.response_time_ms),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Warning Threshold',
                    data: Array(data.length).fill(this.thresholds.responseTimeWarning),
                    borderColor: '#f59e0b',
                    borderDash: [5, 5],
                    borderWidth: 1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    },

    /**
     * Update search type chart
     */
    updateSearchTypeChart() {
        const data = this.metrics.search_by_type || {};
        if (Object.keys(data).length === 0) return;

        const ctx = document.getElementById('obs-search-type-chart');
        if (!ctx) return;

        if (this.charts.searchType) {
            this.charts.searchType.destroy();
        }

        this.charts.searchType = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true }
                }
            }
        });
    },

    /**
     * Update error rate chart
     */
    updateErrorRateChart() {
        const data = this.metrics.error_rate_timeline || [];
        if (!data.length) return;

        const ctx = document.getElementById('obs-error-rate-chart');
        if (!ctx) return;

        if (this.charts.errorRate) {
            this.charts.errorRate.destroy();
        }

        this.charts.errorRate = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
                datasets: [{
                    label: 'Error Rate (%)',
                    data: data.map(d => d.error_rate * 100),
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    },

    /**
     * Update system health chart
     */
    updateSystemHealthChart() {
        const ctx = document.getElementById('obs-system-health-chart');
        if (!ctx) return;

        if (this.charts.systemHealth) {
            this.charts.systemHealth.destroy();
        }

        this.charts.systemHealth = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['CPU', 'Memory', 'Disk', 'Network', 'API Health'],
                datasets: [{
                    label: 'System Health (%)',
                    data: [
                        100 - (this.metrics.cpu_usage || 0),
                        100 - (this.metrics.memory_usage || 0),
                        100 - (this.metrics.disk_usage || 0),
                        this.metrics.network_health || 100,
                        this.metrics.api_health || 100
                    ],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    },

    /**
     * Check for alert conditions
     */
    checkAlerts() {
        this.alerts = [];

        // Response time alerts
        if ((this.metrics.avg_response_time_ms || 0) > this.thresholds.responseTimeError) {
            this.addAlert('error', 'High Response Time',
                `Average response time is ${Math.round(this.metrics.avg_response_time_ms)}ms`);
        } else if ((this.metrics.avg_response_time_ms || 0) > this.thresholds.responseTimeWarning) {
            this.addAlert('warning', 'Elevated Response Time',
                `Average response time is ${Math.round(this.metrics.avg_response_time_ms)}ms`);
        }

        // Error rate alerts
        const errorRate = (this.metrics.total_errors || 0) / (this.metrics.total_searches || 1);
        if (errorRate > this.thresholds.errorRateError) {
            this.addAlert('error', 'High Error Rate',
                `Error rate is ${(errorRate * 100).toFixed(2)}%`);
        } else if (errorRate > this.thresholds.errorRateWarning) {
            this.addAlert('warning', 'Elevated Error Rate',
                `Error rate is ${(errorRate * 100).toFixed(2)}%`);
        }

        // System alerts
        if ((this.metrics.cpu_usage || 0) > this.thresholds.cpuWarning) {
            this.addAlert('warning', 'High CPU Usage',
                `CPU usage is ${this.metrics.cpu_usage}%`);
        }
        if ((this.metrics.memory_usage || 0) > this.thresholds.memoryWarning) {
            this.addAlert('warning', 'High Memory Usage',
                `Memory usage is ${this.metrics.memory_usage}%`);
        }

        this.renderAlerts();
    },

    /**
     * Add alert
     */
    addAlert(severity, title, message) {
        this.alerts.push({
            id: Date.now(),
            timestamp: new Date(),
            severity,
            title,
            message
        });
    },

    /**
     * Render alerts
     */
    renderAlerts() {
        const container = document.getElementById('obs-alerts-container');
        if (!container) return;

        if (this.alerts.length === 0) {
            container.innerHTML = '<div class="obs-no-alerts">✅ No active alerts</div>';
            return;
        }

        const html = this.alerts.map(alert => `
            <div class="obs-alert alert-${alert.severity}">
                <div class="obs-alert-title">${alert.title}</div>
                <div class="obs-alert-message">${alert.message}</div>
                <div class="obs-alert-time">${alert.timestamp.toLocaleTimeString()}</div>
            </div>
        `).join('');

        container.innerHTML = html;
    },

    /**
     * Refresh metrics
     */
    async refresh() {
        await this.loadMetrics();
        ActivityMonitor.addActivity('observability', 'Observability metrics refreshed', 'info');
    },

    /**
     * Cleanup old data
     */
    async cleanup() {
        const days = parseInt(prompt('Delete observability data older than (days):', '30'));
        if (!days || days < 1) return;

        try {
            const response = await fetch('/api/v1/observability/cleanup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ retention_days: days })
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            ActivityMonitor.addActivity('observability',
                `Deleted ${data.deleted_count} old records`, 'success');
            await this.loadMetrics();
        } catch (error) {
            this.addAlert('error', 'Cleanup Failed', error.message);
        }
    },

    /**
     * Export metrics as JSON
     */
    exportMetrics() {
        const data = JSON.stringify(this.metrics, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `observability-metrics-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    },

    /**
     * Format bytes to human-readable
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        if (this.refreshTimer) clearInterval(this.refreshTimer);
        this.refreshTimer = setInterval(() => this.refresh(), this.refreshInterval);
    },

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
};

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Observability.init());
} else {
    Observability.init();
}
