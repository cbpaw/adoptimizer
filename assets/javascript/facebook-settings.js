/**
 * Facebook Ads Settings Page Manager
 * Handles settings page functionality including token validation, account management, and modal interactions
 */

class FacebookSettingsManager {
    constructor() {
        this.csrfToken = this.getCSRFToken();
        this.init();
    }

    /**
     * Initialize the settings manager
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
        this.initializeTokenValidation();
        this.initializeAccountManagement();
        this.initializeModals();
        this.attachGlobalFunctions();
    }

    /**
     * Initialize tab switching functionality
     */
    initializeTabSwitching() {
        // Make switchTab globally available for onclick handlers
        window.switchTab = (tabName) => {
            // Hide all tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            
            // Show selected tab content
            const selectedTab = document.getElementById(`${tabName}-tab`);
            if (selectedTab) {
                selectedTab.style.display = 'block';
            }
            
            // Update tab button states
            document.querySelectorAll('[data-slot="tabs-trigger"]').forEach(button => {
                if (button.dataset.tab === tabName) {
                    button.setAttribute('data-state', 'active');
                    button.classList.add('bg-background', 'text-foreground', 'shadow-sm');
                    button.classList.remove('text-muted-foreground');
                } else {
                    button.setAttribute('data-state', 'inactive');
                    button.classList.remove('bg-background', 'text-foreground', 'shadow-sm');
                    button.classList.add('text-muted-foreground');
                }
            });
        };
    }

    /**
     * Initialize token validation
     */
    initializeTokenValidation() {
        window.validateToken = () => {
            console.log('validateToken called'); // Debug log
            const tokenInput = document.getElementById('access-token-input');
            const validateBtn = document.getElementById('validate-token-btn');
            
            console.log('Token input:', tokenInput); // Debug log
            console.log('Validate button:', validateBtn); // Debug log
            
            if (!tokenInput || !validateBtn) {
                console.error('Token input or validate button not found');
                console.error('Token input element:', tokenInput);
                console.error('Validate button element:', validateBtn);
                return;
            }
            
            const token = tokenInput.value.trim();
            if (!token) {
                window.showError('Voer een access token in');
                return;
            }
            
            // Show loading state
            validateBtn.disabled = true;
            validateBtn.innerHTML = '<span class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></span>Valideren...';
            
            this.performTokenValidation(token).finally(() => {
                validateBtn.disabled = false;
                validateBtn.innerHTML = '<i class="fas fa-check mr-1"></i>Token Valideren';
            });
        };

        window.clearTokenForm = () => {
            const tokenInput = document.getElementById('access-token-input');
            if (tokenInput) {
                tokenInput.value = '';
            }
            
            // Disable fetch accounts button
            const fetchBtn = document.getElementById('fetch-accounts-btn');
            if (fetchBtn) {
                fetchBtn.disabled = true;
            }
        };

        window.testAPI = () => {
            this.testAPIConnectivity();
        };
        
        // Auto-enable fetch button if token is present on page load
        this.checkInitialTokenState();
    }

    /**
     * Check if token is present on page load and enable fetch button
     */
    checkInitialTokenState() {
        const tokenInput = document.getElementById('access-token-input');
        const fetchBtn = document.getElementById('fetch-accounts-btn');
        
        if (tokenInput && fetchBtn && tokenInput.value.trim()) {
            fetchBtn.disabled = false;
            console.log('Token found on page load, fetch button enabled');
        }
    }

