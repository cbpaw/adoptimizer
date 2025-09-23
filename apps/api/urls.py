"""
Pure JSON API endpoints for the AdOptimizer application.
All endpoints return JSON responses only - no HTML templates.
"""
from django.urls import path, include

from . import facebook_api

app_name = "api"

# Facebook API endpoints
facebook_patterns = [
    path("token/status/", facebook_api.FacebookTokenStatusView.as_view(), name="facebook_token_status"),
    path("token/validate/", facebook_api.FacebookTokenValidateView.as_view(), name="facebook_token_validate"),
    path("token/revoke/", facebook_api.FacebookTokenRevokeView.as_view(), name="facebook_token_revoke"),
    path("user/details/", facebook_api.FacebookUserDetailView.as_view(), name="facebook_user_details"),
]

urlpatterns = [
    # Facebook API endpoints - pure JSON
    path("facebook/", include((facebook_patterns, "facebook"), namespace="facebook")),
]