import json
from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.facebook_client import FacebookAPIError, FacebookGraphClient

from .models import FacebookToken
from .serializers import (
    ErrorResponseSerializer,
    FacebookTokenRevokeResponseSerializer,
    FacebookTokenStatusSerializer,
    FacebookTokenValidationResponseSerializer,
    FacebookTokenValidationSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="Get Facebook Token Status",
        description="Retrieve the current Facebook token status for the authenticated user",
        responses={
            200: FacebookTokenStatusSerializer,
            401: ErrorResponseSerializer,
        },
        tags=["Facebook Authentication"],
    )
)
class FacebookTokenStatusAPIView(APIView):
    """API view to get Facebook token status for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get Facebook token status."""
        try:
            facebook_token = request.user.facebook_token
        except FacebookToken.DoesNotExist:
            facebook_token = None

        if facebook_token and facebook_token.is_active:
            data = {
                "has_token": True,
                "facebook_user_name": facebook_token.facebook_user_name,
                "facebook_user_email": facebook_token.facebook_user_email,
                "facebook_user_id": facebook_token.facebook_user_id,
                "scopes": facebook_token.scopes,
                "last_used_at": facebook_token.last_used_at,
                "expires_at": facebook_token.expires_at,
                "token_expired": facebook_token.is_expired,
                "token_expires_soon": facebook_token.expires_soon,
            }
        else:
            data = {"has_token": False}

        return Response(data)


@extend_schema_view(
    post=extend_schema(
        summary="Validate and Save Facebook Token",
        description="""
        Validate a Facebook access token with the Facebook Graph API and save it for the authenticated user.

        This endpoint:
        1. Validates the token with Facebook's API
        2. Retrieves user information and permissions
        3. Stores the token securely for future use
        4. Returns comprehensive token information
        """,
        request=FacebookTokenValidationSerializer,
        responses={
            200: FacebookTokenValidationResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Facebook Authentication"],
    )
)
class FacebookTokenValidationAPIView(APIView):
    """API view to validate and save Facebook access tokens."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Validate and save Facebook access token."""
        serializer = FacebookTokenValidationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        access_token = serializer.validated_data["access_token"]

        try:
            # Validate token with Facebook API
            client = FacebookGraphClient(access_token)

            # Get user info
            user_info = client.get("me", params={"fields": "id,name,email"})

            # Get token permissions
            permissions_response = client.get("me/permissions")
            scopes = [
                perm["permission"]
                for perm in permissions_response.get("data", [])
                if perm.get("status") == "granted"
            ]

        except FacebookAPIError as e:
            return Response(
                {
                    "error": f"Token validation failed: {e.message}",
                    "details": f"Error code: {e.error_code}" if e.error_code else None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate token expiration (Facebook tokens typically last 60 days for long-lived tokens)
        expires_at = timezone.now() + timedelta(days=60)

        # Save or update token
        facebook_token, created = FacebookToken.objects.update_or_create(
            user=request.user,
            defaults={
                "access_token": access_token,
                "token_type": "user_access_token",
                "expires_at": expires_at,
                "scopes": scopes,
                "facebook_user_id": user_info["id"],
                "facebook_user_name": user_info.get("name", ""),
                "facebook_user_email": user_info.get("email", ""),
                "is_active": True,
                "last_used_at": timezone.now(),
            },
        )

        # Return comprehensive response including all token status fields
        response_data = {
            "success": True,
            "message": "Token validated and saved successfully",
            "user_info": {
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "facebook_id": user_info["id"],
            },
            "scopes": scopes,
            "expires_at": expires_at,
            "created": created,
            # Include all status fields for frontend compatibility
            "has_token": True,
            "facebook_user_name": facebook_token.facebook_user_name,
            "facebook_user_email": facebook_token.facebook_user_email,
            "facebook_user_id": facebook_token.facebook_user_id,
            "last_used_at": facebook_token.last_used_at,
            "token_expired": facebook_token.is_expired,
            "token_expires_soon": facebook_token.expires_soon,
        }

        return Response(response_data)


@extend_schema_view(
    post=extend_schema(
        summary="Revoke Facebook Token",
        description="""
        Revoke/deactivate the Facebook access token for the authenticated user.

        This endpoint:
        1. Marks the user's Facebook token as inactive
        2. Prevents future API calls using the token
        3. Maintains token record for audit purposes
        """,
        request=None,
        responses={
            200: FacebookTokenRevokeResponseSerializer,
            401: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Facebook Authentication"],
    )
)
class FacebookTokenRevokeAPIView(APIView):
    """API view to revoke Facebook access tokens."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Revoke Facebook access token."""
        try:
            facebook_token = request.user.facebook_token
            facebook_token.is_active = False
            facebook_token.save()

            return Response({
                "success": True,
                "message": "Token revoked successfully"
            })

        except FacebookToken.DoesNotExist:
            return Response(
                {"error": "No token found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )