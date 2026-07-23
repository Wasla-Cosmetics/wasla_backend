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
ENV=local
SECRET_KEY=change-me
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CSRF_TRUSTED_ORIGINS=
DEBUG=True
AUTH_OTP_TTL_MINUTES=10

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

## Production Settings

Production settings:

- Set `DEBUG = False`.
- Require `SECRET_KEY`.
- Require `ALLOWED_HOSTS`.
- Enable secure cookie settings.
- Support `CSRF_TRUSTED_ORIGINS`.

Example:

```env
ENV=production
SECRET_KEY=your-production-secret
ALLOWED_HOSTS=api.example.com
CSRF_TRUSTED_ORIGINS=https://api.example.com
```
