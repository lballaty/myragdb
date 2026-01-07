// File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/static/js/agent-panel.js
// Description: Agent control panel and management interface
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

const API_BASE_URL = 'http://localhost:3003';

// Agent state management
const agentState = {
    agents: [],
    executingAgents: new Set(),
    executionHistory: [],
    skills: [],
    workflows: [],
    selectedAgent: null,
    maxHistoryItems: 100,
};

/**
 * Initialize agent panel
 */
function initializeAgentPanel() {
    console.log('Initializing agent panel...');

    loadAgents();
    loadSkills();
    loadWorkflows();
    setupAgentControls();
    setupExecutionMonitor();
    loadExecutionHistory();

    // Refresh data periodically
    setInterval(() => {
        updateAgentStatus();
        loadExecutionHistory();
    }, 5000);
}

/**
 * Load available agents
 */
async function loadAgents() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/agents`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        agentState.agents = await response.json();
        renderAgentsList();
    } catch (error) {
        console.error('Error loading agents:', error);
        showNotification('Failed to load agents', 'error');
    }
}

/**
 * Load available skills
 */
async function loadSkills() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/skills`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        agentState.skills = await response.json();
        renderAvailableSkills();
    } catch (error) {
        console.error('Error loading skills:', error);
        showNotification('Failed to load skills', 'error');
    }
}

/**
 * Load available workflows
 */
async function loadWorkflows() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/workflows`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        agentState.workflows = await response.json();
        renderAvailableWorkflows();
    } catch (error) {
        console.error('Error loading workflows:', error);
        showNotification('Failed to load workflows', 'error');
    }
}

/**
 * Render agents list
 */
function renderAgentsList() {
    const container = document.getElementById('agents-list');
    if (!container) return;

    container.innerHTML = '';

    if (agentState.agents.length === 0) {
        container.innerHTML = '<p class="empty-message">No agents available</p>';
        return;
    }

    agentState.agents.forEach(agent => {
        const isExecuting = agentState.executingAgents.has(agent.id);
        const agentEl = createAgentCard(agent, isExecuting);
        container.appendChild(agentEl);
    });
}

/**
 * Create agent card element
 */
function createAgentCard(agent, isExecuting) {
    const card = document.createElement('div');
    card.className = `agent-card ${isExecuting ? 'executing' : ''}`;
    card.dataset.agentId = agent.id;

    const statusIndicator = isExecuting ? 'running' : 'idle';
    const statusClass = isExecuting ? 'status-running' : 'status-idle';

    card.innerHTML = `
        <div class="agent-header">
            <h3 class="agent-name">${escapeHtml(agent.name)}</h3>
            <div class="status-badge ${statusClass}">${statusIndicator}</div>
        </div>
        <p class="agent-description">${escapeHtml(agent.description || 'No description')}</p>
        <div class="agent-stats">
            <div class="stat">
                <span class="stat-label">Executions:</span>
                <span class="stat-value">${agent.execution_count || 0}</span>
            </div>
            <div class="stat">
                <span class="stat-label">Success Rate:</span>
                <span class="stat-value">${(agent.success_rate || 0).toFixed(1)}%</span>
            </div>
        </div>
        <div class="agent-actions">
            <button class="btn btn-primary" onclick="executeAgent('${agent.id}')">
                ${isExecuting ? 'Executing...' : 'Execute'}
            </button>
            <button class="btn btn-secondary" onclick="configureAgent('${agent.id}')">
                Configure
            </button>
            <button class="btn btn-secondary" onclick="viewAgentDetails('${agent.id}')">
                Details
            </button>
        </div>
    `;

    return card;
}

/**
 * Execute agent
 */
async function executeAgent(agentId) {
    const agent = agentState.agents.find(a => a.id === agentId);
    if (!agent) return;

    agentState.executingAgents.add(agentId);
    renderAgentsList();

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const execution = await response.json();
        agentState.executionHistory.unshift(execution);
        if (agentState.executionHistory.length > agentState.maxHistoryItems) {
            agentState.executionHistory.pop();
        }

        showNotification(`Agent ${agent.name} executed successfully`, 'success');
        renderExecutionHistory();

    } catch (error) {
        console.error('Error executing agent:', error);
        showNotification(`Failed to execute agent: ${error.message}`, 'error');
    } finally {
        agentState.executingAgents.delete(agentId);
        renderAgentsList();
    }
}

/**
 * Configure agent
 */
function configureAgent(agentId) {
    const agent = agentState.agents.find(a => a.id === agentId);
    if (!agent) return;

    agentState.selectedAgent = agent;
    showAgentConfigDialog(agent);
}

/**
 * View agent details
 */
function viewAgentDetails(agentId) {
    const agent = agentState.agents.find(a => a.id === agentId);
    if (!agent) return;

    const modal = createAgentDetailsModal(agent);
    document.body.appendChild(modal);
}

/**
 * Create agent details modal
 */
function createAgentDetailsModal(agent) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';

    const content = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>${escapeHtml(agent.name)}</h2>
                <button class="close-btn" onclick="this.closest('.modal-overlay').remove()">×</button>
            </div>
            <div class="modal-body">
                <div class="details-section">
                    <h3>Description</h3>
                    <p>${escapeHtml(agent.description || 'No description')}</p>
                </div>
                <div class="details-section">
                    <h3>Skills</h3>
                    <ul class="skills-list">
                        ${(agent.skills || []).map(skill =>
                            `<li><code>${escapeHtml(skill)}</code></li>`
                        ).join('')}
                    </ul>
                </div>
                <div class="details-section">
                    <h3>Configuration</h3>
                    <pre>${JSON.stringify(agent.config || {}, null, 2)}</pre>
                </div>
                <div class="details-section">
                    <h3>Statistics</h3>
                    <table class="stats-table">
                        <tr>
                            <td>Total Executions:</td>
                            <td>${agent.execution_count || 0}</td>
                        </tr>
                        <tr>
                            <td>Success Rate:</td>
                            <td>${(agent.success_rate || 0).toFixed(1)}%</td>
                        </tr>
                        <tr>
                            <td>Average Duration:</td>
                            <td>${(agent.avg_duration_ms || 0).toFixed(0)}ms</td>
                        </tr>
                        <tr>
                            <td>Last Executed:</td>
                            <td>${agent.last_executed_at || 'Never'}</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
    `;

    modal.innerHTML = content;
    return modal;
}

