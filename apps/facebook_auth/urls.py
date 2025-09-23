from django.urls import path

from . import views

app_name = "facebook_auth"
urlpatterns = [
    path("settings/", views.facebook_settings, name="settings"),
    path("api/validate-token/", views.validate_and_save_token, name="validate_token"),
    path("api/revoke-token/", views.revoke_token, name="revoke_token"),
]
