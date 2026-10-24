# Docker Workflow

The Docker Compose workflow runs Django with PostgreSQL and uses Mailpit to
capture development OTP emails. Nginx is the host-facing service; Django is
available only on the internal Compose network.

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

`down -v` permanently removes the Compose database, Mailpit inbox, uploaded
media, and collected static volumes. Use it only when that local data can be
discarded.

## Container Startup

Before Django starts, the one-shot `volume-init` service:

- Repairs ownership and write permissions on the persistent media and static volumes.
- Copies `default.jpeg` into the media volume when it is missing.

Because the initializer runs as root, it permits only the image's fixed media,
static, default-image, and `django:django` ownership values before any recursive
ownership or permission change.

The service exits after initialization. Django continues to run as the unprivileged
`django` user. Translation catalogs are compiled while the image is built. At
container startup Django runs:

```bash
python manage.py collectstatic --no-input
python manage.py migrate
gunicorn project.asgi:application -k uvicorn_worker.UvicornWorker --bind 0.0.0.0:8000 --workers 2 --timeout 0
```

The migration step also ensures `default.jpeg` exists in the configured media
storage without replacing an existing customized file.

Docker Compose forces Django to use Postgres because the stack includes a
Postgres service.
The Nginx healthcheck calls Django through the internal proxy using an explicit
IPv4 loopback address and the forwarded HTTPS scheme used by deployed traffic.
Deployments wait for service health and fail instead of succeeding with an
unhealthy proxy.

## Useful URLs

- Readiness check: `http://localhost:8000/health/`
- Admin: `http://localhost:8000/admin/`
- Mailpit inbox: `http://localhost:8025/`

Mailpit is enabled through `COMPOSE_PROFILES=mailpit` in `.env.example`. Its
SMTP and web ports bind only to `127.0.0.1`; messages do not leave the machine.
The captured mailbox is persisted in the `mailpit_data` Docker volume.

Nginx and PostgreSQL are also loopback-only on the host. Change `DJANGO_PORT`,
`POSTGRES_HOST_PORT`, `MAILPIT_SMTP_PORT`, or `MAILPIT_UI_PORT` in `.env` when
running multiple environments on one server.

On the remote development server, access the loopback-only inbox with an SSH
tunnel rather than exposing Mailpit publicly:

```bash
ssh -L 8025:127.0.0.1:8025 deploy@development-server
```

Then open `http://localhost:8025/` locally.

## Common Commands

Create a superuser inside Docker:

```bash
docker compose exec django python manage.py createsuperuser
```

Create or refresh development seed data:

```bash
docker compose exec django python manage.py seed_data
```

Run checks inside Docker:

```bash
docker compose exec django python manage.py check
```

Run the Django test suite against the stack's PostgreSQL database:

```bash
docker compose exec django python manage.py test
```

Open a shell inside the Django container:

```bash
docker compose exec django bash
```

## Service Health

`docker compose up --wait` waits for PostgreSQL, Django, and Nginx health.
The `/health/` endpoint performs a database query and returns HTTP `503` when
the database is unavailable, so Django and Nginx do not report healthy while
the API cannot serve database-backed requests.
Inspect failures with:

```bash
docker compose ps
docker compose logs django nginx postgres volume-init
```

An exited `volume-init` container with status `0` is expected: it is a one-shot
initializer, not a long-running service.
