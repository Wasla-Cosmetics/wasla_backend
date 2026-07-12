from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from project.middlewares import TokenAuthMiddleware

from .models import AnonymousUser


class AuthenticationApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()

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

        user = self.user_model.objects.get(phone="+201000000001")
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.otp)
        self.assertIsNotNone(user.otp_expires_at)

    def test_verify_register_otp_activates_user_and_returns_tokens(self):
        user = self.user_model.objects.create_user(
            phone="+201000000002",
            email="verify@example.com",
            full_name="Verify User",
            password="NileBridgePass123!",
            is_active=False,
        )
        user.otp = "123456"
        user.otp_expires_at = timezone.now() + timedelta(minutes=10)
        user.save(update_fields=["otp", "otp_expires_at"])

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

    def test_expired_otp_is_rejected_and_cleared(self):
        user = self.user_model.objects.create_user(
            phone="+201000000003",
            email="expired@example.com",
            full_name="Expired User",
            password="NileBridgePass123!",
            is_active=False,
        )
        user.otp = "123456"
        user.otp_expires_at = timezone.now() - timedelta(minutes=1)
        user.save(update_fields=["otp", "otp_expires_at"])

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

        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertIsNone(user.otp)
        self.assertIsNone(user.otp_expires_at)

    def test_reset_password_cannot_target_another_user(self):
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
        token = RefreshToken.for_user(user)

        response = self.client.post(
            reverse("reset_password"),
            {
                "phone": other_user.phone,
                "password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!",
            },
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        other_user.refresh_from_db()
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


class AnonymousUserApiTests(APITestCase):
    def test_create_anonymous_user_returns_session_key(self):
        response = self.client.post(reverse("anonymous-users"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnonymousUser.objects.count(), 1)
        self.assertEqual(
            response.data["session_key"], AnonymousUser.objects.get().session_key
        )


class TokenAuthMiddlewareTests(APITestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TokenAuthMiddleware(lambda request: request)
        self.user_model = get_user_model()

    def test_sets_request_user_from_bearer_jwt(self):
        user = self.user_model.objects.create_user(
            phone="+201000000007",
            email="middleware@example.com",
            full_name="Middleware User",
            password="NileBridgePass123!",
            is_active=True,
        )
        token = RefreshToken.for_user(user)
        request = self.factory.get(
            "/",
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}",
        )

        response = self.middleware(request)

        self.assertEqual(response.user, user)

    def test_sets_request_user_from_anonymous_token(self):
        anonymous_user = AnonymousUser.objects.create(session_key="anonymous-session")
        request = self.factory.get(
            "/",
            HTTP_X_ANONYMOUS_TOKEN=anonymous_user.session_key,
        )

        response = self.middleware(request)

        self.assertEqual(response.user, anonymous_user)


class HeaderTokenAuthenticationTests(APITestCase):
    def test_drf_request_user_can_be_anonymous_user(self):
        anonymous_user = AnonymousUser.objects.create(session_key="anonymous-session")

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
            HTTP_X_ANONYMOUS_TOKEN=anonymous_user.session_key,
        )
        response = UserEchoView.as_view()(request)

        self.assertEqual(response.data["user_id"], anonymous_user.id)
        self.assertTrue(response.data["is_anonymous"])
