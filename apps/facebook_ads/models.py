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


class FacebookAdSet(BaseModel):
    """Model to store Facebook AdSet information"""
    ad_account = models.ForeignKey(FacebookAdAccount, on_delete=models.CASCADE, related_name='adsets')
    campaign = models.ForeignKey(FacebookCampaign, on_delete=models.CASCADE, related_name='adsets')
    adset_id = models.CharField(max_length=100, unique=True)
    adset_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    effective_status = models.CharField(max_length=50, blank=True)
    configured_status = models.CharField(max_length=50, blank=True)
    
    # Budget & Bidding
    daily_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    lifetime_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bid_strategy = models.CharField(max_length=100, blank=True)
    optimization_goal = models.CharField(max_length=100, blank=True)
    billing_event = models.CharField(max_length=100, blank=True)
    
    # Targeting
    targeting_data = models.JSONField(default=dict, blank=True)
    
    # Performance metrics
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reach = models.BigIntegerField(default=0)
    frequency = models.FloatField(default=0)
    ctr = models.FloatField(default=0)
    cpm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cpc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Conversion metrics
    purchase_roas = models.FloatField(default=0)
    website_purchase_roas = models.FloatField(default=0)
    
    # Timestamps
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_time = models.DateTimeField(null=True, blank=True)
    updated_time = models.DateTimeField(null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    
    # Complex data as JSON
    actions_data = models.JSONField(default=dict, blank=True)
    conversions_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Facebook AdSet"
        verbose_name_plural = "Facebook AdSets"
        ordering = ['-last_synced']
        unique_together = ['ad_account', 'adset_id']
    
    def __str__(self):
        return f"{self.adset_name} ({self.adset_id})"


class FacebookCampaignInsights(BaseModel):
    """Model to store historical campaign insights data"""
    campaign = models.ForeignKey(FacebookCampaign, on_delete=models.CASCADE, related_name='insights')
    date_start = models.DateField()
    date_stop = models.DateField()
    
    # Core Metrics
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reach = models.BigIntegerField(default=0)
    frequency = models.FloatField(default=0)
    
    # Calculated Metrics
    ctr = models.FloatField(default=0)
    cpc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cpm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Conversion Metrics
    purchase_roas = models.FloatField(default=0)
    website_purchase_roas = models.FloatField(default=0)
    purchase_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchases = models.IntegerField(default=0)
    
    # Additional Metrics
    link_clicks = models.BigIntegerField(default=0)
    inline_link_clicks = models.BigIntegerField(default=0)
    outbound_clicks = models.BigIntegerField(default=0)
    post_engagement = models.BigIntegerField(default=0)
    video_views = models.BigIntegerField(default=0)
    unique_clicks = models.BigIntegerField(default=0)
    unique_ctr = models.FloatField(default=0)
    
    # Video metrics
    video_p25_watched = models.BigIntegerField(default=0)
    video_p50_watched = models.BigIntegerField(default=0)
    video_p75_watched = models.BigIntegerField(default=0)
    video_p100_watched = models.BigIntegerField(default=0)
    video_avg_time_watched = models.FloatField(default=0)
    
    # Complex data as JSON
    actions_data = models.JSONField(default=dict, blank=True)
    conversions_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Facebook Campaign Insights"
        verbose_name_plural = "Facebook Campaign Insights"
        ordering = ['-date_start']
        unique_together = ['campaign', 'date_start', 'date_stop']
        indexes = [
            models.Index(fields=['campaign', 'date_start']),
            models.Index(fields=['date_start', 'date_stop']),
        ]
    
    def __str__(self):
        return f"{self.campaign.campaign_name} - {self.date_start} to {self.date_stop}"


class DashboardPeriod(BaseModel):
    """Model to store dashboard period configurations"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    days = models.IntegerField(null=True, blank=True)
    date_preset = models.CharField(max_length=50, blank=True)
    is_custom = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Dashboard Period"
        verbose_name_plural = "Dashboard Periods"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.display_name


class FacebookAdInsights(BaseModel):
    """Model to store historical ad insights data"""
    ad = models.ForeignKey(FacebookAd, on_delete=models.CASCADE, related_name='insights')
    adset = models.ForeignKey(FacebookAdSet, on_delete=models.CASCADE, related_name='ad_insights', null=True, blank=True)
    campaign = models.ForeignKey(FacebookCampaign, on_delete=models.CASCADE, related_name='ad_insights')
    date_start = models.DateField()
    date_stop = models.DateField()
    
    # Core Metrics
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reach = models.BigIntegerField(default=0)
    frequency = models.FloatField(default=0)
    
    # Calculated Metrics
    ctr = models.FloatField(default=0)
    cpc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cpm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Conversion Metrics
    purchase_roas = models.FloatField(default=0)
    website_purchase_roas = models.FloatField(default=0)
    purchase_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchases = models.IntegerField(default=0)
    
    # Additional Metrics
    link_clicks = models.BigIntegerField(default=0)
    inline_link_clicks = models.BigIntegerField(default=0)
    outbound_clicks = models.BigIntegerField(default=0)
    post_engagement = models.BigIntegerField(default=0)
    video_views = models.BigIntegerField(default=0)
    unique_clicks = models.BigIntegerField(default=0)
    unique_ctr = models.FloatField(default=0)
    
    # Video metrics
    video_p25_watched = models.BigIntegerField(default=0)
    video_p50_watched = models.BigIntegerField(default=0)
    video_p75_watched = models.BigIntegerField(default=0)
    video_p100_watched = models.BigIntegerField(default=0)
    video_avg_time_watched = models.FloatField(default=0)
    
    # Complex data as JSON
    actions_data = models.JSONField(default=dict, blank=True)
    conversions_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Facebook Ad Insights"
        verbose_name_plural = "Facebook Ad Insights"
        ordering = ['-date_start']
        unique_together = ['ad', 'date_start', 'date_stop']
        indexes = [
            models.Index(fields=['ad', 'date_start']),
            models.Index(fields=['campaign', 'date_start']),
            models.Index(fields=['date_start', 'date_stop']),
        ]
    
    def __str__(self):
        return f"{self.ad.ad_name} - {self.date_start} to {self.date_stop}"


class OptimizationStrategy(BaseModel):
    """Model to define reusable campaign optimization strategies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='optimization_strategies')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Strategy rules stored as JSON
    # Example structure:
    # {
    #   "rules": [
    #     {
    #       "spend_threshold": 10.00,
    #       "metric": "cpc",
    #       "operator": "less_than",
    #       "value": 1.20,
    #       "action": "keep_running"
    #     },
    #     {
    #       "spend_threshold": 20.00,
    #       "metric": "add_to_cart",
    #       "operator": "greater_than_or_equal",
    #       "value": 1,
    #       "action": "keep_running",
    #       "else_action": "pause"
    #     }
    #   ]
    # }
    rules = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Optimization Strategy"
        verbose_name_plural = "Optimization Strategies"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class CampaignOptimization(BaseModel):
    """Links campaigns to optimization strategies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaign_optimizations')
    campaign = models.ForeignKey(FacebookCampaign, on_delete=models.CASCADE, related_name='optimizations')
    strategy = models.ForeignKey(OptimizationStrategy, on_delete=models.CASCADE, related_name='campaign_links')
    is_active = models.BooleanField(default=True)
    date_enabled = models.DateTimeField(auto_now_add=True)
    date_disabled = models.DateTimeField(null=True, blank=True)

    # Track when the campaign started for this optimization
    optimization_start_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Campaign Optimization"
        verbose_name_plural = "Campaign Optimizations"
        unique_together = ['campaign', 'strategy']
        ordering = ['-date_enabled']

    def __str__(self):
        return f"{self.campaign.campaign_name} - {self.strategy.name}"


class OptimizationLog(BaseModel):
    """Logs all optimization checks and actions taken"""
    ACTION_CHOICES = [
        ('KEEP_RUNNING', 'Keep Running'),
        ('PAUSE', 'Pause Campaign'),
        ('SCALE_UP', 'Scale Up Budget'),
        ('SCALE_DOWN', 'Scale Down Budget'),
        ('NO_ACTION', 'No Action Needed'),
    ]

    campaign_optimization = models.ForeignKey(CampaignOptimization, on_delete=models.CASCADE, related_name='logs')
    campaign = models.ForeignKey(FacebookCampaign, on_delete=models.CASCADE, related_name='optimization_logs')
    strategy = models.ForeignKey(OptimizationStrategy, on_delete=models.CASCADE, related_name='logs')

    # Check information
    check_time = models.DateTimeField(auto_now_add=True)

    # Metrics snapshot at time of check
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cpc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ctr = models.FloatField(default=0)
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    add_to_carts = models.IntegerField(default=0)
    purchases = models.IntegerField(default=0)
    roas = models.FloatField(default=0)

    # Action taken
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    rule_triggered = models.CharField(max_length=255, blank=True)  # Which rule caused this action
    reason = models.TextField(blank=True)  # Detailed reason for the action

    # Success/failure tracking
    action_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Optimization Log"
        verbose_name_plural = "Optimization Logs"
        ordering = ['-check_time']
        indexes = [
            models.Index(fields=['campaign', 'check_time']),
            models.Index(fields=['strategy', 'check_time']),
            models.Index(fields=['check_time']),
        ]

    def __str__(self):
        return f"{self.campaign.campaign_name} - {self.action} - {self.check_time.strftime('%Y-%m-%d %H:%M')}"


class DailyPeriod(BaseModel):
    """Model to represent a daily period for metrics tracking"""
    date = models.DateField(unique=True)

    class Meta:
        verbose_name = "Daily Period"
        verbose_name_plural = "Daily Periods"
        ordering = ['-date']

    def __str__(self):
        return f"Period: {self.date}"


class OptimizationMetrics(BaseModel):
    """Stores daily metrics snapshot for campaigns under optimization"""
    campaign = models.ForeignKey(FacebookCampaign, on_delete=models.CASCADE, related_name='optimization_metrics')
    period = models.ForeignKey(DailyPeriod, on_delete=models.CASCADE, related_name='campaign_metrics')

    # Core metrics
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cpc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cpm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ctr = models.FloatField(default=0)
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)

    # Conversion metrics
    add_to_carts = models.IntegerField(default=0)
    purchases = models.IntegerField(default=0)
    purchase_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    roas = models.FloatField(default=0)

    # Campaign status at time of snapshot
    campaign_status = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Optimization Metrics"
        verbose_name_plural = "Optimization Metrics"
        unique_together = ['campaign', 'period']
        ordering = ['-period__date']
        indexes = [
            models.Index(fields=['campaign', 'period']),
            models.Index(fields=['period']),
        ]

    def __str__(self):
        return f"{self.campaign.campaign_name} - {self.period.date}"
