// File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/web-ui/static/js/workflow-builder.js
// Description: Visual workflow builder for creating and editing workflows
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

const API_BASE_URL = 'http://localhost:3002';

// Workflow builder state
const workflowBuilder = {
    currentWorkflow: null,
    canvas: null,
    nodes: [],
    connections: [],
    selectedNode: null,
    zoom: 1,
    panX: 0,
    panY: 0,
    undoStack: [],
    redoStack: [],
};

/**
 * Initialize workflow builder
 */
function initializeWorkflowBuilder() {
    console.log('Initializing workflow builder...');

    const canvasElement = document.getElementById('workflow-canvas');
    if (!canvasElement) {
        console.warn('Workflow canvas element not found');
        return;
    }

    workflowBuilder.canvas = canvasElement;

    // Setup canvas
    setupCanvas();
    setupToolbar();
    setupContextMenu();
    setupShortcuts();

    // Load existing workflows
    loadWorkflowsForBuilder();
}

/**
 * Setup canvas
 */
function setupCanvas() {
    const canvas = workflowBuilder.canvas;

    // Zoom and pan controls
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        workflowBuilder.zoom *= delta;
        workflowBuilder.zoom = Math.max(0.1, Math.min(3, workflowBuilder.zoom));
        redrawCanvas();
    });

    // Drag to pan
    let isPanning = false;
    let lastX, lastY;

    canvas.addEventListener('mousedown', (e) => {
        if (e.button === 2 || e.ctrlKey) {
            isPanning = true;
            lastX = e.clientX;
            lastY = e.clientY;
        }
    });

    canvas.addEventListener('mousemove', (e) => {
        if (isPanning) {
            const deltaX = e.clientX - lastX;
            const deltaY = e.clientY - lastY;
            workflowBuilder.panX += deltaX;
            workflowBuilder.panY += deltaY;
            lastX = e.clientX;
            lastY = e.clientY;
            redrawCanvas();
        }
    });

    canvas.addEventListener('mouseup', () => {
        isPanning = false;
    });

    // Click handlers
    canvas.addEventListener('click', (e) => {
        const node = getNodeAtPosition(e.offsetX, e.offsetY);
        if (node) {
            selectNode(node);
        } else {
            workflowBuilder.selectedNode = null;
            redrawCanvas();
        }
    });

    // Context menu
    canvas.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showCanvasContextMenu(e.offsetX, e.offsetY);
    });

    redrawCanvas();
}

/**
 * Redraw canvas with all elements
 */
function redrawCanvas() {
    const canvas = workflowBuilder.canvas;
    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw grid
    drawGrid(ctx);

    // Apply transformations
    ctx.save();
    ctx.translate(workflowBuilder.panX, workflowBuilder.panY);
    ctx.scale(workflowBuilder.zoom, workflowBuilder.zoom);

    // Draw connections first
    workflowBuilder.connections.forEach(conn => {
        drawConnection(ctx, conn);
    });

    // Draw nodes
    workflowBuilder.nodes.forEach(node => {
        drawNode(ctx, node, node === workflowBuilder.selectedNode);
    });

    ctx.restore();
}

/**
 * Draw grid background
 */
function drawGrid(ctx) {
    const gridSize = 20;
    const width = ctx.canvas.width;
    const height = ctx.canvas.height;

    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 0.5;

    for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }

    for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
}

/**
 * Draw workflow node
 */
function drawNode(ctx, node, isSelected) {
    const { x, y, width, height, title, type } = node;

    // Node background
    ctx.fillStyle = isSelected ? '#2196F3' : '#fff';
    ctx.strokeStyle = isSelected ? '#1976D2' : '#999';
    ctx.lineWidth = isSelected ? 3 : 2;

    ctx.beginPath();
    ctx.roundRect(x, y, width, height, 5);
    ctx.fill();
    ctx.stroke();

    // Node type indicator
    ctx.fillStyle = getNodeColor(type);
    ctx.fillRect(x, y, 5, height);

    // Title
    ctx.fillStyle = isSelected ? '#fff' : '#000';
    ctx.font = '14px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(title, x + width / 2, y + 25);

    // Ports (input/output)
    drawNodePorts(ctx, node);
}

/**
 * Draw node ports (connection points)
 */
function drawNodePorts(ctx, node) {
    const { x, y, width, height } = node;
    const portRadius = 5;

    // Input port (left)
    ctx.fillStyle = '#4CAF50';
    ctx.beginPath();
    ctx.arc(x - portRadius, y + height / 2, portRadius, 0, 2 * Math.PI);
    ctx.fill();

    // Output port (right)
    ctx.fillStyle = '#FF9800';
    ctx.beginPath();
    ctx.arc(x + width + portRadius, y + height / 2, portRadius, 0, 2 * Math.PI);
    ctx.fill();
}

/**
 * Draw connection between nodes
 */
