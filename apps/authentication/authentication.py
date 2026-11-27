from typing import Any, cast

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import Token

from apps.authentication.models import User
from apps.authentication.tokens import (
    get_guest_token,
    get_guest_user,
    validate_token_version,
)


class HeaderTokenAuthentication(JWTAuthentication):
    def get_user(self, validated_token: Token) -> Any:
        user = super().get_user(validated_token)
        validate_token_version(cast(User, user), validated_token)
        return user

    def authenticate(self, request: Request) -> Any:
        authenticated = super().authenticate(request)
        if authenticated is not None:
            return authenticated

        token = get_guest_token(request)
        if not token:
            return None

        user = get_guest_user(token)
        if not user:
            raise AuthenticationFailed(_("Invalid guest token."))

        return user, token
