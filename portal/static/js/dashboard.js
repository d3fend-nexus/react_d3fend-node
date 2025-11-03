/**
 * BTPI-REACT Dashboard
 * Main dashboard logic and UI management
 */

class Dashboard {
    constructor() {
        this.apiClient = apiClient;
        this.refreshInterval = 5000; // 5 seconds
        this.refreshTimer = null;
        this.currentFilter = 'all';
        this.init();
    }

    /**
     * Initialize dashboard
     */
    async init() {
        try {
            this.attachEventListeners();
            await this.loadInitialData();
            this.startAutoRefresh();
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.showError('Failed to initialize dashboard');
        }
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Refresh button
        document.getElementById('refresh-btn')?.addEventListener('click', () => this.refresh());

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach((btn) => {
            btn.addEventListener('click', (e) => this.handleFilterChange(e));
        });

        // Modal close
        document.querySelector('.modal-close')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modal-close-btn')?.addEventListener('click', () => this.closeModal());

        // Modal background click
        document.getElementById('tool-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'tool-modal') {
                this.closeModal();
            }
        });

        // Clear log button
        document.getElementById('clear-log-btn')?.addEventListener('click', () => this.clearActivityLog());
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        try {
            this.showLoading(true);
            await Promise.all([
                this.updateMetrics(),
                this.updateTools(),
                this.updateActivity(),
            ]);
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
            this.showLoading(false);
        }
    }

    /**
     * Update system metrics
     */
    async updateMetrics() {
        try {
            const data = await this.apiClient.getDashboardMetrics();

            if (data.success) {
                const { system, containers } = data;

                // Update CPU
                document.getElementById('cpu-value').textContent = `${system.cpu_percent.toFixed(1)}%`;
                document.getElementById('cpu-bar').style.width = `${system.cpu_percent}%`;

                // Update Memory
                document.getElementById('memory-value').textContent = `${system.memory_percent.toFixed(1)}%`;
                document.getElementById('memory-bar').style.width = `${system.memory_percent}%`;

                // Update Disk
                document.getElementById('disk-value').textContent = `${system.disk_percent.toFixed(1)}%`;
                document.getElementById('disk-bar').style.width = `${system.disk_percent}%`;

                // Update Container counts
                document.getElementById('running-count').textContent = containers.running;
                document.getElementById('total-count').textContent = containers.total;
                document.getElementById('stopped-count').textContent = containers.stopped;

                // Update navigation
                document.getElementById('nav-container-count').textContent = containers.running;
                document.getElementById('nav-health-percent').textContent = Math.round(containers.health_percentage);
            }
        } catch (error) {
            console.error('Error updating metrics:', error);
        }
    }

    /**
     * Update tools display
     */
    async updateTools() {
        try {
            const data = await this.apiClient.getToolsStatus();

            if (data.success && data.tools) {
                this.renderTools(data.tools);
            }
        } catch (error) {
            console.error('Error updating tools:', error);
        }
    }

    /**
     * Render tools grid
     */
    renderTools(tools) {
        const grid = document.getElementById('tools-grid');
        if (!grid) return;

        grid.innerHTML = '';

        for (const [toolId, toolData] of Object.entries(tools)) {
            // Skip if filtered out
            if (this.currentFilter !== 'all' && toolData.category !== this.currentFilter) {
                continue;
            }

            const card = this.createToolCard(toolId, toolData);
            grid.appendChild(card);
        }

        // Show message if no tools match filter
        if (grid.children.length === 0) {
            grid.innerHTML = '<div class="empty-message"><p>No tools found for this filter</p></div>';
        }
    }

    /**
     * Create tool card
     */
    createToolCard(toolId, toolData) {
        const card = document.createElement('div');
        card.className = `tool-card tool-card-${toolData.status}`;

        const statusIcon = this.getStatusIcon(toolData.status);
        const category = toolData.category || 'unknown';

        card.innerHTML = `
            <div class="tool-card-header">
                <div class="tool-info">
                    <div class="tool-icon">
                        <i class="${toolData.icon || 'fas fa-cube'}"></i>
                    </div>
                    <div>
                        <h3>${toolData.name}</h3>
                        <p class="tool-description">${toolData.description || ''}</p>
                    </div>
                </div>
                <span class="tool-badge tool-badge-${toolData.status}">
                    ${statusIcon} ${toolData.status}
                </span>
            </div>

            <div class="tool-card-body">
                <div class="tool-details">
                    <small>${toolData.status_text || ''}</small>
                    ${toolData.ports ? `<small>Ports: ${toolData.ports}</small>` : ''}
                </div>
            </div>

            <div class="tool-card-footer">
                <div class="tool-actions">
                    ${toolData.status === 'running' ? `
                        <button class="btn btn-sm btn-warning" onclick="dashboard.stopTool('${toolData.name}')">
                            <i class="fas fa-stop"></i> Stop
                        </button>
                        <button class="btn btn-sm btn-info" onclick="dashboard.restartTool('${toolData.name}')">
                            <i class="fas fa-redo"></i> Restart
                        </button>
                    ` : ''}
                    ${toolData.status === 'stopped' ? `
                        <button class="btn btn-sm btn-success" onclick="dashboard.startTool('${toolData.name}')">
                            <i class="fas fa-play"></i> Start
                        </button>
                    ` : ''}
                    ${toolData.access_url ? `
                        <button class="btn btn-sm btn-primary" onclick="window.open('${toolData.access_url.replace('{server_ip}', window.location.hostname)}', '_blank')">
                            <i class="fas fa-external-link-alt"></i> Open
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        return card;
    }

    /**
     * Get status icon
     */
    getStatusIcon(status) {
        const icons = {
            running: '<i class="fas fa-check-circle"></i>',
            stopped: '<i class="fas fa-times-circle"></i>',
            not_found: '<i class="fas fa-question-circle"></i>',
            unknown: '<i class="fas fa-circle"></i>',
        };
        return icons[status] || icons.unknown;
    }

    /**
     * Update activity log
     */
    async updateActivity() {
        try {
            const data = await this.apiClient.getChangelog(10);

            if (data.success && data.entries) {
                this.renderActivityLog(data.entries);
            }
        } catch (error) {
            console.error('Error updating activity:', error);
        }
    }

    /**
     * Render activity log
     */
    renderActivityLog(entries) {
        const logContainer = document.getElementById('activity-log');
        if (!logContainer) return;

        logContainer.innerHTML = '';

        if (entries.length === 0) {
            logContainer.innerHTML = '<div class="empty-message"><p>No activity yet</p></div>';
            return;
        }

        // Reverse to show newest first
        entries.reverse().slice(0, 20).forEach((entry) => {
            const logEntry = this.createActivityEntry(entry);
            logContainer.appendChild(logEntry);
        });
    }

    /**
     * Create activity entry
     */
    createActivityEntry(entry) {
        const div = document.createElement('div');
        div.className = `activity-entry activity-${entry.level}`;

        const time = new Date(entry.timestamp).toLocaleTimeString();
        const action = entry.action.replace(/_/g, ' ').toUpperCase();

        div.innerHTML = `
            <div class="activity-icon">
                <i class="fas fa-circle"></i>
            </div>
            <div class="activity-content">
                <strong>${action}</strong>
                <p>${entry.details}</p>
                <small>${time}</small>
            </div>
        `;

        return div;
    }

    /**
     * Handle tool container action
     */
    async startTool(toolName) {
        await this.performToolAction(toolName, 'start');
    }

    async stopTool(toolName) {
        await this.performToolAction(toolName, 'stop');
    }

    async restartTool(toolName) {
        await this.performToolAction(toolName, 'restart');
    }

    /**
     * Perform tool action
     */
    async performToolAction(toolName, action) {
        try {
            this.showLoading(true);

            const method = {
                start: this.apiClient.startContainer,
                stop: this.apiClient.stopContainer,
                restart: this.apiClient.restartContainer,
            }[action];

            if (!method) throw new Error(`Unknown action: ${action}`);

            const result = await method.call(this.apiClient, toolName);

            if (result.success) {
                this.showSuccess(`${toolName} ${action}ed successfully`);
                await this.updateTools();
            } else {
                this.showError(result.message || `Failed to ${action} ${toolName}`);
            }

            this.showLoading(false);
        } catch (error) {
            console.error(`Error performing ${action}:`, error);
            this.showError(`Error: ${error.message}`);
            this.showLoading(false);
        }
    }

    /**
     * Handle filter change
     */
    handleFilterChange(event) {
        // Update active button
        document.querySelectorAll('.filter-btn').forEach((btn) => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');

        // Update filter and re-render
        this.currentFilter = event.target.dataset.filter;
        this.updateTools();
    }

    /**
     * Refresh dashboard
     */
    async refresh() {
        try {
            const btn = document.getElementById('refresh-btn');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
            }

            await this.loadInitialData();

            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            }

            this.showSuccess('Dashboard refreshed');
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            this.showError('Failed to refresh dashboard');
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(async () => {
            try {
                await this.updateMetrics();
                await this.updateTools();
                await this.updateActivity();
            } catch (error) {
                console.error('Auto-refresh error:', error);
            }
        }, this.refreshInterval);
    }

    /**
     * Clear activity log
     */
    clearActivityLog() {
        const logContainer = document.getElementById('activity-log');
        if (logContainer) {
            logContainer.innerHTML = '<div class="empty-message"><p>Activity log cleared</p></div>';
        }
    }

    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('tool-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Show loading indicator
     */
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('hidden');
            } else {
                overlay.classList.add('hidden');
            }
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        console.log('Success:', message);
        // Could be enhanced with a toast notification
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('Error:', message);
        alert(`Error: ${message}`);
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
