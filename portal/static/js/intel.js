/**
 * BTPI-REACT Threat Intelligence Dashboard
 * Interfaces with MISP for IOC search and threat feed management
 */

class ThreatIntel {
    constructor() {
        this.apiClient = apiClient;
        this.init();
    }

    /**
     * Initialize Intel tab
     */
    async init() {
        try {
            this.attachEventListeners();
            await this.loadInitialData();
        } catch (error) {
            console.error('Intel initialization error:', error);
        }
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Search button
        document.getElementById('intel-search-btn')?.addEventListener('click', () => this.performSearch());

        // Search on Enter key
        document.getElementById('intel-search-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // Refresh button
        document.getElementById('refresh-intel-btn')?.addEventListener('click', () => this.loadInitialData());

        // Sync feeds button
        document.getElementById('sync-feeds-btn')?.addEventListener('click', () => this.syncFeeds());

        // Modal close
        document.querySelector('.modal-close')?.addEventListener('click', () => this.closeIOCModal());
        document.getElementById('close-ioc-modal')?.addEventListener('click', () => this.closeIOCModal());
    }

    /**
     * Load initial Intel data
     */
    async loadInitialData() {
        try {
            // Load statistics
            await this.updateStats();
            // Load feeds
            await this.loadFeeds();
        } catch (error) {
            console.error('Error loading Intel data:', error);
        }
    }

    /**
     * Update MISP statistics
     */
    async updateStats() {
        try {
            const response = await this.apiClient.request('/misp/stats');

            if (response.success) {
                document.getElementById('stat-events').textContent = response.events.toLocaleString();
                document.getElementById('stat-attributes').textContent = response.attributes.toLocaleString();
                document.getElementById('stat-feeds').textContent = response.feeds;
                document.getElementById('stat-last-sync').textContent = new Date(response.timestamp).toLocaleTimeString();
            }
        } catch (error) {
            console.error('Error updating statistics:', error);
            document.getElementById('stat-events').textContent = 'Error';
            document.getElementById('stat-attributes').textContent = 'Error';
        }
    }

    /**
     * Perform IOC search
     */
    async performSearch() {
        try {
            const searchInput = document.getElementById('intel-search-input');
            const typeSelect = document.getElementById('ioc-type-select');

            if (!searchInput?.value.trim()) {
                alert('Please enter an IOC value to search');
                return;
            }

            this.showLoading(true);

            const response = await this.apiClient.request('/misp/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    value: searchInput.value,
                    type: typeSelect?.value || 'auto'
                })
            });

            this.showLoading(false);

