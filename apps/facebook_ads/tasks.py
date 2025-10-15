from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from .models import FacebookAdAccount, FacebookCampaign
from .services import ComprehensiveFacebookAPIService, FacebookInsightsService
import logging

logger = logging.getLogger(__name__)


@shared_task
def sync_facebook_campaigns():
    """Sync Facebook campaigns for all active accounts"""
    logger.info("Starting Facebook campaigns sync for all accounts")
    
    accounts = FacebookAdAccount.objects.filter(is_active=True)
    
    for account in accounts:
        try:
            sync_account_campaigns.delay(account.id)
            logger.info(f"Queued campaign sync for account {account.ad_account_id}")
        except Exception as e:
            logger.error(f"Failed to queue sync for account {account.id}: {str(e)}")
    
    logger.info(f"Queued campaign sync for {accounts.count()} accounts")


@shared_task
def sync_account_campaigns(account_id):
    """Sync campaigns for a specific account"""
    try:
        account = FacebookAdAccount.objects.get(id=account_id)
        logger.info(f"Starting campaign sync for account {account.ad_account_id}")
        
        service = ComprehensiveFacebookAPIService(account)
        
        # Sync campaigns
        campaigns = service.get_comprehensive_campaigns()
        synced_count = service.sync_comprehensive_campaigns_to_database(campaigns)
        
        logger.info(f"Synced {synced_count} campaigns for account {account.ad_account_id}")
        
        # Queue insights sync
        sync_campaign_insights.delay(account.id)
        
        return {'success': True, 'synced_campaigns': synced_count}
        
    except FacebookAdAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return {'success': False, 'error': 'Account not found'}
    except Exception as e:
        logger.error(f"Failed to sync campaigns for account {account_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def sync_campaign_insights(account_id, date_preset='last_30d'):
    """Sync campaign insights for last 30 days"""
    try:
        account = FacebookAdAccount.objects.get(id=account_id)
        logger.info(f"Starting insights sync for account {account.ad_account_id}")
        
        # Get campaigns for this account
        campaigns = FacebookCampaign.objects.filter(
            ad_account=account,
            status__in=['ACTIVE', 'PAUSED']
        )
        
        if not campaigns.exists():
            logger.info(f"No campaigns found for account {account.ad_account_id}")
            return {'success': True, 'synced_insights': 0}
        
        campaign_ids = [c.campaign_id for c in campaigns]
        
        # Get insights
        insights_service = FacebookInsightsService(account)
        insights_data = insights_service.get_campaign_insights(
            campaign_ids=campaign_ids,
            date_preset=date_preset
        )
        
        # Sync to database
        synced_count = insights_service.sync_insights_to_database(insights_data)
        
        logger.info(f"Synced {synced_count} insights for account {account.ad_account_id}")
        
        return {'success': True, 'synced_insights': synced_count}
        
    except FacebookAdAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return {'success': False, 'error': 'Account not found'}
    except Exception as e:
        logger.error(f"Failed to sync insights for account {account_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def sync_daily_insights():
    """Sync daily insights for all active accounts"""
    logger.info("Starting daily insights sync for all accounts")
    
    accounts = FacebookAdAccount.objects.filter(is_active=True)
    
    for account in accounts:
        try:
            sync_campaign_insights.delay(account.id, date_preset='yesterday')
            logger.info(f"Queued daily insights sync for account {account.ad_account_id}")
        except Exception as e:
            logger.error(f"Failed to queue daily insights sync for account {account.id}: {str(e)}")
    
    logger.info(f"Queued daily insights sync for {accounts.count()} accounts")


@shared_task
def sync_specific_campaign_insights(campaign_id, date_preset='last_30d'):
    """Sync insights for a specific campaign"""
    try:
        from .models import FacebookCampaign
        
        campaign = FacebookCampaign.objects.get(campaign_id=campaign_id)
        logger.info(f"Starting insights sync for campaign {campaign.campaign_name}")
        
        insights_service = FacebookInsightsService(campaign.ad_account)
        insights_data = insights_service.get_campaign_insights(
            campaign_ids=[campaign_id],
            date_preset=date_preset
        )
        
        synced_count = insights_service.sync_insights_to_database(insights_data)
        
        logger.info(f"Synced {synced_count} insights for campaign {campaign.campaign_name}")
        
        return {'success': True, 'synced_insights': synced_count}
        
    except FacebookCampaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return {'success': False, 'error': 'Campaign not found'}
    except Exception as e:
        logger.error(f"Failed to sync insights for campaign {campaign_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_insights(days_to_keep=90):
    """Cleanup old insights data to keep database size manageable"""
    try:
        from .models import FacebookCampaignInsights, FacebookAdInsights
        
        cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
        
        # Delete old campaign insights
        campaign_insights_deleted = FacebookCampaignInsights.objects.filter(
            date_start__lt=cutoff_date
        ).delete()
        
        # Delete old ad insights
        ad_insights_deleted = FacebookAdInsights.objects.filter(
            date_start__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {campaign_insights_deleted[0]} campaign insights and {ad_insights_deleted[0]} ad insights older than {days_to_keep} days")
        
        return {
            'success': True,
            'campaign_insights_deleted': campaign_insights_deleted[0],
            'ad_insights_deleted': ad_insights_deleted[0]
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old insights: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def sync_facebook_adsets(account_id):
    """Sync Facebook AdSets for a specific account"""
    try:
        account = FacebookAdAccount.objects.get(id=account_id)
        logger.info(f"Starting AdSet sync for account {account.ad_account_id}")
        
        service = ComprehensiveFacebookAPIService(account)
        
        # Get all campaigns for this account
        campaigns = FacebookCampaign.objects.filter(ad_account=account)
        
        total_synced = 0
        
        for campaign in campaigns:
            try:
                # Get AdSets for this campaign
                adsets = service.get_adsets_for_campaign(campaign.campaign_id)
                synced_count = service.sync_adsets_to_database(campaign, adsets)
                total_synced += synced_count
                
                logger.info(f"Synced {synced_count} AdSets for campaign {campaign.campaign_name}")
                
            except Exception as e:
                logger.error(f"Failed to sync AdSets for campaign {campaign.campaign_id}: {str(e)}")
                continue
        
        logger.info(f"Total synced AdSets: {total_synced} for account {account.ad_account_id}")
        
        return {'success': True, 'synced_adsets': total_synced}
        
    except FacebookAdAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return {'success': False, 'error': 'Account not found'}
    except Exception as e:
        logger.error(f"Failed to sync AdSets for account {account_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def sync_facebook_ads(account_id):
    """Sync Facebook Ads for a specific account"""
    try:
        account = FacebookAdAccount.objects.get(id=account_id)
        logger.info(f"Starting Ads sync for account {account.ad_account_id}")
        
        service = ComprehensiveFacebookAPIService(account)
        
        # Get all campaigns for this account
        campaigns = FacebookCampaign.objects.filter(ad_account=account)
        
        total_synced = 0
        
        for campaign in campaigns:
            try:
                # Get Ads for this campaign
                ads = service.get_ads_for_campaign(campaign.campaign_id)
                synced_count = service.sync_ads_to_database(campaign, ads)
                total_synced += synced_count
                
                logger.info(f"Synced {synced_count} Ads for campaign {campaign.campaign_name}")
                
            except Exception as e:
                logger.error(f"Failed to sync Ads for campaign {campaign.campaign_id}: {str(e)}")
                continue
        
        logger.info(f"Total synced Ads: {total_synced} for account {account.ad_account_id}")
        
        return {'success': True, 'synced_ads': total_synced}
        
    except FacebookAdAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return {'success': False, 'error': 'Account not found'}
    except Exception as e:
        logger.error(f"Failed to sync Ads for account {account_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def full_account_sync(account_id):
    """Perform a complete sync of an account (campaigns, adsets, ads, insights)"""
    try:
        account = FacebookAdAccount.objects.get(id=account_id)
        logger.info(f"Starting full sync for account {account.ad_account_id}")
        
        results = {}
        
        # 1. Sync campaigns
        campaign_result = sync_account_campaigns.delay(account_id).get()
        results['campaigns'] = campaign_result
        
        # 2. Sync AdSets
        adset_result = sync_facebook_adsets.delay(account_id).get()
        results['adsets'] = adset_result
        
        # 3. Sync Ads
        ads_result = sync_facebook_ads.delay(account_id).get()
        results['ads'] = ads_result
        
        # 4. Sync Insights
        insights_result = sync_campaign_insights.delay(account_id).get()
        results['insights'] = insights_result
        
        logger.info(f"Full sync completed for account {account.ad_account_id}")
        
        return {'success': True, 'results': results}
        
    except FacebookAdAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return {'success': False, 'error': 'Account not found'}
    except Exception as e:
        logger.error(f"Failed to perform full sync for account {account_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


# ============================================================================
# OPTIMIZATION ENGINE TASKS
# ============================================================================

@shared_task
def run_campaign_optimization_check():
    """
    Main periodic task to check all campaigns with active optimization.
    This should be run every 15-30 minutes via Celery Beat.
    """
    from .models import CampaignOptimization
    from .optimization_engine import OptimizationEngine

    logger.info("Starting optimization check for all active campaigns")

    # Get all active campaign optimizations
    active_optimizations = CampaignOptimization.objects.filter(
        is_active=True,
        strategy__is_active=True,
        campaign__status='ACTIVE',  # Only check active campaigns
    ).select_related('campaign', 'strategy', 'campaign__ad_account')

    if not active_optimizations.exists():
        logger.info("No active campaign optimizations found")
        return {'success': True, 'checked_campaigns': 0}

    checked_count = 0
    success_count = 0
    error_count = 0

    for campaign_opt in active_optimizations:
        try:
            # Run optimization for this campaign
            engine = OptimizationEngine(campaign_opt)
            log_entry = engine.run_optimization()

            checked_count += 1
            if log_entry.action_successful:
                success_count += 1
            else:
                error_count += 1

            logger.info(
                f"Optimization check completed for campaign {campaign_opt.campaign.campaign_id}. "
                f"Action: {log_entry.action}, Success: {log_entry.action_successful}"
            )

        except Exception as e:
            error_count += 1
            logger.error(
                f"Failed to run optimization for campaign {campaign_opt.campaign.campaign_id}: {str(e)}",
                exc_info=True
            )

    logger.info(
        f"Optimization check completed. Checked: {checked_count}, Success: {success_count}, Errors: {error_count}"
    )

    return {
        'success': True,
        'checked_campaigns': checked_count,
        'successful_actions': success_count,
        'failed_actions': error_count,
    }


@shared_task
def run_single_campaign_optimization(campaign_id):
    """
    Run optimization check for a single campaign.
    Used for manual "Run Now" triggers from the UI.
    """
    from .models import CampaignOptimization, FacebookCampaign
    from .optimization_engine import OptimizationEngine

    try:
        campaign = FacebookCampaign.objects.get(campaign_id=campaign_id)
        logger.info(f"Starting manual optimization check for campaign {campaign_id}")

        # Get active optimization for this campaign
        campaign_opt = CampaignOptimization.objects.filter(
            campaign=campaign,
            is_active=True,
            strategy__is_active=True,
        ).select_related('campaign', 'strategy', 'campaign__ad_account').first()

        if not campaign_opt:
            logger.warning(f"No active optimization found for campaign {campaign_id}")
            return {
                'success': False,
                'error': 'No active optimization found for this campaign'
            }

        # Run optimization
        engine = OptimizationEngine(campaign_opt)
        log_entry = engine.run_optimization()

        logger.info(
            f"Manual optimization completed for campaign {campaign_id}. "
            f"Action: {log_entry.action}, Success: {log_entry.action_successful}"
        )

        return {
            'success': True,
            'campaign_id': campaign_id,
            'action': log_entry.action,
            'action_successful': log_entry.action_successful,
            'reason': log_entry.reason,
        }

    except FacebookCampaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return {'success': False, 'error': 'Campaign not found'}
    except Exception as e:
        logger.error(f"Failed to run optimization for campaign {campaign_id}: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)} 