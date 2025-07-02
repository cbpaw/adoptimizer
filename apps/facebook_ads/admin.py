from django.contrib import admin
from .models import FacebookAdAccount, FacebookAd, FacebookCampaign, SelectedCampaign


@admin.register(FacebookAdAccount)
class FacebookAdAccountAdmin(admin.ModelAdmin):
    list_display = ['ad_account_name', 'ad_account_id', 'user', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['ad_account_name', 'ad_account_id', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'ad_account_id', 'ad_account_name', 'is_active')
        }),
        ('API Credentials', {
            'fields': ('app_id', 'app_secret', 'access_token'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FacebookCampaign)
class FacebookCampaignAdmin(admin.ModelAdmin):
    list_display = ['campaign_name', 'campaign_id', 'status', 'effective_status', 'objective', 'spend', 'impressions', 'clicks', 'ad_account', 'last_synced']
    list_filter = ['status', 'effective_status', 'objective', 'ad_account', 'last_synced']
    search_fields = ['campaign_name', 'campaign_id', 'ad_account__ad_account_name']
    readonly_fields = ['campaign_id', 'last_synced', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Campaign Information', {
            'fields': ('ad_account', 'campaign_id', 'campaign_name', 'objective')
        }),
        ('Status', {
            'fields': ('status', 'effective_status')
        }),
        ('Budget Information', {
            'fields': ('daily_budget', 'lifetime_budget', 'budget_remaining', 'spend_cap', 'bid_strategy', 'buying_type'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('impressions', 'clicks', 'spend', 'reach', 'frequency', 'ctr', 'cpm', 'cpc'),
            'classes': ('collapse',)
        }),
        ('Advanced Metrics', {
            'fields': ('purchase_roas', 'website_purchase_roas', 'link_url_clicks', 'inline_link_clicks', 'outbound_clicks'),
            'classes': ('collapse',)
        }),
        ('Complex Data', {
            'fields': ('actions_data', 'conversions_data', 'special_ad_categories'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('start_time', 'stop_time', 'created_time', 'updated_time', 'last_synced'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ad_account')


@admin.register(SelectedCampaign)
class SelectedCampaignAdmin(admin.ModelAdmin):
    list_display = ['user', 'campaign_name', 'campaign_status', 'ad_account_name', 'is_monitoring', 'created_at']
    list_filter = ['is_monitoring', 'campaign__status', 'campaign__ad_account', 'created_at']
    search_fields = ['user__email', 'campaign__campaign_name', 'campaign__ad_account__ad_account_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def campaign_name(self, obj):
        return obj.campaign.campaign_name
    campaign_name.short_description = 'Campaign Name'
    
    def campaign_status(self, obj):
        return obj.campaign.status
    campaign_status.short_description = 'Campaign Status'
    
    def ad_account_name(self, obj):
        return obj.campaign.ad_account.ad_account_name
    ad_account_name.short_description = 'Ad Account'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'campaign__ad_account')


@admin.register(FacebookAd)
class FacebookAdAdmin(admin.ModelAdmin):
    list_display = ['ad_name', 'ad_id', 'status', 'effective_status', 'campaign_name', 'spend', 'impressions', 'clicks', 'purchase_roas', 'last_synced']
    list_filter = ['status', 'effective_status', 'campaign_objective', 'ad_account', 'last_synced']
    search_fields = ['ad_name', 'ad_id', 'campaign_name', 'adset_name', 'creative_title']
    readonly_fields = ['ad_id', 'last_synced', 'created_time', 'updated_time']
    
    fieldsets = (
        ('Ad Information', {
            'fields': ('ad_account', 'ad_id', 'ad_name', 'status', 'effective_status', 'configured_status')
        }),
        ('Campaign & AdSet', {
            'fields': ('campaign_id', 'campaign_name', 'campaign_objective', 'adset_id', 'adset_name', 'optimization_goal', 'billing_event', 'bid_amount')
        }),
        ('Creative Information', {
            'fields': ('creative_id', 'creative_title', 'creative_body', 'creative_image_url', 'creative_video_id', 'call_to_action_type'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('impressions', 'clicks', 'spend', 'reach', 'frequency', 'ctr', 'cpm', 'cpc'),
            'classes': ('collapse',)
        }),
        ('Advanced Metrics', {
            'fields': ('purchase_roas', 'website_purchase_roas', 'link_url_clicks', 'inline_link_clicks', 'outbound_clicks', 'unique_clicks', 'unique_ctr'),
            'classes': ('collapse',)
        }),
        ('Video Engagement', {
            'fields': ('video_avg_time_watched', 'video_p25_watched', 'video_p50_watched', 'video_p75_watched', 'video_p100_watched'),
            'classes': ('collapse',)
        }),
        ('Quality Rankings', {
            'fields': ('quality_ranking', 'engagement_rate_ranking', 'conversion_rate_ranking'),
            'classes': ('collapse',)
        }),
        ('Complex Data', {
            'fields': ('actions_data', 'conversions_data', 'targeting_data', 'tracking_specs', 'conversion_specs', 'promoted_object'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_time', 'updated_time', 'last_synced'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ad_account')
