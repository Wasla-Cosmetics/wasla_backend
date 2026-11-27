from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import UserManager as DjangoUserManager
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from apps.authentication.models import User


class UserManager(DjangoUserManager["User"]):
    def create_user(  # type: ignore[override]
        self,
        phone: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> User:
        if not phone:
            raise ValueError(_("The phone number must be set"))

        email = extra_fields.get("email")
        if email:
            extra_fields["email"] = self.normalize_email(email)

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(  # type: ignore[override]
        self,
        phone: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> User:
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(phone, password, **extra_fields)
