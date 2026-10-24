# API Behavior

Shared API behavior is configured in `project/settings/local.py` through
`REST_FRAMEWORK`.

## Response Envelope

DRF API responses use one shared top-level shape:

```json
{
  "status": 200,
  "message": "Success",
  "data": {},
  "errors": {},
  "pagination": null
}
```

Validation and API errors keep the same shape:

```json
{
  "status": 400,
  "message": "Validation error",
  "data": {},
  "errors": {
    "phone": "This field is required."
  },
  "pagination": null
}
```

## Pagination

List endpoints use `apps.core.pagination.StandardPageNumberPagination`.

Default behavior is paginated:

```http
GET /api/store/products/
```

Response shape:

```json
{
  "status": 200,
  "message": "Success",
  "data": [],
  "errors": {},
  "pagination": {
    "count": 25,
    "next": "http://localhost:8000/api/store/products/?page=2",
    "previous": null,
    "page": 1,
    "page_size": 10,
    "total_pages": 3
  }
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

The maximum accepted `page_size` is `100`. Public list endpoints are always
paginated; clients cannot disable pagination with a query parameter. The
global catalog search uses a stricter maximum page size of `50`.

## Decimal Values

`REST_FRAMEWORK["COERCE_DECIMAL_TO_STRING"]` is set to `False`.

This keeps serializer `DecimalField` values as decimals instead of converting
them to strings inside DRF serializer output. For example, product
`default_price` is serialized as a numeric decimal value instead of `"150.00"`.
