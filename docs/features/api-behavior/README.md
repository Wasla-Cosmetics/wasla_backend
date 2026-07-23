# API Behavior

Shared API behavior is configured in `project/settings/local.py` through
`REST_FRAMEWORK`.

## Pagination

List endpoints use `apps.core.pagination.OptionalPageNumberPagination`.

Default behavior is paginated:

```http
GET /api/store/products/
```

Response shape:

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/store/products/?page=2",
  "previous": null,
  "results": []
}
```

Request a specific page:

```http
GET /api/store/products/?page=2
```

Request a custom page size:

```http
GET /api/store/products/?page_size=20
```

The maximum accepted `page_size` is `100`.

Disable pagination for small lists:

```http
GET /api/store/products/?is_paginated=false
```

Accepted disabled values:

- `false`
- `0`
- `no`
- `off`

When pagination is disabled, the response is a direct list:

```json
[
  {
    "id": 1,
    "title": "Cleanser",
    "default_price": 150.0
  }
]
```

Do not combine `page` with `is_paginated=false`; disabling pagination ignores
page selection.

## Decimal Values

`REST_FRAMEWORK["COERCE_DECIMAL_TO_STRING"]` is set to `False`.

This keeps serializer `DecimalField` values as decimals instead of converting
them to strings inside DRF serializer output. For example, product
`default_price` is serialized as a numeric decimal value instead of `"150.00"`.
