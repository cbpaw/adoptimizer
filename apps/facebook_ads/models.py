from django.db import models
from django.contrib.auth import get_user_model
from apps.utils.models import BaseModel

User = get_user_model()


class FacebookAdAccount(BaseModel):
    """Model to store Facebook Ad Account information"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='facebook_ad_accounts')
    ad_account_id = models.CharField(max_length=100)
    ad_account_name = models.CharField(max_length=255, blank=True)
    access_token = models.TextField()
    app_id = models.CharField(max_length=100)
    app_secret = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'ad_account_id']
    
    def __str__(self):
        return f"{self.ad_account_name} ({self.ad_account_id})"


class FacebookCampaign(BaseModel):
    """Model to store Facebook/Meta campaigns with comprehensive data"""
    ad_account = models.ForeignKey(FacebookAdAccount, on_delete=models.CASCADE, related_name='campaigns')
    campaign_id = models.CharField(max_length=100, unique=True)
    campaign_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    effective_status = models.CharField(max_length=50, blank=True)
    objective = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    start_time = models.DateTimeField(null=True, blank=True)
    stop_time = models.DateTimeField(null=True, blank=True)
    created_time = models.DateTimeField(null=True, blank=True)
    updated_time = models.DateTimeField(null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    
    # Budget information
    daily_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    lifetime_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_remaining = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    spend_cap = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bid_strategy = models.CharField(max_length=100, blank=True)
    buying_type = models.CharField(max_length=100, blank=True)
    
    # Performance metrics
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reach = models.BigIntegerField(default=0)
    frequency = models.FloatField(default=0)
    ctr = models.FloatField(default=0)  # Click-through rate
    cpm = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Cost per mille
    cpc = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Cost per click
    
    # Advanced metrics
    purchase_roas = models.FloatField(default=0)  # Return on ad spend
    website_purchase_roas = models.FloatField(default=0)
    link_url_clicks = models.BigIntegerField(default=0)
    inline_link_clicks = models.BigIntegerField(default=0)
    outbound_clicks = models.BigIntegerField(default=0)
    
    # Complex data as JSON
    actions_data = models.JSONField(default=dict, blank=True)
    conversions_data = models.JSONField(default=dict, blank=True)
    special_ad_categories = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.campaign_name} ({self.campaign_id})"


class SelectedCampaign(BaseModel):
    """Model to track which campaigns a user has selected for monitoring"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='selected_campaigns')
    campaign = models.ForeignKey(FacebookCampaign, on_delete=models.CASCADE, related_name='selections')
    is_monitoring = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'campaign']
    
    def __str__(self):
        return f"{self.user.email} - {self.campaign.campaign_name}"


class FacebookAd(BaseModel):
    """Model to cache comprehensive Facebook Ad data"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('DELETED', 'Deleted'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('DISAPPROVED', 'Disapproved'),
        ('PREAPPROVED', 'Preapproved'),
        ('PENDING_BILLING_INFO', 'Pending Billing Info'),
        ('CAMPAIGN_PAUSED', 'Campaign Paused'),
        ('ARCHIVED', 'Archived'),
    ]

    ad_account = models.ForeignKey(FacebookAdAccount, on_delete=models.CASCADE, related_name='ads')
    ad_id = models.CharField(max_length=100, unique=True)
    ad_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    effective_status = models.CharField(max_length=50, blank=True)
    configured_status = models.CharField(max_length=50, blank=True)
    
    # Campaign and Adset information
    campaign_id = models.CharField(max_length=100, blank=True)
    campaign_name = models.CharField(max_length=255, blank=True)
    campaign_objective = models.CharField(max_length=100, blank=True)
    adset_id = models.CharField(max_length=100, blank=True)
    adset_name = models.CharField(max_length=255, blank=True)
    optimization_goal = models.CharField(max_length=100, blank=True)
    billing_event = models.CharField(max_length=100, blank=True)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Creative information
    creative_id = models.CharField(max_length=100, blank=True)
    creative_title = models.TextField(blank=True)
    creative_body = models.TextField(blank=True)
    creative_image_url = models.URLField(blank=True)
    creative_video_id = models.CharField(max_length=100, blank=True)
    call_to_action_type = models.CharField(max_length=100, blank=True)
    
    # Performance metrics
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reach = models.BigIntegerField(default=0)
    frequency = models.FloatField(default=0)
    ctr = models.FloatField(default=0)  # Click-through rate
    cpm = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Cost per mille
    cpc = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Cost per click
    
    # Advanced metrics
    purchase_roas = models.FloatField(default=0)  # Return on ad spend
    website_purchase_roas = models.FloatField(default=0)
    link_url_clicks = models.BigIntegerField(default=0)
    inline_link_clicks = models.BigIntegerField(default=0)
    outbound_clicks = models.BigIntegerField(default=0)
    unique_clicks = models.BigIntegerField(default=0)
    unique_ctr = models.FloatField(default=0)
    
    # Video engagement metrics
    video_avg_time_watched = models.FloatField(default=0)
    video_p25_watched = models.BigIntegerField(default=0)
    video_p50_watched = models.BigIntegerField(default=0)
    video_p75_watched = models.BigIntegerField(default=0)
    video_p100_watched = models.BigIntegerField(default=0)
    
    # Quality rankings
    quality_ranking = models.CharField(max_length=50, blank=True)
    engagement_rate_ranking = models.CharField(max_length=50, blank=True)
    conversion_rate_ranking = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_time = models.DateTimeField(null=True, blank=True)
    updated_time = models.DateTimeField(null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    
    # Complex data as JSON
    actions_data = models.JSONField(default=dict, blank=True)
    conversions_data = models.JSONField(default=dict, blank=True)
    targeting_data = models.JSONField(default=dict, blank=True)
    tracking_specs = models.JSONField(default=list, blank=True)
    conversion_specs = models.JSONField(default=list, blank=True)
    promoted_object = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Facebook Ad"
        verbose_name_plural = "Facebook Ads"
        ordering = ['-last_synced']

    def __str__(self):
        return f"{self.ad_name} ({self.ad_id})"
