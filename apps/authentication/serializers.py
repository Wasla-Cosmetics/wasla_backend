from typing import Any, cast
from uuid import uuid4

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import GuestUser, User
from apps.authentication.otp import REGISTER_OTP, RESET_PASSWORD_OTP, verify_otp
from apps.authentication.tokens import (
    get_password_reset_user,
    revoke_user_tokens,
    validate_token_version,
)


class VersionedTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs: Any) -> dict[str, Any]:
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.get("user_id")
        user = User.objects.filter(pk=user_id, is_active=True).first()

        if user is None:
            raise AuthenticationFailed(_("Invalid refresh token"))

        validate_token_version(user, refresh)
        return super().validate(attrs)


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, data: Any) -> dict[str, Any]:
        phone = data.get("phone")
        password = data.get("password")

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            User().set_password(password)
            raise serializers.ValidationError(_("Invalid credentials.")) from None

        if not user.check_password(password):
            raise serializers.ValidationError(_("Invalid credentials."))

        if not user.is_active:
            raise serializers.ValidationError(_("Invalid credentials."))

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        data["user"] = user
        return data


class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField(trim_whitespace=True)
    action = serializers.ChoiceField(choices=["register", "reset-password"])

    def validate(self, data: Any) -> dict[str, Any]:
        phone = data.get("phone")
        otp = data.get("otp")
        action = data.get("action")

        purpose = REGISTER_OTP if action == "register" else RESET_PASSWORD_OTP
        expected_active = action == "reset-password"
        user = User.objects.filter(phone=phone, is_active=expected_active).first()

        if user is None or not verify_otp(user, otp, purpose):
            raise serializers.ValidationError({"otp": _("Invalid or expired OTP")})

        if action == "register":
            user.is_active = True
            user.last_login = timezone.now()
            user.save(update_fields=["is_active", "last_login"])

        data["user"] = user
        return data


class ResetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField(write_only=True, trim_whitespace=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, data: Any) -> dict[str, Any]:
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        user = get_password_reset_user(data.get("reset_token"))

        if user is None:
            raise serializers.ValidationError(
                {"reset_token": _("Invalid or expired reset token")}
            )

        if password != confirm_password:
            raise serializers.ValidationError({"password": _("Passwords do not match")})

        try:
            password_validation.validate_password(password, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc

        data["user"] = user
        return data

    def save(self, **kwargs: Any) -> User:
        user = self.validated_data["user"]
        password = self.validated_data["password"]
        user.set_password(password)
        user.last_login = timezone.now()
        user.otp = None
        user.otp_purpose = None
        user.otp_expires_at = None
        user.save(
            update_fields=[
                "password",
                "last_login",
                "otp",
                "otp_purpose",
                "otp_expires_at",
            ]
        )
        revoke_user_tokens(user)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, data: Any) -> dict[str, Any]:
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"password": _("Passwords do not match")})

        request = cast(Request, self.context.get("request"))
        user = cast(User, request.user)

        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"password": _("Old password is incorrect")}
            )

        try:
            password_validation.validate_password(new_password, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc

        data["user"] = user
        return data

    def save(self, **kwargs: Any) -> User:
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save(update_fields=["password"])
        revoke_user_tokens(user)
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_refresh(self, value: str) -> str:
        try:
            token = RefreshToken(cast(Any, value))
        except TokenError:
            raise serializers.ValidationError(_("Invalid refresh token")) from None

        request = self.context["request"]
        user_id_claim = token.get("user_id")
        if str(user_id_claim) != str(request.user.pk):
            raise serializers.ValidationError(
                _("Refresh token does not belong to this user.")
            )

        context = cast(dict[str, Any], self.context)
        context["token"] = token
        return value

    def save(self, **kwargs: Any) -> RefreshToken:
        token = self.context["token"]
        token.blacklist()
        return token


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, data: Any) -> dict[str, Any]:
        password = data.get("password")
        request = cast(Request, self.context.get("request"))
        user = cast(User, request.user)

        if not user.check_password(password):
            raise serializers.ValidationError({"password": _("Password is incorrect")})

        return data

    def save(self, **kwargs: Any) -> User:
        request = cast(Request, self.context.get("request"))
        user = cast(User, request.user)
        user.delete()
        return user


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, trim_whitespace=False
    )
    cash_back = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "password",
            "full_name",
            "reward_points",
            "cash_back",
        ]
        extra_kwargs = {
            "phone": {"validators": []},
            "email": {"validators": []},
            "reward_points": {"read_only": True},
            "cash_back": {"read_only": True},
        }

    @staticmethod
    def get_cash_back(obj: User) -> int:
        return obj.reward_points // 1000

    def validate(self, attrs: Any) -> dict[str, Any]:
        password = attrs.get("password")
        email = attrs.get("email")

        if self.instance is None and not password:
            raise serializers.ValidationError(
                {"password": _("This field is required.")}
            )

        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    {"password": list(exc.messages)}
                ) from exc

        if email:
            users = User.objects.filter(email=email)
            if self.instance is not None:
                users = users.exclude(pk=self.instance.pk)

            if users.exists():
                raise serializers.ValidationError({"email": _("Email already exists")})

        return attrs

    def create(self, validated_data: Any) -> User:
        phone = validated_data.get("phone")
        email = validated_data.get("email")

        user = User.objects.filter(phone=phone).first()

        if user:
            if user.is_active:
                detail: dict[str, Any] = {
                    "phone": _("Phone number already exists and active"),
                    "is_active": True,
                }
                raise serializers.ValidationError(detail)
            else:
                detail = {
                    "phone": _("Phone number already exists but not active"),
                    "is_active": False,
                }
                raise serializers.ValidationError(detail)

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": _("Email already exists")})

        user_data = dict(validated_data)
        user_data["phone"] = phone
        user_data["email"] = email
        return User.objects.create_user(**user_data)

    def update(self, instance: User, validated_data: Any) -> User:

        if "email" in validated_data:
            email = validated_data["email"]

            if User.objects.exclude(pk=instance.pk).filter(email=email).exists():
                raise serializers.ValidationError({"email": _("Email already exists")})

        if "phone" in validated_data:
            validated_data.pop("phone")

        if "password" in validated_data:
            validated_data.pop("password")

        return super().update(instance, validated_data)


class GuestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestUser
        fields = ["id", "session_key", "expires_at"]
        extra_kwargs = {
            "session_key": {"read_only": True},
            "expires_at": {"read_only": True},
        }

    def create(self, validated_data: Any) -> GuestUser:
        GuestUser.objects.filter(expires_at__lte=timezone.now()).delete()
        session_key = str(uuid4())
        return GuestUser.objects.create(session_key=session_key)
