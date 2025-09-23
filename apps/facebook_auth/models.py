from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.utils.models import BaseModel


class FacebookToken(BaseModel):
    """Store Facebook access tokens for users."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="facebook_token")
    access_token = models.TextField(help_text="Facebook access token")
    token_type = models.CharField(max_length=50, default="user_access_token")
    expires_at = models.DateTimeField(null=True, blank=True)

    # Token scopes and permissions
    scopes = models.JSONField(default=list, help_text="Granted permissions/scopes")

    # Facebook user info
    facebook_user_id = models.CharField(max_length=100, unique=True)
    facebook_user_name = models.CharField(max_length=255, blank=True)
    facebook_user_email = models.EmailField(blank=True)

    # Status and metadata
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facebook Token"
        verbose_name_plural = "Facebook Tokens"

    def __str__(self):
        return f"{self.user.email} - Facebook Token"

    @property
    def is_expired(self):
        """Check if the token has expired."""
        if not self.expires_at:
            return False
        return timezone.now() >= self.expires_at

    @property
    def expires_soon(self):
        """Check if token expires within 7 days."""
        if not self.expires_at:
            return False
        return timezone.now() + timedelta(days=7) >= self.expires_at

    def has_scope(self, scope):
        """Check if token has a specific scope."""
        return scope in self.scopes

    def has_scopes(self, required_scopes):
        """Check if token has all required scopes."""
        return all(scope in self.scopes for scope in required_scopes)


class FacebookApp(BaseModel):
    """Facebook App credentials and configuration."""

    name = models.CharField(max_length=255)
    app_id = models.CharField(max_length=100, unique=True)
    app_secret = models.CharField(max_length=255)

    # App configuration
    is_active = models.BooleanField(default=True)
    environment = models.CharField(
        max_length=20,
        choices=[
            ("development", "Development"),
            ("production", "Production"),
        ],
        default="development",
    )

    # Webhook configuration
    webhook_url = models.URLField(blank=True)
    webhook_verify_token = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Facebook App"
        verbose_name_plural = "Facebook Apps"

    def __str__(self):
        return f"{self.name} ({self.app_id})"
