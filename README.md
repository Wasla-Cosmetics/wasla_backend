# Wasla Backend

Django REST API for Wasla's bilingual storefront. It provides phone/JWT
authentication, development OTP delivery through Mailpit, a localized catalog,
catalog-wide search, product reviews, and admin-managed catalog CRUD.

Catalog ownership follows `Brand → Branch → Category → Product`. English and
Arabic are supported, while translated filters and search inspect both
languages regardless of the response language.

## Quick Start

Create your local environment file:

```bash
cp .env.example .env
```

Start the Docker stack:

```bash
docker compose up --build
```

Useful URLs:

- Healthcheck: `http://localhost:8000/health/`
- Admin: `http://localhost:8000/admin/`
- Mailpit: `http://localhost:8025/`

Create repeatable development data:

```bash
docker compose exec django python manage.py seed_data
```

The alternative non-Docker workflow uses Python 3.12 and SQLite; see
[Local Development](docs/features/local-development/README.md).

## Architecture

```text
Client
  └── Nginx
      └── Gunicorn + Uvicorn worker (ASGI)
          ├── authentication app ── JWT, OTP, users, guest sessions
          ├── store app ─────────── catalog, reviews, global search
          └── core app ──────────── timestamps, responses, pagination, commands
              ├── PostgreSQL (Docker/deployed environments)
              ├── SQLite (optional local workflow)
              └── Mailpit (development OTP email only)
```

The application exposes:

- `/api/auth/` for authentication and account management.
- `/api/store/` for catalog and review resources.
- `/api/search/` for global public catalog search.
- `/admin/` for Django administration.
- `/health/` for container and deployment health checks.

All API responses use the shared response envelope documented in
[API Behavior](docs/features/api-behavior/README.md).

## Common Commands

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python -m black --check .
```

Run the same checks inside an active Docker stack by prefixing Django commands
with `docker compose exec django`, for example:

```bash
docker compose exec django python manage.py test
```

## Documentation

Feature and workflow documentation lives in focused README files:

- [Docker Workflow](docs/features/docker/README.md)
- [Local Development](docs/features/local-development/README.md)
- [Localization](docs/features/localization/README.md)
- [App Generation](docs/features/app-generation/README.md)
- [Settings Environments](docs/features/settings/README.md)
- [Development Commands](docs/features/development-commands/README.md)
- [API Behavior](docs/features/api-behavior/README.md)
- [Authentication](docs/features/authentication/README.md)
- [Store App](docs/features/store/README.md)

## Tech Stack

- Python 3.12
- Django 6
- PostgreSQL 17 for Docker development
- SQLite for simple local development
- Gunicorn with Uvicorn worker for ASGI serving
- python-dotenv for environment configuration
- Black for formatting

## Project Structure

```text
.
├── apps/
│   ├── authentication/
│   ├── core/
│   └── store/
├── docs/
│   └── features/
├── docker/
├── nginx/
├── tests/
│   └── integration/
├── locale/
│   └── ar/
├── project/
│   ├── settings/
│   ├── asgi.py
│   ├── urls.py
│   └── exception_handler.py
├── requirements/
├── Dockerfile
├── docker-compose.yaml
├── manage.py
└── .env.example
```

## Important Files

- `project/settings/__init__.py` selects the settings module using `ENV`.
- `project/settings/local.py` contains the shared base/local settings.
- `project/settings/deployed.py` provides the shared fail-fast staging and production security baseline.
- `project/settings/production.py` enables the production HSTS duration.
- `project/asgi.py` is the sole application server entry point.
- `apps/core/management/commands/startapp.py` overrides Django's `startapp` command to support nested app paths and auto-register apps.
- `apps/core/management/commands/seed_data.py` creates idempotent bilingual development data.
- `locale/` contains committed translation source files.
- `docker-compose.yaml` runs Nginx, Django, PostgreSQL, volume initialization,
  and the optional Mailpit profile.
- `.env.example` documents the environment variables needed to run the project.
- `requirements/base.lock` pins and hashes the complete production dependency tree.

## Verification And Deployment

Pull requests verify Django checks, pending migrations, translations, the full
PostgreSQL test suite, the production settings baseline, the dependency lock
and audit, Black formatting, container volume initialization, and Nginx health.

Pushes to `dev`, `stage`, and `master` run the deployment workflow after the
same quality gate. Development uses Mailpit. Staging and production require a
configured HTTPS OTP webhook or real SMTP service; see
[Settings Environments](docs/features/settings/README.md).

## Notes

- `.env` is ignored by Git. Commit `.env.example`, not `.env`.
- `.po` translation files are committed; generated `.mo` files are ignored.
- `.venv/`, `__pycache__/`, `staticfiles/`, `media/`, and SQLite database files are ignored.
- The default Docker workflow is Postgres.
- The recommended non-Docker local workflow is SQLite.
