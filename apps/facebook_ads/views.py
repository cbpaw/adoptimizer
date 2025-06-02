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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import FacebookAdAccount, FacebookAd, FacebookCampaign, SelectedCampaign
from .services import FacebookMarketingAPIService, get_facebook_auth_url, exchange_code_for_token

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
def manage_accounts(request):
    """Manage Facebook ad accounts"""
    accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
    return render(request, 'facebook_ads/manage_accounts.html', {
        'accounts': accounts,
        'active_tab': 'facebook-ads'
    })


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
        # Use DRF's request.data instead of json.loads(request.body)
        access_token = request.data.get('access_token')
        
        if not access_token:
            return Response({
                'success': False,
                'message': 'Access token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Make API call to Facebook to get ad accounts
        url = f'https://graph.facebook.com/v19.0/me/adaccounts'
        params = {
            'access_token': access_token,
            'fields': 'id,name,account_status,currency,timezone_name'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.error(f"Facebook API error: {response.text}")
            return Response({
                'success': False,
                'message': 'Failed to fetch ad accounts from Facebook'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        facebook_data = response.json()
        accounts = []
        
        for account_data in facebook_data.get('data', []):
            accounts.append({
                'id': account_data['id'],
                'name': account_data['name'],
                'account_status': account_data.get('account_status'),
                'currency': account_data.get('currency'),
                'timezone': account_data.get('timezone_name')
            })
        
        return Response({
            'success': True,
            'accounts': accounts
        })
        
    except Exception as e:
        logger.error(f"Error fetching ad accounts: {str(e)}")
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
        app_id = request.data.get('app_id')
        access_token = request.data.get('access_token')
        account_id = request.data.get('account_id')
        
        if not all([app_id, access_token, account_id]):
            return Response({
                'success': False,
                'message': 'App ID, access token, and account ID are required'
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
        
        # Check if account already exists for this user
        existing_account = FacebookAdAccount.objects.filter(
            user=request.user,
            ad_account_id=account_id,
            is_active=True
        ).first()
        
        if existing_account:
            # Update existing account
            existing_account.access_token = access_token
            existing_account.app_id = app_id
            existing_account.ad_account_name = account_info.get('name', '')
            existing_account.save()
            fb_account = existing_account
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
        
        # Immediately sync some ads to test the connection
        try:
            service = FacebookMarketingAPIService(fb_account)
            ads_data = service.fetch_ads(limit=50, status_filter=['ACTIVE', 'PAUSED'])
            synced_count = service.sync_ads_to_database(ads_data)
            
            return Response({
                'success': True,
                'message': f'Account connected successfully! Synced {synced_count} ads.',
                'account_id': fb_account.id,
                'synced_count': synced_count
            })
        except Exception as sync_error:
            logger.warning(f"Account connected but failed to sync ads: {str(sync_error)}")
            return Response({
                'success': True,
                'message': 'Account connected successfully! You can sync ads manually.',
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
    
    return render(request, 'facebook_ads/campaign_selection.html', {
        'campaigns': campaigns,
        'selected_campaign_ids': list(selected_campaign_ids),
        'user_accounts': user_accounts,
        'active_tab': 'facebook-ads'
    })


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
                    
                    # Update or create campaign
                    campaign, created = FacebookCampaign.objects.update_or_create(
                        ad_account=account,
                        campaign_id=campaign_data['id'],
                        defaults={
                            'campaign_name': campaign_data['name'],
                            'status': campaign_data['status'],
                            'effective_status': campaign_data.get('effective_status', ''),
                            'start_time': start_time,
                        }
                    )
                    total_campaigns += 1
                    
                    if created:
                        logger.info(f"Created new campaign: {campaign.campaign_name}")
                    else:
                        logger.info(f"Updated campaign: {campaign.campaign_name}")
                        
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
    
    return render(request, 'facebook_ads/settings.html', {
        'user_accounts': user_accounts,
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
