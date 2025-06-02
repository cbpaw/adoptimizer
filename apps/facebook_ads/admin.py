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
    list_display = ['campaign_name', 'campaign_id', 'status', 'effective_status', 'ad_account', 'start_time', 'last_synced']
    list_filter = ['status', 'effective_status', 'ad_account', 'last_synced']
    search_fields = ['campaign_name', 'campaign_id', 'ad_account__ad_account_name']
    readonly_fields = ['campaign_id', 'last_synced', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Campaign Information', {
            'fields': ('ad_account', 'campaign_id', 'campaign_name')
        }),
        ('Status', {
            'fields': ('status', 'effective_status')
        }),
        ('Timestamps', {
            'fields': ('start_time', 'last_synced', 'created_at', 'updated_at'),
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
    list_display = ['ad_name', 'ad_id', 'status', 'campaign_name', 'spend', 'impressions', 'clicks', 'last_synced']
    list_filter = ['status', 'objective', 'ad_account', 'last_synced']
    search_fields = ['ad_name', 'ad_id', 'campaign_name', 'adset_name']
    readonly_fields = ['ad_id', 'last_synced', 'created_time', 'updated_time']
    
    fieldsets = (
        ('Ad Information', {
            'fields': ('ad_account', 'ad_id', 'ad_name', 'status')
        }),
        ('Campaign & AdSet', {
            'fields': ('campaign_id', 'campaign_name', 'adset_id', 'adset_name', 'objective')
        }),
        ('Performance Metrics', {
            'fields': ('impressions', 'clicks', 'spend', 'ctr', 'cpm', 'cpc')
        }),
        ('Timestamps', {
            'fields': ('created_time', 'updated_time', 'last_synced'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ad_account')
