/**
 * Comprehensive Data Display Module
 * Handles advanced Facebook campaign and ads data visualization
 */

class ComprehensiveDataDisplay {
    constructor() {
        this.comprehensiveDataLoaded = false;
        this.comprehensiveCampaigns = [];
        this.comprehensiveAds = [];
        this.currentDataView = 'basic';
        this.csrfToken = this.getCsrfToken();
        
        // Bind methods
        this.syncComprehensiveData = this.syncComprehensiveData.bind(this);
        this.changeDataView = this.changeDataView.bind(this);
        this.showCampaignDetails = this.showCampaignDetails.bind(this);
        this.changeCampaignFilter = this.changeCampaignFilter.bind(this);
        
        // Initialize
        this.init();
    }
    
    getCsrfToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenElement ? tokenElement.value : '';
    }
    
    init() {
        // Make functions globally available
        window.syncComprehensiveData = this.syncComprehensiveData;
        window.changeDataView = this.changeDataView;
        window.showCampaignDetails = this.showCampaignDetails;
        window.changeCampaignFilter = this.changeCampaignFilter;
        
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
    }
    
    onDOMReady() {
        // Auto-load comprehensive data if campaigns exist
        const campaignStatsCount = document.querySelectorAll('.campaign-row').length;
        if (campaignStatsCount > 0) {
            this.loadComprehensiveData();
        }
        
        // Initialize basic campaign filtering
        this.initializeBasicFiltering();
    }
    
    async syncComprehensiveData() {
        const loadingDiv = document.getElementById('loading-comprehensive');
        if (loadingDiv) {
            loadingDiv.classList.remove('hidden');
        }

        try {
            // Get accounts from data attribute or global variable
            const accountsData = document.querySelector('[data-facebook-accounts]');
            let accounts = [];
            
            if (accountsData) {
                accounts = JSON.parse(accountsData.dataset.facebookAccounts);
            } else if (window.facebookAccounts) {
                accounts = window.facebookAccounts;
            }
            
            for (const account of accounts) {
                try {
                    // Sync campaigns
                    const campaignsResponse = await fetch('/facebook-ads/api/comprehensive-sync-campaigns/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.csrfToken
                        },
                        body: JSON.stringify({ account_id: account.id })
                    });

                    // Sync ads
                    const adsResponse = await fetch('/facebook-ads/api/comprehensive-sync-ads/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.csrfToken
                        },
                        body: JSON.stringify({ account_id: account.id })
                    });

                    const campaignsData = await campaignsResponse.json();
                    const adsData = await adsResponse.json();

                    if (campaignsData.success && adsData.success) {
                        this.showSuccess(`Synced ${campaignsData.synced_count} campaigns and ${adsData.synced_count} ads for ${account.ad_account_name}`);
                    }
                } catch (accountError) {
                    console.error(`Error syncing account ${account.id}:`, accountError);
                    this.showError(`Failed to sync account ${account.ad_account_name}`);
                }
            }

            // Load comprehensive data
            await this.loadComprehensiveData();
            
        } catch (error) {
            console.error('Error syncing comprehensive data:', error);
            this.showError('Failed to sync comprehensive data');
        } finally {
            if (loadingDiv) {
                loadingDiv.classList.add('hidden');
            }
        }
    }

    async loadComprehensiveData() {
        try {
            // Load campaigns
            const filterSelect = document.getElementById('campaign-type-filter');
            const filterValue = filterSelect ? filterSelect.value : 'active';
            
            const campaignsResponse = await fetch('/facebook-ads/api/comprehensive-campaign-data/?' + 
                new URLSearchParams({ filter: filterValue }));
            
            const campaignsData = await campaignsResponse.json();
            
            if (campaignsData.success) {
                this.comprehensiveCampaigns = campaignsData.campaigns;
                this.updateComprehensiveCampaignsTable();
            }

            // Load ads
            const adsResponse = await fetch('/facebook-ads/api/comprehensive-ads-data/?limit=100');
            const adsData = await adsResponse.json();
            
            if (adsData.success) {
                this.comprehensiveAds = adsData.ads;
                this.updateComprehensiveAdsTable();
            }

            this.comprehensiveDataLoaded = true;
            this.updateOverviewCards();
            
        } catch (error) {
            console.error('Error loading comprehensive data:', error);
            this.showError('Failed to load comprehensive data');
        }
    }

    changeDataView(view) {
        this.currentDataView = view;
        
        // Hide all views
        const basicView = document.getElementById('basic-view');
        const comprehensiveView = document.getElementById('comprehensive-view');
        const adsView = document.getElementById('ads-view');
        
        if (basicView) basicView.classList.add('hidden');
        if (comprehensiveView) comprehensiveView.classList.add('hidden');
        if (adsView) adsView.classList.add('hidden');
        
        // Show selected view
        if (view === 'basic' && basicView) {
            basicView.classList.remove('hidden');
        } else if (view === 'comprehensive' && comprehensiveView) {
            comprehensiveView.classList.remove('hidden');
            if (!this.comprehensiveDataLoaded) {
                this.loadComprehensiveData();
            }
        } else if (view === 'ads' && adsView) {
            adsView.classList.remove('hidden');
            if (!this.comprehensiveDataLoaded) {
                this.loadComprehensiveData();
            }
        }
    }

    updateComprehensiveCampaignsTable() {
        const tbody = document.getElementById('comprehensive-campaigns-table');
        if (!tbody) return;
        
        tbody.innerHTML = this.comprehensiveCampaigns.map(campaign => `
            <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                <td class="p-4 align-middle">
                    <div>
                        <div class="font-medium">${this.escapeHtml(campaign.campaign_name)}</div>
                        <div class="text-sm text-muted-foreground">${campaign.objective || 'N/A'}</div>
                        <div class="text-xs text-muted-foreground">${this.escapeHtml(campaign.account_name)}</div>
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm">
                        ${campaign.daily_budget ? `<div>Daily: €${campaign.daily_budget}</div>` : ''}
                        ${campaign.lifetime_budget ? `<div>Lifetime: €${campaign.lifetime_budget}</div>` : ''}
                        ${campaign.budget_remaining ? `<div>Remaining: €${campaign.budget_remaining}</div>` : ''}
                        <div class="text-xs text-muted-foreground">${campaign.bid_strategy || ''} ${campaign.buying_type || ''}</div>
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm">
                        <div>€${campaign.spend.toFixed(2)} | ${campaign.impressions.toLocaleString()} imp</div>
                        <div>${campaign.clicks.toLocaleString()} clicks | ${campaign.reach.toLocaleString()} reach</div>
                        <div>CTR: ${campaign.ctr.toFixed(2)}% | CPC: €${campaign.cpc.toFixed(3)}</div>
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm">
                        <div>ROAS: ${campaign.purchase_roas.toFixed(2)}x</div>
                        <div>Link clicks: ${campaign.link_url_clicks.toLocaleString()}</div>
                        <div>Outbound: ${campaign.outbound_clicks.toLocaleString()}</div>
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm">
                        ${this.renderConversionsData(campaign.conversions_data)}
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <button onclick="showCampaignDetails('${campaign.campaign_id}')" 
                            class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-8 px-3">
                        Details
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updateComprehensiveAdsTable() {
        const tbody = document.getElementById('comprehensive-ads-table');
        if (!tbody) return;
        
        tbody.innerHTML = this.comprehensiveAds.map(ad => `
            <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                <td class="p-4 align-middle">
                    <div>
                        <div class="font-medium">${this.escapeHtml(ad.ad_name)}</div>
                        <div class="text-sm text-muted-foreground">${this.escapeHtml(ad.campaign_name)}</div>
                        <div class="text-xs text-muted-foreground">${ad.status} | ${ad.effective_status}</div>
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm max-w-xs">
                        ${ad.creative_title ? `<div class="font-medium">${this.escapeHtml(ad.creative_title.substring(0, 50))}...</div>` : ''}
                        ${ad.creative_body ? `<div class="text-muted-foreground">${this.escapeHtml(ad.creative_body.substring(0, 80))}...</div>` : ''}
                        ${ad.call_to_action_type ? `<div class="text-xs">CTA: ${ad.call_to_action_type}</div>` : ''}
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm">
                        <div>€${ad.spend.toFixed(2)} | ${ad.impressions.toLocaleString()} imp</div>
                        <div>${ad.clicks.toLocaleString()} clicks | ROAS: ${ad.purchase_roas.toFixed(2)}x</div>
                        <div>CTR: ${ad.ctr.toFixed(2)}% | CPC: €${ad.cpc.toFixed(3)}</div>
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm">
                        ${ad.video_p25_watched > 0 ? `<div>25%: ${ad.video_p25_watched}</div>` : ''}
                        ${ad.video_p50_watched > 0 ? `<div>50%: ${ad.video_p50_watched}</div>` : ''}
                        ${ad.video_p100_watched > 0 ? `<div>100%: ${ad.video_p100_watched}</div>` : ''}
                        ${ad.video_avg_time_watched > 0 ? `<div>Avg: ${ad.video_avg_time_watched.toFixed(1)}s</div>` : ''}
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm">
                        ${ad.quality_ranking ? `<div>Quality: ${ad.quality_ranking}</div>` : ''}
                        ${ad.engagement_rate_ranking ? `<div>Engagement: ${ad.engagement_rate_ranking}</div>` : ''}
                        ${ad.conversion_rate_ranking ? `<div>Conversion: ${ad.conversion_rate_ranking}</div>` : ''}
                    </div>
                </td>
                <td class="p-4 align-middle">
                    <div class="text-sm">
                        ${Object.keys(ad.targeting_data).length > 0 ? 
                            `<div class="text-xs text-muted-foreground">Targeting configured</div>` : 
                            '<div class="text-xs text-muted-foreground">No targeting data</div>'
                        }
                        ${ad.optimization_goal ? `<div class="text-xs">Goal: ${ad.optimization_goal}</div>` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    }

    updateOverviewCards() {
        if (this.comprehensiveCampaigns.length === 0) return;

        const totalSpend = this.comprehensiveCampaigns.reduce((sum, c) => sum + c.spend, 0);
        const totalImpressions = this.comprehensiveCampaigns.reduce((sum, c) => sum + c.impressions, 0);
        const totalClicks = this.comprehensiveCampaigns.reduce((sum, c) => sum + c.clicks, 0);
        const avgCpc = this.comprehensiveCampaigns.reduce((sum, c) => sum + c.cpc, 0) / this.comprehensiveCampaigns.length;
        const avgRoas = this.comprehensiveCampaigns.reduce((sum, c) => sum + c.purchase_roas, 0) / this.comprehensiveCampaigns.length;

        const elements = {
            'total-spend': `€${totalSpend.toFixed(2)}`,
            'total-impressions': totalImpressions.toLocaleString(),
            'total-clicks': totalClicks.toLocaleString(),
            'avg-cpc': `€${avgCpc.toFixed(3)}`,
            'avg-roas': `${avgRoas.toFixed(2)}x`,
            'total-campaigns': `${this.comprehensiveCampaigns.length} campagne(s)`
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    async showCampaignDetails(campaignId) {
        try {
            const response = await fetch('/facebook-ads/api/campaign-detailed-insights/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ campaign_id: campaignId })
            });

            const data = await response.json();
            
            if (data.success) {
                console.log('Campaign insights:', data.campaign_insights);
                this.showSuccess('Campaign details loaded - check console for full data');
            } else {
                this.showError(data.message || 'Failed to load campaign details');
            }
        } catch (error) {
            console.error('Error loading campaign details:', error);
            this.showError('Failed to load campaign details');
        }
    }

    changeCampaignFilter(filter) {
        const url = new URL(window.location);
        url.searchParams.set('filter', filter);
        window.location = url;
    }

    initializeBasicFiltering() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        const campaignRows = document.querySelectorAll('.campaign-row');
        const searchInput = document.getElementById('search-campaigns');
        const campaignCount = document.getElementById('campaign-count');

        // Filter by status
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Update active filter button
                filterButtons.forEach(btn => {
                    btn.classList.remove('bg-primary', 'text-primary-foreground');
                    btn.classList.add('bg-secondary', 'text-secondary-foreground');
                });
                this.classList.remove('bg-secondary', 'text-secondary-foreground');
                this.classList.add('bg-primary', 'text-primary-foreground');

                const status = this.dataset.status;
                filterCampaigns(status, searchInput ? searchInput.value : '');
            });
        });

        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                const activeFilter = document.querySelector('.filter-btn.bg-primary')?.dataset.status || 'all';
                filterCampaigns(activeFilter, this.value);
            });
        }

        function filterCampaigns(status, searchTerm) {
            let visibleCount = 0;
            
            campaignRows.forEach(row => {
                const rowStatus = row.dataset.status;
                const campaignName = row.dataset.campaignName;
                
                const statusMatch = status === 'all' || rowStatus === status;
                const searchMatch = campaignName.includes(searchTerm.toLowerCase());
                
                if (statusMatch && searchMatch) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            if (campaignCount) {
                campaignCount.textContent = `${visibleCount} campagne(s)`;
            }
        }

        // Initialize first filter as active
        if (filterButtons.length > 0) {
            filterButtons[0].click();
        }
    }

    renderConversionsData(conversionsData) {
        if (!conversionsData || Object.keys(conversionsData).length === 0) {
            return '<div class="text-muted-foreground">Geen conversies</div>';
        }
        
        return Object.entries(conversionsData).slice(0, 2).map(([type, data]) => 
            `<div>${type}: ${data.value || data}</div>`
        ).join('');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showSuccess(message) {
        if (window.showSuccess) {
            window.showSuccess(message);
        } else {
            console.log('Success:', message);
        }
    }

    showError(message) {
        if (window.showError) {
            window.showError(message);
        } else {
            console.error('Error:', message);
        }
    }
}

// Initialize the comprehensive data display
window.comprehensiveDataDisplay = new ComprehensiveDataDisplay(); 