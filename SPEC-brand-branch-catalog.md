# Spec: Brand And Branch Catalog Ownership

## Objective

Extend the Wasla catalog with a strict ownership chain:

```text
Brand → Branch → Category → Product
```

A brand owns branches, each branch owns an independent category tree, and a
product inherits its branch and brand from its category. The API must expose
the hierarchy without storing redundant branch or brand foreign keys on
products.

## Tech Stack

- Python 3.12
- Django 6 and Django REST Framework 3.18
- django-modeltranslation for English and Arabic fields
- django-mptt for branch-scoped category trees
- PostgreSQL in deployed environments and SQLite for local checks

## Commands

```bash
ENV=local DATABASE_TYPE=sqlite3 SQLITE_NAME=/tmp/wasla.sqlite3 .venv/bin/python manage.py test
ENV=local DATABASE_TYPE=sqlite3 SQLITE_NAME=/tmp/wasla.sqlite3 .venv/bin/python manage.py check
ENV=local DATABASE_TYPE=sqlite3 SQLITE_NAME=/tmp/wasla.sqlite3 .venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/black --check .
docker compose run --rm --build django python manage.py test --verbosity 1
```

## Project Structure

- `apps/store/models.py`: catalog ownership models and relationships
- `apps/store/serializers.py`: nested read and foreign-key write contracts
- `apps/store/views.py`, `filters.py`, `urls.py`: CRUD and filters
- `apps/store/search.py`: multilingual global search integration
- `apps/store/admin.py`, `translation.py`: admin and translations
- `apps/store/migrations/`: schema and existing-data migration
- `apps/core/management/commands/seed_data.py`: development hierarchy
- `apps/store/tests.py`, `apps/store/test_search.py`: API regression tests
- `docs/features/store/README.md`: public API documentation

## Code Style

Follow the existing explicit Django model and serializer style:

```python
class Branch(TimeStampedModel):
    brand = models.ForeignKey(
        Brand,
        related_name="branches",
        on_delete=models.PROTECT,
    )
    title = models.CharField(_("title"), max_length=255)
```

Use Black formatting, descriptive relationship names, and no redundant
`Product.branch` or `Product.brand` fields.

## Testing Strategy

- Write failing API tests before each behavior slice.
- Cover CRUD permissions, translation output, nested ownership, filtering,
  invalid cross-branch category parents, protected deletion, search, and seed
  data.
- Run focused store tests after each slice.
- Run the complete SQLite and PostgreSQL/Docker suites before completion.

## Boundaries

- Always: preserve the response envelope, pagination, admin-only catalog
  writes, and multilingual matching behavior.
- Always: migrate existing categories to a generated `Wasla → Main Branch`
  hierarchy before making `Category.branch` required.
- Always: return HTTP `409` when a populated brand or branch is deleted.
- Ask first: adding address, contact, geolocation, opening-hours, or
  branch-specific pricing/inventory fields.
- Never: duplicate branch or brand foreign keys on Product.
- Never: silently allow a category parent from another branch.
- Never: cascade deletion from a brand or branch into the catalog.

## API Contract

- `GET|POST /api/store/brands/`
- `GET|PUT|PATCH|DELETE /api/store/brands/{id}/`
- `GET|POST /api/store/branches/`
- `GET|PUT|PATCH|DELETE /api/store/branches/{id}/`
- Brand and branch reads are public; writes require an admin.
- Brand and branch fields are `id`, localized `title`, `image`, and their
  relationship fields.
- Branch writes accept `brand_id`; branch reads include nested `brand`.
- Category writes require `branch_id`; reads include nested `branch`.
- Product reads inherit the full hierarchy through their nested category.
- Brand, branch, category, and product lists support ownership filters.
- Global search supports `brand` and `branch` types and searches their title
  translations.
- `Accept-Language: ar` returns Arabic fields; `all` includes every configured
  translation on collection responses.

## Success Criteria

- Brand, branch, category, and product relationships form the approved chain.
- Existing category and product records survive migration under the default
  hierarchy.
- Cross-branch category parent assignments are rejected.
- Populated brands and branches cannot be deleted and return HTTP `409`.
- New CRUD endpoints use the existing permission, envelope, and pagination
  conventions.
- Filters work by IDs and translated titles across every language.
- Global search finds and serializes brands and branches in `en`, `ar`, and
  `all` modes.
- Seed data creates valid multilingual brands, branches, categories, and
  products.
- All formatting, checks, migrations, and SQLite/PostgreSQL tests pass.

## Open Questions

None. Address, contact, geolocation, opening hours, and branch-specific
inventory are explicitly outside this feature.
