from django.utils.translation import gettext_lazy as _
from rest_framework import status

from apps.authentication.models import User
from apps.authentication.otp import REGISTER_OTP, RESET_PASSWORD_OTP, issue_otp
from apps.authentication.serializers import UserSerializer
from apps.authentication.tokens import create_refresh_token
from apps.core.responses import build_response


def handle_otp_for_user(phone, action):
    if not phone:
        return build_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=_("Phone number is required"),
            data={},
        )

    user = User.objects.filter(phone=phone).first()

    if not user:
        if action == "register":
            return build_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=_("User not found"),
                data={},
            )
        return build_response(
            status_code=status.HTTP_200_OK,
            message=_("If the account exists, an OTP has been sent."),
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

    purpose = RESET_PASSWORD_OTP if user.is_active else REGISTER_OTP
    issue_otp(user, purpose)

    if action != "register":
        message_status = _("If the account exists, an OTP has been sent.")
        data = {}

    return build_response(status_code=status_code, message=message_status, data=data)


def generate_successful_auth_response(user, message, request):
    refresh = create_refresh_token(user)
    user_data = UserSerializer(user, context={"request": request}).data

    data = {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": user_data,
    }

    return build_response(status_code=status.HTTP_200_OK, message=message, data=data)
