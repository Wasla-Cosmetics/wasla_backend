# App Generation

This project includes a custom `startapp` command.

Run it from the repository root. Targets must be relative Python package paths;
absolute paths and paths containing `..` are rejected.

## Create Apps

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

## Command Behavior

The custom command will:

- Create the app package.
- Fix the generated `AppConfig.name`.
- Add parent `__init__.py` files when needed.
- Register the app in `LOCAL_APPS`.
- Run Black if it is installed.
- Run `python manage.py check`.

The command refuses to overwrite an existing app. It registers the generated
`AppConfig` path in `LOCAL_APPS` inside `project/settings/local.py`, so review
both the new package and the settings edit before committing.
