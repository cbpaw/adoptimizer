from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.template.response import TemplateResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.forms import DateRangeForm
from apps.dashboard.serializers import UserSignupStatsSerializer
from apps.dashboard.services import get_user_signups
from apps.users.models import CustomUser
from apps.facebook_ads.models import FacebookAdAccount, FacebookAd, SelectedCampaign


def _string_to_date(date_str: str) -> datetime.date:
    date_format = "%Y-%m-%d"
    return datetime.strptime(date_str, date_format).date()


@user_passes_test(lambda u: u.is_superuser, login_url="/404")
@staff_member_required
def dashboard(request):
    end_str = request.GET.get("end")
    end = _string_to_date(end_str) if end_str else timezone.now().date() + timedelta(days=1)
    start_str = request.GET.get("start")
    start = _string_to_date(start_str) if start_str else end - timedelta(days=90)
    serializer = UserSignupStatsSerializer(get_user_signups(start, end), many=True)
    form = DateRangeForm(initial={"start": start, "end": end})
    start_value = CustomUser.objects.filter(date_joined__lt=start).count()
    
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
    
    return TemplateResponse(
        request,
        "dashboard/user_dashboard.html",
        context={
            "active_tab": "project-dashboard",
            "signup_data": serializer.data,
            "form": form,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "start_value": start_value,
            "facebook_accounts": facebook_accounts_data,
            "facebook_ads": facebook_ads,
            "selected_campaigns_count": selected_campaigns.count(),
            "show_facebook_setup_modal": not facebook_accounts.exists(),
        },
    )


class UserSignupStatsView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=None, responses=UserSignupStatsSerializer(many=True))
    def get(self, request):
        serializer = UserSignupStatsSerializer(get_user_signups(), many=True)
        return Response(serializer.data)
