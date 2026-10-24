# Settings Environments

The selected settings file is controlled by `ENV`.

## Environment File

Create your local `.env` file:

```bash
cp .env.example .env
```

Main variables:

```env
SERVER_NAME=local_wasla_backend_server
DJANGO_IMAGE=wasla_backend:latest
DJANGO_PORT=8000
COMPOSE_PROFILES=mailpit
MAILPIT_SMTP_PORT=1025
MAILPIT_UI_PORT=8025
ENV=local
SECRET_KEY=change-me
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CSRF_TRUSTED_ORIGINS=
TRUSTED_PROXY_COUNT=1
DEBUG=True
AUTH_OTP_TTL_MINUTES=10
AUTH_OTP_DELIVERY_BACKEND=apps.authentication.otp.EmailOtpDeliveryBackend
AUTH_OTP_WEBHOOK_URL=
AUTH_OTP_WEBHOOK_TOKEN=
AUTH_OTP_WEBHOOK_TIMEOUT_SECONDS=10
AUTH_IP_THROTTLE_RATE=20/minute
AUTH_PHONE_THROTTLE_RATE=5/minute
PASSWORD_RESET_TIMEOUT=600
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailpit
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False
EMAIL_TIMEOUT_SECONDS=10
DEFAULT_FROM_EMAIL=no-reply@wasla.local

DATABASE_TYPE=postgres

POSTGRES_DB=wasla
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_HOST_PORT=4404

SQLITE_NAME=db.sqlite3
```

`DATABASE_TYPE` supports:

- `postgres`
- `sqlite3`

For local commands without Docker, use SQLite:

```env
DATABASE_TYPE=sqlite3
SQLITE_NAME=db.sqlite3
```

## Ngrok And CSRF

When using Django admin or browser form POST requests through ngrok, include the
ngrok host in `ALLOWED_HOSTS` without a scheme and in `CSRF_TRUSTED_ORIGINS`
with the `https://` scheme.

Example:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,vocal-duckling-steadily.ngrok-free.app
CSRF_TRUSTED_ORIGINS=https://vocal-duckling-steadily.ngrok-free.app
```

## Supported ENV Values

- `local`
- `dev` or `development`
- `stage` or `staging`
- `prod` or `production`

## Deployed Settings

Staging and production settings:

- Set `DEBUG = False`.
- Require a strong `SECRET_KEY` of at least 50 characters.
- Require `ALLOWED_HOSTS`.
- Require a configured OTP delivery backend.
- Enable secure cookie settings.
- Redirect HTTP to HTTPS by default.
- Support `CSRF_TRUSTED_ORIGINS`.
- Require an explicit trusted reverse-proxy count so client IP throttles ignore
  spoofed `X-Forwarded-For` prefixes.

The included webhook delivery backend sends `{ "phone": ..., "otp": ... }` to
an HTTPS provider endpoint using the configured bearer token. Staging defaults
HSTS to one day; production defaults it to one year.

To deliver OTPs through a real SMTP service instead, select
`apps.authentication.otp.EmailOtpDeliveryBackend` and configure the `EMAIL_*`
settings. Do not use Mailpit outside development.

Example:

```env
ENV=production
SECRET_KEY=replace-with-a-random-secret-of-at-least-fifty-characters
ALLOWED_HOSTS=api.example.com
CSRF_TRUSTED_ORIGINS=https://api.example.com
TRUSTED_PROXY_COUNT=2
AUTH_OTP_DELIVERY_BACKEND=apps.authentication.otp.WebhookOtpDeliveryBackend
AUTH_OTP_WEBHOOK_URL=https://sms-provider.example.com/otp
AUTH_OTP_WEBHOOK_TOKEN=replace-with-a-secret
```

## Deployment OTP Providers

The `dev` deployment always uses Mailpit and does not require webhook or SMTP
credentials. Staging and production default to the HTTPS webhook backend and
remain fail-closed until their provider configuration exists.

| GitHub configuration | Staging | Production | Storage |
| --- | --- | --- | --- |
| Webhook URL | `STAGE_OTP_WEBHOOK_URL` | `MASTER_OTP_WEBHOOK_URL` | Variable |
| Webhook bearer token | `STAGE_OTP_WEBHOOK_TOKEN` | `MASTER_OTP_WEBHOOK_TOKEN` | Secret |

To select real SMTP email delivery later, set the environment-specific
`*_OTP_DELIVERY_BACKEND` variable to
`apps.authentication.otp.EmailOtpDeliveryBackend` and configure:

| Setting suffix | Example | Storage |
| --- | --- | --- |
| `EMAIL_HOST` | `smtp.example.com` | Variable |
| `EMAIL_PORT` | `587` | Variable |
| `EMAIL_USE_TLS` | `True` | Variable |
| `EMAIL_USE_SSL` | `False` | Variable |
| `DEFAULT_FROM_EMAIL` | `no-reply@example.com` | Variable |
| `EMAIL_HOST_USER` | SMTP account username | Secret |
| `EMAIL_HOST_PASSWORD` | SMTP account password | Secret |

Prefix every name with `STAGE_` or `MASTER_`, matching the target GitHub
environment. SMTP username and password are required for deployed email
delivery; Mailpit remains unauthenticated and development-only.
