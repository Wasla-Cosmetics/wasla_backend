from django.core.exceptions import ImproperlyConfigured

from project.settings.local import *

DEBUG = env_bool("DEBUG", False)

SECRET_KEY = env.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY must be set when ENV=production/prod.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
vercel_host = env.get("VERCEL_URL")
if vercel_host and vercel_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(vercel_host)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set when ENV=production/prod.")

if vercel_host:
    vercel_origin = f"https://{vercel_host}"
    if vercel_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(vercel_origin)

if DATABASES["default"].get("ENGINE") == "django.db.backends.sqlite3":
    raise ImproperlyConfigured(
        "SQLite is not suitable for production on Vercel. Set DATABASE_URL "
        "to a persistent PostgreSQL database, or use DATABASE_TYPE=postgres "
        "with POSTGRES_* variables."
    )

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = int(env.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_REFERRER_POLICY = "same-origin"
USE_X_FORWARDED_HOST = True
X_FRAME_OPTIONS = "DENY"
