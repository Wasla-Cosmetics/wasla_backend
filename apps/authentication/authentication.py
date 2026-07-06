from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.authentication.tokens import get_anonymous_token, get_anonymous_user


class HeaderTokenAuthentication(JWTAuthentication):
    def authenticate(self, request):
        authenticated = super().authenticate(request)
        if authenticated is not None:
            return authenticated

        token = get_anonymous_token(request)
        if not token:
            return None

        user = get_anonymous_user(token)
        if not user:
            raise AuthenticationFailed(_("Invalid anonymous token."))

        return user, token
