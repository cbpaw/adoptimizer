from django.db import models

from apps.utils.models import BaseModel


class InsightBase(BaseModel):
    """Base model for Facebook insights data."""

    # Time period
    date_start = models.DateField()
    date_stop = models.DateField()

    # Core metrics
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Calculated metrics
    cpc = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    cpm = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    ctr = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)

    # Additional metrics
    reach = models.BigIntegerField(null=True, blank=True)
    frequency = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    conversions = models.BigIntegerField(null=True, blank=True)
    conversion_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Raw insights data from Facebook
    raw_data = models.JSONField(default=dict, help_text="Raw insights data from Facebook API")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["date_start", "date_stop"]),
        ]


class AccountInsight(InsightBase):
    """Insights data for Facebook ad accounts."""

    account = models.ForeignKey(
        "facebook_accounts.FacebookAdAccount", on_delete=models.CASCADE, related_name="insights"
    )

    class Meta:
        verbose_name = "Account Insight"
        verbose_name_plural = "Account Insights"
        unique_together = ["account", "date_start", "date_stop"]
        indexes = [
            models.Index(fields=["account", "date_start"]),
        ]

    def __str__(self):
        return f"{self.account.name} - {self.date_start} to {self.date_stop}"


class CampaignInsight(InsightBase):
    """Insights data for Facebook campaigns."""

    campaign = models.ForeignKey("facebook_ads.Campaign", on_delete=models.CASCADE, related_name="insights")

    class Meta:
        verbose_name = "Campaign Insight"
        verbose_name_plural = "Campaign Insights"
        unique_together = ["campaign", "date_start", "date_stop"]
        indexes = [
            models.Index(fields=["campaign", "date_start"]),
        ]

    def __str__(self):
        return f"{self.campaign.name} - {self.date_start} to {self.date_stop}"


class AdSetInsight(InsightBase):
    """Insights data for Facebook ad sets."""

    adset = models.ForeignKey("facebook_ads.AdSet", on_delete=models.CASCADE, related_name="insights")

    class Meta:
        verbose_name = "AdSet Insight"
        verbose_name_plural = "AdSet Insights"
        unique_together = ["adset", "date_start", "date_stop"]
        indexes = [
            models.Index(fields=["adset", "date_start"]),
        ]

    def __str__(self):
        return f"{self.adset.name} - {self.date_start} to {self.date_stop}"


class AdInsight(InsightBase):
    """Insights data for Facebook ads."""

    ad = models.ForeignKey("facebook_ads.Ad", on_delete=models.CASCADE, related_name="insights")

    class Meta:
        verbose_name = "Ad Insight"
        verbose_name_plural = "Ad Insights"
        unique_together = ["ad", "date_start", "date_stop"]
        indexes = [
            models.Index(fields=["ad", "date_start"]),
        ]

    def __str__(self):
        return f"{self.ad.name} - {self.date_start} to {self.date_stop}"


class InsightField(BaseModel):
    """Track available insight fields and their configuration."""

    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=255)
    field_type = models.CharField(
        max_length=50,
        choices=[
            ("integer", "Integer"),
            ("decimal", "Decimal"),
            ("string", "String"),
            ("json", "JSON"),
        ],
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Field configuration
    is_metric = models.BooleanField(default=False, help_text="Is this a performance metric?")
    is_dimension = models.BooleanField(default=False, help_text="Is this a dimension for grouping?")
    is_calculated = models.BooleanField(default=False, help_text="Is this calculated from other fields?")

    class Meta:
        verbose_name = "Insight Field"
        verbose_name_plural = "Insight Fields"

    def __str__(self):
        return f"{self.display_name} ({self.name})"
