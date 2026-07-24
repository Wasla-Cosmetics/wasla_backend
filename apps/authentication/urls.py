from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    ChangePasswordView,
    ResetPasswordView,
    DeleteAccountView,
    UserViewSet,
    GuestUserCreateView,
    UserProfileView,
    SendOtpView,
    VerifyOtpView,
    LogoutView,
)

router = DefaultRouter()
router.register(
    "users",
    UserViewSet,
    basename="users",
)

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("send-otp/", SendOtpView.as_view(), name="send_otp"),
    path("verify-otp/", VerifyOtpView.as_view(), name="verify_otp"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("delete-account/", DeleteAccountView.as_view(), name="delete-account"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("guest-users/", GuestUserCreateView.as_view(), name="guest-users"),
]
