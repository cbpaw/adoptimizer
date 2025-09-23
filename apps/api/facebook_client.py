"""
Facebook Graph API client for handling requests with proper authentication
and error handling.
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class FacebookAPIError(Exception):
    """Custom exception for Facebook API errors."""

    def __init__(self, message: str, error_code: str = None, http_status: int = None):
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        super().__init__(self.message)


class FacebookGraphClient:
    """Client for Facebook Graph API interactions."""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()

    def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict[str, Any]:
        """Make authenticated request to Facebook Graph API."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        # Add access token to params
        if params is None:
            params = {}
        params["access_token"] = self.access_token

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data if method in ["POST", "PATCH", "PUT"] else None,
                timeout=30,
            )

            # Log the actual URL for debugging
            logger.info(f"Facebook API call: {method} {response.url}")

            # Parse response
            response_data = response.json()

            if not response.ok:
                error_info = response_data.get("error", {})
                raise FacebookAPIError(
                    message=error_info.get("message", "Unknown Facebook API error"),
                    error_code=error_info.get("code"),
                    http_status=response.status_code,
                )

            # Add upstream URL info for external API endpoints
            response_data["upstream_url"] = response.url

            return response_data

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise FacebookAPIError(f"Request failed: {str(e)}") from e

    def get(self, endpoint: str, params: dict = None) -> dict[str, Any]:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict = None, params: dict = None) -> dict[str, Any]:
        """Make POST request."""
        return self._make_request("POST", endpoint, params=params, data=data)

    def patch(self, endpoint: str, data: dict = None, params: dict = None) -> dict[str, Any]:
        """Make PATCH request."""
        return self._make_request("PATCH", endpoint, params=params, data=data)

    def delete(self, endpoint: str, params: dict = None) -> dict[str, Any]:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint, params=params)

    # Account methods
    def get_ad_accounts(self, fields: str = None) -> dict[str, Any]:
        """Get user's ad accounts."""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get("me/adaccounts", params=params)

    # Campaign methods
    def get_campaigns(self, account_id: str, fields: str = None) -> dict[str, Any]:
        """Get campaigns for an ad account."""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get(f"{account_id}/campaigns", params=params)

    def create_campaign(self, account_id: str, campaign_data: dict) -> dict[str, Any]:
        """Create a new campaign."""
        return self.post(f"{account_id}/campaigns", data=campaign_data)

    def get_campaign(self, campaign_id: str, fields: str = None) -> dict[str, Any]:
        """Get a specific campaign."""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get(campaign_id, params=params)

    def update_campaign(self, campaign_id: str, campaign_data: dict) -> dict[str, Any]:
        """Update a campaign."""
        return self.patch(campaign_id, data=campaign_data)

    def delete_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Delete/archive a campaign."""
        return self.delete(campaign_id)

    # AdSet methods
    def get_adsets(self, campaign_id: str, fields: str = None) -> dict[str, Any]:
        """Get ad sets for a campaign."""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get(f"{campaign_id}/adsets", params=params)

    def create_adset(self, campaign_id: str, adset_data: dict) -> dict[str, Any]:
        """Create a new ad set."""
        return self.post(f"{campaign_id}/adsets", data=adset_data)

    def get_adset(self, adset_id: str, fields: str = None) -> dict[str, Any]:
        """Get a specific ad set."""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get(adset_id, params=params)

    def update_adset(self, adset_id: str, adset_data: dict) -> dict[str, Any]:
        """Update an ad set."""
        return self.patch(adset_id, data=adset_data)

    def delete_adset(self, adset_id: str) -> dict[str, Any]:
        """Delete/archive an ad set."""
        return self.delete(adset_id)

    # Ad methods
    def get_ads(self, adset_id: str, fields: str = None) -> dict[str, Any]:
        """Get ads for an ad set."""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get(f"{adset_id}/ads", params=params)

    def create_ad(self, adset_id: str, ad_data: dict) -> dict[str, Any]:
        """Create a new ad."""
        return self.post(f"{adset_id}/ads", data=ad_data)

    def get_ad(self, ad_id: str, fields: str = None) -> dict[str, Any]:
        """Get a specific ad."""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get(ad_id, params=params)

    def update_ad(self, ad_id: str, ad_data: dict) -> dict[str, Any]:
        """Update an ad."""
        return self.patch(ad_id, data=ad_data)

    def delete_ad(self, ad_id: str) -> dict[str, Any]:
        """Delete/archive an ad."""
        return self.delete(ad_id)

    # Creative methods
    def get_creatives(self, account_id: str, fields: str = None) -> dict[str, Any]:
        """Get creatives for an ad account."""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get(f"{account_id}/adcreatives", params=params)

    def create_creative(self, account_id: str, creative_data: dict) -> dict[str, Any]:
        """Create a new creative."""
        return self.post(f"{account_id}/adcreatives", data=creative_data)

    # Insights methods
    def get_insights(self, entity_id: str, params: dict = None) -> dict[str, Any]:
        """Get insights for an entity (account, campaign, adset, ad)."""
        if params is None:
            params = {}
        return self.get(f"{entity_id}/insights", params=params)
