from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from apps.facebook_ads.models import FacebookAdAccount, FacebookAd, SelectedCampaign


def home(request):
    if request.user.is_authenticated:
        # Get Facebook ads data for selected campaigns only
        facebook_accounts = FacebookAdAccount.objects.filter(user=request.user, is_active=True)
        
        # Get selected campaigns for this user
        selected_campaigns = SelectedCampaign.objects.filter(
            user=request.user, 
            is_monitoring=True
        ).select_related('campaign')
        
        # Get campaign IDs for filtering ads
        selected_campaign_ids = [sc.campaign.campaign_id for sc in selected_campaigns]
        
        # Filter ads to only show those from selected campaigns
        if selected_campaign_ids:
            facebook_ads = FacebookAd.objects.filter(
                ad_account__in=facebook_accounts,
                campaign_id__in=selected_campaign_ids
            ).order_by('-last_synced')[:10]
        else:
            facebook_ads = FacebookAd.objects.none()  # No ads if no campaigns selected
        
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
                "selected_campaigns_count": selected_campaigns.count(),
                "show_facebook_setup_modal": not facebook_accounts.exists(),
            },
        )
    else:
        return render(request, "web/landing_page.html")


def simulate_error(request):
    raise Exception("This is a simulated error.")
