# Localization

Localization is configured in `project/settings/local.py` and `project/urls.py`.

## Source And Generated Files

Translation source files (`.po`) are committed.

Compiled message files (`.mo`) are generated and ignored by Git and Docker build context.

## Supported Languages

Current project languages:

- English: `en`
- Arabic: `ar`

## Workflow

After adding or changing translatable strings, update the Arabic catalog:

```bash
python manage.py makemessages -l ar
```

After editing translations, compile the runtime message files:

```bash
python manage.py compilemessages --ignore ".venv/*" --verbosity 0
```

## Docker Behavior

Docker builds compile messages with:

```bash
django-admin compilemessages --ignore ".venv/*" --verbosity 0
```

Docker Compose compiles messages on startup with:

```bash
python manage.py compilemessages --ignore ".venv/*" --verbosity 0
```

The Compose startup command is needed because the local bind mount can hide `.mo` files generated during image build.

## Adding Translatable Strings

Use lazy translations for import-time values such as settings, admin labels, and model metadata:

```python
from django.utils.translation import gettext_lazy as _

admin.site.site_header = _("Wasla Admin")
```

Use regular translations for request-time values when needed:

```python
from django.utils.translation import gettext as _
```
