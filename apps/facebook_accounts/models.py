from django.conf import settings
from django.db import models

from apps.utils.models import BaseModel


class FacebookAdAccount(BaseModel):
    """Facebook Ad Account information and connection to users."""

    # Facebook account details
    account_id = models.CharField(max_length=100, unique=True, help_text="Facebook ad account ID (e.g. act_123...)")
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=10)
    timezone_name = models.CharField(max_length=100, blank=True)

    # Account status from Facebook
    account_status = models.IntegerField(help_text="Facebook account status code")

    # Business information
    business_id = models.CharField(max_length=100, blank=True)
    business_name = models.CharField(max_length=255, blank=True)

    # User relationship
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="facebook_ad_accounts")

    # Access and permissions
    access_token = models.ForeignKey(
        "facebook_auth.FacebookToken", on_delete=models.CASCADE, related_name="ad_accounts"
    )

    # Account capabilities and limits
    capabilities = models.JSONField(default=list, help_text="Account capabilities")
    restrictions = models.JSONField(default=dict, help_text="Account restrictions")

    # Sync metadata
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_enabled = models.BooleanField(default=True)

    # Performance stats cache
    total_spend = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_impressions = models.BigIntegerField(null=True, blank=True)
    total_clicks = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Facebook Ad Account"
        verbose_name_plural = "Facebook Ad Accounts"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["account_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.account_id})"

    @property
    def facebook_account_id(self):
        """Return the account ID without act_ prefix if present."""
        return self.account_id.replace("act_", "") if self.account_id.startswith("act_") else self.account_id

    @property
    def full_account_id(self):
        """Return the account ID with act_ prefix."""
        return f"act_{self.facebook_account_id}"

    def has_capability(self, capability):
        """Check if account has a specific capability."""
        return capability in self.capabilities

    def has_capabilities(self, required_capabilities):
        """Check if account has all required capabilities."""
        return all(cap in self.capabilities for cap in required_capabilities)


class AccountPermission(BaseModel):
    """Track specific permissions for ad accounts."""

    account = models.ForeignKey(FacebookAdAccount, on_delete=models.CASCADE, related_name="permissions")

    permission = models.CharField(max_length=100)
    granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Account Permission"
        verbose_name_plural = "Account Permissions"
        unique_together = ["account", "permission"]

    def __str__(self):
        return f"{self.account.name} - {self.permission} ({'✓' if self.granted else '✗'})"
