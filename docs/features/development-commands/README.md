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

Never edit an applied migration to represent a new model change. Add a new
migration and verify both forward and reverse behavior when the data change is
non-trivial.

## Tests

Run the full Django suite:

```bash
python manage.py test
```

Run one app or test module while iterating:

```bash
python manage.py test apps.store
python manage.py test apps.store.test_search
```

The CI suite uses PostgreSQL. SQLite is convenient locally, but changes to
queries, constraints, migrations, or transaction handling should also be
verified against PostgreSQL through Docker or the pull-request pipeline.

Run the container integration checks directly:

```bash
tests/integration/test_volume_initialization.sh
tests/integration/test_nginx_healthcheck.sh
```

## Dependencies

Regenerate the production dependency lock after changing `requirements/base.txt`:

```bash
pip-compile --no-header --no-annotate --strip-extras --generate-hashes --resolver=backtracking --output-file=requirements/base.lock requirements/base.txt
```

Audit the locked production dependencies:

```bash
pip-audit --require-hashes -r requirements/base.lock
```

`requirements/base.txt` is the human-maintained production input.
`requirements/base.lock` is the generated, hashed deployment lock and must be
committed whenever the input changes.

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

The command is idempotent and seeds users, a guest user, ads, one brand, one
branch, hierarchical categories, products, product images, and product
reviews. It preserves the `Brand → Branch → Category → Product` ownership
chain, never deletes existing records, and refuses to run when `ENV` is
staging or production.

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

Run Django commands in the active stack with:

```bash
docker compose exec django python manage.py check
docker compose exec django python manage.py test
```

## Pull-Request Quality Gate

Before opening a pull request, run at least:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py compilemessages --ignore ".venv/*" --verbosity 0
python manage.py test
python -m black --check .
```

CI additionally verifies production settings, the dependency lock and audit,
PostgreSQL behavior, writable container volumes, and the Nginx healthcheck.
