from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import GuestUser, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("phone", "email", "full_name", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("phone", "email", "full_name")
    ordering = ("phone",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (_("Personal info"), {"fields": ("email", "full_name", "reward_points")}),
        (_("OTP"), {"fields": ("otp", "otp_expires_at")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone",
                    "email",
                    "full_name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


@admin.register(GuestUser)
class GuestUserAdmin(admin.ModelAdmin):
    list_display = ("id", "session_key", "created_at", "updated_at")
    search_fields = ("session_key",)
    readonly_fields = ("created_at", "updated_at")
