from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.facebook_ads.models import FacebookAdAccount
from apps.facebook_ads.services import FacebookMarketingAPIService

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync Facebook ads for all active accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=str,
            help='Sync ads for a specific account ID only',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Sync ads for a specific user only',
        )

    def handle(self, *args, **options):
        accounts = FacebookAdAccount.objects.filter(is_active=True)
        
        if options['account_id']:
            accounts = accounts.filter(ad_account_id=options['account_id'])
        
        if options['user_email']:
            try:
                user = User.objects.get(email=options['user_email'])
                accounts = accounts.filter(user=user)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {options["user_email"]} not found')
                )
                return

        if not accounts.exists():
            self.stdout.write(self.style.WARNING('No Facebook ad accounts found'))
            return

        total_synced = 0
        for account in accounts:
            self.stdout.write(f'Syncing ads for account: {account.ad_account_name} ({account.ad_account_id})')
            
            try:
                service = FacebookMarketingAPIService(account)
                
                # Test connection first
                if not service.test_connection():
                    self.stdout.write(
                        self.style.ERROR(f'Failed to connect to account {account.ad_account_id}')
                    )
                    continue
                
                # Fetch and sync ads
                ads_data = service.fetch_ads(limit=100, status_filter=['ACTIVE', 'PAUSED'])
                synced_count = service.sync_ads_to_database(ads_data)
                
                total_synced += synced_count
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully synced {synced_count} ads for account {account.ad_account_id}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing account {account.ad_account_id}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Total ads synced: {total_synced}')
        ) 