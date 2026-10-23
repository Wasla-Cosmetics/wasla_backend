# Development Commands

Common commands for day-to-day development.

## Django Checks

```bash
python manage.py check
```

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

Regenerate the production dependency lock after changing `requirements/base.txt`:

```bash
pip-compile --no-header --strip-extras --generate-hashes --resolver=backtracking --output-file=requirements/base.lock requirements/base.txt
```

Audit the locked production dependencies:

```bash
pip-audit --require-hashes -r requirements/base.lock
```

## Formatting

Format the project:

```bash
python -m black project apps
```

Check formatting:

```bash
python -m black --check project apps
```

## Local Server

```bash
python manage.py runserver
```

## Docker Stack

```bash
docker compose up -d --build
docker compose logs -f django
docker compose down
```
