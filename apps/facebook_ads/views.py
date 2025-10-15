import logging
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json

from .models import (
    FacebookAdAccount, FacebookAd, FacebookCampaign, SelectedCampaign,
    OptimizationStrategy, CampaignOptimization, OptimizationLog,
    DailyPeriod, OptimizationMetrics
)
from .services import FacebookMarketingAPIService, ComprehensiveFacebookAPIService, get_facebook_auth_url, exchange_code_for_token

logger = logging.getLogger(__name__)


@login_required
def facebook_auth_start(request):
    """Start Facebook OAuth flow"""
    app_id = request.GET.get('app_id')
    if not app_id:
        messages.error(request, 'App ID is required')
        return redirect('dashboard:dashboard')
    
    redirect_uri = request.build_absolute_uri(reverse('facebook_ads:auth_callback'))
    auth_url = get_facebook_auth_url(app_id, redirect_uri)
    
    # Store app_id in session for callback
    request.session['facebook_app_id'] = app_id
    
    return redirect(auth_url)


@login_required
def facebook_auth_callback(request):
    """Handle Facebook OAuth callback"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f'Facebook authorization failed: {error}')
        return redirect('dashboard:dashboard')
    
    if not code:
        messages.error(request, 'Authorization code not received')
        return redirect('dashboard:dashboard')
    
    app_id = request.session.get('facebook_app_id')
    if not app_id:
        messages.error(request, 'App ID not found in session')
        return redirect('dashboard:dashboard')
    
    try:
        # Get app secret from form or settings
        app_secret = request.GET.get('app_secret')
        if not app_secret:
            messages.error(request, 'App secret is required')
            return redirect('dashboard:dashboard')
        
        redirect_uri = request.build_absolute_uri(reverse('facebook_ads:auth_callback'))
        access_token = exchange_code_for_token(app_id, app_secret, code, redirect_uri)
        
        # Store credentials in session for account setup
        request.session['facebook_credentials'] = {
            'app_id': app_id,
            'app_secret': app_secret,
            'access_token': access_token
        }
        
        messages.success(request, 'Facebook authorization successful! Please enter your ad account ID.')
        return redirect('facebook_ads:setup_account')
        
    except Exception as e:
        logger.error(f"Facebook OAuth callback error: {str(e)}")
        messages.error(request, f'Failed to complete authorization: {str(e)}')
        return redirect('dashboard:dashboard')


@login_required
def setup_account(request):
    """Setup Facebook ad account"""
    credentials = request.session.get('facebook_credentials')
    if not credentials:
        messages.error(request, 'No Facebook credentials found. Please authorize again.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')
        if not ad_account_id:
            messages.error(request, 'Ad account ID is required')
            return render(request, 'facebook_ads/setup_account.html', {'active_tab': 'facebook-ads'})
        
        try:
            # Create temporary ad account to test connection
            temp_account = FacebookAdAccount(
                user=request.user,
                ad_account_id=ad_account_id,
                access_token=credentials['access_token'],
                app_id=credentials['app_id'],
                app_secret=credentials['app_secret']
            )
            
            # Test connection and get account info
            service = FacebookMarketingAPIService(temp_account)
            if not service.test_connection():
                messages.error(request, 'Failed to connect to Facebook ad account. Please check your ad account ID.')
                return render(request, 'facebook_ads/setup_account.html', {'active_tab': 'facebook-ads'})
            
            account_info = service.get_ad_account_info()
            
            # Save the account
            temp_account.ad_account_name = account_info.get('name', '')
            temp_account.save()
            
            # Clear session
            del request.session['facebook_credentials']
            
            messages.success(request, f'Facebook ad account "{temp_account.ad_account_name}" connected successfully!')
            return redirect('dashboard:dashboard')
            
        except Exception as e:
            logger.error(f"Failed to setup Facebook ad account: {str(e)}")
            messages.error(request, f'Failed to setup ad account: {str(e)}')
    
    return render(request, 'facebook_ads/setup_account.html', {'active_tab': 'facebook-ads'})


@login_required
@require_http_methods(["POST"])
def sync_ads(request, account_id):
    """Sync ads for a specific account"""
    account = get_object_or_404(FacebookAdAccount, id=account_id, user=request.user)
    
    try:
        service = FacebookMarketingAPIService(account)
        
        # Fetch ads from Facebook API
        ads_data = service.fetch_ads(limit=100, status_filter=['ACTIVE', 'PAUSED'])
        
        # Sync to database
        synced_count = service.sync_ads_to_database(ads_data)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully synced {synced_count} ads',
            'synced_count': synced_count
        })
        
    except Exception as e:
        logger.error(f"Failed to sync ads for account {account_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to sync ads: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_ads(request):
    """API endpoint to get user's Facebook ads from selected campaigns only"""
    try:
        # Get selected campaigns for this user
        selected_campaigns = SelectedCampaign.objects.filter(
            user=request.user, 
            is_monitoring=True
        ).select_related('campaign')
        
        # Get campaign IDs for filtering ads
        selected_campaign_ids = [sc.campaign.campaign_id for sc in selected_campaigns]
        
        # Get all ads for user's accounts from selected campaigns only
        user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        
        if selected_campaign_ids:
            ads = FacebookAd.objects.filter(
                ad_account__in=user_accounts,
                campaign_id__in=selected_campaign_ids
            ).order_by('-last_synced')
        else:
            ads = FacebookAd.objects.none()  # No ads if no campaigns selected
        
        # Serialize ads data
        ads_data = []
        for ad in ads:
            ads_data.append({
                'id': ad.ad_id,
                'name': ad.ad_name,
                'status': ad.status,
                'campaign_name': ad.campaign_name,
                'adset_name': ad.adset_name,
                'objective': ad.objective,
                'impressions': ad.impressions,
                'clicks': ad.clicks,
                'spend': float(ad.spend),
                'ctr': ad.ctr,
                'cpm': float(ad.cpm),
                'cpc': float(ad.cpc),
                'created_time': ad.created_time.isoformat() if ad.created_time else None,
                'last_synced': ad.last_synced.isoformat(),
                'account_name': ad.ad_account.ad_account_name
            })
        
        return Response({
            'success': True,
            'ads': ads_data,
            'total_count': len(ads_data),
            'selected_campaigns_count': selected_campaigns.count()
        })
        
    except Exception as e:
        logger.error(f"Failed to get user ads: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ads_summary(request):
    """API endpoint to get ads performance summary for selected campaigns only"""
    try:
        # Get selected campaigns for this user
        selected_campaigns = SelectedCampaign.objects.filter(
            user=request.user, 
            is_monitoring=True
        ).select_related('campaign')
        
        # Get campaign IDs for filtering ads
        selected_campaign_ids = [sc.campaign.campaign_id for sc in selected_campaigns]
        
        user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        
        if selected_campaign_ids:
            ads = FacebookAd.objects.filter(
                ad_account__in=user_accounts,
                campaign_id__in=selected_campaign_ids
            )
        else:
            ads = FacebookAd.objects.none()  # No ads if no campaigns selected
        
        # Calculate summary metrics
        total_ads = ads.count()
        active_ads = ads.filter(status='ACTIVE').count()
        total_spend = sum(ad.spend for ad in ads)
        total_impressions = sum(ad.impressions for ad in ads)
        total_clicks = sum(ad.clicks for ad in ads)
        
        # Calculate averages
        avg_ctr = sum(ad.ctr for ad in ads) / total_ads if total_ads > 0 else 0
        avg_cpm = sum(ad.cpm for ad in ads) / total_ads if total_ads > 0 else 0
        avg_cpc = sum(ad.cpc for ad in ads) / total_ads if total_ads > 0 else 0
        
        return Response({
            'success': True,
            'summary': {
                'total_ads': total_ads,
                'active_ads': active_ads,
                'total_spend': float(total_spend),
                'total_impressions': total_impressions,
                'total_clicks': total_clicks,
                'avg_ctr': avg_ctr,
                'avg_cpm': float(avg_cpm),
                'avg_cpc': float(avg_cpc)
            },
            'selected_campaigns_count': selected_campaigns.count()
        })
        
    except Exception as e:
        logger.error(f"Failed to get ads summary: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_ad_accounts(request):
    """Fetch ad accounts from Facebook using access token"""
    try:
        logger.info("Starting fetch_ad_accounts request")
        
        # Use DRF's request.data instead of json.loads(request.body)
        access_token = request.data.get('access_token')
        
        if not access_token:
            logger.warning("No access token provided")
            return Response({
                'success': False,
                'message': 'Access token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Access token received (length: {len(access_token)})")
        
        # Make API call to Facebook to get ad accounts using the correct endpoint
        api_version = 'v19.0'
        url = f'https://graph.facebook.com/{api_version}/me/adaccounts'
        params = {
            'access_token': access_token,
            'fields': 'id,account_id,name,account_status'
        }
        
        logger.info(f"Making Facebook API call to: {url}")
        response = requests.get(url, params=params)
        logger.info(f"Facebook API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Facebook API error: {response.text}")
            return Response({
                'success': False,
                'message': f'Failed to fetch ad accounts from Facebook: {response.text}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        facebook_data = response.json()
        logger.info(f"Facebook API returned {len(facebook_data.get('data', []))} accounts")
        
        accounts = []
        
        for account_data in facebook_data.get('data', []):
            # Extract account ID (remove 'act_' prefix if present)
            account_id = account_data.get('account_id', account_data['id'])
            if account_id.startswith('act_'):
                account_id = account_id[4:]
            
            accounts.append({
                'id': account_id,
                'name': account_data['name'],
                'account_status': account_data.get('account_status'),
                'full_id': account_data['id']  # Keep the full ID for reference
            })
        
        logger.info(f"Successfully processed {len(accounts)} accounts")
        
        return Response({
            'success': True,
            'accounts': accounts
        })
        
    except Exception as e:
        logger.error(f"Error fetching ad accounts: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_token(request):
    """Test and validate a Facebook access token"""
    try:
        access_token = request.data.get('access_token')
        
        if not access_token:
            return Response({
                'success': False,
                'message': 'Access token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test the token by calling Facebook's debug endpoint
        api_version = 'v19.0'
        debug_url = f'https://graph.facebook.com/{api_version}/debug_token'
        debug_params = {
            'input_token': access_token,
            'access_token': access_token  # Use the same token to debug itself
        }
        
        debug_response = requests.get(debug_url, params=debug_params)
        
        if debug_response.status_code != 200:
            logger.error(f"Facebook debug token API error: {debug_response.text}")
            return Response({
                'success': False,
                'message': 'Invalid access token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        debug_data = debug_response.json()
        token_data = debug_data.get('data', {})
        
        if not token_data.get('is_valid'):
            return Response({
                'success': False,
                'message': 'Token is not valid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get additional user and app info
        me_url = f'https://graph.facebook.com/{api_version}/me'
        me_params = {
            'access_token': access_token,
            'fields': 'id,name'
        }
        
        me_response = requests.get(me_url, params=me_params)
        me_data = {}
        if me_response.status_code == 200:
            me_data = me_response.json()
        
        # Format expiration time if available
        expires_at = 'Never'
        if token_data.get('expires_at'):
            try:
                from datetime import datetime
                expires_timestamp = int(token_data['expires_at'])
                expires_at = datetime.fromtimestamp(expires_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except:
                expires_at = 'Unknown'
        
        return Response({
            'success': True,
            'message': 'Token is valid',
            'app_id': token_data.get('app_id'),
            'app_name': token_data.get('application'),
            'user_id': token_data.get('user_id'),
            'user_name': me_data.get('name', 'Unknown'),
            'permissions': token_data.get('scopes', []),
            'expires_at': expires_at,
            'is_valid': token_data.get('is_valid', False)
        })
        
    except Exception as e:
        logger.error(f"Error testing token: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_ad_account(request):
    """Connect a Facebook ad account to the user"""
    try:
        # Use DRF's request.data instead of json.loads(request.body)
        access_token = request.data.get('access_token')
        account_id = request.data.get('account_id')
        
        if not all([access_token, account_id]):
            return Response({
                'success': False,
                'message': 'Access token and account ID are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove 'act_' prefix if present
        if account_id.startswith('act_'):
            account_id = account_id[4:]
        
        # Test the connection by making a call to get account info
        url = f'https://graph.facebook.com/v19.0/act_{account_id}'
        params = {
            'access_token': access_token,
            'fields': 'id,name,account_status,currency,timezone_name'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.error(f"Facebook API error: {response.text}")
            return Response({
                'success': False,
                'message': 'Failed to connect to the selected ad account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        account_info = response.json()
        
        # Get app_id from the access token debug endpoint
        debug_url = f'https://graph.facebook.com/v19.0/debug_token'
        debug_params = {
            'input_token': access_token,
            'access_token': access_token
        }
        
        debug_response = requests.get(debug_url, params=debug_params)
        app_id = 'unknown'
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            app_id = debug_data.get('data', {}).get('app_id', 'unknown')
        
        # Check if account already exists for this user (active or inactive)
        existing_account = FacebookAdAccount.objects.filter(
            user=request.user,
            ad_account_id=account_id
        ).first()
        
        if existing_account:
            # Reactivate and update existing account (whether it was active or inactive)
            existing_account.access_token = access_token
            existing_account.app_id = app_id
            existing_account.ad_account_name = account_info.get('name', '')
            existing_account.is_active = True  # Reactivate if it was disconnected
            existing_account.save()
            fb_account = existing_account
            
            action_message = "reconnected" if not existing_account.is_active else "updated"
        else:
            # Create new account
            fb_account = FacebookAdAccount.objects.create(
                user=request.user,
                ad_account_id=account_id,
                ad_account_name=account_info.get('name', ''),
                access_token=access_token,
                app_id=app_id,
                app_secret='',  # Not needed for token-based auth
                is_active=True
            )
            action_message = "connected"
        
        # Immediately sync some ads to test the connection
        try:
            service = FacebookMarketingAPIService(fb_account)
            ads_data = service.fetch_ads(limit=50, status_filter=['ACTIVE', 'PAUSED'])
            synced_count = service.sync_ads_to_database(ads_data)
            
            return Response({
                'success': True,
                'message': f'Account {action_message} successfully! Synced {synced_count} ads.',
                'account_id': fb_account.id,
                'synced_count': synced_count
            })
        except Exception as sync_error:
            logger.warning(f"Account {action_message} but failed to sync ads: {str(sync_error)}")
            return Response({
                'success': True,
                'message': f'Account {action_message} successfully! You can sync ads manually.',
                'account_id': fb_account.id
            })
        
    except Exception as e:
        logger.error(f"Error connecting ad account: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_ads_from_facebook(request):
    """Fetch ads directly from Facebook for a selected account"""
    try:
        # Use DRF's request.data instead of json.loads(request.body)
        access_token = request.data.get('access_token')
        account_id = request.data.get('account_id')
        app_id = request.data.get('app_id')
        
        if not all([access_token, account_id]):
            return Response({
                'success': False,
                'message': 'Access token and account ID are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove 'act_' prefix if present
        if account_id.startswith('act_'):
            clean_account_id = account_id[4:]
        else:
            clean_account_id = account_id
            account_id = f'act_{account_id}'
        
        # Make API call to Facebook to get ads
        api_version = 'v19.0'
        url = f'https://graph.facebook.com/{api_version}/{account_id}/ads'
        params = {
            'access_token': access_token,
            'fields': 'id,name,status,created_time,campaign{id,name,objective},adset{id,name}',
            'limit': 100
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.error(f"Facebook API error: {response.text}")
            return Response({
                'success': False,
                'message': 'Failed to fetch ads from Facebook'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        facebook_data = response.json()
        ads = []
        
        for ad_data in facebook_data.get('data', []):
            campaign_data = ad_data.get('campaign', {})
            adset_data = ad_data.get('adset', {})
            
            # Get insights for this ad
            insights_url = f'https://graph.facebook.com/{api_version}/{ad_data["id"]}/insights'
            insights_params = {
                'access_token': access_token,
                'fields': 'impressions,clicks,spend,ctr,cpm,cpc',
                'time_range': '{"since":"2024-01-01","until":"2025-01-31"}'
            }
            
            insights_response = requests.get(insights_url, params=insights_params)
            insights_data = {}
            
            if insights_response.status_code == 200:
                insights_json = insights_response.json()
                if insights_json.get('data'):
                    insights_data = insights_json['data'][0]
            
            ad_info = {
                'id': ad_data['id'],
                'name': ad_data['name'],
                'status': ad_data['status'],
                'campaign_name': campaign_data.get('name', ''),
                'campaign_id': campaign_data.get('id', ''),
                'adset_name': adset_data.get('name', ''),
                'adset_id': adset_data.get('id', ''),
                'objective': campaign_data.get('objective', ''),
                'impressions': int(insights_data.get('impressions', 0) or 0),
                'clicks': int(insights_data.get('clicks', 0) or 0),
                'spend': float(insights_data.get('spend', 0) or 0),
                'ctr': float(insights_data.get('ctr', 0) or 0),
                'cpm': float(insights_data.get('cpm', 0) or 0),
                'cpc': float(insights_data.get('cpc', 0) or 0),
                'created_time': ad_data.get('created_time', '')
            }
            ads.append(ad_info)
        
        return Response({
            'success': True,
            'ads': ads,
            'total_count': len(ads)
        })
        
    except Exception as e:
        logger.error(f"Error fetching ads from Facebook: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def campaign_selection(request):
    """View for selecting campaigns to monitor"""
    user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
    
    # Get all campaigns for user's accounts
    campaigns = FacebookCampaign.objects.filter(ad_account__in=user_accounts).order_by('ad_account__ad_account_name', 'campaign_name')
    
    # Get currently selected campaigns
    selected_campaign_ids = SelectedCampaign.objects.filter(
        user=request.user,
        is_monitoring=True
    ).values_list('campaign__id', flat=True)
    
    # Prepare account data with campaigns for each account
    accounts_with_campaigns = []
    for account in user_accounts:
        account_campaigns = campaigns.filter(ad_account=account)
        selected_count = sum(1 for c in account_campaigns if c.id in selected_campaign_ids)
        
        accounts_with_campaigns.append({
            'account': account,
            'campaigns': account_campaigns,
            'campaign_count': account_campaigns.count(),
            'selected_count': selected_count
        })
    
    return render(request, 'facebook_ads/campaign_selection.html', {
        'accounts_with_campaigns': accounts_with_campaigns,
        'selected_campaign_ids': list(selected_campaign_ids),
        'user_accounts': user_accounts,
        'active_tab': 'campaigns'
    })


@login_required
def campaign_detail(request, campaign_id):
    """View for campaign detail page with analytics and ads"""
    # Get the campaign and verify it belongs to user's accounts
    campaign = get_object_or_404(
        FacebookCampaign, 
        id=campaign_id, 
        ad_account__user=request.user,
        ad_account__is_active=True
    )
    
    # Get all ads for this campaign
    ads = FacebookAd.objects.filter(
        ad_account=campaign.ad_account,
        campaign_id=campaign.campaign_id
    ).order_by('-last_synced')
    
    # Calculate campaign metrics
    total_ads = ads.count()
    active_ads = ads.filter(status='ACTIVE').count()
    paused_ads = ads.filter(status='PAUSED').count()
    
    # Performance metrics
    total_impressions = sum(ad.impressions for ad in ads)
    total_clicks = sum(ad.clicks for ad in ads)
    total_spend = sum(ad.spend for ad in ads)
    
    # Calculate averages
    avg_ctr = sum(ad.ctr for ad in ads) / total_ads if total_ads > 0 else 0
    avg_cpm = sum(ad.cpm for ad in ads) / total_ads if total_ads > 0 else 0
    avg_cpc = sum(ad.cpc for ad in ads) / total_ads if total_ads > 0 else 0
    
    # Check if campaign is selected for monitoring
    is_selected = SelectedCampaign.objects.filter(
        user=request.user,
        campaign=campaign,
        is_monitoring=True
    ).exists()
    
    # Prepare data for charts (last 30 days simulation)
    from datetime import datetime, timedelta
    import random
    
    # Generate sample chart data (in real implementation, this would come from historical data)
    chart_dates = []
    impressions_data = []
    clicks_data = []
    spend_data = []
    
    for i in range(30):
        date = datetime.now() - timedelta(days=29-i)
        chart_dates.append(date.strftime('%Y-%m-%d'))
        
        # Simulate realistic daily variations
        base_impressions = total_impressions / 30 if total_impressions > 0 else 1000
        daily_impressions = int(base_impressions * (0.7 + random.random() * 0.6))
        impressions_data.append(daily_impressions)
        
        base_clicks = total_clicks / 30 if total_clicks > 0 else 50
        daily_clicks = int(base_clicks * (0.7 + random.random() * 0.6))
        clicks_data.append(daily_clicks)
        
        base_spend = float(total_spend) / 30 if total_spend > 0 else 100
        daily_spend = round(base_spend * (0.7 + random.random() * 0.6), 2)
        spend_data.append(daily_spend)
    
    # Get optimization info
    campaign_optimization = CampaignOptimization.objects.filter(
        campaign=campaign,
        is_active=True
    ).select_related('strategy').first()

    # Get recent optimization logs
    optimization_logs = OptimizationLog.objects.filter(
        campaign=campaign
    ).order_by('-check_time')[:5]

    # Get available strategies for enabling optimization
    strategies = OptimizationStrategy.objects.filter(
        user=request.user,
        is_active=True
    )

    context = {
        'campaign': campaign,
        'ads': ads,
        'is_selected': is_selected,
        'total_ads': total_ads,
        'active_ads': active_ads,
        'paused_ads': paused_ads,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'total_spend': float(total_spend),
        'avg_ctr': avg_ctr,
        'avg_cpm': float(avg_cpm),
        'avg_cpc': float(avg_cpc),
        'chart_dates': chart_dates,
        'impressions_data': impressions_data,
        'clicks_data': clicks_data,
        'spend_data': spend_data,
        'campaign_optimization': campaign_optimization,
        'optimization_logs': optimization_logs,
        'strategies': strategies,
        'active_tab': 'campaigns'
    }

    return render(request, 'facebook_ads/campaign_detail.html', context)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_campaigns(request):
    """Fetch campaigns from Meta Marketing API for all user's accounts"""
    try:
        user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        
        if not user_accounts.exists():
            return Response({
                'success': False,
                'message': 'No Facebook ad accounts found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        total_campaigns = 0
        
        for account in user_accounts:
            try:
                # Make API call to Facebook to get campaigns
                url = f'https://graph.facebook.com/v19.0/act_{account.ad_account_id}/campaigns'
                params = {
                    'access_token': account.access_token,
                    'fields': 'id,name,status,effective_status,start_time,updated_time',
                    'limit': 100
                }
                
                response = requests.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook API error for account {account.ad_account_id}: {response.text}")
                    continue
                
                facebook_data = response.json()
                
                for campaign_data in facebook_data.get('data', []):
                    # Parse start_time if it exists
                    start_time = None
                    if campaign_data.get('start_time'):
                        try:
                            from datetime import datetime
                            start_time = datetime.fromisoformat(campaign_data['start_time'].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    # Use get_or_create to handle duplicate keys more gracefully
                    try:
                        campaign, created = FacebookCampaign.objects.get_or_create(
                            campaign_id=campaign_data['id'],
                            defaults={
                                'ad_account': account,
                                'campaign_name': campaign_data['name'],
                                'status': campaign_data['status'],
                                'effective_status': campaign_data.get('effective_status', ''),
                                'start_time': start_time,
                            }
                        )
                        
                        # If campaign exists but belongs to different account, update it
                        if not created and campaign.ad_account != account:
                            campaign.ad_account = account
                            campaign.campaign_name = campaign_data['name']
                            campaign.status = campaign_data['status']
                            campaign.effective_status = campaign_data.get('effective_status', '')
                            campaign.start_time = start_time
                            campaign.save()
                            logger.info(f"Transferred campaign to new account: {campaign.campaign_name}")
                        elif not created:
                            # Update existing campaign data
                            campaign.campaign_name = campaign_data['name']
                            campaign.status = campaign_data['status']
                            campaign.effective_status = campaign_data.get('effective_status', '')
                            campaign.start_time = start_time
                            campaign.save()
                            logger.info(f"Updated existing campaign: {campaign.campaign_name}")
                        
                        total_campaigns += 1
                        
                        if created:
                            logger.info(f"Created new campaign: {campaign.campaign_name}")
                            
                    except Exception as e:
                        logger.error(f"Error processing campaign {campaign_data.get('id', 'unknown')}: {str(e)}")
                        continue
                    
            except Exception as e:
                logger.error(f"Error fetching campaigns for account {account.ad_account_id}: {str(e)}")
                continue
        
        return Response({
            'success': True,
            'message': f'Successfully synced {total_campaigns} campaigns',
            'total_campaigns': total_campaigns
        })
        
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_selected_campaigns(request):
    """Save user's selected campaigns for monitoring"""
    try:
        campaign_ids = request.data.get('campaign_ids', [])
        
        if not isinstance(campaign_ids, list):
            return Response({
                'success': False,
                'message': 'campaign_ids must be a list'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get campaigns that belong to user's accounts
        user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        valid_campaigns = FacebookCampaign.objects.filter(
            ad_account__in=user_accounts,
            id__in=campaign_ids
        )
        
        # Clear existing selections
        SelectedCampaign.objects.filter(user=request.user).delete()
        
        # Create new selections
        selected_campaigns = []
        for campaign in valid_campaigns:
            selected_campaign = SelectedCampaign.objects.create(
                user=request.user,
                campaign=campaign,
                is_monitoring=True
            )
            selected_campaigns.append(selected_campaign)
        
        return Response({
            'success': True,
            'message': f'Successfully selected {len(selected_campaigns)} campaigns for monitoring',
            'selected_count': len(selected_campaigns)
        })
        
    except Exception as e:
        logger.error(f"Error saving selected campaigns: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def settings(request):
    """Settings page for Facebook ads configuration"""
    user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
    
    # Prepare existing account IDs as JSON for the template
    existing_account_ids = [account.ad_account_id for account in user_accounts]
    
    return render(request, 'facebook_ads/settings.html', {
        'user_accounts': user_accounts,
        'existing_account_ids_json': json.dumps(existing_account_ids),
        'active_tab': 'settings'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_account(request):
    """Disconnect a Facebook ad account"""
    try:
        account_id = request.data.get('account_id')
        
        if not account_id:
            return Response({
                'success': False,
                'message': 'Account ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the account and verify it belongs to the user
        account = FacebookAdAccount.objects.filter(
            id=account_id,
            user=request.user,
            is_active=True
        ).first()
        
        if not account:
            return Response({
                'success': False,
                'message': 'Account not found or already disconnected'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Deactivate the account instead of deleting (to preserve data)
        account.is_active = False
        account.save()
        
        # Also remove any selected campaigns for this account
        SelectedCampaign.objects.filter(
            user=request.user,
            campaign__ad_account=account
        ).delete()
        
        return Response({
            'success': True,
            'message': f'Account "{account.ad_account_name}" has been disconnected'
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting account: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_account_connection(request):
    """Test connection to a Facebook ad account"""
    try:
        account_id = request.data.get('account_id')
        
        if not account_id:
            return Response({
                'success': False,
                'message': 'Account ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the account and verify it belongs to the user
        account = FacebookAdAccount.objects.filter(
            id=account_id,
            user=request.user,
            is_active=True
        ).first()
        
        if not account:
            return Response({
                'success': False,
                'message': 'Account not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Test the connection by calling Facebook API
        api_version = 'v19.0'
        url = f'https://graph.facebook.com/{api_version}/act_{account.ad_account_id}'
        params = {
            'access_token': account.access_token,
            'fields': 'id,name,account_status'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.error(f"Facebook API error testing account {account.ad_account_id}: {response.text}")
            return Response({
                'success': False,
                'message': 'Failed to connect to Facebook account. Token may be expired or invalid.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        account_data = response.json()
        
        return Response({
            'success': True,
            'message': 'Account connection test successful',
            'account_name': account_data.get('name', account.ad_account_name),
            'account_status': account_data.get('account_status', 'Unknown')
        })
        
    except Exception as e:
        logger.error(f"Error testing account connection: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fetch_campaigns_for_account(request):
    """Fetch campaigns from Meta Marketing API for a specific account"""
    try:
        account_id = request.data.get('account_id')
        
        if not account_id:
            return Response({
                'success': False,
                'message': 'Account ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the specific account
        account = FacebookAdAccount.objects.filter(
            id=account_id,
            user=request.user,
            is_active=True
        ).first()
        
        if not account:
            return Response({
                'success': False,
                'message': 'Account not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        campaigns_synced = 0
        
        try:
            # Make API call to Facebook to get campaigns for this specific account
            url = f'https://graph.facebook.com/v19.0/act_{account.ad_account_id}/campaigns'
            params = {
                'access_token': account.access_token,
                'fields': 'id,name,status,effective_status,start_time,updated_time',
                'limit': 100
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Facebook API error for account {account.ad_account_id}: {response.text}")
                return Response({
                    'success': False,
                    'message': f'Failed to fetch campaigns from Facebook: {response.text}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            facebook_data = response.json()
            
            for campaign_data in facebook_data.get('data', []):
                # Parse start_time if it exists
                start_time = None
                if campaign_data.get('start_time'):
                    try:
                        from datetime import datetime
                        start_time = datetime.fromisoformat(campaign_data['start_time'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # Use get_or_create to handle duplicate keys more gracefully
                try:
                    campaign, created = FacebookCampaign.objects.get_or_create(
                        campaign_id=campaign_data['id'],
                        defaults={
                            'ad_account': account,
                            'campaign_name': campaign_data['name'],
                            'status': campaign_data['status'],
                            'effective_status': campaign_data.get('effective_status', ''),
                            'start_time': start_time,
                        }
                    )
                    
                    # If campaign exists but belongs to different account, update it
                    if not created and campaign.ad_account != account:
                        campaign.ad_account = account
                        campaign.campaign_name = campaign_data['name']
                        campaign.status = campaign_data['status']
                        campaign.effective_status = campaign_data.get('effective_status', '')
                        campaign.start_time = start_time
                        campaign.save()
                        logger.info(f"Transferred campaign to new account: {campaign.campaign_name}")
                    elif not created:
                        # Update existing campaign data
                        campaign.campaign_name = campaign_data['name']
                        campaign.status = campaign_data['status']
                        campaign.effective_status = campaign_data.get('effective_status', '')
                        campaign.start_time = start_time
                        campaign.save()
                        logger.info(f"Updated existing campaign: {campaign.campaign_name}")
                    
                    campaigns_synced += 1
                    
                    if created:
                        logger.info(f"Created new campaign: {campaign.campaign_name}")
                        
                except Exception as e:
                    logger.error(f"Error processing campaign {campaign_data.get('id', 'unknown')}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching campaigns for account {account.ad_account_id}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error fetching campaigns: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'message': f'Successfully synced {campaigns_synced} campaigns for {account.ad_account_name}',
            'campaigns_synced': campaigns_synced,
            'account_name': account.ad_account_name
        })
        
    except Exception as e:
        logger.error(f"Error in fetch_campaigns_for_account: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_account_campaigns(request):
    """Get campaigns for a specific account with their selection status"""
    try:
        account_id = request.GET.get('account_id')
        
        if not account_id:
            return Response({
                'success': False,
                'message': 'Account ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the specific account
        account = FacebookAdAccount.objects.filter(
            id=account_id,
            user=request.user,
            is_active=True
        ).first()
        
        if not account:
            return Response({
                'success': False,
                'message': 'Account not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get campaigns for this account
        campaigns = FacebookCampaign.objects.filter(ad_account=account).order_by('campaign_name')
        
        # Get currently selected campaigns
        selected_campaign_ids = SelectedCampaign.objects.filter(
            user=request.user,
            is_monitoring=True,
            campaign__ad_account=account
        ).values_list('campaign__id', flat=True)
        
        # Serialize campaigns data
        campaigns_data = []
        for campaign in campaigns:
            campaigns_data.append({
                'id': campaign.id,
                'campaign_id': campaign.campaign_id,
                'campaign_name': campaign.campaign_name,
                'status': campaign.status,
                'effective_status': campaign.effective_status,
                'start_time': campaign.start_time.isoformat() if campaign.start_time else None,
                'last_synced': campaign.last_synced.isoformat() if campaign.last_synced else None,
            })
        
        selected_count = sum(1 for c in campaigns if c.id in selected_campaign_ids)
        
        return Response({
            'success': True,
            'campaigns': campaigns_data,
            'campaign_count': campaigns.count(),
            'selected_count': selected_count,
            'selected_campaign_ids': list(selected_campaign_ids)
        })
        
    except Exception as e:
        logger.error(f"Error getting account campaigns: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def account_detail(request, account_id):
    """Detailed view for a specific Facebook ad account"""
    # Get the account and verify it belongs to the user
    account = get_object_or_404(
        FacebookAdAccount, 
        id=account_id, 
        user=request.user, 
        is_active=True
    )
    
    # Get Facebook account info from API
    account_info = {}
    connection_status = 'unknown'
    try:
        api_version = 'v19.0'
        url = f'https://graph.facebook.com/{api_version}/act_{account.ad_account_id}'
        params = {
            'access_token': account.access_token,
            'fields': 'id,name,account_status,currency,timezone_name,min_campaign_group_spend_cap,spend_cap,amount_spent,balance,account_id,business,created_time,funding_source_details,owner,partner,disable_reason,end_advertiser,end_advertiser_name,is_notifications_enabled,is_personal,is_prepay_account,is_tax_id_required,line_numbers,media_agency,offsite_pixels_tos_accepted,tax_id,tax_id_status,tax_id_type,timezone_id,timezone_offset_hours_utc,tos_accepted,user_tasks,user_tos_accepted'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            account_info = response.json()
            connection_status = 'active'
        else:
            connection_status = 'error'
            logger.error(f"Facebook API error for account {account.ad_account_id}: {response.text}")
    except Exception as e:
        connection_status = 'error'
        logger.error(f"Error fetching account info: {str(e)}")
    
    # Get campaigns for this account
    campaigns = FacebookCampaign.objects.filter(ad_account=account).order_by('-start_time')
    
    # Get selected campaigns
    selected_campaigns = SelectedCampaign.objects.filter(
        user=request.user,
        is_monitoring=True,
        campaign__ad_account=account
    ).select_related('campaign')
    
    # Get ads for this account
    ads = FacebookAd.objects.filter(ad_account=account).order_by('-last_synced')[:50]
    
    # Calculate statistics
    stats = {
        'total_campaigns': campaigns.count(),
        'selected_campaigns': selected_campaigns.count(),
        'total_ads': ads.count(),
        'account_spend': account_info.get('amount_spent', 0),
        'account_balance': account_info.get('balance', 0),
        'spend_cap': account_info.get('spend_cap', 0),
    }
    
    return render(request, 'facebook_ads/account_detail.html', {
        'account': account,
        'account_info': account_info,
        'connection_status': connection_status,
        'campaigns': campaigns,
        'selected_campaigns': selected_campaigns,
        'ads': ads,
        'stats': stats,
        'active_tab': 'accounts'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pause_campaign(request):
    """Pause a Facebook campaign"""
    try:
        campaign_id = request.data.get('campaign_id')
        
        if not campaign_id:
            return Response({
                'success': False,
                'message': 'Campaign ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the campaign and verify it belongs to the user
        campaign = FacebookCampaign.objects.filter(
            campaign_id=campaign_id,
            ad_account__user=request.user,
            ad_account__is_active=True
        ).first()
        
        if not campaign:
            return Response({
                'success': False,
                'message': 'Campaign not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Make API call to Facebook to pause the campaign
        api_version = 'v19.0'
        url = f'https://graph.facebook.com/{api_version}/{campaign_id}'
        
        data = {
            'status': 'PAUSED',
            'access_token': campaign.ad_account.access_token
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            # Update local campaign status
            campaign.status = 'PAUSED'
            campaign.effective_status = 'PAUSED'
            campaign.save()
            
            return Response({
                'success': True,
                'message': f'Campaign "{campaign.campaign_name}" has been paused'
            })
        else:
            logger.error(f"Facebook API error pausing campaign {campaign_id}: {response.text}")
            return Response({
                'success': False,
                'message': 'Failed to pause campaign on Facebook'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error pausing campaign: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resume_campaign(request):
    """Resume a Facebook campaign"""
    try:
        campaign_id = request.data.get('campaign_id')
        
        if not campaign_id:
            return Response({
                'success': False,
                'message': 'Campaign ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the campaign and verify it belongs to the user
        campaign = FacebookCampaign.objects.filter(
            campaign_id=campaign_id,
            ad_account__user=request.user,
            ad_account__is_active=True
        ).first()
        
        if not campaign:
            return Response({
                'success': False,
                'message': 'Campaign not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Make API call to Facebook to resume the campaign
        api_version = 'v19.0'
        url = f'https://graph.facebook.com/{api_version}/{campaign_id}'
        
        data = {
            'status': 'ACTIVE',
            'access_token': campaign.ad_account.access_token
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            # Update local campaign status
            campaign.status = 'ACTIVE'
            campaign.effective_status = 'ACTIVE'
            campaign.save()
            
            return Response({
                'success': True,
                'message': f'Campaign "{campaign.campaign_name}" has been resumed'
            })
        else:
            logger.error(f"Facebook API error resuming campaign {campaign_id}: {response.text}")
            return Response({
                'success': False,
                'message': 'Failed to resume campaign on Facebook'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error resuming campaign: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comprehensive_sync_campaigns(request):
    """Comprehensive sync of campaigns with detailed insights and budget information"""
    try:
        account_id = request.data.get('account_id')
        
        if not account_id:
            return Response({
                'success': False,
                'message': 'Account ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the specific account
        account = FacebookAdAccount.objects.filter(
            id=account_id,
            user=request.user,
            is_active=True
        ).first()
        
        if not account:
            return Response({
                'success': False,
                'message': 'Account not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Use comprehensive service for detailed data
            service = ComprehensiveFacebookAPIService(account)
            
            # Fetch comprehensive campaign data
            campaigns_data = service.fetch_comprehensive_campaigns(limit=100)
            
            # Sync to database with all comprehensive fields
            synced_count = service.sync_comprehensive_campaigns_to_database(campaigns_data)
            
            return Response({
                'success': True,
                'message': f'Successfully synced {synced_count} campaigns with comprehensive data for {account.ad_account_name}',
                'synced_count': synced_count,
                'account_name': account.ad_account_name,
                'data_types': [
                    'Basic campaign info',
                    'Budget information',
                    'Performance metrics',
                    'Advanced insights',
                    'Actions and conversions data',
                    'Video engagement metrics'
                ]
            })
            
        except Exception as e:
            logger.error(f"Error in comprehensive campaign sync for account {account.ad_account_id}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error syncing comprehensive campaigns: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error in comprehensive_sync_campaigns: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comprehensive_sync_ads(request):
    """Comprehensive sync of ads with creative information and detailed insights"""
    try:
        account_id = request.data.get('account_id')
        
        if not account_id:
            return Response({
                'success': False,
                'message': 'Account ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the specific account
        account = FacebookAdAccount.objects.filter(
            id=account_id,
            user=request.user,
            is_active=True
        ).first()
        
        if not account:
            return Response({
                'success': False,
                'message': 'Account not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Use comprehensive service for detailed data
            service = ComprehensiveFacebookAPIService(account)
            
            # Fetch comprehensive ads data
            ads_data = service.fetch_comprehensive_ads(limit=200)
            
            # Sync to database with all comprehensive fields
            synced_count = service.sync_comprehensive_ads_to_database(ads_data)
            
            return Response({
                'success': True,
                'message': f'Successfully synced {synced_count} ads with comprehensive data for {account.ad_account_name}',
                'synced_count': synced_count,
                'account_name': account.ad_account_name,
                'data_types': [
                    'Basic ad information',
                    'Creative details (title, body, images, videos)',
                    'Campaign and adset info',
                    'Performance metrics',
                    'Advanced insights',
                    'Video engagement metrics',
                    'Quality rankings',
                    'Actions and conversions data',
                    'Targeting information'
                ]
            })
            
        except Exception as e:
            logger.error(f"Error in comprehensive ads sync for account {account.ad_account_id}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error syncing comprehensive ads: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error in comprehensive_sync_ads: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_campaign_detailed_insights(request):
    """Get detailed insights for a specific campaign with custom parameters"""
    try:
        campaign_id = request.data.get('campaign_id')
        time_range = request.data.get('time_range')  # Optional custom time range
        
        if not campaign_id:
            return Response({
                'success': False,
                'message': 'Campaign ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the campaign and verify it belongs to user's accounts
        campaign = FacebookCampaign.objects.filter(
            campaign_id=campaign_id,
            ad_account__user=request.user,
            ad_account__is_active=True
        ).first()
        
        if not campaign:
            return Response({
                'success': False,
                'message': 'Campaign not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Use comprehensive service for detailed insights
            service = ComprehensiveFacebookAPIService(campaign.ad_account)
            
            # Get detailed insights
            insights_data = service.get_campaign_detailed_insights(campaign_id, time_range)
            
            # Process and structure the response
            processed_insights = {
                'campaign_info': {
                    'id': campaign.campaign_id,
                    'name': campaign.campaign_name,
                    'status': campaign.status,
                    'objective': campaign.objective,
                },
                'performance_metrics': {
                    'impressions': int(insights_data.get('impressions', 0) or 0),
                    'clicks': int(insights_data.get('clicks', 0) or 0),
                    'spend': float(insights_data.get('spend', 0) or 0),
                    'reach': int(insights_data.get('reach', 0) or 0),
                    'frequency': float(insights_data.get('frequency', 0) or 0),
                    'ctr': float(insights_data.get('ctr', 0) or 0),
                    'cpm': float(insights_data.get('cpm', 0) or 0),
                    'cpc': float(insights_data.get('cpc', 0) or 0),
                },
                'advanced_metrics': {
                    'purchase_roas': float(insights_data.get('purchase_roas', 0) or 0),
                    'website_purchase_roas': float(insights_data.get('website_purchase_roas', 0) or 0),
                    'link_url_clicks': int(insights_data.get('link_url_clicks', 0) or 0),
                    'inline_link_clicks': int(insights_data.get('inline_link_clicks', 0) or 0),
                    'outbound_clicks': int(insights_data.get('outbound_clicks', 0) or 0),
                },
                'video_metrics': {
                    'video_p25_watched': int(insights_data.get('video_p25_watched_actions', 0) or 0),
                    'video_p50_watched': int(insights_data.get('video_p50_watched_actions', 0) or 0),
                    'video_p75_watched': int(insights_data.get('video_p75_watched_actions', 0) or 0),
                    'video_p100_watched': int(insights_data.get('video_p100_watched_actions', 0) or 0),
                },
                'actions_data': insights_data.get('actions_data', {}),
                'conversions_data': insights_data.get('conversions_data', {}),
            }
            
            return Response({
                'success': True,
                'campaign_insights': processed_insights,
                'time_range_used': time_range or 'Last 30 days'
            })
            
        except Exception as e:
            logger.error(f"Error getting detailed insights for campaign {campaign_id}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error fetching detailed insights: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error in get_campaign_detailed_insights: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comprehensive_campaign_data(request):
    """Get comprehensive campaign data from database with all metrics"""
    try:
        account_id = request.GET.get('account_id')
        campaign_filter = request.GET.get('filter', 'all')  # all, active, selected
        
        # Base queryset
        campaigns_queryset = FacebookCampaign.objects.filter(
            ad_account__user=request.user,
            ad_account__is_active=True
        ).select_related('ad_account')
        
        # Apply account filter if specified
        if account_id:
            campaigns_queryset = campaigns_queryset.filter(ad_account__id=account_id)
        
        # Apply campaign filter
        if campaign_filter == 'active':
            campaigns_queryset = campaigns_queryset.filter(status__in=['ACTIVE', 'LEARNING'])
        elif campaign_filter == 'selected':
            selected_campaign_ids = SelectedCampaign.objects.filter(
                user=request.user,
                is_monitoring=True
            ).values_list('campaign__id', flat=True)
            campaigns_queryset = campaigns_queryset.filter(id__in=selected_campaign_ids)
        
        # Serialize comprehensive campaign data
        campaigns_data = []
        for campaign in campaigns_queryset.order_by('-last_synced'):
            campaigns_data.append({
                'id': campaign.id,
                'campaign_id': campaign.campaign_id,
                'campaign_name': campaign.campaign_name,
                'status': campaign.status,
                'effective_status': campaign.effective_status,
                'objective': campaign.objective,
                'account_name': campaign.ad_account.ad_account_name,
                
                # Budget information
                'daily_budget': float(campaign.daily_budget) if campaign.daily_budget else None,
                'lifetime_budget': float(campaign.lifetime_budget) if campaign.lifetime_budget else None,
                'budget_remaining': float(campaign.budget_remaining) if campaign.budget_remaining else None,
                'spend_cap': float(campaign.spend_cap) if campaign.spend_cap else None,
                'bid_strategy': campaign.bid_strategy,
                'buying_type': campaign.buying_type,
                
                # Performance metrics
                'impressions': campaign.impressions,
                'clicks': campaign.clicks,
                'spend': float(campaign.spend),
                'reach': campaign.reach,
                'frequency': campaign.frequency,
                'ctr': campaign.ctr,
                'cpm': float(campaign.cpm),
                'cpc': float(campaign.cpc),
                
                # Advanced metrics
                'purchase_roas': campaign.purchase_roas,
                'website_purchase_roas': campaign.website_purchase_roas,
                'link_url_clicks': campaign.link_url_clicks,
                'inline_link_clicks': campaign.inline_link_clicks,
                'outbound_clicks': campaign.outbound_clicks,
                
                # Complex data
                'actions_data': campaign.actions_data,
                'conversions_data': campaign.conversions_data,
                'special_ad_categories': campaign.special_ad_categories,
                
                # Timestamps
                'created_time': campaign.created_time.isoformat() if campaign.created_time else None,
                'updated_time': campaign.updated_time.isoformat() if campaign.updated_time else None,
                'start_time': campaign.start_time.isoformat() if campaign.start_time else None,
                'stop_time': campaign.stop_time.isoformat() if campaign.stop_time else None,
                'last_synced': campaign.last_synced.isoformat(),
            })
        
        return Response({
            'success': True,
            'campaigns': campaigns_data,
            'total_count': len(campaigns_data),
            'filter_applied': campaign_filter
        })
        
    except Exception as e:
        logger.error(f"Error in get_comprehensive_campaign_data: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comprehensive_ads_data(request):
    """Get comprehensive ads data from database with all metrics and creative info"""
    try:
        account_id = request.GET.get('account_id')
        campaign_id = request.GET.get('campaign_id')
        limit = int(request.GET.get('limit', 50))
        
        # Base queryset
        ads_queryset = FacebookAd.objects.filter(
            ad_account__user=request.user,
            ad_account__is_active=True
        ).select_related('ad_account')
        
        # Apply filters
        if account_id:
            ads_queryset = ads_queryset.filter(ad_account__id=account_id)
        
        if campaign_id:
            ads_queryset = ads_queryset.filter(campaign_id=campaign_id)
        
        # Serialize comprehensive ads data
        ads_data = []
        for ad in ads_queryset.order_by('-last_synced')[:limit]:
            ads_data.append({
                'id': ad.id,
                'ad_id': ad.ad_id,
                'ad_name': ad.ad_name,
                'status': ad.status,
                'effective_status': ad.effective_status,
                'configured_status': ad.configured_status,
                'account_name': ad.ad_account.ad_account_name,
                
                # Campaign and Adset info
                'campaign_id': ad.campaign_id,
                'campaign_name': ad.campaign_name,
                'campaign_objective': ad.campaign_objective,
                'adset_id': ad.adset_id,
                'adset_name': ad.adset_name,
                'optimization_goal': ad.optimization_goal,
                'billing_event': ad.billing_event,
                'bid_amount': float(ad.bid_amount) if ad.bid_amount else None,
                
                # Creative information
                'creative_id': ad.creative_id,
                'creative_title': ad.creative_title,
                'creative_body': ad.creative_body,
                'creative_image_url': ad.creative_image_url,
                'creative_video_id': ad.creative_video_id,
                'call_to_action_type': ad.call_to_action_type,
                
                # Performance metrics
                'impressions': ad.impressions,
                'clicks': ad.clicks,
                'spend': float(ad.spend),
                'reach': ad.reach,
                'frequency': ad.frequency,
                'ctr': ad.ctr,
                'cpm': float(ad.cpm),
                'cpc': float(ad.cpc),
                
                # Advanced metrics
                'purchase_roas': ad.purchase_roas,
                'website_purchase_roas': ad.website_purchase_roas,
                'link_url_clicks': ad.link_url_clicks,
                'inline_link_clicks': ad.inline_link_clicks,
                'outbound_clicks': ad.outbound_clicks,
                'unique_clicks': ad.unique_clicks,
                'unique_ctr': ad.unique_ctr,
                
                # Video engagement metrics
                'video_avg_time_watched': ad.video_avg_time_watched,
                'video_p25_watched': ad.video_p25_watched,
                'video_p50_watched': ad.video_p50_watched,
                'video_p75_watched': ad.video_p75_watched,
                'video_p100_watched': ad.video_p100_watched,
                
                # Quality rankings
                'quality_ranking': ad.quality_ranking,
                'engagement_rate_ranking': ad.engagement_rate_ranking,
                'conversion_rate_ranking': ad.conversion_rate_ranking,
                
                # Complex data
                'actions_data': ad.actions_data,
                'conversions_data': ad.conversions_data,
                'targeting_data': ad.targeting_data,
                'tracking_specs': ad.tracking_specs,
                'conversion_specs': ad.conversion_specs,
                'promoted_object': ad.promoted_object,
                
                # Timestamps
                'created_time': ad.created_time.isoformat() if ad.created_time else None,
                'updated_time': ad.updated_time.isoformat() if ad.updated_time else None,
                'last_synced': ad.last_synced.isoformat(),
            })
        
        return Response({
            'success': True,
            'ads': ads_data,
            'total_count': len(ads_data),
            'limit_applied': limit
        })
        
    except Exception as e:
        logger.error(f"Error in get_comprehensive_ads_data: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# New Dashboard API Endpoints

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """Get dashboard data with period filtering"""
    try:
        from .services import DashboardService
        
        period = request.GET.get('period', 'last_7d')
        account_ids = request.GET.get('account_ids', '')
        
        # Parse account IDs
        account_ids_list = []
        if account_ids:
            account_ids_list = [int(id.strip()) for id in account_ids.split(',') if id.strip()]
        
        service = DashboardService(request.user)
        data = service.get_dashboard_data(period, account_ids_list)
        
        return Response({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting dashboard data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_insights(request, campaign_id):
    """Get insights for a specific campaign"""
    try:
        from .services import DashboardService
        
        period = request.GET.get('period', 'last_30d')
        
        # Find the campaign
        campaign = FacebookCampaign.objects.get(
            campaign_id=campaign_id,
            ad_account__user=request.user
        )
        
        service = DashboardService(request.user)
        insights = service.get_campaign_insights(campaign, period)
        
        return Response({
            'success': True,
            'data': insights
        })
        
    except FacebookCampaign.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Campaign not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting campaign insights: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting campaign insights: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_periods(request):
    """Get available dashboard periods"""
    try:
        from .services import DashboardService
        
        service = DashboardService(request.user)
        periods = [
            {'name': 'today', 'display_name': 'Vandaag'},
            {'name': 'yesterday', 'display_name': 'Gisteren'},
            {'name': 'last_7d', 'display_name': 'Laatste 7 dagen'},
            {'name': 'last_14d', 'display_name': 'Laatste 14 dagen'},
            {'name': 'last_30d', 'display_name': 'Laatste 30 dagen'},
            {'name': 'this_month', 'display_name': 'Deze maand'},
            {'name': 'last_month', 'display_name': 'Vorige maand'},
        ]
        
        return Response({
            'success': True,
            'periods': periods
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard periods: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting dashboard periods: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_sync(request):
    """Trigger manual sync for user's accounts"""
    try:
        from .tasks import sync_facebook_campaigns, full_account_sync
        
        sync_type = request.data.get('sync_type', 'campaigns')
        account_id = request.data.get('account_id')
        
        if account_id:
            # Sync specific account
            account = FacebookAdAccount.objects.get(
                id=account_id,
                user=request.user,
                is_active=True
            )
            
            if sync_type == 'full':
                task = full_account_sync.delay(account.id)
            else:
                task = sync_facebook_campaigns.delay(account.id)
            
            return Response({
                'success': True,
                'message': f'Sync started for account {account.ad_account_name}',
                'task_id': task.id
            })
        else:
            # Sync all user's accounts
            task = sync_facebook_campaigns.delay()
            
            return Response({
                'success': True,
                'message': 'Sync started for all accounts',
                'task_id': task.id
            })
            
    except FacebookAdAccount.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Account not found or not accessible'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error triggering sync: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error triggering sync: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_status(request, task_id):
    """Get sync task status"""
    try:
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        return Response({
            'success': True,
            'task_id': task_id,
            'status': task.status,
            'result': task.result,
            'info': task.info
        })
        
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting sync status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_performance_alerts(request):
    """Get performance alerts for campaigns"""
    try:
        from .services import DashboardService
        
        service = DashboardService(request.user)
        
        # Get campaigns
        campaigns = FacebookCampaign.objects.filter(
            ad_account__user=request.user,
            ad_account__is_active=True
        )
        
        # Generate alerts
        alerts = service._generate_alerts(None, campaigns)
        
        return Response({
            'success': True,
            'alerts': alerts
        })
        
    except Exception as e:
        logger.error(f"Error getting performance alerts: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting performance alerts: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_trends(request):
    """Get campaign trends data"""
    try:
        from .services import DashboardService
        
        period = request.GET.get('period', 'last_30d')
        campaign_ids = request.GET.get('campaign_ids', '')
        
        service = DashboardService(request.user)
        
        # Get specific campaigns or all campaigns
        if campaign_ids:
            campaign_ids_list = [id.strip() for id in campaign_ids.split(',') if id.strip()]
            campaigns = FacebookCampaign.objects.filter(
                campaign_id__in=campaign_ids_list,
                ad_account__user=request.user
            )
        else:
            campaigns = FacebookCampaign.objects.filter(
                ad_account__user=request.user,
                ad_account__is_active=True
            )
        
        # Get period and date range
        period_config = service._get_period_config(period)
        date_range = service._get_date_range(period_config)
        
        # Get insights for trends
        insights = service._get_insights_for_period(campaigns, date_range)
        trends = service._calculate_trends(insights)
        
        return Response({
            'success': True,
            'trends': trends,
            'period': period_config
        })
        
    except Exception as e:
        logger.error(f"Error getting campaign trends: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting campaign trends: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def adset_data(request, campaign_id):
    """Get AdSet data for a specific campaign"""
    try:
        from .models import FacebookAdSet
        
        # Verify campaign belongs to user
        campaign = FacebookCampaign.objects.get(
            campaign_id=campaign_id,
            ad_account__user=request.user
        )
        
        # Get AdSets for this campaign
        adsets = FacebookAdSet.objects.filter(
            campaign=campaign
        ).order_by('-last_synced')
        
        adset_data = []
        for adset in adsets:
            adset_data.append({
                'adset_id': adset.adset_id,
                'adset_name': adset.adset_name,
                'status': adset.status,
                'effective_status': adset.effective_status,
                'daily_budget': float(adset.daily_budget) if adset.daily_budget else None,
                'lifetime_budget': float(adset.lifetime_budget) if adset.lifetime_budget else None,
                'bid_amount': float(adset.bid_amount) if adset.bid_amount else None,
                'optimization_goal': adset.optimization_goal,
                'spend': float(adset.spend),
                'impressions': adset.impressions,
                'clicks': adset.clicks,
                'ctr': adset.ctr,
                'cpc': float(adset.cpc),
                'roas': adset.purchase_roas,
                'start_time': adset.start_time,
                'end_time': adset.end_time,
                'last_synced': adset.last_synced
            })
        
        return Response({
            'success': True,
            'campaign': {
                'id': campaign.campaign_id,
                'name': campaign.campaign_name,
                'status': campaign.status
            },
            'adsets': adset_data
        })
        
    except FacebookCampaign.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Campaign not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting AdSet data: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting AdSet data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ad_data(request, campaign_id):
    """Get Ad data for a specific campaign"""
    try:
        # Verify campaign belongs to user
        campaign = FacebookCampaign.objects.get(
            campaign_id=campaign_id,
            ad_account__user=request.user
        )
        
        # Get Ads for this campaign
        ads = FacebookAd.objects.filter(
            campaign_id=campaign_id,
            ad_account__user=request.user
        ).order_by('-last_synced')
        
        ad_data = []
        for ad in ads:
            ad_data.append({
                'ad_id': ad.ad_id,
                'ad_name': ad.ad_name,
                'status': ad.status,
                'effective_status': ad.effective_status,
                'adset_id': ad.adset_id,
                'adset_name': ad.adset_name,
                'creative_title': ad.creative_title,
                'creative_body': ad.creative_body,
                'creative_image_url': ad.creative_image_url,
                'call_to_action_type': ad.call_to_action_type,
                'spend': float(ad.spend),
                'impressions': ad.impressions,
                'clicks': ad.clicks,
                'ctr': ad.ctr,
                'cpc': float(ad.cpc),
                'roas': ad.purchase_roas,
                'quality_ranking': ad.quality_ranking,
                'engagement_rate_ranking': ad.engagement_rate_ranking,
                'conversion_rate_ranking': ad.conversion_rate_ranking,
                'created_time': ad.created_time,
                'last_synced': ad.last_synced
            })
        
        return Response({
            'success': True,
            'campaign': {
                'id': campaign.campaign_id,
                'name': campaign.campaign_name,
                'status': campaign.status
            },
            'ads': ad_data
        })
        
    except FacebookCampaign.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Campaign not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting Ad data: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting Ad data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# OPTIMIZATION STRATEGY MANAGEMENT VIEWS
# ============================================================================

@login_required
def strategy_list(request):
    """View to list all optimization strategies for the current user"""
    strategies = OptimizationStrategy.objects.filter(user=request.user).order_by('-created_at')

    # Count campaigns using each strategy
    for strategy in strategies:
        strategy.campaign_count = CampaignOptimization.objects.filter(
            strategy=strategy,
            is_active=True
        ).count()

    return render(request, 'facebook_ads/optimization/strategy_list.html', {
        'strategies': strategies,
        'active_tab': 'optimization'
    })


@login_required
def strategy_detail(request, strategy_id):
    """View to show details of a specific strategy"""
    strategy = get_object_or_404(OptimizationStrategy, id=strategy_id, user=request.user)

    # Get campaigns using this strategy
    campaign_optimizations = CampaignOptimization.objects.filter(
        strategy=strategy,
        is_active=True
    ).select_related('campaign')

    # Get recent logs for this strategy
    recent_logs = OptimizationLog.objects.filter(
        strategy=strategy
    ).select_related('campaign').order_by('-check_time')[:20]

    return render(request, 'facebook_ads/optimization/strategy_detail.html', {
        'strategy': strategy,
        'campaign_optimizations': campaign_optimizations,
        'recent_logs': recent_logs,
        'active_tab': 'optimization'
    })


@login_required
def strategy_create(request):
    """View to create a new optimization strategy"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        rules_json = request.POST.get('rules')

        try:
            import json
            rules = json.loads(rules_json) if rules_json else {'rules': []}

            strategy = OptimizationStrategy.objects.create(
                user=request.user,
                name=name,
                description=description,
                is_active=is_active,
                rules=rules
            )

            messages.success(request, f'Strategy "{name}" created successfully!')
            return redirect('facebook_ads:strategy_detail', strategy_id=strategy.id)

        except Exception as e:
            messages.error(request, f'Error creating strategy: {str(e)}')
            logger.error(f"Error creating strategy: {str(e)}")

    return render(request, 'facebook_ads/optimization/strategy_form.html', {
        'mode': 'create',
        'active_tab': 'optimization'
    })


@login_required
def strategy_edit(request, strategy_id):
    """View to edit an existing optimization strategy"""
    strategy = get_object_or_404(OptimizationStrategy, id=strategy_id, user=request.user)

    if request.method == 'POST':
        strategy.name = request.POST.get('name')
        strategy.description = request.POST.get('description', '')
        strategy.is_active = request.POST.get('is_active') == 'on'

        rules_json = request.POST.get('rules')
        try:
            import json
            strategy.rules = json.loads(rules_json) if rules_json else {'rules': []}
            strategy.save()

            messages.success(request, f'Strategy "{strategy.name}" updated successfully!')
            return redirect('facebook_ads:strategy_detail', strategy_id=strategy.id)

        except Exception as e:
            messages.error(request, f'Error updating strategy: {str(e)}')
            logger.error(f"Error updating strategy: {str(e)}")

    import json
    return render(request, 'facebook_ads/optimization/strategy_form.html', {
        'mode': 'edit',
        'strategy': strategy,
        'rules_json': json.dumps(strategy.rules, indent=2),
        'active_tab': 'optimization'
    })


@login_required
def strategy_delete(request, strategy_id):
    """View to delete an optimization strategy"""
    strategy = get_object_or_404(OptimizationStrategy, id=strategy_id, user=request.user)

    if request.method == 'POST':
        # Check if strategy is in use
        active_optimizations = CampaignOptimization.objects.filter(
            strategy=strategy,
            is_active=True
        ).count()

        if active_optimizations > 0:
            messages.error(
                request,
                f'Cannot delete strategy "{strategy.name}" - it is currently active on {active_optimizations} campaign(s). '
                'Please disable it on all campaigns first.'
            )
            return redirect('facebook_ads:strategy_detail', strategy_id=strategy.id)

        strategy_name = strategy.name
        strategy.delete()
        messages.success(request, f'Strategy "{strategy_name}" deleted successfully!')
        return redirect('facebook_ads:strategy_list')

    return render(request, 'facebook_ads/optimization/strategy_delete_confirm.html', {
        'strategy': strategy,
        'active_tab': 'optimization'
    })


@login_required
def optimization_dashboard(request):
    """Main optimization dashboard showing all campaigns with optimization status"""
    from django.db.models import Q, Count, Max
    from datetime import date, timedelta

    # Get date filter from query params (default to today)
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    # Get all user's campaigns with optimization status
    user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
    campaigns = FacebookCampaign.objects.filter(
        ad_account__in=user_accounts
    ).select_related('ad_account').prefetch_related('optimizations')

    # Add optimization info to each campaign
    campaign_data = []
    for campaign in campaigns:
        active_opt = campaign.optimizations.filter(is_active=True).first()

        # Get latest metrics for the selected date
        try:
            period = DailyPeriod.objects.get(date=selected_date)
            metrics = OptimizationMetrics.objects.filter(
                campaign=campaign,
                period=period
            ).first()
        except (DailyPeriod.DoesNotExist, OptimizationMetrics.DoesNotExist):
            metrics = None

        # Get latest log entry
        latest_log = OptimizationLog.objects.filter(
            campaign=campaign
        ).order_by('-check_time').first()

        campaign_data.append({
            'campaign': campaign,
            'optimization': active_opt,
            'metrics': metrics,
            'latest_log': latest_log,
            'has_optimization': active_opt is not None,
        })

    # Get available strategies
    strategies = OptimizationStrategy.objects.filter(user=request.user, is_active=True)

    # Summary stats
    total_campaigns = len(campaign_data)
    optimized_campaigns = sum(1 for c in campaign_data if c['has_optimization'])
    active_campaigns = campaigns.filter(status='ACTIVE').count()

    return render(request, 'facebook_ads/optimization/dashboard.html', {
        'campaign_data': campaign_data,
        'strategies': strategies,
        'selected_date': selected_date,
        'total_campaigns': total_campaigns,
        'optimized_campaigns': optimized_campaigns,
        'active_campaigns': active_campaigns,
        'active_tab': 'optimization'
    })


@login_required
def optimization_logs(request):
    """View optimization logs with filtering"""
    from datetime import datetime, timedelta

    # Get filter parameters
    campaign_id = request.GET.get('campaign')
    strategy_id = request.GET.get('strategy')
    action = request.GET.get('action')
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')

    # Base query - only logs for user's campaigns
    user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
    user_campaigns = FacebookCampaign.objects.filter(ad_account__in=user_accounts)

    logs = OptimizationLog.objects.filter(
        campaign__in=user_campaigns
    ).select_related('campaign', 'strategy', 'campaign_optimization').order_by('-check_time')

    # Apply filters
    if campaign_id:
        logs = logs.filter(campaign_id=campaign_id)

    if strategy_id:
        logs = logs.filter(strategy_id=strategy_id)

    if action:
        logs = logs.filter(action=action)

    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            logs = logs.filter(check_time__gte=date_from)
        except ValueError:
            pass

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            # Add one day to include the entire end date
            date_to = date_to + timedelta(days=1)
            logs = logs.filter(check_time__lt=date_to)
        except ValueError:
            pass

    # Get filter options
    campaigns = user_campaigns.order_by('campaign_name')
    strategies = OptimizationStrategy.objects.filter(user=request.user).order_by('name')
    action_choices = OptimizationLog.ACTION_CHOICES

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)  # Show 50 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'facebook_ads/optimization/logs.html', {
        'logs': page_obj,
        'campaigns': campaigns,
        'strategies': strategies,
        'action_choices': action_choices,
        'filters': {
            'campaign_id': campaign_id,
            'strategy_id': strategy_id,
            'action': action,
            'date_from': date_from_str,
            'date_to': date_to_str,
        },
        'active_tab': 'optimization'
    })


# ============================================================================
# OPTIMIZATION API ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enable_campaign_optimization(request):
    """Enable optimization for a campaign with a specific strategy"""
    campaign_id = request.data.get('campaign_id')
    strategy_id = request.data.get('strategy_id')

    try:
        # Verify user owns the campaign
        user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        campaign = FacebookCampaign.objects.get(
            id=campaign_id,
            ad_account__in=user_accounts
        )

        # Verify user owns the strategy
        strategy = OptimizationStrategy.objects.get(
            id=strategy_id,
            user=request.user
        )

        # Check if optimization already exists (active or inactive)
        existing = CampaignOptimization.objects.filter(
            campaign=campaign,
            strategy=strategy
        ).first()

        if existing:
            # Re-enable or update existing optimization
            if not existing.is_active:
                existing.is_active = True
                existing.optimization_start_date = timezone.now().date()
                existing.save()
                message = f'Re-enabled optimization for {campaign.campaign_name}'
            else:
                # Already active with this strategy
                message = f'Optimization already active for {campaign.campaign_name}'
        else:
            # Check if there's an active optimization with a different strategy
            active_optimization = CampaignOptimization.objects.filter(
                campaign=campaign,
                is_active=True
            ).first()

            if active_optimization:
                # Update to new strategy
                active_optimization.strategy = strategy
                active_optimization.optimization_start_date = timezone.now().date()
                active_optimization.save()
                message = f'Updated optimization strategy for {campaign.campaign_name}'
            else:
                # Create new optimization
                CampaignOptimization.objects.create(
                    user=request.user,
                    campaign=campaign,
                    strategy=strategy,
                    is_active=True
                )
                message = f'Enabled optimization for {campaign.campaign_name}'

        return Response({
            'success': True,
            'message': message
        })

    except FacebookCampaign.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Campaign not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except OptimizationStrategy.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Strategy not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error enabling optimization: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_campaign_optimization(request):
    """Disable optimization for a campaign"""
    campaign_id = request.data.get('campaign_id')

    try:
        from datetime import datetime

        # Verify user owns the campaign
        user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        campaign = FacebookCampaign.objects.get(
            id=campaign_id,
            ad_account__in=user_accounts
        )

        # Find and disable active optimization
        optimization = CampaignOptimization.objects.filter(
            campaign=campaign,
            is_active=True
        ).first()

        if optimization:
            optimization.is_active = False
            optimization.date_disabled = datetime.now()
            optimization.save()

            return Response({
                'success': True,
                'message': f'Disabled optimization for {campaign.campaign_name}'
            })
        else:
            return Response({
                'success': False,
                'message': 'No active optimization found for this campaign'
            }, status=status.HTTP_404_NOT_FOUND)

    except FacebookCampaign.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Campaign not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error disabling optimization: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_optimization_now(request):
    """Manually trigger optimization check for a campaign"""
    campaign_id = request.data.get('campaign_id')

    try:
        # Verify user owns the campaign
        user_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        campaign = FacebookCampaign.objects.get(
            id=campaign_id,
            ad_account__in=user_accounts
        )

        # Check if optimization is enabled
        optimization = CampaignOptimization.objects.filter(
            campaign=campaign,
            is_active=True
        ).first()

        if not optimization:
            return Response({
                'success': False,
                'message': 'Optimization is not enabled for this campaign'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Trigger Celery task to run optimization
        from .tasks import run_single_campaign_optimization
        run_single_campaign_optimization.delay(campaign.campaign_id)

        return Response({
            'success': True,
            'message': f'Optimization check started for {campaign.campaign_name}'
        })

    except FacebookCampaign.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Campaign not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error running optimization: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
