from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from project.settings.local import *

DEBUG = False

SECRET_KEY = env.get("SECRET_KEY", "")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured(
        "SECRET_KEY must be a strong value of at least 50 characters in deployed "
        "environments."
    )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set in deployed environments.")
if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS cannot contain '*' when deployed.")

if REST_FRAMEWORK["NUM_PROXIES"] < 1:
    raise ImproperlyConfigured(
        "TRUSTED_PROXY_COUNT must include every trusted reverse proxy in deployed "
        "environments."
    )

UNCONFIGURED_OTP_BACKEND = "apps.authentication.otp.UnconfiguredOtpDeliveryBackend"
EMAIL_OTP_BACKEND = "apps.authentication.otp.EmailOtpDeliveryBackend"
WEBHOOK_OTP_BACKEND = "apps.authentication.otp.WebhookOtpDeliveryBackend"
SUPPORTED_OTP_BACKENDS = {EMAIL_OTP_BACKEND, WEBHOOK_OTP_BACKEND}

if AUTH_OTP_DELIVERY_BACKEND == UNCONFIGURED_OTP_BACKEND:
    raise ImproperlyConfigured(
        "AUTH_OTP_DELIVERY_BACKEND must be configured in deployed environments."
    )

if AUTH_OTP_DELIVERY_BACKEND not in SUPPORTED_OTP_BACKENDS:
    raise ImproperlyConfigured(
        "AUTH_OTP_DELIVERY_BACKEND must select a supported OTP delivery backend."
    )

if AUTH_OTP_DELIVERY_BACKEND == WEBHOOK_OTP_BACKEND:
    if not AUTH_OTP_WEBHOOK_URL or not AUTH_OTP_WEBHOOK_TOKEN:
        raise ImproperlyConfigured(
            "AUTH_OTP_WEBHOOK_URL and AUTH_OTP_WEBHOOK_TOKEN are required for "
            "WebhookOtpDeliveryBackend."
        )
    if urlparse(AUTH_OTP_WEBHOOK_URL).scheme != "https":
        raise ImproperlyConfigured("AUTH_OTP_WEBHOOK_URL must use HTTPS.")

if AUTH_OTP_DELIVERY_BACKEND == EMAIL_OTP_BACKEND:
    if EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
        raise ImproperlyConfigured(
            "EmailOtpDeliveryBackend requires Django's SMTP email backend when "
            "deployed."
        )
    if not all([EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD]) or (
        not DEFAULT_FROM_EMAIL or DEFAULT_FROM_EMAIL == "no-reply@wasla.local"
    ):
        raise ImproperlyConfigured(
            "EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, and "
            "DEFAULT_FROM_EMAIL are required for deployed email OTP delivery."
        )
    if EMAIL_USE_TLS == EMAIL_USE_SSL:
        raise ImproperlyConfigured(
            "Deployed email OTP delivery must enable exactly one of EMAIL_USE_TLS "
            "or EMAIL_USE_SSL."
        )

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
