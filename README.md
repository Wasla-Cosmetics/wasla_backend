# Wasla Backend

Django backend service for Wasla.

The project is configured for two main workflows:

- Docker Compose with PostgreSQL.
- Local development with SQLite.

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
│       ├── apps.py
│       └── management/
│           └── commands/
│               └── startapp.py
├── project/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── local.py
│   │   ├── development.py
│   │   ├── staging.py
│   │   └── production.py
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   ├── development.txt
│   ├── staging.txt
│   └── production.txt
├── Dockerfile
├── docker-compose.yaml
├── manage.py
└── .env.example
```

### Important Files

- `project/settings/__init__.py` selects the settings module using `ENV`.
- `project/settings/local.py` contains the shared base/local settings.
- `project/settings/production.py` imports local settings, disables `DEBUG`, and requires production-safe values.
- `apps/core/management/commands/startapp.py` overrides Django's `startapp` command to support nested app paths and auto-register apps.
- `docker-compose.yaml` runs Django and PostgreSQL together.
- `.env.example` documents the environment variables needed to run the project.

## Environment Setup

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
DEBUG=True

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

Docker Compose forces Django to use Postgres because the Compose stack includes a Postgres service. For local commands without Docker, use SQLite:

```env
DATABASE_TYPE=sqlite3
SQLITE_NAME=db.sqlite3
```

## Run With Docker

Build and start the stack:

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up -d --build
```

Check containers:

```bash
docker compose ps
```

Follow Django logs:

```bash
docker compose logs -f django
```

Stop containers:

```bash
docker compose down
```

Stop containers and remove volumes:

```bash
docker compose down -v
```

The Django container runs:

```bash
python manage.py collectstatic --no-input
python manage.py migrate
gunicorn project.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2 --timeout 0
```

Useful URLs:

- Healthcheck: `http://localhost:8000/health/`
- Admin: `http://localhost:8000/admin/`

Create a superuser inside Docker:

```bash
docker compose exec django python manage.py createsuperuser
```

Run checks inside Docker:

```bash
docker compose exec django python manage.py check
```

## Run Locally Without Docker

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements/local.txt
```

Use SQLite for local-only commands:

```env
DATABASE_TYPE=sqlite3
SQLITE_NAME=db.sqlite3
```

Apply migrations:

```bash
python manage.py migrate
```

Run the development server:

```bash
python manage.py runserver
```

Run system checks:

```bash
python manage.py check
```

Create a superuser:

```bash
python manage.py createsuperuser
```

## Creating Apps

This project includes a custom `startapp` command.

Create an app at the project root:

```bash
python manage.py startapp store
```

Create an app inside `apps/`:

```bash
python manage.py startapp apps/orders
```

Create an app using Django's two-argument style:

```bash
python manage.py startapp orders apps/orders
```

The command will:

- Create the app package.
- Fix the generated `AppConfig.name`.
- Add parent `__init__.py` files when needed.
- Register the app in `LOCAL_APPS`.
- Run Black if it is installed.
- Run `python manage.py check`.

## Migrations

Create migrations:

```bash
python manage.py makemigrations
```

Apply migrations:

```bash
python manage.py migrate
```

Check that model changes have migrations:

```bash
python manage.py makemigrations --check --dry-run
```

## Formatting

Format the project:

```bash
python -m black project apps
```

## Settings Environments

The selected settings file is controlled by `ENV`.

Supported values:

- `local`
- `dev` or `development`
- `stage` or `staging`
- `prod` or `production`

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

## Common Commands

```bash
# Django checks
python manage.py check

# Migrations
python manage.py makemigrations
python manage.py migrate

# Local server
python manage.py runserver

# Docker stack
docker compose up -d --build
docker compose logs -f django
docker compose down

# Docker shell
docker compose exec django bash
```

## Notes

- `.env` is ignored by Git. Commit `.env.example`, not `.env`.
- `.venv/`, `__pycache__/`, `staticfiles/`, `media/`, and SQLite database files are ignored.
- The default Docker workflow is Postgres.
- The recommended non-Docker local workflow is SQLite.
