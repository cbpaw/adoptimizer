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
    """Model to store Facebook/Meta campaigns available for monitoring"""
    ad_account = models.ForeignKey(FacebookAdAccount, on_delete=models.CASCADE, related_name='campaigns')
    campaign_id = models.CharField(max_length=100, unique=True)
    campaign_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    effective_status = models.CharField(max_length=50, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['ad_account', 'campaign_id']
    
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
    """Model to cache Facebook Ad data"""
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
    campaign_id = models.CharField(max_length=100, blank=True)
    campaign_name = models.CharField(max_length=255, blank=True)
    adset_id = models.CharField(max_length=100, blank=True)
    adset_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=50)
    objective = models.CharField(max_length=100, blank=True)
    
    # Performance metrics
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ctr = models.FloatField(default=0)  # Click-through rate
    cpm = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Cost per mille
    cpc = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Cost per click
    
    # Timestamps
    created_time = models.DateTimeField(null=True, blank=True)
    updated_time = models.DateTimeField(null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facebook Ad"
        verbose_name_plural = "Facebook Ads"
        ordering = ['-last_synced']

    def __str__(self):
        return f"{self.ad_name} ({self.ad_id})"
