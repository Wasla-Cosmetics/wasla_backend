from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.authentication.managers import UserManager


class AuthenticatedUser(AbstractUser):
    username = None
    phone = models.CharField(_("phone"), max_length=255, unique=True)
    email = models.EmailField(_("email"), max_length=255, unique=True)
    full_name = models.CharField(_("full name"), max_length=255)
    is_active = models.BooleanField(_("active"), default=False)
    points = models.PositiveIntegerField(_("points"), default=0)
    otp = models.CharField(_("otp"), max_length=6, null=True, blank=True)
    otp_expires_at = models.DateTimeField(_("otp expires at"), null=True, blank=True)
    objects = UserManager()
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["email", "full_name"]

    class Meta:
        verbose_name = _("authenticated user")
        verbose_name_plural = _("authenticated users")

    def __str__(self):
        return self.phone


class AnonymousUser(models.Model):
    session_key = models.CharField(_("session key"), max_length=40, unique=True)

    @property
    def is_anonymous(self):
        return True

    @property
    def is_authenticated(self):
        return False

    class Meta:
        verbose_name = _("anonymous user")
        verbose_name_plural = _("anonymous users")

    def __str__(self):
        return self.session_key
