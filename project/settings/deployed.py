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
WEBHOOK_OTP_BACKEND = "apps.authentication.otp.WebhookOtpDeliveryBackend"

if AUTH_OTP_DELIVERY_BACKEND == UNCONFIGURED_OTP_BACKEND:
    raise ImproperlyConfigured(
        "AUTH_OTP_DELIVERY_BACKEND must be configured in deployed environments."
    )

if AUTH_OTP_DELIVERY_BACKEND == WEBHOOK_OTP_BACKEND:
    if not AUTH_OTP_WEBHOOK_URL or not AUTH_OTP_WEBHOOK_TOKEN:
        raise ImproperlyConfigured(
            "AUTH_OTP_WEBHOOK_URL and AUTH_OTP_WEBHOOK_TOKEN are required for "
            "WebhookOtpDeliveryBackend."
        )
    if urlparse(AUTH_OTP_WEBHOOK_URL).scheme != "https":
        raise ImproperlyConfigured("AUTH_OTP_WEBHOOK_URL must use HTTPS.")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
