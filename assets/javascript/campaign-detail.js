/**
 * Campaign Detail Page Manager
 * Handles campaign detail page functionality including charts and sync operations
 */

class CampaignDetailManager {
    constructor() {
        this.csrfToken = this.getCSRFToken();
        this.init();
    }

    /**
     * Initialize the campaign detail manager
     */
    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
        } else {
            this.initializeComponents();
        }
    }

    /**
     * Get CSRF token from page
     * @returns {string} CSRF token
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    /**
     * Initialize all components
     */
    initializeComponents() {
        this.initializeCharts();
        this.initializeSyncFunctionality();
    }

    /**
     * Initialize charts
     */
    initializeCharts() {
        // Get chart data from page
        const chartDatesElement = document.getElementById('chart-dates');
        const impressionsDataElement = document.getElementById('impressions-data');
        const clicksDataElement = document.getElementById('clicks-data');
        const spendDataElement = document.getElementById('spend-data');

        if (!chartDatesElement || !impressionsDataElement || !clicksDataElement || !spendDataElement) {
            console.log('Chart data elements not found, skipping chart initialization');
            return;
        }

        const chartDates = JSON.parse(chartDatesElement.textContent);
        const impressionsData = JSON.parse(impressionsDataElement.textContent);
        const clicksData = JSON.parse(clicksDataElement.textContent);
        const spendData = JSON.parse(spendDataElement.textContent);

        this.createImpressionsChart(chartDates, impressionsData);
        this.createClicksChart(chartDates, clicksData);
        this.createSpendChart(chartDates, spendData);
    }

    /**
     * Create impressions chart
     * @param {Array} chartDates - Chart date labels
     * @param {Array} impressionsData - Impressions data
     */
    createImpressionsChart(chartDates, impressionsData) {
        const ctx = document.getElementById('impressions-chart');
        if (!ctx) return;

        new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: chartDates,
                datasets: [{
                    label: 'Impressions',
                    data: impressionsData,
                    borderColor: '#f97316',
                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 7
                        }
                    }
                }
            }
        });
    }

    /**
     * Create clicks chart
     * @param {Array} chartDates - Chart date labels
     * @param {Array} clicksData - Clicks data
     */
    createClicksChart(chartDates, clicksData) {
        const ctx = document.getElementById('clicks-chart');
        if (!ctx) return;

        new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: chartDates,
                datasets: [{
                    label: 'Clicks',
                    data: clicksData,
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 7
                        }
                    }
                }
            }
        });
    }

    /**
     * Create spend chart
     * @param {Array} chartDates - Chart date labels
     * @param {Array} spendData - Spend data
     */
    createSpendChart(chartDates, spendData) {
        const ctx = document.getElementById('spend-chart');
        if (!ctx) return;

        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: chartDates,
                datasets: [{
                    label: 'Daily Spend',
                    data: spendData,
                    backgroundColor: '#a855f7',
                    borderColor: '#9333ea',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 10
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize sync functionality
     */
    initializeSyncFunctionality() {
        // Make syncCampaign globally available for onclick handlers
        window.syncCampaign = () => {
            this.handleSyncCampaign();
        };
    }

    /**
     * Handle sync campaign action
     */
    async handleSyncCampaign() {
        const btn = event.target.closest('button');
        const originalContent = btn.innerHTML;
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';

        try {
            // Get account ID
            const accountIdElement = document.getElementById('account-id');
            if (!accountIdElement) {
                throw new Error('Account ID not found');
            }
            
            const accountId = JSON.parse(accountIdElement.textContent);

            const response = await fetch('/facebook-ads/api/fetch-campaigns-for-account/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ account_id: accountId })
            });

            const data = await response.json();

            if (data.success) {
                window.showSuccess(`Successfully synced ${data.campaigns_synced} campaigns!`);
                
                // Reload page to show updated data
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                window.showError('Sync failed: ' + data.message);
            }
        } catch (error) {
            console.error('Error:', error);
            window.showError('An error occurred while syncing the campaign.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalContent;
        }
    }
}

// Initialize when DOM is ready
new CampaignDetailManager(); 