            if (response.success) {
                this.displaySearchResults(response);
            } else {
                alert(`Search failed: ${response.error}`);
            }
        } catch (error) {
            console.error('Error performing search:', error);
            this.showLoading(false);
            alert(`Search error: ${error.message}`);
        }
    }

    /**
     * Display search results
     */
    displaySearchResults(data) {
        const resultsSection = document.getElementById('search-results-section');
        const resultsContainer = document.getElementById('search-results');

        if (!resultsSection || !resultsContainer) return;

        resultsSection.style.display = 'block';
        resultsContainer.innerHTML = '';

        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="empty-message">
                    <p>No results found for <strong>${this.escapeHtml(data.value)}</strong></p>
                    <small>IOC Type: ${data.ioc_type}</small>
                </div>
            `;
            return;
        }

        // Create results table
        const table = document.createElement('table');
        table.className = 'results-table';

        // Header
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Type</th>
                <th>Value</th>
                <th>Tags</th>
                <th>Timestamp</th>
                <th>Action</th>
            </tr>
        `;
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        data.results.forEach((result, index) => {
            const row = document.createElement('tr');
            const tags = result.tags ? result.tags.split(',').join(', ') : 'None';

            row.innerHTML = `
                <td>${this.escapeHtml(result.type || 'unknown')}</td>
                <td>${this.escapeHtml(result.value)}</td>
                <td>${this.escapeHtml(tags)}</td>
                <td>${result.timestamp ? new Date(result.timestamp).toLocaleString() : 'N/A'}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="threatIntel.showIOCDetails('${this.escapeHtml(result.value)}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);

        resultsContainer.appendChild(table);
    }

    /**
     * Load and display feeds
     */
    async loadFeeds() {
        try {
            const response = await this.apiClient.request('/misp/feeds');

            if (response.success && response.feeds) {
                this.displayFeeds(response.feeds);
            }
        } catch (error) {
            console.error('Error loading feeds:', error);
        }
    }

    /**
     * Display feeds table
     */
    displayFeeds(feeds) {
        const tbody = document.getElementById('feeds-table-body');
        if (!tbody) return;

        tbody.innerHTML = '';

        feeds.forEach((feed, index) => {
            const row = document.createElement('tr');
            const status = feed.enabled ? 'Active' : 'Inactive';
            const statusBadge = feed.enabled ? 'success' : 'secondary';

            row.innerHTML = `
                <td>${this.escapeHtml(feed.name)}</td>
                <td><span class="badge badge-${statusBadge}">${status}</span></td>
                <td>--</td>
                <td>${feed.last_updated ? new Date(feed.last_updated).toLocaleString() : 'Never'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="threatIntel.syncFeeds()">
                        <i class="fas fa-sync"></i> Sync
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * Sync MISP feeds
     */
    async syncFeeds() {
        try {
            const btn = event.target.closest('button');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-sync fa-spin"></i> Syncing...';
            }

            const response = await this.apiClient.request('/misp/sync-feeds', {
                method: 'POST'
            });

            if (response.success) {
                alert('Feed synchronization initiated');
                // Refresh data after sync
                setTimeout(() => {
                    this.loadInitialData();
                }, 2000);
            } else {
                alert(`Sync failed: ${response.error}`);
            }

            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-download"></i> Sync All Feeds';
            }
        } catch (error) {
            console.error('Error syncing feeds:', error);
            alert(`Sync error: ${error.message}`);
            const btn = event.target.closest('button');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-download"></i> Sync All Feeds';
            }
        }
    }

    /**
     * Show IOC details modal
     */
    showIOCDetails(iocValue) {
        const modal = document.getElementById('ioc-modal');
        const modalBody = document.getElementById('ioc-modal-body');

        if (!modal || !modalBody) return;

        modalBody.innerHTML = `
            <div class="ioc-details">
                <div class="detail-item">
                    <strong>IOC Value:</strong>
                    <code>${this.escapeHtml(iocValue)}</code>
                </div>
                <div class="detail-item">
                    <strong>IOC Type:</strong>
                    <span id="ioc-detail-type">--</span>
                </div>
                <div class="detail-item">
                    <strong>Last Seen:</strong>
                    <span id="ioc-detail-lastseen">--</span>
                </div>
                <div class="detail-item">
                    <strong>Threat Level:</strong>
                    <span id="ioc-detail-threat" class="badge badge-warning">--</span>
                </div>
                <div class="detail-item">
                    <strong>Associated Tags:</strong>
                    <div id="ioc-detail-tags" class="tag-list">
                        <!-- Tags populated here -->
                    </div>
                </div>
                <div class="detail-item">
                    <strong>Associated Events:</strong>
                    <div id="ioc-detail-events">
                        Loading events...
                    </div>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');

        // Store IOC value for copy functionality
        document.getElementById('copy-ioc-btn').onclick = () => this.copyIOC(iocValue);
    }

    /**
     * Close IOC modal
     */
    closeIOCModal() {
        const modal = document.getElementById('ioc-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Copy IOC to clipboard
     */
    copyIOC(value) {
        navigator.clipboard.writeText(value).then(() => {
            alert('IOC copied to clipboard');
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
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
     * Escape HTML entities
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize threat intelligence when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('intel-content')) {
        window.threatIntel = new ThreatIntel();
    }
});