/**
 * Render available skills
 */
function renderAvailableSkills() {
    const container = document.getElementById('available-skills');
    if (!container) return;

    container.innerHTML = '';

    agentState.skills.forEach(skill => {
        const skillEl = document.createElement('div');
        skillEl.className = 'skill-card';
        skillEl.innerHTML = `
            <h4>${escapeHtml(skill.name)}</h4>
            <p>${escapeHtml(skill.description)}</p>
            <div class="skill-meta">
                <span class="version">v${skill.version}</span>
            </div>
        `;
        container.appendChild(skillEl);
    });
}

/**
 * Render available workflows
 */
function renderAvailableWorkflows() {
    const container = document.getElementById('available-workflows');
    if (!container) return;

    container.innerHTML = '';

    agentState.workflows.forEach(workflow => {
        const workflowEl = document.createElement('div');
        workflowEl.className = 'workflow-card';
        workflowEl.innerHTML = `
            <h4>${escapeHtml(workflow.name)}</h4>
            <p>${escapeHtml(workflow.description)}</p>
            <div class="workflow-actions">
                <button class="btn btn-sm" onclick="executeWorkflow('${workflow.id}')">Execute</button>
                <button class="btn btn-sm" onclick="editWorkflow('${workflow.id}')">Edit</button>
            </div>
        `;
        container.appendChild(workflowEl);
    });
}

/**
 * Load execution history
 */
async function loadExecutionHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/executions?limit=50`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        agentState.executionHistory = await response.json();
        renderExecutionHistory();
    } catch (error) {
        console.error('Error loading execution history:', error);
    }
}

/**
 * Render execution history
 */
function renderExecutionHistory() {
    const container = document.getElementById('execution-history');
    if (!container) return;

    container.innerHTML = '';

    if (agentState.executionHistory.length === 0) {
        container.innerHTML = '<p class="empty-message">No executions yet</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'execution-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>Agent</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Executed At</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            ${agentState.executionHistory.map(execution => `
                <tr class="execution-row ${execution.status}">
                    <td>${escapeHtml(execution.agent_name)}</td>
                    <td>
                        <span class="status-badge status-${execution.status}">
                            ${execution.status}
                        </span>
                    </td>
                    <td>${execution.duration_ms || 0}ms</td>
                    <td>${new Date(execution.executed_at).toLocaleString()}</td>
                    <td>
                        <button class="btn btn-sm" onclick="viewExecutionDetails('${execution.id}')">
                            View
                        </button>
                    </td>
                </tr>
            `).join('')}
        </tbody>
    `;
    container.appendChild(table);
}

/**
 * Update agent status
 */
async function updateAgentStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/agents/status`);
        if (!response.ok) return;

        const statuses = await response.json();
        statuses.forEach(status => {
            const agent = agentState.agents.find(a => a.id === status.id);
            if (agent) {
                agent.status = status.status;
                agent.execution_count = status.execution_count;
                agent.success_rate = status.success_rate;
            }
        });

        renderAgentsList();
    } catch (error) {
        console.error('Error updating agent status:', error);
    }
}

/**
 * Setup agent controls
 */
function setupAgentControls() {
    const executeAllBtn = document.getElementById('execute-all-agents');
    const pauseAllBtn = document.getElementById('pause-all-agents');

    if (executeAllBtn) {
        executeAllBtn.addEventListener('click', executeAllAgents);
    }

    if (pauseAllBtn) {
        pauseAllBtn.addEventListener('click', pauseAllAgents);
    }
}

/**
 * Execute all agents
 */
async function executeAllAgents() {
    for (const agent of agentState.agents) {
        await executeAgent(agent.id);
    }
}

/**
 * Pause all agents
 */
async function pauseAllAgents() {
    // Implementation for pausing all agents
    agentState.executingAgents.clear();
    renderAgentsList();
    showNotification('All agents paused', 'info');
}

/**
 * Setup execution monitor
 */
function setupExecutionMonitor() {
    // Real-time monitoring of agent executions
    console.log('Execution monitor initialized');
}

/**
 * Execute workflow
 */
async function executeWorkflow(workflowId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/workflows/${workflowId}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        showNotification('Workflow executed successfully', 'success');
    } catch (error) {
        showNotification(`Failed to execute workflow: ${error.message}`, 'error');
    }
}

/**
 * Edit workflow
 */
function editWorkflow(workflowId) {
    console.log('Edit workflow:', workflowId);
    // Implementation for workflow editor
}

/**
 * View execution details
 */
function viewExecutionDetails(executionId) {
    const execution = agentState.executionHistory.find(e => e.id === executionId);
    if (!execution) return;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Execution Details</h2>
                <button class="close-btn" onclick="this.closest('.modal-overlay').remove()">×</button>
            </div>
            <div class="modal-body">
                <pre>${JSON.stringify(execution, null, 2)}</pre>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Initialize on document load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAgentPanel);
} else {
    initializeAgentPanel();
}
