from rest_framework import serializers


class FacebookTokenValidationSerializer(serializers.Serializer):
    """Serializer for Facebook token validation request."""

    access_token = serializers.CharField(
        max_length=500,
        help_text="Facebook access token to validate and store"
    )


class FacebookTokenValidationResponseSerializer(serializers.Serializer):
    """Serializer for Facebook token validation response."""

    success = serializers.BooleanField(help_text="Whether the operation was successful")
    message = serializers.CharField(help_text="Success message")
    user_info = serializers.DictField(
        help_text="Facebook user information",
        child=serializers.CharField()
    )
    scopes = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of granted Facebook permissions"
    )
    expires_at = serializers.DateTimeField(help_text="Token expiration timestamp")
    created = serializers.BooleanField(help_text="Whether a new token was created")

    # Include all the token status fields for consistency
    has_token = serializers.BooleanField(help_text="Whether user has an active token")
    facebook_user_name = serializers.CharField(help_text="Facebook user's display name")
    facebook_user_email = serializers.CharField(help_text="Facebook user's email address")
    facebook_user_id = serializers.CharField(help_text="Facebook user ID")
    last_used_at = serializers.DateTimeField(help_text="When token was last used")
    token_expired = serializers.BooleanField(help_text="Whether token has expired")
    token_expires_soon = serializers.BooleanField(help_text="Whether token expires within 7 days")


class FacebookTokenStatusSerializer(serializers.Serializer):
    """Serializer for Facebook token status response."""

    has_token = serializers.BooleanField(help_text="Whether user has an active token")
    facebook_user_name = serializers.CharField(
        help_text="Facebook user's display name",
        required=False,
        allow_null=True
    )
    facebook_user_email = serializers.CharField(
        help_text="Facebook user's email address",
        required=False,
        allow_null=True
    )
    facebook_user_id = serializers.CharField(
        help_text="Facebook user ID",
        required=False,
        allow_null=True
    )
    scopes = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of granted Facebook permissions",
        required=False,
        allow_null=True
    )
    last_used_at = serializers.DateTimeField(
        help_text="When token was last used",
        required=False,
        allow_null=True
    )
    expires_at = serializers.DateTimeField(
        help_text="Token expiration timestamp",
        required=False,
        allow_null=True
    )
    token_expired = serializers.BooleanField(
        help_text="Whether token has expired",
        required=False
    )
    token_expires_soon = serializers.BooleanField(
        help_text="Whether token expires within 7 days",
        required=False
    )


class FacebookTokenRevokeResponseSerializer(serializers.Serializer):
    """Serializer for Facebook token revocation response."""

    success = serializers.BooleanField(help_text="Whether the operation was successful")
    message = serializers.CharField(help_text="Success message")


class FacebookUserDetailSerializer(serializers.Serializer):
    """Serializer for Facebook user detail response."""

    id = serializers.CharField(help_text="Facebook user ID")
    name = serializers.CharField(help_text="User's display name")
    email = serializers.CharField(
        help_text="User's email address",
        required=False,
        allow_null=True
    )
    first_name = serializers.CharField(
        help_text="User's first name",
        required=False,
        allow_null=True
    )
    last_name = serializers.CharField(
        help_text="User's last name",
        required=False,
        allow_null=True
    )
    picture = serializers.DictField(
        help_text="User's profile picture data",
        required=False,
        allow_null=True
    )
    locale = serializers.CharField(
        help_text="User's locale",
        required=False,
        allow_null=True
    )
    timezone = serializers.IntegerField(
        help_text="User's timezone offset",
        required=False,
        allow_null=True
    )
    gender = serializers.CharField(
        help_text="User's gender",
        required=False,
        allow_null=True
    )
    age_range = serializers.DictField(
        help_text="User's age range",
        required=False,
        allow_null=True
    )
    link = serializers.CharField(
        help_text="Link to user's Facebook profile",
        required=False,
        allow_null=True
    )
    verified = serializers.BooleanField(
        help_text="Whether the user is verified",
        required=False
    )


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""

    error = serializers.CharField(help_text="Error message")
    details = serializers.CharField(
        help_text="Additional error details",
        required=False,
        allow_null=True
    )