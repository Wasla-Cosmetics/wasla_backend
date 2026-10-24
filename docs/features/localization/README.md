# Localization

Localization is configured in `project/settings/local.py` and `project/urls.py`.

## Source And Generated Files

Translation source files (`.po`) are committed.

Compiled message files (`.mo`) are generated and ignored by Git and the Docker
build context.

## Supported Languages

Current project languages:

- English: `en`
- Arabic: `ar`

## API Language Selection

Use the standard `Accept-Language` header to select one language for localized
model fields:

```http
GET /api/store/products/
Accept-Language: ar
```

`ar` returns Arabic `title` and `description` values where those translated
fields exist; `en` returns their English values. Django-modeltranslation falls
back to English when an Arabic value is empty.

Brand, branch, category, product, and ad list endpoints and the global catalog
search also accept the special value `all`. The response keeps the existing
localized fields and adds every configured translation using the language
suffix:

```http
GET /api/store/products/
Accept-Language: all
```

```json
{
  "title": "Cleanser",
  "title_en": "Cleanser",
  "title_ar": "غسول",
  "description": "Gentle daily cleanser",
  "description_en": "Gentle daily cleanser",
  "description_ar": "غسول يومي لطيف"
}
```

This special value applies only to catalog collection responses. Detail and
write responses keep their existing shape.

The supported collection responses are ads, brands, branches, categories,
products, and global catalog search results. Authentication and review payloads
do not gain language-suffixed model fields.

Translated filters and admin searches always inspect every configured
language. `Accept-Language` controls the response language; it does not limit
which translated values can match. For example, both requests find the same
product:

```http
GET /api/store/products/?title=clean
Accept-Language: ar
```

```http
GET /api/store/products/?title=غسول
Accept-Language: en
```

The same rule applies to brand, branch, category, and product filters and to
global search:

```http
GET /api/search/?q=غسول
Accept-Language: en
```

Ad text is searched in every language by global search. Ads do not currently
expose standalone title filters.

## Workflow

After adding or changing translatable strings, update the Arabic catalog:

```bash
python manage.py makemessages -l ar
```

After editing translations, compile the runtime message files:

```bash
python manage.py compilemessages --ignore ".venv/*" --verbosity 0
```

Commit the updated `.po` source. Do not commit generated `.mo` files.

## Docker Behavior

Docker builds compile messages with:

```bash
django-admin compilemessages --ignore ".venv/*" --verbosity 0
```

Docker Compose uses the compiled catalogs from the image. The project does not
bind-mount source code over those files at runtime.

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
