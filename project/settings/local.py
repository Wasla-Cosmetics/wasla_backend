import os
from pathlib import Path
from os import environ as env
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name, default=False):
    value = env.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    value = env.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.get("SECRET_KEY", "django-insecure-local-development-key-change-me")

# Allowed hosts
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DEBUG", True)

# Security settings for deployments behind a trusted reverse proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", False)
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SECURE_CONTENT_TYPE_NOSNIFF = True

# Application definition
BUILT_IN_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MODELTRANSLATION_APPS = [
    "modeltranslation",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "mptt",
]

LOCAL_APPS = [
    "apps.core.apps.CoreConfig",
    "apps.authentication.apps.AuthenticationConfig",
    "apps.store.apps.StoreConfig",
]

INSTALLED_APPS = MODELTRANSLATION_APPS + BUILT_IN_APPS + THIRD_PARTY_APPS + LOCAL_APPS

BUILT_IN_MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

LOCAL_MIDDLEWARE = [
    "project.middlewares.UnifiedAPIResponseMiddleware",
]

MIDDLEWARE = BUILT_IN_MIDDLEWARE + LOCAL_MIDDLEWARE

# URL Configuration
ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ASGI
ASGI_APPLICATION = "project.asgi.application"

# Database
DATABASE_TYPE = env["DATABASE_TYPE"]

if DATABASE_TYPE == "sqlite3":
    sqlite_name = Path(env["SQLITE_NAME"])
    if not sqlite_name.is_absolute():
        sqlite_name = BASE_DIR / sqlite_name

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_name,
        },
    }
elif DATABASE_TYPE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env["POSTGRES_DB"],
            "USER": env["POSTGRES_USER"],
            "PASSWORD": env["POSTGRES_PASSWORD"],
            "HOST": env["POSTGRES_HOST"],
            "PORT": env["POSTGRES_PORT"],
        },
    }
else:
    raise ImproperlyConfigured("DATABASE_TYPE must be either 'postgres' or 'sqlite3'.")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"

LANGUAGES = [
    ("en", _("English")),
    ("ar", _("Arabic")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("en", "ar")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en",)

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "api_throttle_cache",
        "OPTIONS": {
            "MAX_ENTRIES": 10_000,
            "CULL_FREQUENCY": 3,
        },
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

EMAIL_BACKEND = env.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env.get("EMAIL_PORT", "25"))
EMAIL_HOST_USER = env.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = int(env.get("EMAIL_TIMEOUT_SECONDS", "10"))
DEFAULT_FROM_EMAIL = env.get("DEFAULT_FROM_EMAIL", "no-reply@wasla.local")

AUTH_USER_MODEL = "authentication.User"
AUTH_OTP_TTL_MINUTES = int(env.get("AUTH_OTP_TTL_MINUTES", "10"))
AUTH_OTP_DELIVERY_BACKEND = env.get(
    "AUTH_OTP_DELIVERY_BACKEND",
    "apps.authentication.otp.UnconfiguredOtpDeliveryBackend",
)
AUTH_OTP_WEBHOOK_URL = env.get("AUTH_OTP_WEBHOOK_URL", "")
AUTH_OTP_WEBHOOK_TOKEN = env.get("AUTH_OTP_WEBHOOK_TOKEN", "")
AUTH_OTP_WEBHOOK_TIMEOUT_SECONDS = int(
    env.get("AUTH_OTP_WEBHOOK_TIMEOUT_SECONDS", "10")
)
PASSWORD_RESET_TIMEOUT = int(env.get("PASSWORD_RESET_TIMEOUT", "600"))
GUEST_USER_TTL_DAYS = int(env.get("GUEST_USER_TTL_DAYS", "30"))
TRUSTED_PROXY_COUNT = int(env.get("TRUSTED_PROXY_COUNT", "0"))

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.authentication.authentication.HeaderTokenAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPageNumberPagination",
    "EXCEPTION_HANDLER": "project.exception_handler.custom_exception_handler",
    "COERCE_DECIMAL_TO_STRING": False,
    "NUM_PROXIES": TRUSTED_PROXY_COUNT,
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_RATES": {
        "auth_ip": env.get("AUTH_IP_THROTTLE_RATE", "20/minute"),
        "auth_phone": env.get("AUTH_PHONE_THROTTLE_RATE", "5/minute"),
        "guest_user": env.get("GUEST_USER_THROTTLE_RATE", "10/hour"),
        "catalog_search": env.get("CATALOG_SEARCH_THROTTLE_RATE", "30/minute"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
