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
pip-compile --no-header --no-annotate --strip-extras --generate-hashes --resolver=backtracking --output-file=requirements/base.lock requirements/base.txt
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

## Seed Data

Create or refresh bilingual development data:

```bash
python manage.py seed_data
```

The command is idempotent and seeds users, a guest user, ads, hierarchical
categories, products, product images, and product reviews. It never deletes
existing records and refuses to run when `ENV` is staging or production.

The default demo accounts are:

```text
Admin:     +201000000001
Customer:  +201000000002
Customer:  +201000000003
Password:  WaslaDemo123!
```

Set another password for all seeded accounts with:

```bash
python manage.py seed_data --password "AnotherStrongPassword123!"
```

Operational cache rows and third-party token/session tables are intentionally
not seeded.

## Docker Stack

```bash
docker compose up -d --build
docker compose logs -f django
docker compose down
```
