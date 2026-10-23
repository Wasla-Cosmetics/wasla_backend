from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.authentication.managers import UserManager
from apps.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    username = None
    phone = models.CharField(_("phone"), max_length=255, unique=True)
    email = models.EmailField(_("email"), max_length=255, unique=True)
    full_name = models.CharField(_("full name"), max_length=255)
    is_active = models.BooleanField(_("active"), default=False)
    reward_points = models.PositiveIntegerField(_("reward points"), default=0)
    otp = models.CharField(_("otp"), max_length=128, null=True, blank=True)
    otp_purpose = models.CharField(
        _("otp purpose"),
        max_length=32,
        null=True,
        blank=True,
    )
    otp_expires_at = models.DateTimeField(_("otp expires at"), null=True, blank=True)
    token_version = models.PositiveIntegerField(_("token version"), default=0)
    objects = UserManager()
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["email", "full_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.phone


class GuestUser(TimeStampedModel):
    session_key = models.CharField(_("session key"), max_length=40, unique=True)

    @property
    def is_anonymous(self):
        return True

    @property
    def is_authenticated(self):
        return False

    class Meta:
        verbose_name = _("guest user")
        verbose_name_plural = _("guest users")

    def __str__(self):
        return self.session_key
