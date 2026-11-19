from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm

from apps.authentication.forms import (
    WaslaUserChangeForm,
    WaslaUserCreationForm,
)
from apps.authentication.models import GuestUser, User


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    model = User

    form = WaslaUserChangeForm
    add_form = WaslaUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "phone",
        "email",
        "full_name",
        "reward_points",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
        "created_at",
    )
    search_fields = ("phone", "email", "full_name")
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "date_joined",
        "otp",
        "otp_purpose",
        "otp_expires_at",
        "token_version",
    )
    list_per_page = 25
    list_filter_submit = True

    fieldsets = (
        (
            _("Account"),
            {
                "fields": (
                    "phone",
                    "password",
                    "is_active",
                )
            },
        ),
        (
            _("Personal information"),
            {
                "fields": (
                    "email",
                    "full_name",
                    "reward_points",
                )
            },
        ),
        (
            _("Security information"),
            {
                "classes": ("collapse",),
                "fields": (
                    "otp",
                    "otp_purpose",
                    "otp_expires_at",
                    "token_version",
                ),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            _("Create user"),
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
class GuestUserAdmin(ModelAdmin):
    list_display = (
        "id",
        "session_key",
        "expires_at",
        "created_at",
        "updated_at",
    )
    search_fields = ("session_key",)
    readonly_fields = (
        "session_key",
        "created_at",
        "updated_at",
        "expires_at",
    )
    ordering = ("-created_at",)
    list_per_page = 25


try:
    admin.site.unregister(Group)
except NotRegistered:
    pass


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    list_per_page = 25