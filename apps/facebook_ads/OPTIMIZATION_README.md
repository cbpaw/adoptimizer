# Campaign Optimization System

This document describes the automated campaign optimization system for Facebook Ads.

## Overview

The optimization system automatically monitors Facebook ad campaigns and takes actions (pause, scale budget) based on predefined strategies. It runs as a background Celery task and logs all checks and actions for complete visibility.

## Architecture

### Components

1. **Optimization Models** (`models.py`)
   - `OptimizationStrategy`: Reusable rule-based strategies
   - `CampaignOptimization`: Links campaigns to strategies
   - `OptimizationLog`: Audit trail of all checks and actions
   - `OptimizationMetrics`: Aggregated performance data
   - `DailyPeriod`: Date range tracking

2. **Optimization Engine** (`optimization_engine.py`)
   - `OptimizationEngine`: Core logic for evaluating campaigns
   - Fetches current metrics from database
   - Evaluates strategy rules against metrics
   - Takes actions via Facebook Marketing API
   - Creates detailed log entries

3. **Celery Tasks** (`tasks.py`)
   - `run_campaign_optimization_check`: Periodic task (every 20 minutes)
   - `run_single_campaign_optimization`: Manual trigger for single campaign

4. **UI Components**
   - Strategy Management: Create and edit optimization strategies
   - Optimization Dashboard: Overview of all campaigns
   - Logs Viewer: Filter and view optimization logs
   - Campaign Detail: Per-campaign optimization controls

## How It Works

### 1. Strategy Definition

Strategies consist of rules that are evaluated in sequence based on spend thresholds:

```json
{
  "rules": [
    {
      "spend_threshold": "10.00",
      "metric": "cpc",
      "operator": "less_than",
      "value": "1.20",
      "action": "PAUSE"
    },
    {
      "spend_threshold": "20.00",
      "metric": "add_to_cart",
      "operator": "at_least",
      "value": "1",
      "action": "PAUSE"
    },
    {
      "spend_threshold": "30.00",
      "metric": "purchases",
      "operator": "at_least",
      "value": "1",
      "action": "PAUSE"
    }
  ]
}
```

**Rule Evaluation Logic:**
- Rules are sorted by `spend_threshold` (ascending)
- Only the highest threshold that has been reached is evaluated
- If the rule condition **fails**, the specified action is taken
- If the rule condition **passes**, the campaign keeps running

**Example:**
If a campaign has spent €25:
- The €10 rule is passed (not evaluated)
- The €20 rule is the highest reached threshold
- Check: Does the campaign have at least 1 add-to-cart?
  - NO → Action: PAUSE the campaign
  - YES → Action: KEEP_RUNNING

### 2. Metrics Calculation

Metrics are aggregated from `FacebookCampaignInsights` starting from the `optimization_start_date`:

- **Spend**: Total ad spend (€)
- **CPC**: Cost Per Click (spend / clicks)
- **Add to Cart**: Total add-to-cart events
- **Purchases**: Total purchase events
- **ROAS**: Return on Ad Spend (revenue / spend)

### 3. Available Actions

- **KEEP_RUNNING**: No action, campaign continues
- **PAUSE**: Pause the campaign via Facebook API
- **SCALE_UP**: Increase daily budget by 20%
- **SCALE_DOWN**: Decrease daily budget by 20%
- **NO_ACTION**: Spend threshold not reached yet

### 4. Automatic Execution

The Celery Beat scheduler runs `run_campaign_optimization_check` every 20 minutes:

1. Fetches all campaigns with active optimization
2. For each campaign:
   - Gets current metrics
   - Evaluates strategy rules
   - Takes action if needed
   - Logs the result
3. Updates campaign status in database

## Usage

### Creating a Strategy

1. Navigate to **Optimization → Strategies**
2. Click **Create New Strategy**
3. Enter strategy name and description
4. Add rules using the visual rule builder:
   - Set spend threshold (when to evaluate this rule)
   - Select metric to check
   - Choose comparison operator
   - Set threshold value
   - Select action to take if rule fails
5. Save strategy

### Enabling Optimization for a Campaign

**From Campaign Detail Page:**
1. Open campaign detail page
2. Scroll to "Optimization" section
3. Select a strategy from dropdown
4. Click "Enable Optimization"

**From Optimization Dashboard:**
1. Navigate to **Optimization → Dashboard**
2. Find campaign in table
3. Select strategy from dropdown in "Optimization" column
4. Click "Enable"

### Viewing Logs

1. Navigate to **Optimization → Logs**
2. Use filters to narrow down:
   - Campaign
   - Strategy
   - Action taken
   - Date range
3. View detailed metrics snapshot and action reasons

### Manual Trigger

To immediately run optimization check on a campaign:

1. Open campaign detail page
2. In optimization section, click "Run Check Now"
3. Or from dashboard, click "Run Now" button

## Database Schema

### OptimizationStrategy
- `name`: Strategy name
- `description`: Strategy description
- `rules`: JSON field with rule definitions
- `is_active`: Enable/disable strategy

### CampaignOptimization
- `campaign`: Foreign key to FacebookCampaign
- `strategy`: Foreign key to OptimizationStrategy
- `is_active`: Enable/disable optimization
- `optimization_start_date`: Date to start aggregating metrics from

