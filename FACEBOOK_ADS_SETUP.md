# Facebook Marketing API Integration

This document explains how to set up and use the Facebook Marketing API integration in AdOptimizer.

## Prerequisites

1. **Facebook Developer Account**: You need a Facebook Developer account to create an app and get API credentials.
2. **Facebook Ad Account**: You need an active Facebook Ad Account with running ads.
3. **Facebook App**: Create a Facebook app with Marketing API permissions.

## Setup Steps

### 1. Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "Create App" and choose "Business" as the app type
3. Fill in your app details and create the app
4. Note down your **App ID** and **App Secret**

### 2. Configure App Permissions

1. In your Facebook app dashboard, go to "App Review" > "Permissions and Features"
2. Request the following permissions:
   - `ads_read` - To read ads data
   - `ads_management` - To manage ads (if needed)
   - `business_management` - To access business accounts

### 3. Get Your Ad Account ID

1. Go to [Facebook Ads Manager](https://www.facebook.com/adsmanager/)
2. Click on the account Settings from the menu on the bottom left
3. Your Ad Account ID will be displayed (e.g., 123456789012345)
4. Copy the number (without 'act_' prefix if shown)

### 4. Connect Your Account in AdOptimizer

1. Log into your AdOptimizer dashboard
2. In the Facebook Ads section, click "Connect Facebook Account"
3. Enter your Facebook App ID when prompted
4. You'll be redirected to Facebook for authorization
5. After authorization, enter your Ad Account ID
6. Your account will be connected and ready to sync ads

## Features

### Dashboard Integration

The dashboard displays:
- **Total Ads**: Number of ads in your connected accounts
- **Active Ads**: Number of currently active ads
- **Total Spend**: Total amount spent on ads
- **Total Impressions**: Total impressions across all ads
- **Recent Ads Table**: List of recent ads with performance metrics

### API Endpoints

- `GET /facebook-ads/api/ads/` - Get all user's Facebook ads
- `GET /facebook-ads/api/summary/` - Get ads performance summary
- `POST /facebook-ads/accounts/<id>/sync/` - Sync ads for a specific account

### Management Commands

```bash
# Sync all Facebook ads
make manage ARGS="sync_facebook_ads"

# Sync ads for a specific account
make manage ARGS="sync_facebook_ads --account-id=123456789012345"

# Sync ads for a specific user
make manage ARGS="sync_facebook_ads --user-email=user@example.com"
```

## Data Synced

For each ad, the following data is synced:
- Ad ID and Name
- Campaign ID and Name
- AdSet ID and Name
- Status (Active, Paused, etc.)
- Objective
- Performance metrics:
  - Impressions
  - Clicks
  - Spend
  - CTR (Click-through rate)
  - CPM (Cost per mille)
  - CPC (Cost per click)

## Security Notes

- App secrets and access tokens are stored securely in the database
- All API calls use HTTPS
- Access tokens are scoped to only necessary permissions
- Users can only access their own ad accounts

## Troubleshooting

### Common Issues

1. **"Failed to connect to Facebook ad account"**
   - Check that your Ad Account ID is correct
   - Ensure your Facebook app has the necessary permissions
   - Verify that your access token is valid

2. **"No ads found"**
   - Make sure you have active or paused ads in your account
   - Check that the date range includes your ads
   - Verify that your account has ads with the filtered statuses

3. **"Permission denied"**
   - Ensure your Facebook app has been approved for Marketing API access
   - Check that you have the necessary permissions for the ad account
   - Verify that your access token hasn't expired

### Getting Help

If you encounter issues:
1. Check the Django logs for detailed error messages
2. Test your Facebook app credentials in the Facebook Graph API Explorer
3. Ensure your ad account is active and has the necessary permissions

## Rate Limits

Facebook Marketing API has rate limits:
- Be mindful of the number of API calls
- The sync process is designed to respect rate limits
- Large accounts may take longer to sync

## Data Refresh

- Ads data is cached in the database for performance
- Use the "Sync Ads" button to refresh data from Facebook
- Set up periodic sync using the management command with cron jobs if needed 