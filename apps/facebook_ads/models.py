from django.db import models

from apps.utils.models import BaseModel


class FacebookEntityMixin(models.Model):
    """Base mixin for Facebook advertising entities."""

    facebook_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("PAUSED", "Paused"),
        ("DELETED", "Deleted"),
        ("ARCHIVED", "Archived"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")

    # Sync metadata
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_enabled = models.BooleanField(default=True)

    # Raw Facebook data
    facebook_data = models.JSONField(default=dict, help_text="Raw data from Facebook API")

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.name} ({self.facebook_id})"


class Campaign(FacebookEntityMixin, BaseModel):
    """Facebook advertising campaign."""

    account = models.ForeignKey(
        "facebook_accounts.FacebookAdAccount", on_delete=models.CASCADE, related_name="campaigns"
    )

    # Campaign-specific fields
    objective = models.CharField(max_length=100, blank=True)

    # Budget fields
    daily_budget = models.CharField(max_length=20, null=True, blank=True)
    lifetime_budget = models.CharField(max_length=20, null=True, blank=True)

    # Campaign configuration
    buying_type = models.CharField(max_length=50, blank=True)
    special_ad_categories = models.JSONField(default=list)

    # Performance cache
    spend = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    impressions = models.BigIntegerField(null=True, blank=True)
    clicks = models.BigIntegerField(null=True, blank=True)
    reach = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Facebook Campaign"
        verbose_name_plural = "Facebook Campaigns"
        indexes = [
            models.Index(fields=["account", "status"]),
            models.Index(fields=["facebook_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.facebook_id})"


class AdSet(FacebookEntityMixin, BaseModel):
    """Facebook ad set."""

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="adsets")

    # Budget and scheduling
    daily_budget = models.CharField(max_length=20, null=True, blank=True)
    lifetime_budget = models.CharField(max_length=20, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # Optimization and billing
    billing_event = models.CharField(max_length=50, blank=True)
    optimization_goal = models.CharField(max_length=50, blank=True)

    # Targeting
    targeting = models.JSONField(default=dict, help_text="Ad set targeting configuration")

    # Performance cache
    spend = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    impressions = models.BigIntegerField(null=True, blank=True)
    clicks = models.BigIntegerField(null=True, blank=True)
    reach = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Facebook Ad Set"
        verbose_name_plural = "Facebook Ad Sets"
        indexes = [
            models.Index(fields=["campaign", "status"]),
            models.Index(fields=["facebook_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.facebook_id})"


class Ad(FacebookEntityMixin, BaseModel):
    """Facebook ad."""

    adset = models.ForeignKey(AdSet, on_delete=models.CASCADE, related_name="ads")

    # Creative reference
    creative_id = models.CharField(max_length=100, null=True, blank=True)

    # Performance cache
    spend = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    impressions = models.BigIntegerField(null=True, blank=True)
    clicks = models.BigIntegerField(null=True, blank=True)
    reach = models.BigIntegerField(null=True, blank=True)

    # Calculated metrics cache
    cpc = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    cpm = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    ctr = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = "Facebook Ad"
        verbose_name_plural = "Facebook Ads"
        indexes = [
            models.Index(fields=["adset", "status"]),
            models.Index(fields=["facebook_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.facebook_id})"


class Creative(FacebookEntityMixin, BaseModel):
    """Facebook ad creative."""

    account = models.ForeignKey(
        "facebook_accounts.FacebookAdAccount", on_delete=models.CASCADE, related_name="creatives"
    )

    # Creative content
    object_story_spec = models.JSONField(default=dict, help_text="Creative object story specification")

    # Creative metadata
    creative_type = models.CharField(max_length=50, blank=True)
    thumbnail_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Facebook Creative"
        verbose_name_plural = "Facebook Creatives"
        indexes = [
            models.Index(fields=["account", "status"]),
            models.Index(fields=["facebook_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.facebook_id})"
