/**
 * Campaign Selection Page Manager
 * Handles campaign selection, sync operations, and UI interactions
 */

class CampaignSelectionManager {
    constructor() {
        this.csrfToken = this.getCSRFToken();
        this.storagePrefix = 'campaignSync_'; // Match sync manager prefix
        this.init();
    }

    /**
     * Initialize the campaign selection manager
     */
    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeEventListeners());
        } else {
            this.initializeEventListeners();
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
     * Initialize all event listeners
     */
    initializeEventListeners() {
        this.initializeTabSwitching();
        this.initializeCheckboxes();
        this.initializeSyncButtons();
        this.initializeSaveButtons();
        this.initializeSelectionCounts();
    }

    /**
     * Initialize tab switching functionality
     */
    initializeTabSwitching() {
        // Make switchAccountTab globally available for onclick handlers
        window.switchAccountTab = (accountId) => {
            // Hide all tab contents
            document.querySelectorAll('.account-tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            
            // Show selected tab content
            const selectedContent = document.getElementById(`account-tab-${accountId}`);
            if (selectedContent) {
                selectedContent.classList.remove('hidden');
            }
            
            // Update tab button states
            document.querySelectorAll('.account-tab').forEach(tab => {
                if (tab.dataset.accountId === accountId) {
                    tab.classList.remove('border-transparent', 'text-muted-foreground');
                    tab.classList.add('border-primary', 'text-foreground');
                } else {
                    tab.classList.remove('border-primary', 'text-foreground');
                    tab.classList.add('border-transparent', 'text-muted-foreground');
                }
            });
        };
    }

    /**
     * Initialize checkbox functionality
     */
    initializeCheckboxes() {
        // Handle select all checkboxes
        document.querySelectorAll('.select-all-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const accountId = e.target.dataset.accountId;
                const campaignCheckboxes = document.querySelectorAll(`.campaign-checkbox[data-account-id="${accountId}"]`);
                
                campaignCheckboxes.forEach(campaignCheckbox => {
                    campaignCheckbox.checked = e.target.checked;
                });
                
                this.updateSelectedCount(accountId);
            });
        });

        // Handle individual campaign checkboxes
        document.querySelectorAll('.campaign-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const accountId = e.target.dataset.accountId;
                this.updateSelectedCount(accountId);
            });
        });

        // Initialize counts
        document.querySelectorAll('.select-all-checkbox').forEach(checkbox => {
            const accountId = checkbox.dataset.accountId;
            this.updateSelectedCount(accountId);
        });
    }

    /**
     * Initialize sync buttons
     */
    initializeSyncButtons() {
        document.querySelectorAll('.sync-account-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const accountId = e.target.dataset.accountId;
                this.handleSyncAccount(accountId, e.target);
            });
        });
    }

    /**
     * Initialize save buttons
     */
    initializeSaveButtons() {
        document.querySelectorAll('.save-selection-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const accountId = e.target.dataset.accountId;
                this.handleSaveSelection(accountId, e.target);
            });
        });
    }

    /**
     * Initialize selection counts
     */
    initializeSelectionCounts() {
        document.querySelectorAll('.select-all-checkbox').forEach(checkbox => {
            const accountId = checkbox.dataset.accountId;
            this.updateSelectedCount(accountId);
        });
    }

    /**
     * Update selected count for an account
     * @param {string} accountId - The account ID
     */
    updateSelectedCount(accountId) {
        const checkboxes = document.querySelectorAll(`.campaign-checkbox[data-account-id="${accountId}"]`);
        const checkedBoxes = document.querySelectorAll(`.campaign-checkbox[data-account-id="${accountId}"]:checked`);
        const count = checkedBoxes.length;
        
        const selectedCountElement = document.querySelector(`.selected-count[data-account-id="${accountId}"]`);
        const saveBtn = document.querySelector(`.save-selection-btn[data-account-id="${accountId}"]`);
        const selectAllCheckbox = document.querySelector(`.select-all-checkbox[data-account-id="${accountId}"]`);
        
        if (selectedCountElement) {
            selectedCountElement.textContent = `${count} geselecteerd`;
        }
        
        if (saveBtn) {
            saveBtn.disabled = count === 0;
        }
        
        // Update select all checkbox state
        if (selectAllCheckbox) {
            selectAllCheckbox.indeterminate = count > 0 && count < checkboxes.length;
            selectAllCheckbox.checked = count === checkboxes.length && count > 0;
        }
    }

    /**
     * Handle sync account action
     * @param {string} accountId - The account ID
     * @param {HTMLElement} button - The sync button element
     */
    async handleSyncAccount(accountId, button) {
        const originalContent = button.innerHTML;

        // Show loading state
        button.disabled = true;
        button.innerHTML = '<span class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></span>Synchroniseren...';

        try {
            // Use comprehensive sync endpoint for full campaign data with metrics
            const response = await fetch('/facebook-ads/api/comprehensive-sync-campaigns/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ account_id: accountId })
            });

            const data = await response.json();

            if (data.success) {
                // Record sync attempt using the sync manager
                if (window.campaignSyncManager) {
                    window.campaignSyncManager.recordSyncAttempt(accountId, data.synced_count);
                }

                // Show success notification with data types
                window.showSuccess(`${data.synced_count} campagne(s) succesvol gesynchroniseerd voor ${data.account_name} met volledige metrics!\n\nData types:\n${data.data_types.join('\n')}`);

                // Refresh campaign data
                setTimeout(() => {
                    this.refreshAccountCampaigns(accountId);
                }, 1000);
            } else {
                window.showError('Fout bij synchroniseren: ' + data.message);
            }
        } catch (error) {
            console.error('Error:', error);
            window.showError('Er is een fout opgetreden bij het synchroniseren van campagnes.');
        } finally {
            // Reset button
            button.disabled = false;
            button.innerHTML = originalContent;
        }
    }

    /**
     * Handle save selection action
     * @param {string} accountId - The account ID
     * @param {HTMLElement} button - The save button element
     */
    async handleSaveSelection(accountId, button) {
        const selectedIds = Array.from(document.querySelectorAll(`.campaign-checkbox[data-account-id="${accountId}"]:checked`))
            .map(checkbox => parseInt(checkbox.value));

        if (selectedIds.length === 0) {
            window.showError('Selecteer ten minste één campagne.');
            return;
        }

        const originalContent = button.innerHTML;
        
        // Show loading state
        button.disabled = true;
        button.innerHTML = '<span class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>Opslaan...';

        try {
            const response = await fetch('/facebook-ads/api/save-selected-campaigns/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ campaign_ids: selectedIds })
            });

            const data = await response.json();

            if (data.success) {
                window.showSuccess(`${data.selected_count} campagne(s) succesvol toegevoegd voor monitoring!`);
                
                // Redirect to dashboard after short delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            } else {
                window.showError('Fout: ' + data.message);
                // Reset button
                button.disabled = false;
                button.innerHTML = originalContent;
            }
        } catch (error) {
            console.error('Error:', error);
            window.showError('Er is een fout opgetreden bij het opslaan van de selectie.');
            // Reset button
            button.disabled = false;
            button.innerHTML = originalContent;
        }
    }

    /**
     * Refresh campaign data for an account
     * @param {string} accountId - The account ID
     */
    async refreshAccountCampaigns(accountId) {
        try {
            const response = await fetch(`/facebook-ads/api/get-account-campaigns/?account_id=${accountId}`, {
                method: 'GET',
                headers: { 'X-CSRFToken': this.csrfToken }
            });

            const data = await response.json();

            if (data.success) {
                this.updateAccountCampaignsTable(accountId, data);
                this.updateAccountInfo(accountId, data);
                this.updateTabBadge(accountId, data.campaign_count);
                window.showInfo('Campagne data bijgewerkt!');
            } else {
                window.showError('Fout bij het ophalen van bijgewerkte data: ' + data.message);
            }
        } catch (error) {
            console.error('Error refreshing campaigns:', error);
            window.showError('Er is een fout opgetreden bij het bijwerken van de campagne data.');
        }
    }

    /**
     * Update account campaigns table
     * @param {string} accountId - The account ID
     * @param {Object} data - Campaign data
     */
    updateAccountCampaignsTable(accountId, data) {
        const tableBody = document.querySelector(`#account-tab-${accountId} tbody`);
        if (!tableBody) return;

        if (data.campaigns.length === 0) {
            // Hide table and let sync manager handle empty state
            const tableContainer = document.querySelector(`#account-tab-${accountId} .overflow-x-auto`);
            if (tableContainer) {
                tableContainer.style.display = 'none';
            }
            
            // Trigger sync manager to update state
            if (window.campaignSyncManager) {
                window.campaignSyncManager.initializeAccount(accountId);
            }
            return;
        } else {
            // Show table
            const tableContainer = document.querySelector(`#account-tab-${accountId} .overflow-x-auto`);
            if (tableContainer) {
                tableContainer.style.display = 'block';
            }
        }

        // Build campaigns HTML
        const campaignsHtml = data.campaigns.map(campaign => {
            const isSelected = data.selected_campaign_ids.includes(campaign.id);
            const statusClass = campaign.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                               campaign.status === 'PAUSED' ? 'bg-yellow-100 text-yellow-800' :
                               'bg-red-100 text-red-800';
            
            return `
                <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted" data-slot="table-row">
                    <td class="p-4 align-middle" data-slot="table-cell">
                        <input type="checkbox" 
                               class="h-4 w-4 rounded border border-input bg-background text-primary focus:ring-2 focus:ring-ring focus:ring-offset-2 campaign-checkbox" 
                               value="${campaign.id}"
                               data-account-id="${accountId}"
                               ${isSelected ? 'checked' : ''}>
                    </td>
                    <td class="p-4 align-middle" data-slot="table-cell">
                        <div class="font-medium text-gray-900">${campaign.campaign_name}</div>
                        <div class="text-xs text-gray-500">ID: ${campaign.campaign_id}</div>
                    </td>
                    <td class="p-4 align-middle" data-slot="table-cell">
                        <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusClass}" data-slot="badge">
                            ${campaign.status}
                        </span>
                        ${campaign.effective_status && campaign.effective_status !== campaign.status ? 
                          `<div class="text-xs text-muted-foreground mt-1">${campaign.effective_status}</div>` : ''}
                    </td>
                    <td class="p-4 align-middle" data-slot="table-cell">
                        <div class="text-sm">${campaign.last_synced ? this.formatDateTime(campaign.last_synced) : 'Niet gesynchroniseerd'}</div>
                    </td>
                    <td class="p-4 align-middle" data-slot="table-cell">
                        ${campaign.start_time ? 
                          `<div class="text-sm">${this.formatDate(campaign.start_time)}</div>` : 
                          '<span class="text-muted-foreground">-</span>'}
                    </td>
                    <td class="p-4 align-middle" data-slot="table-cell">
                        <a href="/facebook-ads/campaigns/${campaign.id}/" 
                           class="cursor-pointer inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-[color,box-shadow] disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-xs hover:bg-accent hover:text-accent-foreground h-8 px-3 py-1" 
                           data-slot="button">
                            <i class="fas fa-chart-line mr-1"></i>
                            Details
                        </a>
                    </td>
                </tr>
            `;
        }).join('');

        tableBody.innerHTML = campaignsHtml;

        // Re-attach event listeners for new checkboxes
        this.attachCampaignCheckboxListeners(accountId);
        this.updateSelectedCount(accountId);
    }

    /**
     * Update account info
     * @param {string} accountId - The account ID
     * @param {Object} data - Campaign data
     */
    updateAccountInfo(accountId, data) {
        const selectedCountElement = document.querySelector(`.selected-count[data-account-id="${accountId}"]`);
        if (selectedCountElement) {
            selectedCountElement.textContent = `${data.selected_count} geselecteerd`;
        }
    }

    /**
     * Update tab badge
     * @param {string} accountId - The account ID
     * @param {number} campaignCount - Number of campaigns
     */
    updateTabBadge(accountId, campaignCount) {
        const tabButton = document.querySelector(`.account-tab[data-account-id="${accountId}"] .bg-muted`);
        if (tabButton) {
            tabButton.textContent = `${campaignCount} campagnes`;
        }
    }

    /**
     * Attach campaign checkbox listeners
     * @param {string} accountId - The account ID
     */
    attachCampaignCheckboxListeners(accountId) {
        document.querySelectorAll(`.campaign-checkbox[data-account-id="${accountId}"]`).forEach(checkbox => {
            const newCheckbox = checkbox.cloneNode(true);
            checkbox.parentNode.replaceChild(newCheckbox, checkbox);
            
            newCheckbox.addEventListener('change', () => {
                this.updateSelectedCount(accountId);
            });
        });
    }

    /**
     * Format date time
     * @param {string} isoString - ISO date string
     * @returns {string} Formatted date time
     */
    formatDateTime(isoString) {
        const date = new Date(isoString);
        return date.toLocaleDateString('nl-NL', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        }) + ' ' + date.toLocaleTimeString('nl-NL', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Format date
     * @param {string} isoString - ISO date string
     * @returns {string} Formatted date
     */
    formatDate(isoString) {
        const date = new Date(isoString);
        return date.toLocaleDateString('nl-NL', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }
}

// Initialize when DOM is ready
new CampaignSelectionManager(); 