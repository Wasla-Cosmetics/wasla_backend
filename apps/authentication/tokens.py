from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import GuestUser, User

GUEST_TOKEN_HEADER = "X-Guest-Token"
TOKEN_VERSION_CLAIM = "token_version"


def get_guest_token(request):
    return request.headers.get(GUEST_TOKEN_HEADER)


def get_guest_user(token):
    if not token:
        return None

    try:
        return GuestUser.objects.get(
            session_key=token,
            expires_at__gt=timezone.now(),
        )
    except GuestUser.DoesNotExist:
        return None


def create_refresh_token(user):
    refresh = RefreshToken.for_user(user)
    refresh[TOKEN_VERSION_CLAIM] = user.token_version
    return refresh


def validate_token_version(user, token):
    token_version = token.get(TOKEN_VERSION_CLAIM, 0)
    if token_version != user.token_version:
        raise AuthenticationFailed(_("Token is no longer valid."))


def revoke_user_tokens(user):
    user.token_version += 1
    user.save(update_fields=["token_version"])

    outstanding_tokens = OutstandingToken.objects.filter(user=user)
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in outstanding_tokens],
        ignore_conflicts=True,
    )


def create_password_reset_token(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{uid}.{token}"


def get_password_reset_user(reset_token):
    try:
        uid, token = reset_token.split(".", 1)
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None

    if not default_token_generator.check_token(user, token):
        return None

    return user
