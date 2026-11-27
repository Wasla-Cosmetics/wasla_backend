from hashlib import sha256

from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class AuthIPRateThrottle(SimpleRateThrottle):
    scope = "auth_ip"

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class GuestUserRateThrottle(AuthIPRateThrottle):
    scope = "guest_user"


class AuthPhoneRateThrottle(SimpleRateThrottle):
    scope = "auth_phone"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if not isinstance(request.data, dict):
            return None
        phone = request.data.get("phone")
        if not phone:
            return None

        phone_digest = sha256(str(phone).strip().encode()).hexdigest()
        return self.cache_format % {
            "scope": self.scope,
            "ident": phone_digest,
        }
