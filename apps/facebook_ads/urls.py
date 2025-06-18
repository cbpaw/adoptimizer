from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'facebook_ads'

urlpatterns = [
    # OAuth flow
    path('auth/start/', views.facebook_auth_start, name='auth_start'),
    path('auth/callback/', views.facebook_auth_callback, name='auth_callback'),
    path('setup/', views.setup_account, name='setup_account'),
    
    # Account management
    path('accounts/<int:account_id>/sync/', views.sync_ads, name='sync_ads'),
    
    # Campaign selection
    path('campaigns/', views.campaign_selection, name='campaign_selection'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
    
    # API endpoints
    path('api/ads/', views.get_user_ads, name='api_ads'),
    path('api/summary/', views.get_ads_summary, name='api_summary'),
    path('api/test-token/', views.test_token, name='api_test_token'),
    path('api/fetch-accounts/', views.fetch_ad_accounts, name='api_fetch_accounts'),
    path('api/connect-account/', views.connect_ad_account, name='api_connect_account'),
    path('api/test-account-connection/', views.test_account_connection, name='api_test_account_connection'),
    path('api/fetch-ads/', views.fetch_ads_from_facebook, name='api_fetch_ads'),
    path('api/fetch-campaigns/', views.fetch_campaigns_for_account, name='fetch_campaigns_for_account'),
    path('api/fetch-campaigns-for-account/', views.fetch_campaigns_for_account, name='api_fetch_campaigns_for_account'),
    path('api/save-selected-campaigns/', views.save_selected_campaigns, name='api_save_selected_campaigns'),
    path('api/disconnect-account/', views.disconnect_account, name='api_disconnect_account'),
    path('api/get-account-campaigns/', views.get_account_campaigns, name='get_account_campaigns'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 