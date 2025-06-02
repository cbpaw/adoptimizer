import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.exceptions import FacebookRequestError

from .models import FacebookAdAccount, FacebookAd

logger = logging.getLogger(__name__)


class FacebookMarketingAPIService:
    """Service class for Facebook Marketing API operations"""
    
    def __init__(self, ad_account: FacebookAdAccount):
        self.ad_account = ad_account
        self.api = None
        self._initialize_api()
    
    def _initialize_api(self):
        """Initialize Facebook Ads API with credentials"""
        try:
            # For token-based auth, app_secret might be empty
            if self.ad_account.app_secret:
                FacebookAdsApi.init(
                    app_id=self.ad_account.app_id,
                    app_secret=self.ad_account.app_secret,
                    access_token=self.ad_account.access_token,
                )
            else:
                # Initialize with just app_id and access_token for token-based auth
                FacebookAdsApi.init(
                    app_id=self.ad_account.app_id,
                    app_secret=None,
                    access_token=self.ad_account.access_token,
                )
            self.api = FacebookAdsApi.get_default_api()
            logger.info(f"Facebook API initialized for account {self.ad_account.ad_account_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Facebook API: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            account = AdAccount(f"act_{self.ad_account.ad_account_id}")
            account.api_get(fields=['name', 'account_status'])
            return True
        except FacebookRequestError as e:
            logger.error(f"Facebook API connection test failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing Facebook API connection: {str(e)}")
            return False
    
    def get_ad_account_info(self) -> Dict[str, Any]:
        """Get ad account information"""
        try:
            account = AdAccount(f"act_{self.ad_account.ad_account_id}")
            account_data = account.api_get(fields=[
                'name',
                'account_status',
                'currency',
                'timezone_name',
                'business_name',
                'spend_cap',
                'amount_spent'
            ])
            return account_data
        except FacebookRequestError as e:
            logger.error(f"Failed to get ad account info: {str(e)}")
            raise
    
    def fetch_ads(self, limit: int = 100, status_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch ads from Facebook Marketing API"""
        try:
            account = AdAccount(f"act_{self.ad_account.ad_account_id}")
            
            # Set up parameters
            params = {
                'limit': limit,
                'fields': [
                    'id',
                    'name',
                    'status',
                    'created_time',
                    'updated_time',
                    'campaign{id,name,objective}',
                    'adset{id,name}',
                ]
            }
            
            if status_filter:
                params['filtering'] = [{'field': 'ad.effective_status', 'operator': 'IN', 'value': status_filter}]
            
            ads = account.get_ads(params=params)
            
            ads_data = []
            for ad in ads:
                ad_data = dict(ad)
                
                # Get insights (performance metrics)
                try:
                    insights = ad.get_insights(
                        fields=[
                            'impressions',
                            'clicks',
                            'spend',
                            'ctr',
                            'cpm',
                            'cpc'
                        ],
                        params={
                            'time_range': {
                                'since': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                                'until': timezone.now().strftime('%Y-%m-%d')
                            }
                        }
                    )
                    
                    if insights:
                        insight_data = dict(insights[0])
                        ad_data.update(insight_data)
                
                except Exception as e:
                    logger.warning(f"Failed to get insights for ad {ad['id']}: {str(e)}")
                    # Set default values if insights fail
                    ad_data.update({
                        'impressions': '0',
                        'clicks': '0',
                        'spend': '0',
                        'ctr': '0',
                        'cpm': '0',
                        'cpc': '0'
                    })
                
                ads_data.append(ad_data)
            
            return ads_data
            
        except FacebookRequestError as e:
            logger.error(f"Failed to fetch ads: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching ads: {str(e)}")
            raise
    
    def sync_ads_to_database(self, ads_data: List[Dict[str, Any]]) -> int:
        """Sync fetched ads data to the database"""
        synced_count = 0
        
        for ad_data in ads_data:
            try:
                # Parse campaign and adset data
                campaign_data = ad_data.get('campaign', {})
                adset_data = ad_data.get('adset', {})
                
                # Convert string values to appropriate types
                impressions = int(ad_data.get('impressions', 0) or 0)
                clicks = int(ad_data.get('clicks', 0) or 0)
                spend = Decimal(str(ad_data.get('spend', 0) or 0))
                ctr = float(ad_data.get('ctr', 0) or 0)
                cpm = Decimal(str(ad_data.get('cpm', 0) or 0))
                cpc = Decimal(str(ad_data.get('cpc', 0) or 0))
                
                # Parse timestamps
                created_time = None
                updated_time = None
                
                if ad_data.get('created_time'):
                    created_time = datetime.fromisoformat(ad_data['created_time'].replace('Z', '+00:00'))
                if ad_data.get('updated_time'):
                    updated_time = datetime.fromisoformat(ad_data['updated_time'].replace('Z', '+00:00'))
                
                # Update or create ad record
                ad, created = FacebookAd.objects.update_or_create(
                    ad_id=ad_data['id'],
                    defaults={
                        'ad_account': self.ad_account,
                        'ad_name': ad_data.get('name', ''),
                        'campaign_id': campaign_data.get('id', ''),
                        'campaign_name': campaign_data.get('name', ''),
                        'adset_id': adset_data.get('id', ''),
                        'adset_name': adset_data.get('name', ''),
                        'status': ad_data.get('status', ''),
                        'objective': campaign_data.get('objective', ''),
                        'impressions': impressions,
                        'clicks': clicks,
                        'spend': spend,
                        'ctr': ctr,
                        'cpm': cpm,
                        'cpc': cpc,
                        'created_time': created_time,
                        'updated_time': updated_time,
                    }
                )
                
                synced_count += 1
                
                if created:
                    logger.info(f"Created new ad record: {ad.ad_name} ({ad.ad_id})")
                else:
                    logger.info(f"Updated ad record: {ad.ad_name} ({ad.ad_id})")
                    
            except Exception as e:
                logger.error(f"Failed to sync ad {ad_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        return synced_count
    
    def get_campaigns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch campaigns from Facebook Marketing API"""
        try:
            account = AdAccount(f"act_{self.ad_account.ad_account_id}")
            
            campaigns = account.get_campaigns(
                fields=[
                    'id',
                    'name',
                    'status',
                    'objective',
                    'created_time',
                    'updated_time',
                    'start_time',
                    'stop_time'
                ],
                params={'limit': limit}
            )
            
            return [dict(campaign) for campaign in campaigns]
            
        except FacebookRequestError as e:
            logger.error(f"Failed to fetch campaigns: {str(e)}")
            raise


def get_facebook_auth_url(app_id: str, redirect_uri: str) -> str:
    """Generate Facebook OAuth URL for getting access token"""
    base_url = "https://www.facebook.com/v21.0/dialog/oauth"
    scope = "ads_read,ads_management,business_management"
    
    auth_url = (
        f"{base_url}?"
        f"client_id={app_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}&"
        f"response_type=code"
    )
    
    return auth_url


def exchange_code_for_token(app_id: str, app_secret: str, code: str, redirect_uri: str) -> str:
    """Exchange authorization code for access token"""
    import requests
    
    url = "https://graph.facebook.com/v21.0/oauth/access_token"
    params = {
        'client_id': app_id,
        'client_secret': app_secret,
        'redirect_uri': redirect_uri,
        'code': code
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    return data['access_token'] 