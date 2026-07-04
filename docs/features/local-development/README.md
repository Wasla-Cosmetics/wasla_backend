# Local Development

The local development workflow uses a Python virtual environment and SQLite.

## Setup

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

## Run Locally

Apply migrations:

```bash
python manage.py migrate
```

Run the development server:

```bash
python manage.py runserver
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Run system checks:

```bash
python manage.py check
```
