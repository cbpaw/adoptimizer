"""
Clean JSON-only Facebook API endpoints.
All endpoints return JSON responses and are designed for API consumption.
"""
import json
from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.facebook_client import FacebookAPIError, FacebookGraphClient
from apps.facebook_auth.models import FacebookToken
from apps.facebook_auth.serializers import (
    ErrorResponseSerializer,
    FacebookTokenRevokeResponseSerializer,
    FacebookTokenStatusSerializer,
    FacebookTokenValidationResponseSerializer,
    FacebookTokenValidationSerializer,
    FacebookUserDetailSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="Get Facebook Token Status",
        description="Retrieve the current Facebook token status for the authenticated user",
        responses={
            200: FacebookTokenStatusSerializer,
            401: ErrorResponseSerializer,
        },
        tags=["Facebook API"],
    )
)
class FacebookTokenStatusView(APIView):
    """Get Facebook token status - pure JSON API endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current Facebook token status."""
        try:
            facebook_token = request.user.facebook_token

            if facebook_token and facebook_token.is_active:
                return Response({
                    "has_token": True,
                    "facebook_user_name": facebook_token.facebook_user_name,
                    "facebook_user_email": facebook_token.facebook_user_email,
                    "facebook_user_id": facebook_token.facebook_user_id,
                    "scopes": facebook_token.scopes or [],
                    "last_used_at": facebook_token.last_used_at,
                    "expires_at": facebook_token.expires_at,
                    "token_expired": facebook_token.is_expired,
                    "token_expires_soon": facebook_token.expires_soon,
                })
            else:
                return Response({
                    "has_token": False,
                    "facebook_user_name": None,
                    "facebook_user_email": None,
                    "facebook_user_id": None,
                    "scopes": [],
                    "last_used_at": None,
                    "expires_at": None,
                    "token_expired": False,
                    "token_expires_soon": False,
                })

        except FacebookToken.DoesNotExist:
            return Response({
                "has_token": False,
                "facebook_user_name": None,
                "facebook_user_email": None,
                "facebook_user_id": None,
                "scopes": [],
                "last_used_at": None,
                "expires_at": None,
                "token_expired": False,
                "token_expires_soon": False,
            })


@extend_schema_view(
    post=extend_schema(
        summary="Validate and Save Facebook Token",
        description="""
        Validate a Facebook access token with Facebook's API and save it securely.

        This endpoint:
        1. Validates the token with Facebook Graph API
        2. Retrieves user information and permissions
        3. Stores the token for future API calls
        4. Returns comprehensive token information
        """,
        request=FacebookTokenValidationSerializer,
        responses={
            200: FacebookTokenValidationResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
        },
        tags=["Facebook API"],
    )
)
class FacebookTokenValidateView(APIView):
    """Validate and save Facebook token - pure JSON API endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Validate and save Facebook access token."""
        serializer = FacebookTokenValidationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "error": "Invalid request data",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        access_token = serializer.validated_data["access_token"]

        try:
            # Validate with Facebook API
            client = FacebookGraphClient(access_token)

            # Get user info
            user_info = client.get("me", params={"fields": "id,name,email"})

            # Get permissions
            permissions_response = client.get("me/permissions")
            scopes = [
                perm["permission"]
                for perm in permissions_response.get("data", [])
                if perm.get("status") == "granted"
            ]

        except FacebookAPIError as e:
            return Response(
                {
                    "error": f"Facebook API validation failed: {e.message}",
                    "details": f"Error code: {e.error_code}" if e.error_code else None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate expiration (60 days for long-lived tokens)
        expires_at = timezone.now() + timedelta(days=60)

        # Save token
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

        return Response({
            "success": True,
            "message": "Token validated and saved successfully",
            "created": created,
            "user_info": {
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "facebook_id": user_info["id"],
            },
            "token_info": {
                "scopes": scopes,
                "expires_at": expires_at,
                "facebook_user_name": facebook_token.facebook_user_name,
                "facebook_user_email": facebook_token.facebook_user_email,
                "facebook_user_id": facebook_token.facebook_user_id,
                "last_used_at": facebook_token.last_used_at,
                "token_expired": facebook_token.is_expired,
                "token_expires_soon": facebook_token.expires_soon,
            }
        })


@extend_schema_view(
    post=extend_schema(
        summary="Revoke Facebook Token",
        description="""
        Deactivate the user's Facebook access token.

        This endpoint:
        1. Marks the token as inactive
        2. Prevents future API calls
        3. Maintains record for audit purposes
        """,
        responses={
            200: FacebookTokenRevokeResponseSerializer,
            401: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=["Facebook API"],
    )
)
class FacebookTokenRevokeView(APIView):
    """Revoke Facebook token - pure JSON API endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Revoke Facebook access token."""
        try:
            facebook_token = request.user.facebook_token
            facebook_token.is_active = False
            facebook_token.save()

            return Response({
                "success": True,
                "message": "Facebook token revoked successfully"
            })

        except FacebookToken.DoesNotExist:
            return Response(
                {
                    "error": "No Facebook token found for this user"
                },
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema_view(
    get=extend_schema(
        summary="Get Facebook User Details",
        description="""
        Retrieve detailed information about the authenticated user's Facebook profile.

        This endpoint:
        1. Uses the stored Facebook token to fetch user details
        2. Retrieves comprehensive profile information from Facebook
        3. Returns structured user data for display
        """,
        responses={
            200: FacebookUserDetailSerializer,
            401: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            400: ErrorResponseSerializer,
        },
        tags=["Facebook API"],
    )
)
class FacebookUserDetailView(APIView):
    """Get Facebook user details - pure JSON API endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get detailed Facebook user information."""
        try:
            facebook_token = request.user.facebook_token

            if not facebook_token.is_active:
                return Response(
                    {"error": "Facebook token is not active"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if facebook_token.is_expired:
                return Response(
                    {"error": "Facebook token has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Use the Facebook API client
            client = FacebookGraphClient(facebook_token.access_token)

            try:
                # Get detailed user information
                user_data = client.get("me", params={
                    "fields": "id,name,email,first_name,last_name,picture.width(200).height(200),locale,timezone,gender,age_range,link,verified"
                })

                # Update last used timestamp
                facebook_token.last_used_at = timezone.now()
                facebook_token.save(update_fields=["last_used_at"])

                return Response(user_data)

            except FacebookAPIError as e:
                return Response(
                    {
                        "error": f"Failed to fetch user details: {e.message}",
                        "details": f"Error code: {e.error_code}" if e.error_code else None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except FacebookToken.DoesNotExist:
            return Response(
                {"error": "No Facebook token found for this user"},
                status=status.HTTP_404_NOT_FOUND
            )