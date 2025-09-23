from django import template
from apps.facebook_auth.models import FacebookToken

register = template.Library()


@register.simple_tag
def get_facebook_token(user):
    """Get the active Facebook token for a user."""
    try:
        return user.facebook_token if user.facebook_token.is_active else None
    except FacebookToken.DoesNotExist:
        return None