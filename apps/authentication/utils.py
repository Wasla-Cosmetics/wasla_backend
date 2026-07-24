from datetime import timedelta
from secrets import randbelow

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from apps.core.responses import build_response
from apps.authentication.models import AuthenticatedUser
from apps.authentication.serializers import AuthenticatedUserSerializer


def generate_otp():
    return f"{randbelow(1_000_000):06d}"


def handle_otp_for_user(phone, action):
    if not phone:
        return build_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=_("Phone number is required"),
            data={},
        )

    otp = generate_otp()
    user = AuthenticatedUser.objects.filter(phone=phone).first()

    if not user:
        return build_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=_("User not found"),
            data={},
        )

    message_status = _("OTP sent")
    status_code = 200
    data = {}

    if not user.is_active:
        if action == "register":
            message_status = _("Registration successful, OTP sent")
            status_code = 201
        else:
            message_status = _("OTP sent")
            status_code = 200
            data["is_active"] = False

    # user.otp = otp
    user.otp = "123456"
    user.otp_expires_at = timezone.now() + timedelta(
        minutes=settings.AUTH_OTP_TTL_MINUTES
    )
    user.save(update_fields=["otp", "otp_expires_at"])

    return build_response(status_code=status_code, message=message_status, data=data)


def generate_successful_auth_response(user, message, request):
    refresh = RefreshToken.for_user(user)
    user_data = AuthenticatedUserSerializer(user, context={"request": request}).data

    data = {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": user_data,
    }

    return build_response(status_code=status.HTTP_200_OK, message=message, data=data)