function drawConnection(ctx, connection) {
    const { fromNode, toNode } = connection;

    const fromX = fromNode.x + fromNode.width;
    const fromY = fromNode.y + fromNode.height / 2;
    const toX = toNode.x;
    const toY = toNode.y + toNode.height / 2;

    // Curved line
    ctx.strokeStyle = '#666';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(fromX, fromY);

    const controlX = (fromX + toX) / 2;
    ctx.quadraticCurveTo(controlX, fromY, (fromX + toX) / 2, fromY);
    ctx.quadraticCurveTo(controlX, toY, toX, toY);
    ctx.stroke();

    // Arrow
    drawArrow(ctx, toX - 5, toY);
}

/**
 * Draw arrow head
 */
function drawArrow(ctx, x, y) {
    const arrowSize = 10;
    ctx.fillStyle = '#666';
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x - arrowSize, y - arrowSize / 2);
    ctx.lineTo(x - arrowSize, y + arrowSize / 2);
    ctx.closePath();
    ctx.fill();
}

/**
 * Get node color based on type
 */
function getNodeColor(type) {
    const colors = {
        'trigger': '#E91E63',
        'action': '#2196F3',
        'condition': '#FF9800',
        'end': '#4CAF50',
        'skill': '#9C27B0',
    };
    return colors[type] || '#999';
}

/**
 * Get node at position
 */
function getNodeAtPosition(x, y) {
    // Reverse transforms
    const realX = (x - workflowBuilder.panX) / workflowBuilder.zoom;
    const realY = (y - workflowBuilder.panY) / workflowBuilder.zoom;

    for (const node of workflowBuilder.nodes) {
        if (realX >= node.x && realX <= node.x + node.width &&
            realY >= node.y && realY <= node.y + node.height) {
            return node;
        }
    }
    return null;
}

/**
 * Select node
 */
function selectNode(node) {
    workflowBuilder.selectedNode = node;
    renderNodeProperties(node);
    redrawCanvas();
}

/**
 * Render node properties panel
 */
function renderNodeProperties(node) {
    const propertiesPanel = document.getElementById('node-properties');
    if (!propertiesPanel) return;

    propertiesPanel.innerHTML = `
        <div class="properties-panel">
            <h3>Node Properties</h3>
            <div class="property">
                <label>Title:</label>
                <input type="text" value="${node.title}"
                    onchange="updateNodeProperty(this, 'title')">
            </div>
            <div class="property">
                <label>Type:</label>
                <select onchange="updateNodeProperty(this, 'type')">
                    <option value="trigger" ${node.type === 'trigger' ? 'selected' : ''}>Trigger</option>
                    <option value="action" ${node.type === 'action' ? 'selected' : ''}>Action</option>
                    <option value="condition" ${node.type === 'condition' ? 'selected' : ''}>Condition</option>
                    <option value="skill" ${node.type === 'skill' ? 'selected' : ''}>Skill</option>
                    <option value="end" ${node.type === 'end' ? 'selected' : ''}>End</option>
                </select>
            </div>
            <div class="property">
                <label>Configuration:</label>
                <textarea onchange="updateNodeProperty(this, 'config')">${
                    JSON.stringify(node.config || {}, null, 2)
                }</textarea>
            </div>
            <div class="property-actions">
                <button class="btn btn-danger" onclick="deleteNode()">Delete Node</button>
            </div>
        </div>
    `;
}

/**
 * Update node property
 */
function updateNodeProperty(input, property) {
    if (!workflowBuilder.selectedNode) return;

    try {
        if (property === 'config') {
            workflowBuilder.selectedNode.config = JSON.parse(input.value);
        } else {
            workflowBuilder.selectedNode[property] = input.value;
        }
        redrawCanvas();
    } catch (e) {
        console.error('Error updating property:', e);
    }
}

/**
 * Add node to workflow
 */
function addNode(type) {
    const newNode = {
        id: 'node_' + Date.now(),
        title: `${type.charAt(0).toUpperCase() + type.slice(1)} ${workflowBuilder.nodes.length + 1}`,
        type: type,
        x: 100 + Math.random() * 300,
        y: 100 + Math.random() * 300,
        width: 150,
        height: 60,
        config: {},
    };

    workflowBuilder.nodes.push(newNode);
    pushUndoState();
    redrawCanvas();
}

/**
 * Delete node
 */
function deleteNode() {
    if (!workflowBuilder.selectedNode) return;

    const index = workflowBuilder.nodes.indexOf(workflowBuilder.selectedNode);
    if (index > -1) {
        workflowBuilder.nodes.splice(index, 1);
    }

    // Remove connections
    workflowBuilder.connections = workflowBuilder.connections.filter(
        conn => conn.fromNode !== workflowBuilder.selectedNode &&
                conn.toNode !== workflowBuilder.selectedNode
    );

    workflowBuilder.selectedNode = null;
    pushUndoState();
    redrawCanvas();
}

/**
 * Connect nodes
 */
function connectNodes(fromNode, toNode) {
    // Prevent duplicate connections
    const exists = workflowBuilder.connections.some(
        conn => conn.fromNode === fromNode && conn.toNode === toNode
    );

    if (!exists) {
        workflowBuilder.connections.push({
            fromNode,
            toNode,
        });
        pushUndoState();
        redrawCanvas();
    }
}

