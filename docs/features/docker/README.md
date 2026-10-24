# Docker Workflow

The Docker Compose workflow runs Django with PostgreSQL and uses Mailpit to
capture development OTP emails.

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

Before Django starts, the one-shot `volume-init` service:

- Repairs ownership and write permissions on the persistent media and static volumes.
- Copies `default.jpeg` into the media volume when it is missing.

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

Docker Compose forces Django to use Postgres because the stack includes a Postgres service.
The Nginx healthcheck calls Django through the internal proxy using an explicit
IPv4 loopback address and the forwarded HTTPS scheme used by deployed traffic.
Deployments wait for service health and fail instead of succeeding with an
unhealthy proxy.

## Useful URLs

- Healthcheck: `http://localhost:8000/health/`
- Admin: `http://localhost:8000/admin/`
- Mailpit inbox: `http://localhost:8025/`

Mailpit is enabled through `COMPOSE_PROFILES=mailpit` in `.env.example`. Its
SMTP and web ports bind only to `127.0.0.1`; messages do not leave the machine.
The captured mailbox is persisted in the `mailpit_data` Docker volume.

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

Open a shell inside the Django container:

```bash
docker compose exec django bash
```
