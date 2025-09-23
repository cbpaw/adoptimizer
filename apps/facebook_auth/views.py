import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.api.facebook_client import FacebookAPIError, FacebookGraphClient

from .models import FacebookToken


@login_required
def facebook_settings(request):
    """Settings page for Facebook token management."""
    try:
        facebook_token = request.user.facebook_token
    except FacebookToken.DoesNotExist:
        facebook_token = None

    # If this is an AJAX request, return JSON data for the panel
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if facebook_token and facebook_token.is_active:
            return JsonResponse({
                "has_token": True,
                "facebook_user_name": facebook_token.facebook_user_name,
                "facebook_user_email": facebook_token.facebook_user_email,
                "facebook_user_id": facebook_token.facebook_user_id,
                "scopes": facebook_token.scopes,
                "last_used_at": facebook_token.last_used_at.isoformat() if facebook_token.last_used_at else None,
                "expires_at": facebook_token.expires_at.isoformat() if facebook_token.expires_at else None,
                "token_expired": facebook_token.is_expired,
                "token_expires_soon": facebook_token.expires_soon,
            })
        else:
            return JsonResponse({"has_token": False})

    # For regular requests, render the full page (fallback)
    facebook_token_json = None
    if facebook_token and facebook_token.is_active:
        facebook_token_json = json.dumps({
            "has_token": True,
            "facebook_user_name": facebook_token.facebook_user_name,
            "facebook_user_email": facebook_token.facebook_user_email,
            "facebook_user_id": facebook_token.facebook_user_id,
            "scopes": facebook_token.scopes,
            "last_used_at": facebook_token.last_used_at.isoformat() if facebook_token.last_used_at else None,
            "expires_at": facebook_token.expires_at.isoformat() if facebook_token.expires_at else None,
            "token_expired": facebook_token.is_expired,
            "token_expires_soon": facebook_token.expires_soon,
        })

    context = {
        "facebook_token": facebook_token,
        "has_token": facebook_token is not None and facebook_token.is_active,
        "token_expired": facebook_token.is_expired if facebook_token else False,
        "token_expires_soon": facebook_token.expires_soon if facebook_token else False,
        "facebook_token_json": facebook_token_json,
    }

    return render(request, "facebook_auth/settings.html", context)


@require_http_methods(["POST"])
@csrf_exempt
def validate_and_save_token(request):
    """API endpoint to validate and save Facebook access token."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
        access_token = data.get("access_token", "").strip()

        if not access_token:
            return JsonResponse({"error": "Access token is required"}, status=400)

        # Validate token with Facebook API
        client = FacebookGraphClient(access_token)

        try:
            # Get user info
            user_info = client.get("me", params={"fields": "id,name,email"})

            # Get token permissions
            permissions_response = client.get("me/permissions")
            scopes = [
                perm["permission"] for perm in permissions_response.get("data", []) if perm.get("status") == "granted"
            ]

        except FacebookAPIError as e:
            return JsonResponse(
                {
                    "error": f"Token validation failed: {e.message}",
                    "details": f"Error code: {e.error_code}" if e.error_code else None,
                },
                status=400,
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

        return JsonResponse(
            {
                "success": True,
                "message": "Token validated and saved successfully",
                "user_info": {
                    "name": user_info.get("name"),
                    "email": user_info.get("email"),
                    "facebook_id": user_info["id"],
                },
                "scopes": scopes,
                "expires_at": expires_at.isoformat(),
                "created": created,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred", "details": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def revoke_token(request):
    """API endpoint to revoke/delete Facebook access token."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        facebook_token = request.user.facebook_token
        facebook_token.is_active = False
        facebook_token.save()

        return JsonResponse({"success": True, "message": "Token revoked successfully"})

    except FacebookToken.DoesNotExist:
        return JsonResponse({"error": "No token found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred", "details": str(e)}, status=500)
