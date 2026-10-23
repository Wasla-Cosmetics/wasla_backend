from datetime import timedelta
import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


from .models import GuestUser
from .otp import WebhookOtpDeliveryBackend
from .tokens import create_password_reset_token, create_refresh_token


class RecordingOtpBackend:
    messages = []

    def send(self, phone, otp):
        self.messages.append({"phone": phone, "otp": otp})


class WebhookOtpDeliveryBackendTests(SimpleTestCase):
    @override_settings(
        AUTH_OTP_WEBHOOK_URL="https://sms.example.com/otp",
        AUTH_OTP_WEBHOOK_TOKEN="secret-token",
        AUTH_OTP_WEBHOOK_TIMEOUT_SECONDS=4,
    )
    @patch("apps.authentication.otp.urlopen")
    def test_sends_otp_to_configured_https_webhook(self, mocked_urlopen):
        response = MagicMock(status=202)
        mocked_urlopen.return_value.__enter__.return_value = response

        WebhookOtpDeliveryBackend().send("+201000000001", "654321")

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://sms.example.com/otp")
        self.assertEqual(
            json.loads(request.data),
            {"phone": "+201000000001", "otp": "654321"},
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-token")
        self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], 4)


@override_settings(
    AUTH_OTP_DELIVERY_BACKEND="apps.authentication.tests.RecordingOtpBackend"
)
class AuthenticationApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        RecordingOtpBackend.messages.clear()
        cache.clear()

    def test_register_creates_inactive_user_with_otp(self):
        response = self.client.post(
            reverse("register"),
            {
                "phone": "+201000000001",
                "email": "user@example.com",
                "full_name": "Wasla User",
                "password": "NileBridgePass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["errors"], {})
        self.assertIsNone(response.data["pagination"])

        user = self.user_model.objects.get(phone="+201000000001")
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.otp)
        self.assertIsNotNone(user.otp_expires_at)
        self.assertEqual(user.otp_purpose, "register")
        delivered_otp = RecordingOtpBackend.messages[0]["otp"]
        self.assertNotEqual(delivered_otp, "123456")
        self.assertNotEqual(user.otp, delivered_otp)
        self.assertTrue(check_password(delivered_otp, user.otp))

    def test_verify_register_otp_activates_user_and_returns_tokens(self):
        user = self.user_model.objects.create_user(
            phone="+201000000002",
            email="verify@example.com",
            full_name="Verify User",
            password="NileBridgePass123!",
            is_active=False,
        )
        user.otp = make_password("123456")
        user.otp_purpose = "register"
        user.otp_expires_at = timezone.now() + timedelta(minutes=10)
        user.save(update_fields=["otp", "otp_purpose", "otp_expires_at"])

        response = self.client.post(
            reverse("verify_otp"),
            {
                "phone": user.phone,
                "otp": "123456",
                "action": "register",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.otp)
        self.assertIsNone(user.otp_expires_at)

    def test_refresh_token_returns_rotated_session_tokens(self):
        user = self.user_model.objects.create_user(
            phone="+201000000020",
            email="refresh@example.com",
            full_name="Refresh User",
            password="NileBridgePass123!",
            is_active=True,
        )
        refresh = create_refresh_token(user)

        response = self.client.post(
            reverse("token_refresh"),
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

        reused_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(reused_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_rejects_token_after_password_change(self):
        user = self.user_model.objects.create_user(
            phone="+201000000021",
            email="revoked-refresh@example.com",
            full_name="Revoked Refresh User",
            password="NileBridgePass123!",
            is_active=True,
        )
        refresh = create_refresh_token(user)
        self.client.post(
            reverse("change_password"),
            {
                "old_password": "NileBridgePass123!",
                "new_password": "NewNileBridgePass123!",
                "confirm_password": "NewNileBridgePass123!",
            },
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}",
            format="json",
        )

        response = self.client.post(
            reverse("token_refresh"),
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_otp_is_rejected_and_cleared(self):
        user = self.user_model.objects.create_user(
            phone="+201000000003",
            email="expired@example.com",
            full_name="Expired User",
            password="NileBridgePass123!",
            is_active=False,
        )
        user.otp = make_password("123456")
        user.otp_purpose = "register"
        user.otp_expires_at = timezone.now() - timedelta(minutes=1)
        user.save(update_fields=["otp", "otp_purpose", "otp_expires_at"])

        response = self.client.post(
            reverse("verify_otp"),
            {
                "phone": user.phone,
                "otp": "123456",
                "action": "register",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Validation error")
        self.assertIn("otp", response.data["errors"])

        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertIsNone(user.otp)
        self.assertIsNone(user.otp_expires_at)

    def test_send_otp_does_not_reveal_whether_phone_exists(self):
        self.user_model.objects.create_user(
            phone="+201000000020",
            email="known@example.com",
            full_name="Known User",
            password="NileBridgePass123!",
            is_active=True,
        )

        known_response = self.client.post(
            reverse("send_otp"),
            {"phone": "+201000000020"},
            format="json",
        )
        unknown_response = self.client.post(
            reverse("send_otp"),
            {"phone": "+201000000099"},
            format="json",
        )

        self.assertEqual(known_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            known_response.data["message"], unknown_response.data["message"]
        )
        self.assertEqual(known_response.data["data"], unknown_response.data["data"])

    def test_reset_otp_returns_scoped_token_and_invalidates_old_access_token(self):
        user = self.user_model.objects.create_user(
            phone="+201000000021",
            email="reset@example.com",
            full_name="Reset User",
            password="NileBridgePass123!",
            is_active=True,
        )
        old_refresh = RefreshToken.for_user(user)

        send_response = self.client.post(
            reverse("send_otp"),
            {"phone": user.phone},
            format="json",
        )
        self.assertEqual(send_response.status_code, status.HTTP_200_OK)
        delivered_otp = RecordingOtpBackend.messages[0]["otp"]

        verify_response = self.client.post(
            reverse("verify_otp"),
            {
                "phone": user.phone,
                "otp": delivered_otp,
                "action": "reset-password",
            },
            format="json",
        )

        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertIn("reset_token", verify_response.data["data"])
        self.assertNotIn("access", verify_response.data["data"])
        self.assertNotIn("refresh", verify_response.data["data"])

        reset_response = self.client.post(
            reverse("reset_password"),
            {
                "reset_token": verify_response.data["data"]["reset_token"],
                "password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(reset_response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPass123!"))

        profile_response = self.client.get(
            reverse("profile"),
            HTTP_AUTHORIZATION=f"Bearer {old_refresh.access_token}",
        )
        self.assertEqual(profile_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_uses_same_error_for_unknown_phone_and_wrong_password(self):
        self.user_model.objects.create_user(
            phone="+201000000022",
            email="login@example.com",
            full_name="Login User",
            password="NileBridgePass123!",
            is_active=True,
        )
        self.user_model.objects.create_user(
            phone="+201000000025",
            email="inactive-login@example.com",
            full_name="Inactive Login User",
            password="NileBridgePass123!",
            is_active=False,
        )

        unknown_response = self.client.post(
            reverse("login"),
            {"phone": "+201000000099", "password": "WrongPass123!"},
            format="json",
        )
        wrong_password_response = self.client.post(
            reverse("login"),
            {"phone": "+201000000022", "password": "WrongPass123!"},
            format="json",
        )
        inactive_response = self.client.post(
            reverse("login"),
            {"phone": "+201000000025", "password": "NileBridgePass123!"},
            format="json",
        )

        self.assertEqual(unknown_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            unknown_response.data["errors"],
            wrong_password_response.data["errors"],
        )
        self.assertEqual(
            unknown_response.data["errors"],
            inactive_response.data["errors"],
        )

    def test_logout_rejects_refresh_token_owned_by_another_user(self):
        user = self.user_model.objects.create_user(
            phone="+201000000023",
            email="logout@example.com",
            full_name="Logout User",
            password="NileBridgePass123!",
            is_active=True,
        )
        other_user = self.user_model.objects.create_user(
            phone="+201000000024",
            email="other-logout@example.com",
            full_name="Other Logout User",
            password="NileBridgePass123!",
            is_active=True,
        )
        access = RefreshToken.for_user(user).access_token
        other_refresh = RefreshToken.for_user(other_user)

        response = self.client.post(
            reverse("logout"),
            {"refresh": str(other_refresh)},
            HTTP_AUTHORIZATION=f"Bearer {access}",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("refresh", response.data["errors"])

    def test_login_is_throttled_by_phone_across_source_ips(self):
        self.user_model.objects.create_user(
            phone="+201000000026",
            email="throttled-login@example.com",
            full_name="Throttled Login User",
            password="NileBridgePass123!",
            is_active=True,
        )

        responses = [
            self.client.post(
                reverse("login"),
                {"phone": "+201000000026", "password": "WrongPass123!"},
                REMOTE_ADDR=f"192.0.2.{index}",
                format="json",
            )
            for index in range(1, 7)
        ]

        self.assertTrue(
            all(
                response.status_code == status.HTTP_400_BAD_REQUEST
                for response in responses[:5]
            )
        )
        self.assertEqual(responses[5].status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_reset_password_token_cannot_target_another_user(self):
        user = self.user_model.objects.create_user(
            phone="+201000000004",
            email="owner@example.com",
            full_name="Owner User",
            password="NileBridgePass123!",
            is_active=True,
        )
        other_user = self.user_model.objects.create_user(
            phone="+201000000005",
            email="other@example.com",
            full_name="Other User",
            password="NileBridgePass123!",
            is_active=True,
        )
        reset_token = create_password_reset_token(user)

        response = self.client.post(
            reverse("reset_password"),
            {
                "reset_token": f"{reset_token}tampered",
                "password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Validation error")
        self.assertIn("reset_token", response.data["errors"])

        user.refresh_from_db()
        other_user.refresh_from_db()
        self.assertTrue(user.check_password("NileBridgePass123!"))
        self.assertTrue(other_user.check_password("NileBridgePass123!"))

    def test_change_password_accepts_post(self):
        user = self.user_model.objects.create_user(
            phone="+201000000006",
            email="change@example.com",
            full_name="Change User",
            password="NileBridgePass123!",
            is_active=True,
        )
        token = RefreshToken.for_user(user)

        response = self.client.post(
            reverse("change_password"),
            {
                "old_password": "NileBridgePass123!",
                "new_password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!",
            },
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPass123!"))


class GuestUserApiTests(APITestCase):
    def test_create_guest_user_returns_session_key(self):
        response = self.client.post(reverse("guest-users"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GuestUser.objects.count(), 1)
        self.assertEqual(
            response.data["data"]["session_key"],
            GuestUser.objects.get().session_key,
        )
        self.assertEqual(response.data["errors"], {})
        self.assertIsNone(response.data["pagination"])


class HeaderTokenAuthenticationTests(APITestCase):
    def test_drf_request_user_can_be_guest_user(self):
        guest_user = GuestUser.objects.create(session_key="guest-session")

        class UserEchoView(APIView):
            def get(self, request):
                return Response(
                    {
                        "user_id": request.user.id,
                        "is_anonymous": request.user.is_anonymous,
                    }
                )

        request = APIRequestFactory().get(
            "/",
            HTTP_X_GUEST_TOKEN=guest_user.session_key,
        )
        response = UserEchoView.as_view()(request)

        self.assertEqual(response.data["user_id"], guest_user.id)
        self.assertTrue(response.data["is_anonymous"])
