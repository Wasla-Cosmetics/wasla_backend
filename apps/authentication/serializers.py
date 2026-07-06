from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from uuid import uuid4
from apps.authentication.models import AuthenticatedUser, AnonymousUser


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, data):
        phone = data.get("phone")
        password = data.get("password")

        try:
            user = AuthenticatedUser.objects.get(phone=phone)
        except AuthenticatedUser.DoesNotExist:
            raise serializers.ValidationError({"phone": _("Phone number not found")})

        if not user.check_password(password):
            raise serializers.ValidationError({"password": _("Invalid password.")})

        if not user.is_active:
            raise serializers.ValidationError({"is_active": False})

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        data["user"] = user
        return data


class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField(trim_whitespace=True)
    action = serializers.ChoiceField(choices=["register", "reset-password"])

    def validate(self, data):
        phone = data.get("phone")
        otp = data.get("otp")
        action = data.get("action")

        try:
            if action == "register":
                user = AuthenticatedUser.objects.get(phone=phone, is_active=False)
            elif action == "reset-password":
                user = AuthenticatedUser.objects.get(phone=phone, is_active=True)
            else:
                raise serializers.ValidationError({"action": _("Invalid action")})
        except AuthenticatedUser.DoesNotExist:
            raise serializers.ValidationError({"phone": _("Phone number not found")})

        if not user.otp or user.otp != otp:
            raise serializers.ValidationError({"otp": _("Invalid OTP")})

        now = timezone.now()
        if user.otp_expires_at and user.otp_expires_at <= now:
            user.otp = None
            user.otp_expires_at = None
            user.save(update_fields=["otp", "otp_expires_at"])
            raise serializers.ValidationError({"otp": _("OTP has expired")})

        user.is_active = True
        user.last_login = now
        user.otp = None
        user.otp_expires_at = None
        user.save(update_fields=["is_active", "last_login", "otp", "otp_expires_at"])
        data["user"] = user
        return data


class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, data):
        phone = data.get("phone")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        user = self.context["request"].user

        if phone and phone != user.phone:
            raise serializers.ValidationError(
                {"phone": _("Phone number does not match authenticated user")}
            )

        if password != confirm_password:
            raise serializers.ValidationError({"password": _("Passwords do not match")})

        try:
            password_validation.validate_password(password, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        password = self.validated_data["password"]
        user.set_password(password)
        user.last_login = timezone.now()
        user.otp = None
        user.otp_expires_at = None
        user.save(update_fields=["password", "last_login", "otp", "otp_expires_at"])
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, data):
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"password": _("Passwords do not match")})

        user = self.context.get("request").user

        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"password": _("Old password is incorrect")}
            )

        try:
            password_validation.validate_password(new_password, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
            self.context["token"] = token
        except TokenError:
            raise serializers.ValidationError({"refresh": _("Invalid refresh token")})
        return value

    def save(self):
        token = self.context["token"]
        token.blacklist()
        return token


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, data):
        password = data.get("password")
        user = self.context.get("request").user

        if not user.check_password(password):
            raise serializers.ValidationError({"password": _("Password is incorrect")})

        return data

    def save(self):
        user = self.context.get("request").user
        user.delete()
        return user


class AuthenticatedUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, trim_whitespace=False
    )
    cash_back = serializers.SerializerMethodField()

    class Meta:
        model = AuthenticatedUser
        fields = [
            "id",
            "phone",
            "email",
            "password",
            "full_name",
            "points",
            "cash_back",
        ]
        extra_kwargs = {
            "phone": {"validators": []},
            "email": {"validators": []},
            "points": {"read_only": True},
            "cash_back": {"read_only": True},
        }

    @staticmethod
    def get_cash_back(obj):
        return obj.points // 1000

    def validate(self, attrs):
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
                raise serializers.ValidationError({"password": list(exc.messages)})

        if email:
            users = AuthenticatedUser.objects.filter(email=email)
            if self.instance is not None:
                users = users.exclude(pk=self.instance.pk)

            if users.exists():
                raise serializers.ValidationError({"email": _("Email already exists")})

        return attrs

    def create(self, validated_data):
        phone = validated_data.get("phone")
        email = validated_data.get("email")

        user = AuthenticatedUser.objects.filter(phone=phone).first()

        if user:
            if user.is_active:
                raise serializers.ValidationError(
                    {
                        "phone": _("Phone number already exists and active"),
                        "is_active": True,
                    }
                )
            else:
                raise serializers.ValidationError(
                    {
                        "phone": _("Phone number already exists but not active"),
                        "is_active": False,
                    }
                )

        if AuthenticatedUser.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": _("Email already exists")})

        validated_data["phone"] = phone
        validated_data["email"] = email
        return AuthenticatedUser.objects.create_user(**validated_data)

    def update(self, instance, validated_data):

        if "email" in validated_data:
            email = validated_data["email"]

            if (
                AuthenticatedUser.objects.exclude(pk=instance.pk)
                .filter(email=email)
                .exists()
            ):
                raise serializers.ValidationError({"email": _("Email already exists")})

        if "phone" in validated_data:
            validated_data.pop("phone")

        if "password" in validated_data:
            validated_data.pop("password")

        return super().update(instance, validated_data)


class AnonymousUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnonymousUser
        fields = ["id", "session_key"]
        extra_kwargs = {
            "session_key": {"read_only": True},
        }

    def create(self, validated_data):
        session_key = str(uuid4())
        return AnonymousUser.objects.create(session_key=session_key)
