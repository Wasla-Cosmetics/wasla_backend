from django.db import transaction
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.models import GuestUser, User
from apps.authentication.serializers import (
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    GuestUserSerializer,
    LoginSerializer,
    LogoutSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    VerifyOtpSerializer,
    VersionedTokenRefreshSerializer,
)
from apps.authentication.throttles import AuthIPRateThrottle, AuthPhoneRateThrottle
from apps.authentication.tokens import create_password_reset_token
from apps.authentication.utils import (
    generate_successful_auth_response,
    handle_otp_for_user,
)
from apps.core.responses import build_response

AUTH_THROTTLES = [AuthIPRateThrottle, AuthPhoneRateThrottle]


class VersionedTokenRefreshView(TokenRefreshView):
    serializer_class = VersionedTokenRefreshSerializer
    throttle_classes = AUTH_THROTTLES


class RegisterView(APIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    throttle_classes = AUTH_THROTTLES

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
            response = handle_otp_for_user(request.data.get("phone"), "register")
        return Response(response, status=response["status"])


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = AUTH_THROTTLES

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        response = generate_successful_auth_response(
            user, _("Login successful"), self.request
        )
        return Response(response, status=response["status"])


class SendOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = AUTH_THROTTLES

    def post(self, request, *args, **kwargs):
        response = handle_otp_for_user(request.data.get("phone"), "send-otp")
        return Response(response, status=response["status"])


class VerifyOtpView(APIView):
    serializer_class = VerifyOtpSerializer
    permission_classes = [AllowAny]
    throttle_classes = AUTH_THROTTLES

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if serializer.validated_data["action"] == "reset-password":
            response = build_response(
                status_code=status.HTTP_200_OK,
                message=_("OTP verified"),
                data={"reset_token": create_password_reset_token(user)},
            )
        else:
            response = generate_successful_auth_response(
                user, _("OTP verified"), self.request
            )
        return Response(response, status=response["status"])


class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    throttle_classes = AUTH_THROTTLES

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = build_response(
            status_code=status.HTTP_200_OK,
            message=_("Password reset successfully"),
            data={},
        )
        return Response(response, status=response["status"])


class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = build_response(
            status_code=status.HTTP_200_OK,
            message=_("Password changed successfully"),
            data={},
        )
        return Response(response, status=response["status"])


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = build_response(
            status_code=status.HTTP_200_OK,
            message=_("Logout successful"),
            data={},
        )
        return Response(response, status=response["status"])


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteAccountSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = build_response(
            status_code=status.HTTP_200_OK,
            message=_("Account deleted successfully"),
            data={},
        )
        return Response(response, status=response["status"])


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["phone"]


class GuestUserCreateView(CreateAPIView):
    queryset = GuestUser.objects.all()
    serializer_class = GuestUserSerializer
    permission_classes = [AllowAny]
