/**
 * Campaign Sync State Manager
 * Manages persistent sync information display for campaign accounts
 */

class CampaignSyncManager {
    constructor() {
        this.storagePrefix = 'campaignSync_';
        this.init();
    }

    /**
     * Initialize the sync manager
     */
    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeAllAccounts());
        } else {
            this.initializeAllAccounts();
        }
    }

    /**
     * Initialize sync state for all accounts on the page
     */
    initializeAllAccounts() {
        // Find all account tabs/sections
        const accountElements = document.querySelectorAll('[data-account-id]');
        const accountIds = new Set();
        
        accountElements.forEach(element => {
            const accountId = element.dataset.accountId;
            if (accountId) {
                accountIds.add(accountId);
            }
        });

        // Initialize each unique account
        accountIds.forEach(accountId => {
            setTimeout(() => this.initializeAccount(accountId), 100);
        });
    }

    /**
     * Initialize sync state for a specific account
     * @param {string} accountId - The account ID
     */
    initializeAccount(accountId) {
        console.log('Initializing sync state for account:', accountId);
        
        const accountState = this.getAccountState(accountId);
        const elements = this.getAccountElements(accountId);
        
        if (!elements.emptyState) {
            console.log(`No empty state found for account ${accountId}, skipping`);
            return;
        }

        if (accountState.hasBeenSynced) {
            this.showSyncedState(accountId, elements, accountState);
        } else {
            this.showDefaultState(accountId, elements);
        }
    }

    /**
     * Get account elements by ID
     * @param {string} accountId - The account ID
     * @returns {Object} Object containing relevant DOM elements
     */
    getAccountElements(accountId) {
        return {
            emptyState: document.querySelector(`#empty-state-${accountId}`),
            syncInfo: document.querySelector(`.sync-info-${accountId}`),
            mainText: document.querySelector(`.main-text-${accountId}`),
            syncTimeElement: document.querySelector(`.last-sync-time-${accountId}`)
        };
    }

    /**
     * Get account sync state from storage
     * @param {string} accountId - The account ID
     * @returns {Object} Account sync state
     */
    getAccountState(accountId) {
        const lastSyncTimestamp = localStorage.getItem(`${this.storagePrefix}${accountId}`);
        return {
            hasBeenSynced: !!lastSyncTimestamp,
            lastSyncTimestamp: lastSyncTimestamp,
            lastSyncDate: lastSyncTimestamp ? new Date(lastSyncTimestamp) : null
        };
    }

    /**
     * Show synced state for an account
     * @param {string} accountId - The account ID
     * @param {Object} elements - DOM elements
     * @param {Object} accountState - Account state
     */
    showSyncedState(accountId, elements, accountState) {
        // Update main text
        if (elements.mainText) {
            elements.mainText.textContent = 'Dit account is gesynchroniseerd maar heeft geen campagnes.';
        }

        // Show sync info box
        if (elements.syncInfo) {
            elements.syncInfo.classList.remove('hidden');
        }

        // Update sync time
        if (elements.syncTimeElement && accountState.lastSyncDate) {
            elements.syncTimeElement.textContent = this.formatDateTime(accountState.lastSyncDate);
        }

        console.log('Showing synced state for account', accountId);
    }

    /**
     * Show default state for an account
     * @param {string} accountId - The account ID
     * @param {Object} elements - DOM elements
     */
    showDefaultState(accountId, elements) {
        // Update main text
        if (elements.mainText) {
            elements.mainText.textContent = 'Voor dit account zijn nog geen campagnes opgehaald.';
        }

        // Hide sync info box
        if (elements.syncInfo) {
            elements.syncInfo.classList.add('hidden');
        }

        console.log('Showing default state for account', accountId);
    }

    /**
     * Record a sync attempt for an account
     * @param {string} accountId - The account ID
     * @param {number} campaignsFound - Number of campaigns found (optional)
     */
    recordSyncAttempt(accountId, campaignsFound = 0) {
        const timestamp = new Date().toISOString();
        localStorage.setItem(`${this.storagePrefix}${accountId}`, timestamp);
        
        console.log(`Recorded sync attempt for account ${accountId} at ${timestamp}`);
        
        // Immediately update the display
        this.initializeAccount(accountId);
        
        return timestamp;
    }

    /**
     * Format date and time for display
     * @param {Date} date - Date object
     * @returns {string} Formatted date string
     */
    formatDateTime(date) {
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
     * Clear sync state for an account
     * @param {string} accountId - The account ID
     */
    clearAccountSync(accountId) {
        localStorage.removeItem(`${this.storagePrefix}${accountId}`);
        this.initializeAccount(accountId);
        console.log(`Cleared sync state for account ${accountId}`);
    }

    /**
     * Get all synced accounts
     * @returns {Array} Array of account IDs that have been synced
     */
    getAllSyncedAccounts() {
        const syncedAccounts = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.storagePrefix)) {
                const accountId = key.replace(this.storagePrefix, '');
                syncedAccounts.push({
                    accountId: accountId,
                    lastSync: localStorage.getItem(key)
                });
            }
        }
        return syncedAccounts;
    }

    /**
     * Debug function to check account state
     * @param {string} accountId - The account ID
     */
    debugAccountState(accountId) {
        console.log('=== Debug Account State ===');
        console.log('Account ID:', accountId);
        
        const elements = this.getAccountElements(accountId);
        const state = this.getAccountState(accountId);
        
        console.log('Elements found:', {
            emptyState: !!elements.emptyState,
            syncInfo: !!elements.syncInfo,
            mainText: !!elements.mainText,
            syncTimeElement: !!elements.syncTimeElement
        });
        
        console.log('Account state:', state);
        
        if (elements.mainText) {
            console.log('Current text:', elements.mainText.textContent);
        }
        
        return { elements, state };
    }
}

// Create global instance
window.campaignSyncManager = new CampaignSyncManager();

// Export for module use if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CampaignSyncManager;
} 