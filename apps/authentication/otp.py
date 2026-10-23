from datetime import timedelta
import json
from secrets import randbelow
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException

REGISTER_OTP = "register"
RESET_PASSWORD_OTP = "reset-password"


class OtpDeliveryUnavailable(APIException):
    status_code = 503
    default_detail = _("OTP delivery is temporarily unavailable.")
    default_code = "otp_delivery_unavailable"


class UnconfiguredOtpDeliveryBackend:
    def send(self, phone, otp):
        raise OtpDeliveryUnavailable()


class WebhookOtpDeliveryBackend:
    def send(self, phone, otp):
        payload = json.dumps({"phone": phone, "otp": otp}).encode("utf-8")
        request = Request(
            settings.AUTH_OTP_WEBHOOK_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {settings.AUTH_OTP_WEBHOOK_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=settings.AUTH_OTP_WEBHOOK_TIMEOUT_SECONDS,
            ) as response:
                if response.status >= 400:
                    raise OtpDeliveryUnavailable()
        except (OSError, URLError) as exc:
            raise OtpDeliveryUnavailable() from exc


def generate_otp():
    return f"{randbelow(1_000_000):06d}"


def get_delivery_backend():
    backend_class = import_string(settings.AUTH_OTP_DELIVERY_BACKEND)
    return backend_class()


def clear_otp(user):
    user.otp = None
    user.otp_purpose = None
    user.otp_expires_at = None
    user.save(update_fields=["otp", "otp_purpose", "otp_expires_at"])


def issue_otp(user, purpose):
    otp = generate_otp()
    user.otp = make_password(otp)
    user.otp_purpose = purpose
    user.otp_expires_at = timezone.now() + timedelta(
        minutes=settings.AUTH_OTP_TTL_MINUTES
    )
    user.save(update_fields=["otp", "otp_purpose", "otp_expires_at"])

    try:
        get_delivery_backend().send(user.phone, otp)
    except Exception:
        clear_otp(user)
        raise


def verify_otp(user, otp, purpose):
    now = timezone.now()
    if (
        not user.otp
        or user.otp_purpose != purpose
        or user.otp_expires_at is None
        or user.otp_expires_at <= now
        or not check_password(otp, user.otp)
    ):
        if user.otp_expires_at is not None and user.otp_expires_at <= now:
            clear_otp(user)
        return False

    clear_otp(user)
    return True
