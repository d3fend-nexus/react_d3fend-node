/**
 * API Client for BTPI-REACT Portal
 * Handles all communication with the Flask backend
 */

class APIClient {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
        this.timeout = 10000; // 10 seconds
    }

    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            timeout: this.timeout,
            ...options,
        };

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), config.timeout);

            const response = await fetch(url, {
                ...config,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error: ${endpoint}`, error);
            throw error;
        }
    }

    // ========================================
    // Container Management
    // ========================================

    /**
     * Get container count
     */
    async getContainerCount() {
        return this.request('/containers/count');
    }

    /**
     * Get all container status
     */
    async getContainersStatus() {
        return this.request('/containers/status');
    }

    /**
     * Start a container
     */
    async startContainer(containerName) {
        return this.request(`/containers/${containerName}/start`, {
            method: 'POST',
        });
    }

    /**
     * Stop a container
     */
    async stopContainer(containerName) {
        return this.request(`/containers/${containerName}/stop`, {
            method: 'POST',
        });
    }

    /**
     * Restart a container
     */
    async restartContainer(containerName) {
        return this.request(`/containers/${containerName}/restart`, {
            method: 'POST',
        });
    }

    // ========================================
    // Tools Management
    // ========================================

    /**
     * Get BTPI-REACT tools status
     */
    async getToolsStatus() {
        return this.request('/tools/status');
    }

    /**
     * Get available tools configuration
     */
    async getTools() {
        return this.request('/tools');
    }

    // ========================================
    // Dashboard & Metrics
    // ========================================

    /**
     * Get dashboard metrics
     */
    async getDashboardMetrics() {
        return this.request('/dashboard/metrics');
    }

    /**
     * Get server information
     */
    async getServerInfo() {
        return this.request('/server-info');
    }

    /**
     * Health check
     */
    async healthCheck() {
        return this.request('/health');
    }

    // ========================================
    // Changelog & Activity
    // ========================================

    /**
     * Get changelog entries
     */
    async getChangelog(limit = 20, level = null) {
        let endpoint = `/changelog?limit=${limit}`;
        if (level) {
            endpoint += `&level=${level}`;
        }
        return this.request(endpoint);
    }

    /**
     * Get changelog statistics
     */
    async getChangelogStats() {
        return this.request('/changelog/stats');
    }
}

// Export the API client
const apiClient = new APIClient();
