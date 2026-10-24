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
EMAIL_HOST=127.0.0.1
```

Start only Mailpit when Django runs from the virtual environment:

```bash
docker compose --profile mailpit up -d mailpit
```

Development OTP emails appear at `http://localhost:8025/`.

## Run Locally

Apply migrations:

```bash
python manage.py migrate
```

Create or refresh development seed data:

```bash
python manage.py seed_data
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
