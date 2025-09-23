"""
API mixins to reduce redundancy and provide common functionality
for Facebook API endpoints.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from apps.facebook_accounts.models import FacebookAdAccount
from apps.facebook_auth.models import FacebookToken

from .facebook_client import FacebookAPIError, FacebookGraphClient


class FacebookAuthMixin:
    """Mixin to handle Facebook authentication and token validation."""

    def get_facebook_token(self) -> FacebookToken:
        """Get the Facebook token for the current user."""
        try:
            token = FacebookToken.objects.get(user=self.request.user, is_active=True)
            if token.is_expired:
                return Response(
                    {"error": "Facebook token has expired. Please reconnect your account."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            return token
        except FacebookToken.DoesNotExist:
            return Response(
                {"error": "Facebook account not connected. Please connect your Facebook account first."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    def get_facebook_client(self) -> FacebookGraphClient:
        """Get authenticated Facebook client."""
        token = self.get_facebook_token()
        if isinstance(token, Response):  # Error response
            return token
        return FacebookGraphClient(token.access_token)


class FacebookAccountMixin(FacebookAuthMixin):
    """Mixin to handle Facebook ad account access and validation."""

    def get_facebook_account(self, account_id: str) -> FacebookAdAccount:
        """Get and validate Facebook ad account access."""
        account = get_object_or_404(FacebookAdAccount, account_id=account_id, user=self.request.user, is_active=True)
        return account


class FacebookProxyMixin(FacebookAccountMixin):
    """
    Base mixin for endpoints that proxy requests to Facebook Graph API.
    Provides consistent error handling and response formatting.
    """

    def handle_facebook_error(self, error: FacebookAPIError) -> Response:
        """Convert Facebook API errors to DRF responses."""
        error_data = {
            "error": error.message,
            "facebook_error_code": error.error_code,
        }

        if error.http_status:
            # Map Facebook HTTP status codes to appropriate DRF status codes
            status_mapping = {
                400: status.HTTP_400_BAD_REQUEST,
                401: status.HTTP_401_UNAUTHORIZED,
                403: status.HTTP_403_FORBIDDEN,
                404: status.HTTP_404_NOT_FOUND,
                429: status.HTTP_429_TOO_MANY_REQUESTS,
                500: status.HTTP_502_BAD_GATEWAY,
            }
            response_status = status_mapping.get(error.http_status, status.HTTP_502_BAD_GATEWAY)
        else:
            response_status = status.HTTP_502_BAD_GATEWAY

        return Response(error_data, status=response_status)

    def proxy_facebook_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> Response:
        """
        Proxy a request to Facebook Graph API and return formatted response.
        """
        client = self.get_facebook_client()
        if isinstance(client, Response):  # Error response from get_facebook_client
            return client

        try:
            if method.upper() == "GET":
                response_data = client.get(endpoint, params=params)
            elif method.upper() == "POST":
                response_data = client.post(endpoint, data=data, params=params)
            elif method.upper() == "PATCH":
                response_data = client.patch(endpoint, data=data, params=params)
            elif method.upper() == "DELETE":
                response_data = client.delete(endpoint, params=params)
            else:
                return Response(
                    {"error": f"Unsupported HTTP method: {method}"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
                )

            # Determine response status based on method
            if method.upper() == "POST":
                response_status = status.HTTP_201_CREATED
            elif method.upper() == "DELETE":
                response_status = status.HTTP_204_NO_CONTENT
            else:
                response_status = status.HTTP_200_OK

            return Response(response_data, status=response_status)

        except FacebookAPIError as e:
            return self.handle_facebook_error(e)


class PaginationMixin:
    """Mixin to handle Facebook API pagination."""

    def paginate_facebook_response(self, response_data: dict) -> dict:
        """
        Convert Facebook pagination format to a standardized format.
        """
        data = response_data.get("data", [])
        paging = response_data.get("paging", {})

        return {
            "results": data,
            "paging": {
                "next": paging.get("next"),
                "previous": paging.get("previous"),
            },
            "upstream_url": response_data.get("upstream_url"),
        }


class FacebookEntityMixin(FacebookProxyMixin, PaginationMixin):
    """
    Combined mixin for Facebook entity endpoints (campaigns, adsets, ads).
    Provides CRUD operations with consistent patterns.
    """

    entity_name = None  # Should be overridden in subclasses
    facebook_fields = None  # Default fields to request from Facebook

    def get_facebook_fields(self) -> str | None:
        """Get fields parameter for Facebook API requests."""
        # Check if fields are provided in query params
        fields = self.request.query_params.get("fields")
        if fields:
            return fields
        # Fall back to default fields if defined
        return self.facebook_fields

    def list_entities(self, parent_id: str, endpoint_template: str) -> Response:
        """Generic list method for Facebook entities."""
        params = {}
        fields = self.get_facebook_fields()
        if fields:
            params["fields"] = fields

        endpoint = endpoint_template.format(parent_id=parent_id)
        response = self.proxy_facebook_request("GET", endpoint, params=params)

        if response.status_code == 200:
            # Apply pagination formatting
            paginated_data = self.paginate_facebook_response(response.data)
            return Response(paginated_data)

        return response

    def create_entity(self, parent_id: str, endpoint_template: str, data: dict) -> Response:
        """Generic create method for Facebook entities."""
        endpoint = endpoint_template.format(parent_id=parent_id)
        return self.proxy_facebook_request("POST", endpoint, data=data)

    def retrieve_entity(self, entity_id: str) -> Response:
        """Generic retrieve method for Facebook entities."""
        params = {}
        fields = self.get_facebook_fields()
        if fields:
            params["fields"] = fields

        return self.proxy_facebook_request("GET", entity_id, params=params)

    def update_entity(self, entity_id: str, data: dict) -> Response:
        """Generic update method for Facebook entities."""
        return self.proxy_facebook_request("PATCH", entity_id, data=data)

    def delete_entity(self, entity_id: str) -> Response:
        """Generic delete method for Facebook entities."""
        return self.proxy_facebook_request("DELETE", entity_id)
