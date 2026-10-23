from hashlib import sha256

from rest_framework.throttling import SimpleRateThrottle


class AuthIPRateThrottle(SimpleRateThrottle):
    scope = "auth_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class AuthPhoneRateThrottle(SimpleRateThrottle):
    scope = "auth_phone"

    def get_cache_key(self, request, view):
        phone = request.data.get("phone")
        if not phone:
            return None

        phone_digest = sha256(str(phone).strip().encode()).hexdigest()
        return self.cache_format % {
            "scope": self.scope,
            "ident": phone_digest,
        }
