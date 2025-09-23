from django.apps import AppConfig


class FacebookSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.facebook_sync"
    verbose_name = "Facebook Sync Jobs"
