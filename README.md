# Wasla Backend

Django backend service for Wasla.

The project supports two main development workflows:

- Docker Compose with PostgreSQL.
- Local development with SQLite.

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

## Documentation

Feature and workflow documentation lives in focused README files:

- [Docker Workflow](docs/features/docker/README.md)
- [Local Development](docs/features/local-development/README.md)
- [Localization](docs/features/localization/README.md)
- [App Generation](docs/features/app-generation/README.md)
- [Settings Environments](docs/features/settings/README.md)
- [Development Commands](docs/features/development-commands/README.md)
- [API Behavior](docs/features/api-behavior/README.md)
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
│   └── core/
├── docs/
│   └── features/
├── locale/
│   └── ar/
├── project/
│   ├── settings/
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
├── requirements/
├── Dockerfile
├── docker-compose.yaml
├── manage.py
└── .env.example
```

## Important Files

- `project/settings/__init__.py` selects the settings module using `ENV`.
- `project/settings/local.py` contains the shared base/local settings.
- `project/settings/production.py` imports local settings, disables `DEBUG`, and requires production-safe values.
- `apps/core/management/commands/startapp.py` overrides Django's `startapp` command to support nested app paths and auto-register apps.
- `locale/` contains committed translation source files.
- `docker-compose.yaml` runs Django and PostgreSQL together.
- `.env.example` documents the environment variables needed to run the project.

## Notes

- `.env` is ignored by Git. Commit `.env.example`, not `.env`.
- `.po` translation files are committed; generated `.mo` files are ignored.
- `.venv/`, `__pycache__/`, `staticfiles/`, `media/`, and SQLite database files are ignored.
- The default Docker workflow is Postgres.
- The recommended non-Docker local workflow is SQLite.
