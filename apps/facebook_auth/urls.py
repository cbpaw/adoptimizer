from django.urls import path

from . import api_views, views

app_name = "facebook_auth"
urlpatterns = [
    # Settings page views
    path("settings/", views.facebook_settings, name="settings"),
    path("user-detail/", views.facebook_user_detail, name="user_detail"),

    # Legacy API endpoints (for backward compatibility)
    path("api/validate-token/", views.validate_and_save_token, name="validate_token"),
    path("api/revoke-token/", views.revoke_token, name="revoke_token"),

    # DRF API endpoints with OpenAPI documentation
    path("api/v1/token/status/", api_views.FacebookTokenStatusAPIView.as_view(), name="api_token_status"),
    path("api/v1/token/validate/", api_views.FacebookTokenValidationAPIView.as_view(), name="api_token_validate"),
    path("api/v1/token/revoke/", api_views.FacebookTokenRevokeAPIView.as_view(), name="api_token_revoke"),
]
