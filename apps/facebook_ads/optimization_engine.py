"""
Optimization Engine Service

This module contains the core logic for evaluating optimization strategies
and taking actions on Facebook campaigns.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple

from django.utils import timezone
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.campaign import Campaign as FBCampaign
from facebook_business.exceptions import FacebookRequestError

from .models import (
    CampaignOptimization,
    OptimizationLog,
    OptimizationStrategy,
    FacebookCampaign,
    FacebookAdAccount,
)

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """
    Core optimization engine that evaluates campaigns against strategies
    and takes appropriate actions.
    """

    def __init__(self, campaign_optimization: CampaignOptimization):
        self.campaign_optimization = campaign_optimization
        self.campaign = campaign_optimization.campaign
        self.strategy = campaign_optimization.strategy
        self.ad_account = self.campaign.ad_account
        self.api = None
        self._initialize_api()

    def _initialize_api(self):
        """Initialize Facebook Ads API with account credentials"""
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
            logger.info(f"Facebook API initialized for campaign {self.campaign.campaign_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Facebook API: {str(e)}")
            raise

    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics for the campaign.
        Aggregates data from the optimization start date to now.
        """
        from .models import FacebookCampaignInsights

        # Get insights from optimization start date
        start_date = self.campaign_optimization.optimization_start_date
        end_date = timezone.now().date()

        insights = FacebookCampaignInsights.objects.filter(
            campaign=self.campaign,
            date_start__gte=start_date,
            date_start__lte=end_date,
        )

        # Aggregate metrics
        total_spend = Decimal('0')
        total_clicks = 0
        total_add_to_carts = 0
        total_purchases = 0
        total_revenue = Decimal('0')

        for insight in insights:
            total_spend += insight.spend or Decimal('0')
            total_clicks += insight.clicks or 0
            total_add_to_carts += insight.actions_add_to_cart or 0
            total_purchases += insight.actions_purchase or 0

            # Calculate revenue from purchase value
            if insight.action_values_purchase:
                total_revenue += insight.action_values_purchase

        # Calculate derived metrics
        cpc = (total_spend / total_clicks) if total_clicks > 0 else Decimal('0')
        roas = float(total_revenue / total_spend) if total_spend > 0 else 0.0

        metrics = {
            'spend': float(total_spend),
            'cpc': float(cpc),
            'add_to_carts': total_add_to_carts,
            'purchases': total_purchases,
            'roas': roas,
            'revenue': float(total_revenue),
            'clicks': total_clicks,
        }

        logger.info(f"Current metrics for campaign {self.campaign.campaign_id}: {metrics}")
        return metrics

    def evaluate_strategy(self, metrics: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Evaluate the strategy rules against current metrics.

        Returns:
            Tuple of (action, rule_triggered, reason)
            Actions: KEEP_RUNNING, PAUSE, SCALE_UP, SCALE_DOWN, NO_ACTION
        """
        rules = self.strategy.rules.get('rules', [])
        current_spend = metrics['spend']

        # Sort rules by spend threshold to evaluate in order
        sorted_rules = sorted(rules, key=lambda x: float(x.get('spend_threshold', 0)))

        # Find the highest applicable rule (highest spend threshold that we've reached)
        applicable_rule = None
        for rule in sorted_rules:
            spend_threshold = float(rule.get('spend_threshold', 0))
            if current_spend >= spend_threshold:
                applicable_rule = rule
            else:
                # We haven't reached this threshold yet, skip remaining rules
                break

        if not applicable_rule:
            return ('NO_ACTION', '', 'Spend threshold not yet reached for any rules')

        # Evaluate the rule
        metric_name = applicable_rule.get('metric')
        operator = applicable_rule.get('operator')
        threshold_value = float(applicable_rule.get('value', 0))
        action = applicable_rule.get('action')
        spend_threshold = applicable_rule.get('spend_threshold')

        # Get the actual metric value
        current_value = metrics.get(metric_name, 0)

        # Evaluate the condition
        rule_met = self._evaluate_condition(current_value, operator, threshold_value)

        rule_description = f"At €{spend_threshold} spend: {metric_name} {operator} {threshold_value}"

        if not rule_met:
            # Rule condition failed
            reason = f"Rule triggered: {rule_description}. Current {metric_name}: {current_value}. Action: {action}"
            logger.info(f"Campaign {self.campaign.campaign_id} - {reason}")
            return (action, rule_description, reason)
        else:
            # Rule condition met, keep running
            reason = f"Rule passed: {rule_description}. Current {metric_name}: {current_value}. Continuing."
            logger.info(f"Campaign {self.campaign.campaign_id} - {reason}")
            return ('KEEP_RUNNING', rule_description, reason)

    def _evaluate_condition(self, actual_value: float, operator: str, threshold_value: float) -> bool:
        """Evaluate a condition based on operator"""
        if operator == 'less_than':
            return actual_value < threshold_value
        elif operator == 'greater_than':
            return actual_value > threshold_value
        elif operator == 'equals':
            return actual_value == threshold_value
        elif operator == 'at_least':
            return actual_value >= threshold_value
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

    def take_action(self, action: str) -> bool:
        """
        Execute the determined action via Facebook API.

        Returns:
            bool: True if action was successful, False otherwise
        """
        try:
            fb_campaign = FBCampaign(self.campaign.campaign_id)

            if action == 'PAUSE':
                # Pause the campaign
                fb_campaign.api_update(params={
                    FBCampaign.Field.status: FBCampaign.Status.paused
                })
                logger.info(f"Paused campaign {self.campaign.campaign_id}")

                # Update local database
                self.campaign.status = 'PAUSED'
                self.campaign.save()
                return True

            elif action == 'SCALE_UP':
                # Increase budget by 20%
                current_budget = float(self.campaign.daily_budget or 0)
                new_budget = current_budget * 1.20

                fb_campaign.api_update(params={
                    FBCampaign.Field.daily_budget: int(new_budget * 100)  # Facebook uses cents
                })
                logger.info(f"Scaled up campaign {self.campaign.campaign_id} budget from {current_budget} to {new_budget}")

                # Update local database
                self.campaign.daily_budget = Decimal(str(new_budget))
                self.campaign.save()
                return True

            elif action == 'SCALE_DOWN':
                # Decrease budget by 20%
                current_budget = float(self.campaign.daily_budget or 0)
                new_budget = current_budget * 0.80

                fb_campaign.api_update(params={
                    FBCampaign.Field.daily_budget: int(new_budget * 100)  # Facebook uses cents
                })
                logger.info(f"Scaled down campaign {self.campaign.campaign_id} budget from {current_budget} to {new_budget}")

                # Update local database
                self.campaign.daily_budget = Decimal(str(new_budget))
                self.campaign.save()
                return True

            elif action in ['KEEP_RUNNING', 'NO_ACTION']:
                # No action needed
                logger.info(f"No action needed for campaign {self.campaign.campaign_id}")
                return True

            else:
                logger.warning(f"Unknown action: {action}")
                return False

        except FacebookRequestError as e:
            logger.error(f"Facebook API error while taking action {action} on campaign {self.campaign.campaign_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error taking action {action} on campaign {self.campaign.campaign_id}: {str(e)}")
            return False

    def run_optimization(self) -> OptimizationLog:
        """
        Main method to run optimization check on the campaign.

        Returns:
            OptimizationLog: The log entry for this optimization run
        """
        logger.info(f"Running optimization for campaign {self.campaign.campaign_id} with strategy {self.strategy.name}")

        # Get current metrics
        metrics = self.get_current_metrics()

        # Evaluate strategy
        action, rule_triggered, reason = self.evaluate_strategy(metrics)

        # Take action
        action_successful = self.take_action(action)

        # Log the result
        log_entry = OptimizationLog.objects.create(
            campaign_optimization=self.campaign_optimization,
            campaign=self.campaign,
            strategy=self.strategy,
            spend=Decimal(str(metrics['spend'])),
            cpc=Decimal(str(metrics['cpc'])),
            add_to_carts=metrics['add_to_carts'],
            purchases=metrics['purchases'],
            roas=metrics['roas'],
            action=action,
            rule_triggered=rule_triggered,
            reason=reason,
            action_successful=action_successful,
        )

        logger.info(f"Optimization completed for campaign {self.campaign.campaign_id}. Action: {action}, Success: {action_successful}")

        return log_entry