/**
 * Setup toolbar
 */
function setupToolbar() {
    const toolbar = document.getElementById('workflow-toolbar');
    if (!toolbar) return;

    const buttons = {
        'trigger': () => addNode('trigger'),
        'action': () => addNode('action'),
        'condition': () => addNode('condition'),
        'skill': () => addNode('skill'),
        'end': () => addNode('end'),
        'save': saveWorkflow,
        'clear': clearWorkflow,
    };

    Object.entries(buttons).forEach(([name, handler]) => {
        const btn = toolbar.querySelector(`[data-action="${name}"]`);
        if (btn) {
            btn.addEventListener('click', handler);
        }
    });
}

/**
 * Setup context menu
 */
function setupContextMenu() {
    // Context menu implementation
}

/**
 * Setup keyboard shortcuts
 */
function setupShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'z':
                    e.preventDefault();
                    undo();
                    break;
                case 'y':
                    e.preventDefault();
                    redo();
                    break;
                case 's':
                    e.preventDefault();
                    saveWorkflow();
                    break;
            }
        }
        if (e.key === 'Delete' && workflowBuilder.selectedNode) {
            deleteNode();
        }
    });
}

/**
 * Undo
 */
function undo() {
    if (workflowBuilder.undoStack.length === 0) return;

    const state = workflowBuilder.undoStack.pop();
    workflowBuilder.redoStack.push(JSON.stringify({
        nodes: workflowBuilder.nodes,
        connections: workflowBuilder.connections,
    }));

    Object.assign(workflowBuilder, JSON.parse(state));
    redrawCanvas();
}

/**
 * Redo
 */
function redo() {
    if (workflowBuilder.redoStack.length === 0) return;

    const state = workflowBuilder.redoStack.pop();
    workflowBuilder.undoStack.push(JSON.stringify({
        nodes: workflowBuilder.nodes,
        connections: workflowBuilder.connections,
    }));

    Object.assign(workflowBuilder, JSON.parse(state));
    redrawCanvas();
}

/**
 * Push undo state
 */
function pushUndoState() {
    workflowBuilder.undoStack.push(JSON.stringify({
        nodes: workflowBuilder.nodes,
        connections: workflowBuilder.connections,
    }));

    // Limit undo history
    if (workflowBuilder.undoStack.length > 50) {
        workflowBuilder.undoStack.shift();
    }

    workflowBuilder.redoStack = [];
}

/**
 * Save workflow
 */
async function saveWorkflow() {
    if (!workflowBuilder.currentWorkflow) {
        createNewWorkflow();
        return;
    }

    const workflowData = {
        id: workflowBuilder.currentWorkflow.id,
        name: workflowBuilder.currentWorkflow.name,
        description: workflowBuilder.currentWorkflow.description,
        nodes: workflowBuilder.nodes,
        connections: workflowBuilder.connections,
    };

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/v1/workflows/${workflowData.id}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(workflowData),
            }
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        showNotification('Workflow saved successfully', 'success');
    } catch (error) {
        showNotification(`Error saving workflow: ${error.message}`, 'error');
    }
}

/**
 * Load workflows for builder
 */
async function loadWorkflowsForBuilder() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/workflows`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const workflows = await response.json();
        renderWorkflowList(workflows);
    } catch (error) {
        console.error('Error loading workflows:', error);
    }
}

/**
 * Render workflow list
 */
function renderWorkflowList(workflows) {
    const list = document.getElementById('workflow-list');
    if (!list) return;

    list.innerHTML = workflows.map(wf => `
        <div class="workflow-item" onclick="openWorkflow('${wf.id}')">
            <h4>${escapeHtml(wf.name)}</h4>
            <p>${escapeHtml(wf.description)}</p>
        </div>
    `).join('');
}

/**
 * Open workflow
 */
async function openWorkflow(workflowId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/workflows/${workflowId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        workflowBuilder.currentWorkflow = await response.json();
        workflowBuilder.nodes = workflowBuilder.currentWorkflow.nodes || [];
        workflowBuilder.connections = workflowBuilder.currentWorkflow.connections || [];
        redrawCanvas();
    } catch (error) {
        showNotification(`Error opening workflow: ${error.message}`, 'error');
    }
}

/**
 * Create new workflow
 */
function createNewWorkflow() {
    const name = prompt('Enter workflow name:');
    if (!name) return;

    workflowBuilder.currentWorkflow = {
        id: 'workflow_' + Date.now(),
        name: name,
        description: '',
        nodes: [],
        connections: [],
    };

    workflowBuilder.nodes = [];
    workflowBuilder.connections = [];
    redrawCanvas();
}

/**
 * Clear workflow
 */
function clearWorkflow() {
    if (confirm('Are you sure you want to clear all nodes?')) {
        workflowBuilder.nodes = [];
        workflowBuilder.connections = [];
        workflowBuilder.selectedNode = null;
        pushUndoState();
        redrawCanvas();
    }
}

// Initialize on document load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWorkflowBuilder);
} else {
    initializeWorkflowBuilder();
}