### OptimizationLog
- `campaign_optimization`: Link to CampaignOptimization
- `campaign`: Campaign that was checked
- `strategy`: Strategy that was applied
- `check_time`: When the check was performed
- `spend`, `cpc`, `add_to_carts`, `purchases`, `roas`: Metrics snapshot
- `action`: Action taken
- `rule_triggered`: Which rule was evaluated
- `reason`: Detailed explanation
- `action_successful`: Whether Facebook API call succeeded

## API Endpoints

### Enable Optimization
```http
POST /facebook-ads/api/optimization/enable/
Content-Type: application/json

{
  "campaign_id": 123,
  "strategy_id": 456
}
```

### Disable Optimization
```http
POST /facebook-ads/api/optimization/disable/
Content-Type: application/json

{
  "campaign_id": 123
}
```

### Run Optimization Now
```http
POST /facebook-ads/api/optimization/run-now/
Content-Type: application/json

{
  "campaign_id": 123
}
```

## Configuration

### Celery Beat Schedule

The periodic task is configured via Django migration:
- **Task**: `apps.facebook_ads.tasks.run_campaign_optimization_check`
- **Interval**: Every 20 minutes
- **Expires**: 20 minutes (won't run if delayed)

To change the schedule:
1. Access Django Admin
2. Navigate to **Periodic Tasks**
3. Edit "run-campaign-optimization-checks"
4. Modify interval or crontab

### Facebook API Integration

Actions are executed via Facebook Marketing API:

```python
from facebook_business.adobjects.campaign import Campaign

# Pause campaign
campaign = Campaign(campaign_id)
campaign.api_update(params={
    Campaign.Field.status: Campaign.Status.paused
})

# Update budget (in cents)
campaign.api_update(params={
    Campaign.Field.daily_budget: int(new_budget * 100)
})
```

## Monitoring

### Logs

All optimization activity is logged to:
- **Application logs**: `logger.info()` statements in optimization_engine.py
- **Database**: OptimizationLog table with full details
- **UI**: Logs Viewer page with filtering

### Checking Task Status

View Celery worker logs:
```bash
make logs
# or
docker compose logs -f celery
```

Verify periodic task is running:
```bash
make manage ARGS='shell -c "from django_celery_beat.models import PeriodicTask; print(PeriodicTask.objects.get(name=\"run-campaign-optimization-checks\"))"'
```

## Troubleshooting

### Optimization Not Running

1. **Check Celery is running:**
   ```bash
   docker compose ps
   ```
   Ensure `celery` and `celery-beat` containers are up

2. **Check periodic task is enabled:**
   - Django Admin → Periodic Tasks
   - Verify "run-campaign-optimization-checks" is enabled

3. **Check logs:**
   ```bash
   docker compose logs celery | grep optimization
   ```

### Actions Not Being Taken

1. **Verify Facebook API credentials:**
   - Check ad account has valid access token
   - Ensure token has `ads_management` permission

2. **Check optimization logs:**
   - Look at `action_successful` field
   - Read `reason` for detailed explanation

3. **Verify campaign status:**
   - Campaign must be ACTIVE to be checked
   - CampaignOptimization must be active
   - Strategy must be active

### Metrics Not Updating

1. **Ensure insights are syncing:**
   - Check last sync time on campaign page
   - Run manual sync if needed

2. **Verify optimization start date:**
   - Metrics are calculated from `optimization_start_date`
   - Check if sufficient data exists

## Best Practices

1. **Start with Conservative Rules:**
   - Test strategies on small budgets first
   - Use wider thresholds initially
   - Monitor logs closely

2. **Monitor Regularly:**
   - Check logs daily when starting
   - Review dashboard for unexpected pauses
   - Adjust strategies based on performance

3. **Use Multiple Strategies:**
   - Create different strategies for different campaign types
   - Test variations to find optimal rules
   - Keep successful strategies active

4. **Backup Important Campaigns:**
   - Don't enable optimization on critical campaigns without testing
   - Always have manual override available
   - Keep strategies simple and understandable

## Example Strategies

### Conservative CPC Strategy
- €10 spent → CPC must be < €1.50, else pause
- €25 spent → At least 1 add-to-cart, else pause
- €50 spent → At least 1 purchase, else pause

### Aggressive ROAS Strategy
- €20 spent → ROAS must be > 1.5, else pause
- €40 spent → ROAS must be > 2.0, else pause
- €100 spent → ROAS must be > 2.5, else scale down

### Performance-Based Scaling
- €30 spent → CPC < €1.00, scale up 20%
- €30 spent → CPC > €2.00, scale down 20%
- €50 spent → ROAS > 3.0, scale up 20%

## Future Enhancements

Potential improvements to the optimization system:

- [ ] Ad-level optimization (currently campaign-level only)
- [ ] Email notifications on actions taken
- [ ] Slack/Discord webhooks for alerts
- [ ] A/B testing different strategies
- [ ] Machine learning-based optimization
- [ ] Budget allocation across campaigns
- [ ] Dayparting (time-of-day rules)
- [ ] Geo-targeting rules
- [ ] Audience performance-based rules
