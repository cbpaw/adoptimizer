from django.contrib import admin
from .models import (
    FacebookAdAccount,
    FacebookCampaign,
    SelectedCampaign,
    FacebookAd,
    FacebookAdSet,
    FacebookCampaignInsights,
    FacebookAdInsights,
    DashboardPeriod,
    OptimizationStrategy,
    CampaignOptimization,
    OptimizationLog,
    DailyPeriod,
    OptimizationMetrics,
)


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


@admin.register(FacebookAdSet)
class FacebookAdSetAdmin(admin.ModelAdmin):
    list_display = ['adset_name', 'adset_id', 'status', 'effective_status', 'campaign', 'daily_budget', 'lifetime_budget', 'spend', 'impressions', 'clicks', 'last_synced']
    list_filter = ['status', 'effective_status', 'campaign__ad_account', 'optimization_goal', 'billing_event', 'last_synced']
    search_fields = ['adset_name', 'adset_id', 'campaign__campaign_name']
    readonly_fields = ['adset_id', 'last_synced', 'created_at', 'updated_at']
    
    fieldsets = (
        ('AdSet Information', {
            'fields': ('ad_account', 'campaign', 'adset_id', 'adset_name')
        }),
        ('Status', {
            'fields': ('status', 'effective_status', 'configured_status')
        }),
        ('Budget & Bidding', {
            'fields': ('daily_budget', 'lifetime_budget', 'bid_amount', 'bid_strategy', 'optimization_goal', 'billing_event'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('impressions', 'clicks', 'spend', 'reach', 'frequency', 'ctr', 'cpm', 'cpc'),
            'classes': ('collapse',)
        }),
        ('Conversion Metrics', {
            'fields': ('purchase_roas', 'website_purchase_roas'),
            'classes': ('collapse',)
        }),
        ('Targeting', {
            'fields': ('targeting_data',),
            'classes': ('collapse',)
        }),
        ('Complex Data', {
            'fields': ('actions_data', 'conversions_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('start_time', 'end_time', 'created_time', 'updated_time', 'last_synced'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ad_account', 'campaign')


@admin.register(FacebookCampaignInsights)
class FacebookCampaignInsightsAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'date_start', 'date_stop', 'impressions', 'clicks', 'spend', 'ctr', 'cpc', 'purchase_roas', 'purchases']
    list_filter = ['date_start', 'date_stop', 'campaign__ad_account', 'campaign__status']
    search_fields = ['campaign__campaign_name', 'campaign__campaign_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date_start'
    
    fieldsets = (
        ('Campaign & Period', {
            'fields': ('campaign', 'date_start', 'date_stop')
        }),
        ('Core Metrics', {
            'fields': ('impressions', 'clicks', 'spend', 'reach', 'frequency'),
        }),
        ('Calculated Metrics', {
            'fields': ('ctr', 'cpc', 'cpm'),
        }),
        ('Conversion Metrics', {
            'fields': ('purchase_roas', 'website_purchase_roas', 'purchase_value', 'purchases'),
        }),
        ('Additional Metrics', {
            'fields': ('link_clicks', 'inline_link_clicks', 'outbound_clicks', 'post_engagement', 'video_views', 'unique_clicks', 'unique_ctr'),
            'classes': ('collapse',)
        }),
        ('Video Metrics', {
            'fields': ('video_p25_watched', 'video_p50_watched', 'video_p75_watched', 'video_p100_watched', 'video_avg_time_watched'),
            'classes': ('collapse',)
        }),
        ('Complex Data', {
            'fields': ('actions_data', 'conversions_data'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign')


@admin.register(FacebookAdInsights)
class FacebookAdInsightsAdmin(admin.ModelAdmin):
    list_display = ['ad', 'campaign', 'date_start', 'date_stop', 'impressions', 'clicks', 'spend', 'ctr', 'cpc', 'purchase_roas']
    list_filter = ['date_start', 'date_stop', 'campaign__ad_account', 'ad__status']
    search_fields = ['ad__ad_name', 'ad__ad_id', 'campaign__campaign_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date_start'
    
    fieldsets = (
        ('Ad & Campaign & Period', {
            'fields': ('ad', 'adset', 'campaign', 'date_start', 'date_stop')
        }),
        ('Core Metrics', {
            'fields': ('impressions', 'clicks', 'spend', 'reach', 'frequency'),
        }),
        ('Calculated Metrics', {
            'fields': ('ctr', 'cpc', 'cpm'),
        }),
        ('Conversion Metrics', {
            'fields': ('purchase_roas', 'website_purchase_roas', 'purchase_value', 'purchases'),
        }),
        ('Additional Metrics', {
            'fields': ('link_clicks', 'inline_link_clicks', 'outbound_clicks', 'post_engagement', 'video_views', 'unique_clicks', 'unique_ctr'),
            'classes': ('collapse',)
        }),
        ('Video Metrics', {
            'fields': ('video_p25_watched', 'video_p50_watched', 'video_p75_watched', 'video_p100_watched', 'video_avg_time_watched'),
            'classes': ('collapse',)
        }),
        ('Complex Data', {
            'fields': ('actions_data', 'conversions_data'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ad', 'adset', 'campaign')


@admin.register(DashboardPeriod)
class DashboardPeriodAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'days', 'date_preset', 'is_custom', 'is_active', 'sort_order']
    list_filter = ['is_custom', 'is_active']
    search_fields = ['name', 'display_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['sort_order', 'name']

    fieldsets = (
        ('Period Configuration', {
            'fields': ('name', 'display_name', 'days', 'date_preset', 'sort_order')
        }),
        ('Settings', {
            'fields': ('is_custom', 'is_active'),
        }),
    )


@admin.register(OptimizationStrategy)
class OptimizationStrategyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['name', 'description', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Strategy Information', {
            'fields': ('user', 'name', 'description', 'is_active')
        }),
        ('Rules Configuration', {
            'fields': ('rules',),
            'description': 'JSON configuration for optimization rules'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(CampaignOptimization)
class CampaignOptimizationAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'strategy', 'user', 'is_active', 'date_enabled', 'optimization_start_date']
    list_filter = ['is_active', 'date_enabled', 'optimization_start_date', 'user']
    search_fields = ['campaign__campaign_name', 'strategy__name', 'user__email']
    readonly_fields = ['date_enabled', 'created_at', 'updated_at']
    date_hierarchy = 'date_enabled'

    fieldsets = (
        ('Campaign & Strategy', {
            'fields': ('user', 'campaign', 'strategy')
        }),
        ('Status', {
            'fields': ('is_active', 'optimization_start_date')
        }),
        ('Timestamps', {
            'fields': ('date_enabled', 'date_disabled', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'campaign', 'strategy')


@admin.register(OptimizationLog)
class OptimizationLogAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'strategy', 'action', 'check_time', 'spend', 'cpc', 'add_to_carts', 'purchases', 'roas', 'action_successful']
    list_filter = ['action', 'action_successful', 'check_time', 'strategy']
    search_fields = ['campaign__campaign_name', 'strategy__name', 'rule_triggered', 'reason']
    readonly_fields = ['check_time', 'created_at', 'updated_at']
    date_hierarchy = 'check_time'

    fieldsets = (
        ('Campaign & Strategy', {
            'fields': ('campaign_optimization', 'campaign', 'strategy')
        }),
        ('Check Information', {
            'fields': ('check_time', 'action', 'rule_triggered', 'reason')
        }),
        ('Metrics Snapshot', {
            'fields': ('spend', 'cpc', 'ctr', 'impressions', 'clicks', 'add_to_carts', 'purchases', 'roas'),
            'classes': ('collapse',)
        }),
        ('Result', {
            'fields': ('action_successful', 'error_message')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign', 'strategy', 'campaign_optimization')


@admin.register(DailyPeriod)
class DailyPeriodAdmin(admin.ModelAdmin):
    list_display = ['date', 'created_at']
    search_fields = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(OptimizationMetrics)
class OptimizationMetricsAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'period', 'spend', 'cpc', 'ctr', 'add_to_carts', 'purchases', 'roas', 'campaign_status']
    list_filter = ['period__date', 'campaign_status', 'campaign']
    search_fields = ['campaign__campaign_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'period__date'

    fieldsets = (
        ('Campaign & Period', {
            'fields': ('campaign', 'period', 'campaign_status')
        }),
        ('Core Metrics', {
            'fields': ('spend', 'cpc', 'cpm', 'ctr', 'impressions', 'clicks')
        }),
        ('Conversion Metrics', {
            'fields': ('add_to_carts', 'purchases', 'purchase_value', 'roas')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign', 'period')
