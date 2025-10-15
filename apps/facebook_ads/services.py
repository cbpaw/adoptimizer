import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
import json

from django.conf import settings
from django.utils import timezone
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.exceptions import FacebookRequestError

from .models import FacebookAdAccount, FacebookAd, FacebookCampaign

logger = logging.getLogger(__name__)


class ComprehensiveFacebookAPIService:
    """Comprehensive service class for detailed Facebook Marketing API operations"""
    
    def __init__(self, ad_account: FacebookAdAccount):
        self.ad_account = ad_account
        self.api = None
        self._initialize_api()
    
    def _initialize_api(self):
        """Initialize Facebook Ads API with credentials"""
        try:
            if self.ad_account.app_secret:
                FacebookAdsApi.init(
                    app_id=self.ad_account.app_id,
                    app_secret=self.ad_account.app_secret,
                    access_token=self.ad_account.access_token,
                )
            else:
                FacebookAdsApi.init(
                    app_id=self.ad_account.app_id,
                    app_secret=None,
                    access_token=self.ad_account.access_token,
                )
            self.api = FacebookAdsApi.get_default_api()
            logger.info(f"Comprehensive Facebook API initialized for account {self.ad_account.ad_account_id}")
        except Exception as e:
            logger.error(f"Failed to initialize comprehensive Facebook API: {str(e)}")
            raise
    
    def fetch_comprehensive_campaigns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch comprehensive campaign data with detailed information"""
        try:
            account = AdAccount(f"act_{self.ad_account.ad_account_id}")
            
            campaigns = account.get_campaigns(
                fields=[
                    'id',
                    'name',
                    'status',
                    'effective_status',
                    'objective',
                    'created_time',
                    'updated_time',
                    'start_time',
                    'stop_time',
                    'budget_remaining',
                    'daily_budget',
                    'lifetime_budget',
                    'bid_strategy',
                    'buying_type',
                    'can_use_spend_cap',
                    'configured_status',
                    'special_ad_categories',
                    'special_ad_category_country',
                    'spend_cap',
                ],
                params={'limit': limit}
            )
            
            campaigns_data = []
            for campaign in campaigns:
                campaign_data = dict(campaign)
                
                # Get comprehensive insights for campaign
                try:
                    insights = campaign.get_insights(
                        fields=[
                            'impressions',
                            'clicks',
                            'spend',
                            'ctr',
                            'cpm',
                            'cpc',
                            'reach',
                            'frequency',
                            'actions',
                            'conversions',
                            'conversion_values',
                            'cost_per_action_type',
                            'cost_per_conversion',
                            'purchase_roas',
                            'website_purchase_roas',
                            'video_30_sec_watched_actions',
                            'video_avg_time_watched_actions',
                            'video_p25_watched_actions',
                            'video_p50_watched_actions',
                            'video_p75_watched_actions',
                            'video_p95_watched_actions',
                            'video_p100_watched_actions',
                            'link_url_clicks',
                            'website_ctr',
                            'inline_link_clicks',
                            'inline_link_click_ctr',
                            'outbound_clicks',
                            'outbound_clicks_ctr',
                            'unique_clicks',
                            'unique_ctr',
                            'unique_inline_link_clicks',
                            'unique_inline_link_click_ctr',
                            'unique_link_clicks_ctr',
                            'social_spend',
                            'unique_actions',
                            'cost_per_unique_action_type',
                            'unique_conversions',
                            'cost_per_unique_conversion',
                        ],
                        params={
                            'time_range': {
                                'since': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                                'until': timezone.now().strftime('%Y-%m-%d')
                            },
                            'breakdowns': ['device_platform', 'publisher_platform'],
                            'level': 'campaign'
                        }
                    )
                    
                    if insights:
                        insight_data = dict(insights[0])
                        campaign_data.update(insight_data)
                        
                        # Process actions and conversions data
                        if 'actions' in insight_data:
                            campaign_data['actions_data'] = self._process_actions_data(insight_data['actions'])
                        if 'conversions' in insight_data:
                            campaign_data['conversions_data'] = self._process_conversions_data(insight_data['conversions'])
                
                except Exception as e:
                    logger.warning(f"Failed to get comprehensive insights for campaign {campaign['id']}: {str(e)}")
                    # Set default values
                    campaign_data.update(self._get_default_insight_values())
                
                campaigns_data.append(campaign_data)
            
            return campaigns_data
            
        except FacebookRequestError as e:
            logger.error(f"Failed to fetch comprehensive campaigns: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching comprehensive campaigns: {str(e)}")
            raise
    
    def fetch_comprehensive_ads(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch comprehensive ads data with creative information and detailed insights"""
        try:
            account = AdAccount(f"act_{self.ad_account.ad_account_id}")
            
            ads = account.get_ads(
                fields=[
                    'id',
                    'name',
                    'status',
                    'effective_status',
                    'created_time',
                    'updated_time',
                    'campaign{id,name,objective,status}',
                    'adset{id,name,status,targeting,optimization_goal,billing_event,bid_amount}',
                    'creative{id,name,title,body,image_url,video_id,thumbnail_url,object_story_spec,actor_id,call_to_action_type}',
                    'tracking_specs',
                    'conversion_specs',
                    'promoted_object',
                    'source_ad_id',
                    'configured_status',
                    'recommendations',
                    'issues_info',
                    'preview_shareable_link',
                ],
                params={'limit': limit}
            )
            
            ads_data = []
            for ad in ads:
                ad_data = dict(ad)
                
                # Get comprehensive insights for ad
                try:
                    insights = ad.get_insights(
                        fields=[
                            'impressions',
                            'clicks',
                            'spend',
                            'ctr',
                            'cpm',
                            'cpc',
                            'reach',
                            'frequency',
                            'actions',
                            'conversions',
                            'conversion_values',
                            'cost_per_action_type',
                            'cost_per_conversion',
                            'purchase_roas',
                            'website_purchase_roas',
                            'video_30_sec_watched_actions',
                            'video_avg_time_watched_actions',
                            'video_p25_watched_actions',
                            'video_p50_watched_actions',
                            'video_p75_watched_actions',
                            'video_p95_watched_actions',
                            'video_p100_watched_actions',
                            'link_url_clicks',
                            'website_ctr',
                            'inline_link_clicks',
                            'inline_link_click_ctr',
                            'outbound_clicks',
                            'outbound_clicks_ctr',
                            'unique_clicks',
                            'unique_ctr',
                            'unique_inline_link_clicks',
                            'unique_inline_link_click_ctr',
                            'unique_link_clicks_ctr',
                            'social_spend',
                            'unique_actions',
                            'cost_per_unique_action_type',
                            'unique_conversions',
                            'cost_per_unique_conversion',
                            'quality_ranking',
                            'engagement_rate_ranking',
                            'conversion_rate_ranking',
                        ],
                        params={
                            'time_range': {
                                'since': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                                'until': timezone.now().strftime('%Y-%m-%d')
                            },
                            'breakdowns': ['age', 'gender', 'device_platform', 'publisher_platform', 'placement'],
                            'level': 'ad'
                        }
                    )
                    
                    if insights:
                        insight_data = dict(insights[0])
                        ad_data.update(insight_data)
                        
                        # Process actions and conversions data
                        if 'actions' in insight_data:
                            ad_data['actions_data'] = self._process_actions_data(insight_data['actions'])
                        if 'conversions' in insight_data:
                            ad_data['conversions_data'] = self._process_conversions_data(insight_data['conversions'])
                
                except Exception as e:
                    logger.warning(f"Failed to get comprehensive insights for ad {ad['id']}: {str(e)}")
                    # Set default values
                    ad_data.update(self._get_default_insight_values())
                
                ads_data.append(ad_data)
            
            return ads_data
            
        except FacebookRequestError as e:
            logger.error(f"Failed to fetch comprehensive ads: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching comprehensive ads: {str(e)}")
            raise
    
    def get_campaign_detailed_insights(self, campaign_id: str, time_range: Dict[str, str] = None) -> Dict[str, Any]:
        """Get detailed insights for a specific campaign with custom parameters"""
        try:
            if not time_range:
                time_range = {
                    'since': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'until': timezone.now().strftime('%Y-%m-%d')
                }
            
            campaign = Campaign(campaign_id)
            
            insights = campaign.get_insights(
                fields=[
                    'impressions',
                    'clicks',
                    'spend',
                    'ctr',
                    'cpm',
                    'cpc',
                    'reach',
                    'frequency',
                    'actions',
                    'conversions',
                    'conversion_values',
                    'cost_per_action_type',
                    'cost_per_conversion',
                    'purchase_roas',
                    'website_purchase_roas',
                    'video_engagement_actions',
                    'video_avg_time_watched_actions',
                    'video_p25_watched_actions',
                    'video_p50_watched_actions',
                    'video_p75_watched_actions',
                    'video_p100_watched_actions',
                    'link_url_clicks',
                    'website_ctr',
                    'inline_link_clicks',
                    'inline_link_click_ctr',
                    'outbound_clicks',
                    'outbound_clicks_ctr',
                    'social_spend',
                    'objective',
                    'optimization_goal',
                ],
                params={
                    'time_range': time_range,
                    'breakdowns': ['age', 'gender', 'device_platform', 'publisher_platform', 'placement', 'region', 'country'],
                    'time_increment': 1,  # Daily breakdown
                    'level': 'campaign'
                }
            )
            
            if insights:
                insight_data = dict(insights[0])
                
                # Process complex data structures
                if 'actions' in insight_data:
                    insight_data['actions_data'] = self._process_actions_data(insight_data['actions'])
                if 'conversions' in insight_data:
                    insight_data['conversions_data'] = self._process_conversions_data(insight_data['conversions'])
                
                return insight_data
            else:
                return self._get_default_insight_values()
                
        except FacebookRequestError as e:
            logger.error(f"Failed to get detailed insights for campaign {campaign_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting detailed insights for campaign {campaign_id}: {str(e)}")
            raise
    
    def sync_comprehensive_campaigns_to_database(self, campaigns_data: List[Dict[str, Any]]) -> int:
        """Sync comprehensive campaign data to database with all fields"""
        synced_count = 0
        
        for campaign_data in campaigns_data:
            try:
                # Parse timestamps
                created_time = self._parse_timestamp(campaign_data.get('created_time'))
                updated_time = self._parse_timestamp(campaign_data.get('updated_time'))
                start_time = self._parse_timestamp(campaign_data.get('start_time'))
                stop_time = self._parse_timestamp(campaign_data.get('stop_time'))
                
                # Parse budget values
                daily_budget = self._parse_decimal(campaign_data.get('daily_budget'))
                lifetime_budget = self._parse_decimal(campaign_data.get('lifetime_budget'))
                budget_remaining = self._parse_decimal(campaign_data.get('budget_remaining'))
                spend_cap = self._parse_decimal(campaign_data.get('spend_cap'))
                
                # Parse insights
                impressions = int(campaign_data.get('impressions', 0) or 0)
                clicks = int(campaign_data.get('clicks', 0) or 0)
                spend = self._parse_decimal(campaign_data.get('spend', 0))
                reach = int(campaign_data.get('reach', 0) or 0)
                
                # Update or create campaign with comprehensive data
                campaign, created = FacebookCampaign.objects.update_or_create(
                    campaign_id=campaign_data['id'],
                    defaults={
                        'ad_account': self.ad_account,
                        'campaign_name': campaign_data.get('name', ''),
                        'status': campaign_data.get('status', ''),
                        'effective_status': campaign_data.get('effective_status', ''),
                        'objective': campaign_data.get('objective', ''),
                        'start_time': start_time,
                        'stop_time': stop_time,
                        'created_time': created_time,
                        'updated_time': updated_time,
                        # Budget information
                        'daily_budget': daily_budget,
                        'lifetime_budget': lifetime_budget,
                        'budget_remaining': budget_remaining,
                        'spend_cap': spend_cap,
                        'bid_strategy': campaign_data.get('bid_strategy', ''),
                        'buying_type': campaign_data.get('buying_type', ''),
                        # Performance metrics
                        'impressions': impressions,
                        'clicks': clicks,
                        'spend': spend,
                        'reach': reach,
                        'frequency': float(campaign_data.get('frequency', 0) or 0),
                        'ctr': float(campaign_data.get('ctr', 0) or 0),
                        'cpm': self._parse_decimal(campaign_data.get('cpm', 0)),
                        'cpc': self._parse_decimal(campaign_data.get('cpc', 0)),
                        # Advanced metrics
                        'purchase_roas': float(campaign_data.get('purchase_roas', 0) or 0),
                        'website_purchase_roas': float(campaign_data.get('website_purchase_roas', 0) or 0),
                        'link_url_clicks': int(campaign_data.get('link_url_clicks', 0) or 0),
                        'inline_link_clicks': int(campaign_data.get('inline_link_clicks', 0) or 0),
                        'outbound_clicks': int(campaign_data.get('outbound_clicks', 0) or 0),
                        # Complex data as JSON
                        'actions_data': json.dumps(campaign_data.get('actions_data', {})),
                        'conversions_data': json.dumps(campaign_data.get('conversions_data', {})),
                        'special_ad_categories': json.dumps(campaign_data.get('special_ad_categories', [])),
                    }
                )
                
                synced_count += 1
                
                if created:
                    logger.info(f"Created comprehensive campaign: {campaign.campaign_name} ({campaign.campaign_id})")
                else:
                    logger.info(f"Updated comprehensive campaign: {campaign.campaign_name} ({campaign.campaign_id})")
                    
            except Exception as e:
                logger.error(f"Failed to sync comprehensive campaign {campaign_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        return synced_count
    
    def sync_comprehensive_ads_to_database(self, ads_data: List[Dict[str, Any]]) -> int:
        """Sync comprehensive ads data to database with all fields"""
        synced_count = 0
        
        for ad_data in ads_data:
            try:
                # Parse campaign, adset, and creative data
                campaign_data = ad_data.get('campaign', {})
                adset_data = ad_data.get('adset', {})
                creative_data = ad_data.get('creative', {})
                
                # Parse timestamps
                created_time = self._parse_timestamp(ad_data.get('created_time'))
                updated_time = self._parse_timestamp(ad_data.get('updated_time'))
                
                # Parse performance metrics
                impressions = int(ad_data.get('impressions', 0) or 0)
                clicks = int(ad_data.get('clicks', 0) or 0)
                spend = self._parse_decimal(ad_data.get('spend', 0))
                reach = int(ad_data.get('reach', 0) or 0)
                
                # Parse creative information
                creative_title = creative_data.get('title', '')
                creative_body = creative_data.get('body', '')
                creative_image_url = creative_data.get('image_url', '')
                creative_video_id = creative_data.get('video_id', '')
                call_to_action_type = creative_data.get('call_to_action_type', '')
                
                # Update or create ad with comprehensive data
                ad, created = FacebookAd.objects.update_or_create(
                    ad_id=ad_data['id'],
                    defaults={
                        'ad_account': self.ad_account,
                        'ad_name': ad_data.get('name', ''),
                        'status': ad_data.get('status', ''),
                        'effective_status': ad_data.get('effective_status', ''),
                        'configured_status': ad_data.get('configured_status', ''),
                        # Campaign and Adset information
                        'campaign_id': campaign_data.get('id', ''),
                        'campaign_name': campaign_data.get('name', ''),
                        'campaign_objective': campaign_data.get('objective', ''),
                        'adset_id': adset_data.get('id', ''),
                        'adset_name': adset_data.get('name', ''),
                        'optimization_goal': adset_data.get('optimization_goal', ''),
                        'billing_event': adset_data.get('billing_event', ''),
                        'bid_amount': self._parse_decimal(adset_data.get('bid_amount', 0)),
                        # Creative information
                        'creative_id': creative_data.get('id', ''),
                        'creative_title': creative_title,
                        'creative_body': creative_body,
                        'creative_image_url': creative_image_url,
                        'creative_video_id': creative_video_id,
                        'call_to_action_type': call_to_action_type,
                        # Performance metrics
                        'impressions': impressions,
                        'clicks': clicks,
                        'spend': spend,
                        'reach': reach,
                        'frequency': float(ad_data.get('frequency', 0) or 0),
                        'ctr': float(ad_data.get('ctr', 0) or 0),
                        'cpm': self._parse_decimal(ad_data.get('cpm', 0)),
                        'cpc': self._parse_decimal(ad_data.get('cpc', 0)),
                        # Advanced metrics
                        'purchase_roas': float(ad_data.get('purchase_roas', 0) or 0),
                        'website_purchase_roas': float(ad_data.get('website_purchase_roas', 0) or 0),
                        'link_url_clicks': int(ad_data.get('link_url_clicks', 0) or 0),
                        'inline_link_clicks': int(ad_data.get('inline_link_clicks', 0) or 0),
                        'outbound_clicks': int(ad_data.get('outbound_clicks', 0) or 0),
                        'unique_clicks': int(ad_data.get('unique_clicks', 0) or 0),
                        'unique_ctr': float(ad_data.get('unique_ctr', 0) or 0),
                        # Video engagement metrics
                        'video_avg_time_watched': float(ad_data.get('video_avg_time_watched_actions', 0) or 0),
                        'video_p25_watched': int(ad_data.get('video_p25_watched_actions', 0) or 0),
                        'video_p50_watched': int(ad_data.get('video_p50_watched_actions', 0) or 0),
                        'video_p75_watched': int(ad_data.get('video_p75_watched_actions', 0) or 0),
                        'video_p100_watched': int(ad_data.get('video_p100_watched_actions', 0) or 0),
                        # Quality rankings
                        'quality_ranking': ad_data.get('quality_ranking', ''),
                        'engagement_rate_ranking': ad_data.get('engagement_rate_ranking', ''),
                        'conversion_rate_ranking': ad_data.get('conversion_rate_ranking', ''),
                        # Timestamps
                        'created_time': created_time,
                        'updated_time': updated_time,
                        # Complex data as JSON
                        'actions_data': json.dumps(ad_data.get('actions_data', {})),
                        'conversions_data': json.dumps(ad_data.get('conversions_data', {})),
                        'targeting_data': json.dumps(adset_data.get('targeting', {})),
                        'tracking_specs': json.dumps(ad_data.get('tracking_specs', [])),
                        'conversion_specs': json.dumps(ad_data.get('conversion_specs', [])),
                        'promoted_object': json.dumps(ad_data.get('promoted_object', {})),
                    }
                )
                
                synced_count += 1
                
                if created:
                    logger.info(f"Created comprehensive ad: {ad.ad_name} ({ad.ad_id})")
                else:
                    logger.info(f"Updated comprehensive ad: {ad.ad_name} ({ad.ad_id})")
                    
            except Exception as e:
                logger.error(f"Failed to sync comprehensive ad {ad_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        return synced_count
    
    def _process_actions_data(self, actions: List[Dict]) -> Dict[str, Any]:
        """Process Facebook actions data into a structured format"""
        processed_actions = {}
        
        for action in actions:
            action_type = action.get('action_type', 'unknown')
            value = action.get('value', 0)
            processed_actions[action_type] = {
                'value': int(value) if value else 0,
                '1d_view': int(action.get('1d_view', 0)) if action.get('1d_view') else 0,
                '1d_click': int(action.get('1d_click', 0)) if action.get('1d_click') else 0,
                '7d_view': int(action.get('7d_view', 0)) if action.get('7d_view') else 0,
                '7d_click': int(action.get('7d_click', 0)) if action.get('7d_click') else 0,
                '28d_view': int(action.get('28d_view', 0)) if action.get('28d_view') else 0,
                '28d_click': int(action.get('28d_click', 0)) if action.get('28d_click') else 0,
            }
        
        return processed_actions
    
    def _process_conversions_data(self, conversions: List[Dict]) -> Dict[str, Any]:
        """Process Facebook conversions data into a structured format"""
        processed_conversions = {}
        
        for conversion in conversions:
            action_type = conversion.get('action_type', 'unknown')
            value = conversion.get('value', 0)
            processed_conversions[action_type] = {
                'value': int(value) if value else 0,
                '1d_view': int(conversion.get('1d_view', 0)) if conversion.get('1d_view') else 0,
                '1d_click': int(conversion.get('1d_click', 0)) if conversion.get('1d_click') else 0,
                '7d_view': int(conversion.get('7d_view', 0)) if conversion.get('7d_view') else 0,
                '7d_click': int(conversion.get('7d_click', 0)) if conversion.get('7d_click') else 0,
                '28d_view': int(conversion.get('28d_view', 0)) if conversion.get('28d_view') else 0,
                '28d_click': int(conversion.get('28d_click', 0)) if conversion.get('28d_click') else 0,
            }
        
        return processed_conversions
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None
        
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Failed to parse timestamp {timestamp_str}: {str(e)}")
            return None
    
    def _parse_decimal(self, value: Any) -> Decimal:
        """Parse value to Decimal safely"""
        if value is None or value == '':
            return Decimal('0')
        
        try:
            return Decimal(str(value))
        except Exception as e:
            logger.warning(f"Failed to parse decimal value {value}: {str(e)}")
            return Decimal('0')
    
    def _get_default_insight_values(self) -> Dict[str, Any]:
        """Get default insight values when API call fails"""
        return {
            'impressions': '0',
            'clicks': '0',
            'spend': '0',
            'reach': '0',
            'frequency': '0',
            'ctr': '0',
            'cpm': '0',
            'cpc': '0',
            'purchase_roas': '0',
            'website_purchase_roas': '0',
            'link_url_clicks': '0',
            'inline_link_clicks': '0',
            'outbound_clicks': '0',
            'unique_clicks': '0',
            'unique_ctr': '0',
            'video_avg_time_watched_actions': '0',
            'video_p25_watched_actions': '0',
            'video_p50_watched_actions': '0',
            'video_p75_watched_actions': '0',
            'video_p100_watched_actions': '0',
            'quality_ranking': '',
            'engagement_rate_ranking': '',
            'conversion_rate_ranking': '',
            'actions_data': {},
            'conversions_data': {},
        }


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


from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from decimal import Decimal


class DashboardService:
    """Service class for dashboard data aggregation and analytics"""
    
    def __init__(self, user):
        self.user = user
    
    def get_dashboard_data(self, period_name='last_7d', account_ids=None):
        """Main method to get dashboard data"""
        from .models import FacebookCampaign, FacebookCampaignInsights, DashboardPeriod
        
        period = self._get_period_config(period_name)
        date_range = self._get_date_range(period)
        
        # Get campaigns
        campaigns = self._get_campaigns_for_period(date_range, account_ids)
        
        # Get insights
        insights = self._get_insights_for_period(campaigns, date_range)
        
        # Get current campaign data as fallback
        current_campaign_data = self._get_current_campaign_data(campaigns)
        
        return {
            'summary': self._calculate_summary_metrics(insights, current_campaign_data),
            'campaigns': self._format_campaign_data(campaigns, insights),
            'trends': self._calculate_trends(insights),
            'period': period,
            'date_range': date_range,
            'alerts': self._generate_alerts(insights, campaigns)
        }
    
    def _get_period_config(self, period_name):
        """Get period configuration"""
        periods = {
            'today': {
                'name': 'today',
                'display_name': 'Vandaag',
                'days': 1,
                'date_preset': 'today'
            },
            'yesterday': {
                'name': 'yesterday',
                'display_name': 'Gisteren',
                'days': 1,
                'date_preset': 'yesterday'
            },
            'last_7d': {
                'name': 'last_7d',
                'display_name': 'Laatste 7 dagen',
                'days': 7,
                'date_preset': 'last_7d'
            },
            'last_14d': {
                'name': 'last_14d',
                'display_name': 'Laatste 14 dagen',
                'days': 14,
                'date_preset': 'last_14d'
            },
            'last_30d': {
                'name': 'last_30d',
                'display_name': 'Laatste 30 dagen',
                'days': 30,
                'date_preset': 'last_30d'
            },
            'this_month': {
                'name': 'this_month',
                'display_name': 'Deze maand',
                'days': None,
                'date_preset': 'this_month'
            },
            'last_month': {
                'name': 'last_month',
                'display_name': 'Vorige maand',
                'days': None,
                'date_preset': 'last_month'
            }
        }
        return periods.get(period_name, periods['last_7d'])
    
    def _get_date_range(self, period):
        """Calculate date range based on period"""
        today = timezone.now().date()
        
        if period['name'] == 'today':
            return {'start': today, 'end': today}
        elif period['name'] == 'yesterday':
            yesterday = today - timedelta(days=1)
            return {'start': yesterday, 'end': yesterday}
        elif period['name'] == 'last_7d':
            start = today - timedelta(days=7)
            return {'start': start, 'end': today}
        elif period['name'] == 'last_14d':
            start = today - timedelta(days=14)
            return {'start': start, 'end': today}
        elif period['name'] == 'last_30d':
            start = today - timedelta(days=30)
            return {'start': start, 'end': today}
        elif period['name'] == 'this_month':
            start = today.replace(day=1)
            return {'start': start, 'end': today}
        elif period['name'] == 'last_month':
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            return {'start': first_day_last_month, 'end': last_day_last_month}
        else:
            # Default to last 7 days
            start = today - timedelta(days=7)
            return {'start': start, 'end': today}
    
    def _get_campaigns_for_period(self, date_range, account_ids):
        """Get campaigns for the period"""
        from .models import FacebookCampaign
        
        query = FacebookCampaign.objects.filter(
            ad_account__user=self.user,
            ad_account__is_active=True
        )
        
        if account_ids:
            query = query.filter(ad_account_id__in=account_ids)
        
        return query.select_related('ad_account').order_by('-last_synced')
    
    def _get_insights_for_period(self, campaigns, date_range):
        """Get insights for the period"""
        from .models import FacebookCampaignInsights
        
        campaign_ids = [c.id for c in campaigns]
        
        if not campaign_ids:
            return FacebookCampaignInsights.objects.none()
        
        return FacebookCampaignInsights.objects.filter(
            campaign_id__in=campaign_ids,
            date_start__gte=date_range['start'],
            date_stop__lte=date_range['end']
        ).select_related('campaign').order_by('-date_start')
    
    def _get_current_campaign_data(self, campaigns):
        """Get current campaign data as fallback when no insights available"""
        campaign_data = []
        
        for campaign in campaigns:
            campaign_data.append({
                'campaign_id': campaign.campaign_id,
                'campaign_name': campaign.campaign_name,
                'spend': float(campaign.spend),
                'impressions': campaign.impressions,
                'clicks': campaign.clicks,
                'ctr': campaign.ctr,
                'cpc': float(campaign.cpc),
                'cpm': float(campaign.cpm),
                'purchase_roas': campaign.purchase_roas,
                'status': campaign.status,
                'effective_status': campaign.effective_status
            })
        
        return campaign_data
    
    def _calculate_summary_metrics(self, insights, current_campaign_data):
        """Calculate summary metrics"""
        if insights.exists():
            # Use insights data
            aggregated = insights.aggregate(
                total_spend=Sum('spend'),
                total_impressions=Sum('impressions'),
                total_clicks=Sum('clicks'),
                total_purchases=Sum('purchases'),
                total_purchase_value=Sum('purchase_value'),
                total_reach=Sum('reach'),
                total_link_clicks=Sum('link_clicks')
            )
        else:
            # Use current campaign data as fallback
            aggregated = {
                'total_spend': sum(c['spend'] for c in current_campaign_data),
                'total_impressions': sum(c['impressions'] for c in current_campaign_data),
                'total_clicks': sum(c['clicks'] for c in current_campaign_data),
                'total_purchases': 0,
                'total_purchase_value': 0,
                'total_reach': 0,
                'total_link_clicks': 0
            }
        
        # Calculate derived metrics
        total_spend = float(aggregated['total_spend'] or 0)
        total_impressions = aggregated['total_impressions'] or 0
        total_clicks = aggregated['total_clicks'] or 0
        total_purchase_value = float(aggregated['total_purchase_value'] or 0)
        total_purchases = aggregated['total_purchases'] or 0
        total_reach = aggregated['total_reach'] or 0
        
        return {
            'total_spend': total_spend,
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'total_purchases': total_purchases,
            'total_reach': total_reach,
            'average_cpc': total_spend / total_clicks if total_clicks > 0 else 0,
            'average_ctr': (total_clicks / total_impressions) * 100 if total_impressions > 0 else 0,
            'total_roas': total_purchase_value / total_spend if total_spend > 0 else 0,
            'campaign_count': len(current_campaign_data) if not insights.exists() else insights.values('campaign').distinct().count()
        }
    
    def _format_campaign_data(self, campaigns, insights):
        """Format campaign data for frontend"""
        campaign_data = []
        
        # Group insights by campaign
        insights_by_campaign = {}
        for insight in insights:
            campaign_id = insight.campaign.campaign_id
            if campaign_id not in insights_by_campaign:
                insights_by_campaign[campaign_id] = []
            insights_by_campaign[campaign_id].append(insight)
        
        for campaign in campaigns:
            campaign_insights = insights_by_campaign.get(campaign.campaign_id, [])
            
            if campaign_insights:
                # Aggregate insights data
                total_spend = sum(i.spend for i in campaign_insights)
                total_impressions = sum(i.impressions for i in campaign_insights)
                total_clicks = sum(i.clicks for i in campaign_insights)
                total_purchases = sum(i.purchases for i in campaign_insights)
                total_purchase_value = sum(i.purchase_value for i in campaign_insights)
                
                # Calculate averages
                avg_ctr = sum(i.ctr for i in campaign_insights) / len(campaign_insights) if campaign_insights else 0
                avg_cpc = total_spend / total_clicks if total_clicks > 0 else 0
                avg_roas = total_purchase_value / total_spend if total_spend > 0 else 0
            else:
                # Use current campaign data
                total_spend = float(campaign.spend)
                total_impressions = campaign.impressions
                total_clicks = campaign.clicks
                total_purchases = 0
                total_purchase_value = 0
                avg_ctr = campaign.ctr
                avg_cpc = float(campaign.cpc)
                avg_roas = campaign.purchase_roas
            
            campaign_data.append({
                'campaign_id': campaign.campaign_id,
                'campaign_name': campaign.campaign_name,
                'status': campaign.status,
                'effective_status': campaign.effective_status,
                'objective': campaign.objective,
                'spend': total_spend,
                'impressions': total_impressions,
                'clicks': total_clicks,
                'purchases': total_purchases,
                'purchase_value': total_purchase_value,
                'ctr': avg_ctr,
                'cpc': avg_cpc,
                'roas': avg_roas,
                'daily_budget': float(campaign.daily_budget) if campaign.daily_budget else None,
                'lifetime_budget': float(campaign.lifetime_budget) if campaign.lifetime_budget else None,
                'start_time': campaign.start_time,
                'last_synced': campaign.last_synced,
                'ad_account_name': campaign.ad_account.ad_account_name
            })
        
        return campaign_data
    
    def _calculate_trends(self, insights):
        """Calculate trends data for charts"""
        if not insights.exists():
            return {
                'daily_spend': [],
                'daily_impressions': [],
                'daily_clicks': [],
                'daily_conversions': []
            }
        
        # Group by date
        daily_data = {}
        for insight in insights:
            date_str = insight.date_start.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'spend': 0,
                    'impressions': 0,
                    'clicks': 0,
                    'conversions': 0
                }
            
            daily_data[date_str]['spend'] += float(insight.spend)
            daily_data[date_str]['impressions'] += insight.impressions
            daily_data[date_str]['clicks'] += insight.clicks
            daily_data[date_str]['conversions'] += insight.purchases
        
        # Sort by date
        sorted_dates = sorted(daily_data.keys())
        
        return {
            'daily_spend': [{'date': date, 'value': daily_data[date]['spend']} for date in sorted_dates],
            'daily_impressions': [{'date': date, 'value': daily_data[date]['impressions']} for date in sorted_dates],
            'daily_clicks': [{'date': date, 'value': daily_data[date]['clicks']} for date in sorted_dates],
            'daily_conversions': [{'date': date, 'value': daily_data[date]['conversions']} for date in sorted_dates]
        }
    
    def _generate_alerts(self, insights, campaigns):
        """Generate alerts based on performance"""
        alerts = []
        
        # Check for campaigns with low ROAS
        low_roas_campaigns = []
        for campaign in campaigns:
            if campaign.purchase_roas < 1.0 and campaign.spend > 50:
                low_roas_campaigns.append(campaign)
        
        if low_roas_campaigns:
            alerts.append({
                'type': 'warning',
                'title': 'Lage ROAS gedetecteerd',
                'message': f'{len(low_roas_campaigns)} campagne(s) hebben een ROAS onder de 1.0',
                'campaigns': [c.campaign_name for c in low_roas_campaigns]
            })
        
        # Check for campaigns with high spend but low conversions
        high_spend_low_conversion = []
        for campaign in campaigns:
            if campaign.spend > 100 and campaign.purchase_roas < 0.5:
                high_spend_low_conversion.append(campaign)
        
        if high_spend_low_conversion:
            alerts.append({
                'type': 'danger',
                'title': 'Hoge uitgaven, lage conversies',
                'message': f'{len(high_spend_low_conversion)} campagne(s) hebben hoge uitgaven maar lage conversies',
                'campaigns': [c.campaign_name for c in high_spend_low_conversion]
            })
        
        # Check for paused campaigns with good performance
        paused_good_performance = []
        for campaign in campaigns:
            if campaign.status == 'PAUSED' and campaign.purchase_roas > 2.0:
                paused_good_performance.append(campaign)
        
        if paused_good_performance:
            alerts.append({
                'type': 'info',
                'title': 'Gepauzeerde campagnes met goede prestaties',
                'message': f'{len(paused_good_performance)} gepauzeerde campagne(s) hadden goede prestaties',
                'campaigns': [c.campaign_name for c in paused_good_performance]
            })
        
        return alerts
    
    def get_campaign_insights(self, campaign, period_name='last_30d'):
        """Get detailed insights for a specific campaign"""
        from .models import FacebookCampaignInsights
        
        period = self._get_period_config(period_name)
        date_range = self._get_date_range(period)
        
        insights = FacebookCampaignInsights.objects.filter(
            campaign=campaign,
            date_start__gte=date_range['start'],
            date_stop__lte=date_range['end']
        ).order_by('date_start')
        
        return {
            'campaign': {
                'id': campaign.campaign_id,
                'name': campaign.campaign_name,
                'status': campaign.status,
                'objective': campaign.objective
            },
            'insights': [
                {
                    'date': insight.date_start,
                    'spend': float(insight.spend),
                    'impressions': insight.impressions,
                    'clicks': insight.clicks,
                    'ctr': insight.ctr,
                    'cpc': float(insight.cpc),
                    'roas': insight.purchase_roas,
                    'purchases': insight.purchases,
                    'purchase_value': float(insight.purchase_value)
                } for insight in insights
            ],
            'summary': self._calculate_summary_metrics(insights, []),
            'period': period
        }


class FacebookInsightsService:
    """Service class for Facebook Insights API operations"""
    
    def __init__(self, ad_account: FacebookAdAccount):
        self.ad_account = ad_account
        self.api = None
        self._initialize_api()
    
    def _initialize_api(self):
        """Initialize Facebook Ads API"""
        try:
            if self.ad_account.app_secret:
                FacebookAdsApi.init(
                    app_id=self.ad_account.app_id,
                    app_secret=self.ad_account.app_secret,
                    access_token=self.ad_account.access_token,
                )
            else:
                FacebookAdsApi.init(
                    app_id=self.ad_account.app_id,
                    app_secret=None,
                    access_token=self.ad_account.access_token,
                )
            self.api = FacebookAdsApi.get_default_api()
        except Exception as e:
            logger.error(f"Failed to initialize Facebook Insights API: {str(e)}")
            raise
    
    def get_campaign_insights(self, campaign_ids, date_preset='last_30d', breakdowns=None):
        """Get insights for campaigns"""
        try:
            account = AdAccount(f"act_{self.ad_account.ad_account_id}")
            
            fields = [
                'campaign_id',
                'campaign_name',
                'date_start',
                'date_stop',
                'impressions',
                'clicks',
                'spend',
                'reach',
                'frequency',
                'ctr',
                'cpc',
                'cpm',
                'actions',
                'conversions',
                'purchase_roas',
                'website_purchase_roas'
            ]
            
            params = {
                'time_range': {'since': '30 days ago', 'until': 'today'},
                'date_preset': date_preset,
                'level': 'campaign',
                'filtering': [{'field': 'campaign.id', 'operator': 'IN', 'value': campaign_ids}]
            }
            
            if breakdowns:
                params['breakdowns'] = breakdowns
            
            insights = account.get_insights(fields=fields, params=params)
            
            return [dict(insight) for insight in insights]
            
        except FacebookRequestError as e:
            logger.error(f"Failed to get campaign insights: {str(e)}")
            return []
    
    def sync_insights_to_database(self, insights_data):
        """Sync insights data to database"""
        from .models import FacebookCampaign, FacebookCampaignInsights
        
        synced_count = 0
        
        for insight_data in insights_data:
            try:
                # Find the campaign
                campaign = FacebookCampaign.objects.get(
                    campaign_id=insight_data['campaign_id'],
                    ad_account=self.ad_account
                )
                
                # Parse dates
                date_start = datetime.strptime(insight_data['date_start'], '%Y-%m-%d').date()
                date_stop = datetime.strptime(insight_data['date_stop'], '%Y-%m-%d').date()
                
                # Parse actions and conversions
                actions_data = insight_data.get('actions', [])
                conversions_data = insight_data.get('conversions', [])
                
                # Extract specific metrics
                purchases = self._extract_action_value(actions_data, 'purchase')
                purchase_value = self._extract_action_value(conversions_data, 'purchase', 'value')
                link_clicks = self._extract_action_value(actions_data, 'link_click')
                
                # Create or update insight
                insight, created = FacebookCampaignInsights.objects.update_or_create(
                    campaign=campaign,
                    date_start=date_start,
                    date_stop=date_stop,
                    defaults={
                        'impressions': int(insight_data.get('impressions', 0) or 0),
                        'clicks': int(insight_data.get('clicks', 0) or 0),
                        'spend': Decimal(str(insight_data.get('spend', 0) or 0)),
                        'reach': int(insight_data.get('reach', 0) or 0),
                        'frequency': float(insight_data.get('frequency', 0) or 0),
                        'ctr': float(insight_data.get('ctr', 0) or 0),
                        'cpc': Decimal(str(insight_data.get('cpc', 0) or 0)),
                        'cpm': Decimal(str(insight_data.get('cpm', 0) or 0)),
                        'purchase_roas': float(insight_data.get('purchase_roas', 0) or 0),
                        'website_purchase_roas': float(insight_data.get('website_purchase_roas', 0) or 0),
                        'purchases': purchases,
                        'purchase_value': Decimal(str(purchase_value)),
                        'link_clicks': link_clicks,
                        'actions_data': actions_data,
                        'conversions_data': conversions_data
                    }
                )
                
                synced_count += 1
                
            except FacebookCampaign.DoesNotExist:
                logger.warning(f"Campaign {insight_data['campaign_id']} not found for insights sync")
                continue
            except Exception as e:
                logger.error(f"Error syncing insight for campaign {insight_data.get('campaign_id')}: {str(e)}")
                continue
        
        return synced_count
    
    def _extract_action_value(self, actions_data, action_type, value_type='1d_click'):
        """Extract specific action value from actions data"""
        if not actions_data:
            return 0
        
        for action in actions_data:
            if action.get('action_type') == action_type:
                if value_type == 'value':
                    return float(action.get('value', 0) or 0)
                else:
                    return int(action.get(value_type, 0) or 0)
        
        return 0 