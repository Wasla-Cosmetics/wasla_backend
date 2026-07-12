from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.authentication.models import AnonymousUser, AuthenticatedUser

ANONYMOUS_TOKEN_HEADER = "X-Anonymous-Token"


def get_bearer_token(request):
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()

    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]

    return None


def get_anonymous_token(request):
    return request.headers.get(ANONYMOUS_TOKEN_HEADER)


def get_authenticated_user(token):
    if not token:
        return None

    try:
        access_token = AccessToken(token)
        user_id = access_token.get(settings.SIMPLE_JWT.get("USER_ID_CLAIM", "user_id"))
    except TokenError:
        return None

    try:
        return AuthenticatedUser.objects.get(id=user_id, is_active=True)
    except AuthenticatedUser.DoesNotExist:
        return None


def get_anonymous_user(token):
    if not token:
        return None

    try:
        return AnonymousUser.objects.get(session_key=token)
    except AnonymousUser.DoesNotExist:
        return None
