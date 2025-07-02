from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Avg, Count, F
from apps.facebook_ads.models import FacebookAdAccount, FacebookAd, SelectedCampaign, FacebookCampaign
import requests
import logging

logger = logging.getLogger(__name__)


def home(request):
    if request.user.is_authenticated:
        # Get Facebook ads data for all active campaigns
        facebook_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        
        # Get campaign filter from request (default to 'active')
        campaign_filter = request.GET.get('filter', 'active')
        
        # Get all campaigns based on filter
        if campaign_filter == 'selected':
            # Show only selected campaigns (original behavior)
            selected_campaigns = SelectedCampaign.objects.filter(
                user=request.user, 
                is_monitoring=True
            ).select_related('campaign')
            campaign_ids = [sc.campaign.campaign_id for sc in selected_campaigns]
            campaigns_queryset = FacebookCampaign.objects.filter(
                campaign_id__in=campaign_ids,
                ad_account__in=facebook_accounts
            )
        elif campaign_filter == 'all':
            # Show all campaigns
            campaigns_queryset = FacebookCampaign.objects.filter(
                ad_account__in=facebook_accounts
            )
        else:  # campaign_filter == 'active' (default)
            # Show all active campaigns
            campaigns_queryset = FacebookCampaign.objects.filter(
                ad_account__in=facebook_accounts,
                status__in=['ACTIVE', 'LEARNING']
            )
        
        # Get campaign IDs for filtering ads
        campaign_ids = [campaign.campaign_id for campaign in campaigns_queryset]
        
        # Filter ads to show based on selected filter
        if campaign_ids:
            facebook_ads = FacebookAd.objects.filter(
                ad_account__in=facebook_accounts,
                campaign_id__in=campaign_ids
            ).order_by('-last_synced')[:10]
        else:
            facebook_ads = FacebookAd.objects.none()

        # Get detailed campaign statistics
        campaign_stats = []
        if campaign_ids:
            for campaign in campaigns_queryset:
                # Get ads for this specific campaign
                campaign_ads = FacebookAd.objects.filter(
                    campaign_id=campaign.campaign_id,
                    ad_account__in=facebook_accounts
                ).aggregate(
                    total_spend=Sum('spend'),
                    total_clicks=Sum('clicks'),
                    total_impressions=Sum('impressions'),
                    avg_cpc=Avg('cpc'),
                    avg_cpm=Avg('cpm'),
                    avg_ctr=Avg('ctr'),
                    ad_count=Count('id')
                )

                # Calculate ROAS (dummy calculation - you may want to add actual conversion data)
                roas = 0
                if campaign_ads['total_spend'] and campaign_ads['total_spend'] > 0:
                    # This is a placeholder - you'll need actual conversion value data
                    estimated_revenue = float(campaign_ads['total_spend']) * 2.5  # Example multiplier
                    roas = estimated_revenue / float(campaign_ads['total_spend'])

                # Check if campaign is selected for monitoring
                is_selected = SelectedCampaign.objects.filter(
                    user=request.user,
                    campaign=campaign,
                    is_monitoring=True
                ).exists()

                campaign_stats.append({
                    'campaign': campaign,
                    'total_spend': campaign_ads['total_spend'] or 0,
                    'total_clicks': campaign_ads['total_clicks'] or 0,
                    'total_impressions': campaign_ads['total_impressions'] or 0,
                    'avg_cpc': campaign_ads['avg_cpc'] or 0,
                    'avg_cpm': campaign_ads['avg_cpm'] or 0,
                    'avg_ctr': campaign_ads['avg_ctr'] or 0,
                    'ad_count': campaign_ads['ad_count'] or 0,
                    'roas': round(roas, 2),
                    'status_badge': get_campaign_status_badge(campaign.status, roas),
                    'is_selected': is_selected
                })

        # Calculate overall dashboard metrics
        overall_stats = {
            'total_spend': sum(stat['total_spend'] for stat in campaign_stats),
            'total_clicks': sum(stat['total_clicks'] for stat in campaign_stats),
            'total_impressions': sum(stat['total_impressions'] for stat in campaign_stats),
            'avg_cpc': sum(stat['avg_cpc'] for stat in campaign_stats if stat['avg_cpc']) / len(campaign_stats) if campaign_stats else 0,
            'avg_roas': sum(stat['roas'] for stat in campaign_stats) / len(campaign_stats) if campaign_stats else 0,
            'active_campaigns': len(campaign_stats)
        }

        # Get selected campaigns count for display
        selected_campaigns_count = SelectedCampaign.objects.filter(
            user=request.user, 
            is_monitoring=True
        ).count()

        # Serialize accounts for JavaScript
        facebook_accounts_data = [
            {'id': account.id, 'ad_account_id': account.ad_account_id, 'ad_account_name': account.ad_account_name}
            for account in facebook_accounts
        ]
        
        return render(
            request,
            "web/app_home.html",
            context={
                "active_tab": "dashboard",
                "page_title": _("Dashboard"),
                "facebook_accounts": facebook_accounts_data,
                "facebook_ads": facebook_ads,
                "selected_campaigns_count": selected_campaigns_count,
                "show_facebook_setup_modal": not facebook_accounts.exists(),
                "campaign_stats": campaign_stats,
                "overall_stats": overall_stats,
                "current_filter": campaign_filter,
            },
        )
    else:
        return render(request, "web/landing_page.html")


def get_campaign_status_badge(status, roas):
    """Determine campaign status badge based on status and performance"""
    if status.upper() == 'ACTIVE':
        if roas >= 3.0:
            return {'class': 'bg-green-100 text-green-800', 'text': 'High-Perf'}
        elif roas >= 2.0:
            return {'class': 'bg-blue-100 text-blue-800', 'text': 'Running'}
        elif roas >= 1.0:
            return {'class': 'bg-yellow-100 text-yellow-800', 'text': 'Learning'}
        else:
            return {'class': 'bg-red-100 text-red-800', 'text': 'Under-Perf'}
    elif status.upper() == 'PAUSED':
        return {'class': 'bg-gray-100 text-gray-800', 'text': 'Paused'}
    else:
        return {'class': 'bg-gray-100 text-gray-800', 'text': status.title()}


def simulate_error(request):
    raise Exception("This is a simulated error.")
