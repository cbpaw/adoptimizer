from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
import requests
import logging

from apps.facebook_ads.models import FacebookAdAccount, FacebookCampaign

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync Facebook campaigns for all connected ad accounts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=str,
            help='Sync campaigns for a specific ad account ID only'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of campaigns to fetch per account (default: 100)'
        )
    
    def handle(self, *args, **options):
        account_id = options.get('account_id')
        limit = options.get('limit', 100)
        
        # Get active Facebook ad accounts
        if account_id:
            accounts = FacebookAdAccount.objects.filter(
                ad_account_id=account_id,
                is_active=True
            )
            if not accounts.exists():
                self.stdout.write(
                    self.style.ERROR(f'No active account found with ID: {account_id}')
                )
                return
        else:
            accounts = FacebookAdAccount.objects.filter(is_active=True)
        
        if not accounts.exists():
            self.stdout.write(
                self.style.WARNING('No active Facebook ad accounts found.')
            )
            return
        
        total_campaigns = 0
        total_accounts = accounts.count()
        
        self.stdout.write(f'Starting sync for {total_accounts} account(s)...')
        
        for i, account in enumerate(accounts, 1):
            self.stdout.write(
                f'[{i}/{total_accounts}] Syncing campaigns for account: {account.ad_account_name} ({account.ad_account_id})'
            )
            
            try:
                campaigns_count = self.sync_account_campaigns(account, limit)
                total_campaigns += campaigns_count
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Synced {campaigns_count} campaigns')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to sync campaigns: {str(e)}')
                )
                logger.error(f'Failed to sync campaigns for account {account.ad_account_id}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCompleted! Total campaigns synced: {total_campaigns}')
        )
    
    def sync_account_campaigns(self, account, limit):
        """Sync campaigns for a single ad account"""
        # Make API call to Facebook to get campaigns
        url = f'https://graph.facebook.com/v19.0/act_{account.ad_account_id}/campaigns'
        params = {
            'access_token': account.access_token,
            'fields': 'id,name,status,effective_status,start_time,updated_time,objective',
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            logger.error(f'Facebook API error for account {account.ad_account_id}: {response.text}')
            raise Exception(f'Facebook API returned status {response.status_code}')
        
        facebook_data = response.json()
        campaigns_data = facebook_data.get('data', [])
        
        synced_count = 0
        
        for campaign_data in campaigns_data:
            try:
                # Parse start_time if it exists
                start_time = None
                if campaign_data.get('start_time'):
                    try:
                        start_time = datetime.fromisoformat(
                            campaign_data['start_time'].replace('Z', '+00:00')
                        )
                    except Exception as e:
                        logger.warning(f'Failed to parse start_time for campaign {campaign_data["id"]}: {str(e)}')
                
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
                
                synced_count += 1
                
                if created:
                    logger.info(f'Created new campaign: {campaign.campaign_name} ({campaign.campaign_id})')
                else:
                    logger.info(f'Updated campaign: {campaign.campaign_name} ({campaign.campaign_id})')
                    
            except Exception as e:
                logger.error(f'Failed to sync campaign {campaign_data.get("id", "unknown")}: {str(e)}')
                continue
        
        return synced_count 