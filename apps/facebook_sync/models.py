from django.conf import settings
from django.db import models

from apps.utils.models import BaseModel


class SyncJob(BaseModel):
    """Track sync jobs for Facebook data."""

    SYNC_TYPES = [
        ("accounts", "Ad Accounts"),
        ("campaigns", "Campaigns"),
        ("adsets", "Ad Sets"),
        ("ads", "Ads"),
        ("creatives", "Creatives"),
        ("insights", "Insights"),
        ("full", "Full Sync"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    # Job identification
    job_id = models.UUIDField(unique=True, help_text="Celery task ID")
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # User and account context
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sync_jobs")
    account = models.ForeignKey(
        "facebook_accounts.FacebookAdAccount", on_delete=models.CASCADE, related_name="sync_jobs", null=True, blank=True
    )

    # Job configuration
    parameters = models.JSONField(default=dict, help_text="Job-specific parameters")

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Progress tracking
    total_items = models.IntegerField(null=True, blank=True)
    processed_items = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    # Results
    result_data = models.JSONField(default=dict, help_text="Job results and statistics")
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, help_text="Detailed error information")

    class Meta:
        verbose_name = "Sync Job"
        verbose_name_plural = "Sync Jobs"
        indexes = [
            models.Index(fields=["user", "status", "created_at"]),
            models.Index(fields=["account", "sync_type", "status"]),
            models.Index(fields=["job_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        account_name = self.account.name if self.account else "All Accounts"
        return f"{self.get_sync_type_display()} - {account_name} ({self.status})"

    @property
    def progress_percentage(self):
        """Calculate progress percentage."""
        if not self.total_items or self.total_items == 0:
            return 0
        return int((self.processed_items / self.total_items) * 100)

    @property
    def is_running(self):
        """Check if job is currently running."""
        return self.status in ["pending", "running"]

    @property
    def is_completed(self):
        """Check if job is completed (success or failure)."""
        return self.status in ["completed", "failed", "cancelled"]


class SyncSchedule(BaseModel):
    """Scheduled sync configurations."""

    name = models.CharField(max_length=255)

    # Schedule configuration
    sync_type = models.CharField(max_length=20, choices=SyncJob.SYNC_TYPES)
    account = models.ForeignKey(
        "facebook_accounts.FacebookAdAccount",
        on_delete=models.CASCADE,
        related_name="sync_schedules",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sync_schedules")

    # Schedule timing
    is_active = models.BooleanField(default=True)
    cron_expression = models.CharField(
        max_length=100, help_text="Cron expression for scheduling (e.g., '0 */6 * * *' for every 6 hours)"
    )

    # Job configuration
    parameters = models.JSONField(default=dict, help_text="Default parameters for scheduled jobs")

    # Metadata
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    run_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Sync Schedule"
        verbose_name_plural = "Sync Schedules"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["next_run_at"]),
        ]

    def __str__(self):
        account_name = self.account.name if self.account else "All Accounts"
        return f"{self.name} - {account_name}"


class WebhookEvent(BaseModel):
    """Track Facebook webhook events."""

    EVENT_TYPES = [
        ("campaign_updates", "Campaign Updates"),
        ("adset_updates", "AdSet Updates"),
        ("ad_updates", "Ad Updates"),
        ("account_updates", "Account Updates"),
        ("billing_events", "Billing Events"),
        ("insights_ready", "Insights Ready"),
    ]

    PROCESSING_STATUS = [
        ("received", "Received"),
        ("processing", "Processing"),
        ("processed", "Processed"),
        ("failed", "Failed"),
        ("ignored", "Ignored"),
    ]

    # Event identification
    facebook_event_id = models.CharField(max_length=100, unique=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)

    # Event data
    raw_payload = models.JSONField(help_text="Raw webhook payload from Facebook")

    # Processing
    status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default="received")
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Related objects
    account = models.ForeignKey(
        "facebook_accounts.FacebookAdAccount",
        on_delete=models.CASCADE,
        related_name="webhook_events",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        indexes = [
            models.Index(fields=["event_type", "status"]),
            models.Index(fields=["account", "created_at"]),
            models.Index(fields=["facebook_event_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        account_name = self.account.name if self.account else "Unknown Account"
        return f"{self.get_event_type_display()} - {account_name} ({self.status})"