    /**
     * Perform token validation
     * @param {string} token - Access token to validate
     */
    async performTokenValidation(token) {
        try {
            const response = await fetch('/facebook-ads/api/test-token/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ access_token: token })
            });

            const data = await response.json();

            if (data.success) {
                window.showSuccess('Token succesvol gevalideerd!');
                
                // Enable fetch accounts button
                const fetchBtn = document.getElementById('fetch-accounts-btn');
                if (fetchBtn) {
                    fetchBtn.disabled = false;
                }
                
                // Refresh accounts list after successful validation
                setTimeout(() => {
                    this.refreshAccountsList();
                }, 1000);
            } else {
                window.showError('Token validatie mislukt: ' + data.message);
            }
        } catch (error) {
            console.error('Token validation error:', error);
            
            if (this.handleAuthenticationError(error)) {
                return;
            }
            
            window.showError('Er is een fout opgetreden bij het valideren van de token');
        }
    }

    /**
     * Initialize account management
     */
    initializeAccountManagement() {
        window.fetchAccountsModal = () => {
            this.openAccountSelectionModal();
        };

        window.refreshAccountStatus = (accountId) => {
            this.refreshSingleAccountStatus(accountId);
        };

        window.testAccountConnection = (accountId) => {
            this.testSingleAccountConnection(accountId);
        };

        // Initialize disconnect buttons
        document.querySelectorAll('.disconnect-account-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const accountId = e.target.getAttribute('data-account-id');
                const accountName = e.target.getAttribute('data-account-name');
                this.disconnectAccount(accountId, accountName);
            });
        });
    }

    /**
     * Initialize modal functionality
     */
    initializeModals() {
        window.closeAccountSelectionModal = () => {
            const modal = document.getElementById('account-selection-modal');
            if (modal) {
                modal.classList.add('hidden');
            }
        };

        window.connectSelectedAccountsFromModal = () => {
            this.connectSelectedAccounts();
        };

        window.closeDisconnectModal = () => {
            const modal = document.getElementById('disconnect-confirmation-modal');
            if (modal) {
                modal.classList.add('hidden');
            }
        };

        window.confirmDisconnectAccount = () => {
            this.performAccountDisconnect();
        };
    }

    /**
     * Open account selection modal
     */
    async openAccountSelectionModal() {
        const tokenInput = document.getElementById('access-token-input');
        if (!tokenInput || !tokenInput.value.trim()) {
            window.showError('Voer eerst een geldige access token in en valideer deze');
            return;
        }

        try {
            const response = await fetch('/facebook-ads/api/fetch-accounts/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ access_token: tokenInput.value.trim() })
            });

            const data = await response.json();

            if (data.success) {
                this.populateAccountSelectionModal(data.accounts);
                
                const modal = document.getElementById('account-selection-modal');
                if (modal) {
                    modal.classList.remove('hidden');
                }
            } else {
                window.showError('Fout bij ophalen accounts: ' + data.message);
            }
        } catch (error) {
            console.error('Error fetching accounts:', error);
            window.showError('Er is een fout opgetreden bij het ophalen van accounts');
        }
    }

    /**
     * Populate account selection modal with accounts
     * @param {Array} accounts - List of available accounts
     */
    populateAccountSelectionModal(accounts) {
        const container = document.getElementById('modal-accounts-list');
        const connectBtn = document.getElementById('connect-selected-btn');
        
        if (!container) return;

        if (accounts.length === 0) {
            container.innerHTML = '<p class="text-muted-foreground text-center py-4">Geen accounts gevonden</p>';
            this.updateConnectButton(connectBtn, 'no-accounts');
            return;
        }

        const existingAccountIds = this.getExistingAccountIds();
        console.log('Existing account IDs:', existingAccountIds); // Debug log
        console.log('Available accounts:', accounts.map(a => a.id)); // Debug log
        
        // Filter out already connected accounts
        const filteredAccounts = accounts.filter(account => !existingAccountIds.includes(account.id));
        const connectedAccounts = accounts.filter(account => existingAccountIds.includes(account.id));

        if (filteredAccounts.length === 0) {
            // All accounts are already connected
            let html = '';
            
            if (connectedAccounts.length > 0) {
                html = `
                    <div class="space-y-3">
                        <p class="text-muted-foreground text-center py-2">Alle beschikbare accounts zijn al gekoppeld:</p>
                        ${connectedAccounts.map(account => `
                            <div class="flex items-center gap-3 p-3 rounded-lg border bg-muted/50">
                                <div class="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                                    <i class="fas fa-check text-white text-xs"></i>
                                </div>
                                <div class="flex-1">
                                    <div class="font-medium text-muted-foreground">${account.name}</div>
                                    <div class="text-sm text-muted-foreground">ID: ${account.id} • Gekoppeld</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                html = '<p class="text-muted-foreground text-center py-4">Alle beschikbare accounts zijn al gekoppeld</p>';
            }
            
            container.innerHTML = html;
            this.updateConnectButton(connectBtn, 'all-connected');
            return;
        }

        // Show available accounts for connection and already connected ones
        let html = '';
        
        if (filteredAccounts.length > 0) {
            html += `
                <div class="space-y-3">
                    <p class="text-sm font-medium text-foreground">Beschikbare accounts:</p>
                    ${filteredAccounts.map(account => `
                        <label class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-muted">
                            <input type="checkbox" value="${account.id}" class="account-checkbox">
                            <div class="flex-1">
                                <div class="font-medium">${account.name}</div>
                                <div class="text-sm text-muted-foreground">ID: ${account.id}</div>
                            </div>
                        </label>
                    `).join('')}
                </div>
            `;
        }
        
        if (connectedAccounts.length > 0) {
            html += `
                <div class="space-y-3 mt-6">
                    <p class="text-sm font-medium text-muted-foreground">Al gekoppelde accounts:</p>
                    ${connectedAccounts.map(account => `
                        <div class="flex items-center gap-3 p-3 rounded-lg border bg-muted/50">
                            <div class="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                                <i class="fas fa-check text-white text-xs"></i>
                            </div>
                            <div class="flex-1">
                                <div class="font-medium text-muted-foreground">${account.name}</div>
                                <div class="text-sm text-muted-foreground">ID: ${account.id} • Gekoppeld</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        container.innerHTML = html;

        // Update connect button state when selections change
        const checkboxes = container.querySelectorAll('.account-checkbox');
        
        // Initial button state
        this.updateConnectButton(connectBtn, 'available', 0);
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const selectedCount = container.querySelectorAll('.account-checkbox:checked').length;
                this.updateConnectButton(connectBtn, 'available', selectedCount);
                
                // Update selected count display
                const countElement = document.getElementById('selected-count');
                if (countElement) {
                    countElement.textContent = selectedCount;
                }
            });
        });
    }

    /**
     * Update connect button based on state
     * @param {HTMLElement} button - Connect button element
     * @param {string} state - Button state ('available', 'all-connected', 'no-accounts')
     * @param {number} selectedCount - Number of selected accounts
     */
    updateConnectButton(button, state, selectedCount = 0) {
        if (!button) return;
        
        switch (state) {
            case 'all-connected':
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-arrow-right mr-1"></i>Ga Door naar Campagnes';
                button.onclick = () => {
                    window.closeAccountSelectionModal();
                    // Navigate to campaigns page
                    window.location.href = '/facebook-ads/campaigns/';
                };
                break;
                
            case 'no-accounts':
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-exclamation-triangle mr-1"></i>Geen Accounts Beschikbaar';
                button.onclick = null;
                break;
                
            case 'available':
            default:
                button.disabled = selectedCount === 0;
                button.innerHTML = '<i class="fas fa-link mr-1"></i>Geselecteerde Accounts Koppelen';
                button.onclick = () => this.connectSelectedAccounts();
                break;
        }
    }

    /**
     * Get existing account IDs
     * @returns {Array} Array of existing account IDs
     */
    getExistingAccountIds() {
        const dataElement = document.getElementById('existing-accounts-data');
        if (dataElement && dataElement.dataset.accountIds) {
            return dataElement.dataset.accountIds.split(',').filter(id => id.trim());
        }
        return [];
    }

    /**
     * Connect selected accounts
     */
    async connectSelectedAccounts() {
        const container = document.getElementById('modal-accounts-list');
        const selectedIds = Array.from(container.querySelectorAll('.account-checkbox:checked'))
            .map(checkbox => checkbox.value);

        if (selectedIds.length === 0) {
            window.showError('Selecteer ten minste één account');
            return;
        }

        const tokenInput = document.getElementById('access-token-input');
        if (!tokenInput || !tokenInput.value.trim()) {
            window.showError('Access token ontbreekt');
            return;
        }

        const connectBtn = document.getElementById('connect-selected-btn');
        if (connectBtn) {
            connectBtn.disabled = true;
            connectBtn.innerHTML = '<span class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>Koppelen...';
        }

        let successCount = 0;
        let errorCount = 0;
        const results = [];

        // Connect accounts one by one since the API expects single account connections
        for (const accountId of selectedIds) {
            try {
                const response = await fetch('/facebook-ads/api/connect-account/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    },
                    body: JSON.stringify({ 
                        access_token: tokenInput.value.trim(),
                        account_id: accountId 
                    })
                });

                const data = await response.json();

                if (data.success) {
                    successCount++;
                    results.push(`✓ Account ${accountId}: ${data.message}`);
                } else {
                    errorCount++;
                    results.push(`✗ Account ${accountId}: ${data.message}`);
                }
            } catch (error) {
                errorCount++;
                results.push(`✗ Account ${accountId}: ${error.message}`);
                console.error(`Error connecting account ${accountId}:`, error);
            }
        }

        // Show final results
        if (successCount > 0 && errorCount === 0) {
            window.showSuccess(`Alle ${successCount} accounts succesvol gekoppeld!`);
        } else if (successCount > 0 && errorCount > 0) {
            window.showWarning(`${successCount} accounts gekoppeld, ${errorCount} mislukt. Check de console voor details.`);
            console.log('Connection results:', results);
        } else {
            window.showError(`Koppelen mislukt voor alle ${errorCount} accounts. Check de console voor details.`);
            console.log('Connection results:', results);
        }

        window.closeAccountSelectionModal();
        
        // Refresh accounts list if any were successful
        if (successCount > 0) {
            setTimeout(() => {
                this.refreshAccountsList();
            }, 1000);
        }

        if (connectBtn) {
            connectBtn.disabled = false;
            connectBtn.innerHTML = '<i class="fas fa-link mr-1"></i>Geselecteerde Accounts Koppelen';
        }
    }

    /**
     * Disconnect account
     * @param {string} accountId - Account ID to disconnect
     * @param {string} accountName - Account name for confirmation
     */
    disconnectAccount(accountId, accountName) {
        // Store for confirmation
        this.disconnectData = { accountId, accountName };
        
        // Update modal content
        const modalAccountName = document.getElementById('disconnect-account-name');
        if (modalAccountName) {
            modalAccountName.textContent = accountName;
        }
        
        // Show modal
        const modal = document.getElementById('disconnect-confirmation-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    /**
     * Perform account disconnect
     */
    async performAccountDisconnect() {
        if (!this.disconnectData) return;

        const { accountId, accountName } = this.disconnectData;
        
        try {
            const response = await fetch('/facebook-ads/api/disconnect-account/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ account_id: accountId })
            });

            const data = await response.json();

            if (data.success) {
                window.showSuccess(`Account "${accountName}" succesvol ontkoppeld`);
                window.closeDisconnectModal();
                
                // Refresh accounts list
                setTimeout(() => {
                    this.refreshAccountsList();
                }, 1000);
            } else {
                window.showError('Fout bij ontkoppelen: ' + data.message);
            }
        } catch (error) {
            console.error('Error disconnecting account:', error);
            window.showError('Er is een fout opgetreden bij het ontkoppelen van het account');
        }
        
        this.disconnectData = null;
    }

    /**
     * Refresh accounts list dynamically
     */
    async refreshAccountsList() {
        const accountsContainer = document.querySelector('#accounts-tab .grid');
        const accountsCountSpan = document.querySelector('#accounts-tab h3 + span');
        
        if (!accountsContainer) return;

        try {
            const response = await fetch(window.location.href, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            });

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            const newAccountsContainer = doc.querySelector('#accounts-tab .grid');
            const newAccountsCount = doc.querySelector('#accounts-tab h3 + span');
            const newExistingAccountsData = doc.querySelector('#existing-accounts-data');
            
            if (newAccountsContainer && accountsContainer) {
                accountsContainer.innerHTML = newAccountsContainer.innerHTML;
                
                if (newAccountsCount && accountsCountSpan) {
                    accountsCountSpan.textContent = newAccountsCount.textContent;
                }
                
                if (newExistingAccountsData) {
                    const existingDataElement = document.getElementById('existing-accounts-data');
                    if (existingDataElement) {
                        existingDataElement.dataset.accountIds = newExistingAccountsData.dataset.accountIds;
                    }
                }
                
                // Re-attach event listeners for disconnect buttons
                this.reattachDisconnectListeners();
                
                // Check if we need to show empty state
                this.updateEmptyState(accountsContainer);
            }
        } catch (error) {
            console.error('Error refreshing accounts list:', error);
            window.showError('Fout bij het bijwerken van de accounts lijst');
            
            setTimeout(() => {
                location.reload();
            }, 2000);
        }
    }

    /**
     * Re-attach disconnect button listeners
     */
    reattachDisconnectListeners() {
        document.querySelectorAll('.disconnect-account-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const accountId = e.target.getAttribute('data-account-id');
                const accountName = e.target.getAttribute('data-account-name');
                this.disconnectAccount(accountId, accountName);
            });
        });
    }

    /**
     * Update empty state display
     * @param {HTMLElement} container - Accounts container
     */
    updateEmptyState(container) {
        const accountCards = container.querySelectorAll('[data-slot="card"]');
        if (accountCards.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-16">
                    <div class="mx-auto w-24 h-24 bg-muted rounded-full flex items-center justify-center mb-6">
                        <i class="fab fa-facebook text-4xl text-muted-foreground"></i>
                    </div>
                    <h3 class="text-xl font-medium mb-2">Geen Ad Accounts Gekoppeld</h3>
                    <p class="text-muted-foreground mb-6 max-w-md mx-auto">
                        Voeg uw Facebook access token toe om ad accounts aan het dashboard te koppelen en uw campagnes te beheren.
                    </p>
                    <button 
                        onclick="switchTab('token')" 
                        class="cursor-pointer inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-[color,box-shadow] disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow-xs hover:bg-primary/90 h-10 px-6"
                        data-slot="button"
                    >
                        <i class="fas fa-plus mr-2"></i>
                        Eerste Account Toevoegen
                    </button>
                </div>
            `;
        }
    }

    /**
     * Refresh single account status
     * @param {string} accountId - Account ID to refresh
     */
    /**
     * Refresh single account status
    async refreshSingleAccountStatus(accountId) {
        console.log('Refreshing status for account:', accountId);
        
        try {
            const response = await fetch('/facebook-ads/api/test-account-connection/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ account_id: accountId })
            });

            const data = await response.json();

            if (data.success) {
                window.showSuccess(`Account status bijgewerkt!\n\nAccount: ${data.account_name}\nStatus: ${data.account_status}`);
                
                // Refresh the accounts list to update the UI
                setTimeout(() => {
                    this.refreshAccountsList();
                }, 1000);
            } else {
                window.showWarning(`Status bijwerken mislukt: ${data.message}`);
            }
        } catch (error) {
            console.error('Error refreshing account status:', error);
            window.showError('Er is een fout opgetreden bij het bijwerken van de account status');
    /**
     * Test single account connection
     * @param {string} accountId - Account ID to test
     */
    /**
     * Test single account connection
     * @param {string} accountId - Account ID to test
     */
    async testSingleAccountConnection(accountId) {
        console.log('Testing connection for account:', accountId);
        
        try {
            const response = await fetch('/facebook-ads/api/test-account-connection/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ account_id: accountId })
            });

            const data = await response.json();

            if (data.success) {
                window.showSuccess(`Verbinding succesvol getest!\n\nAccount: ${data.account_name}\nStatus: ${data.account_status}`);
            } else {
                window.showError(`Verbindingstest mislukt!\n\n${data.message}`);
            }
        } catch (error) {
            console.error('Error testing account connection:', error);
            window.showError('Er is een fout opgetreden bij het testen van de account verbinding');
        }
    }
    /**
     * Test API connectivity
     */
    async testAPIConnectivity() {
        console.log('Testing API connectivity...');
        
        try {
            const response = await fetch('/facebook-ads/api/test-token/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify({ access_token: 'test' })
            });

            console.log('Test API response status:', response.status);
            const text = await response.text();
            console.log('Test API response text:', text);
            
            window.showInfo('API connectivity test completed - check console for details');
        } catch (error) {
            console.error('API connectivity test failed:', error);
            
            if (this.handleAuthenticationError(error)) {
                return;
            }
            
            window.showError('API connectivity test failed: ' + error.message);
        }
    }

    /**
     * Handle authentication errors
     * @param {Error} error - Error object
     * @returns {boolean} Whether error was handled
     */
    handleAuthenticationError(error) {
        // Check if it's an authentication error and handle redirect
        if (error.status === 401 || error.status === 403) {
            window.location.href = '/accounts/login/';
            return true;
        }
        return false;
    }

    /**
     * Attach global functions for onclick handlers
     */
    attachGlobalFunctions() {
        // All functions are already defined in the respective initialization methods:
        // window.switchTab
        // window.validateToken
        // window.clearTokenForm
        // window.testAPI
        // window.fetchAccountsModal
        // window.refreshAccountStatus
        // window.testAccountConnection
        // window.closeAccountSelectionModal
        // window.connectSelectedAccountsFromModal
        // window.closeDisconnectModal
        // window.confirmDisconnectAccount
        
        console.log('Facebook Settings Manager initialized successfully');
    }
}

// Initialize when DOM is ready
new FacebookSettingsManager(); 