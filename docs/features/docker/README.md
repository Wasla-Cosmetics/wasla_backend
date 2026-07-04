# Docker Workflow

The Docker Compose workflow runs Django with PostgreSQL.

## Start The Stack

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

## Container Startup

The Django container runs:

```bash
python manage.py compilemessages --ignore ".venv/*" --verbosity 0
python manage.py collectstatic --no-input
python manage.py migrate
gunicorn project.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2 --timeout 0
```

Docker Compose forces Django to use Postgres because the stack includes a Postgres service.

## Useful URLs

- Healthcheck: `http://localhost:8000/health/`
- Admin: `http://localhost:8000/admin/`

## Common Commands

Create a superuser inside Docker:

```bash
docker compose exec django python manage.py createsuperuser
```

Run checks inside Docker:

```bash
docker compose exec django python manage.py check
```

Open a shell inside the Django container:

```bash
docker compose exec django bash
```
