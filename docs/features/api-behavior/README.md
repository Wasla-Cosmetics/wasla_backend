# API Behavior

Shared API behavior is configured in `project/settings/local.py` through
`REST_FRAMEWORK`.

All paths below are relative to the same host. API clients should send JSON for
ordinary request bodies and `multipart/form-data` when uploading images.

## Authentication And Language Headers

Authenticated endpoints expect a JWT access token:

```http
Authorization: Bearer <access-token>
```

Guest sessions use `X-Guest-Token` instead. A guest session identifies a
client but does not grant permissions reserved for authenticated users.

Use `Accept-Language: en` or `Accept-Language: ar` to select translated output.
Catalog lists and global search additionally support `Accept-Language: all`;
see [Localization](../localization/README.md).

## Response Envelope

DRF API responses that contain a body use one shared top-level shape:

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

The `status` field mirrors the HTTP status code. `data` contains successful
content, while `errors` contains validation or API error details. Successful
resource deletion uses HTTP `204 No Content` and therefore has no response
body.

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

The maximum accepted `page_size` is `100`. List endpoints are always paginated;
clients cannot disable pagination with a query parameter. The global catalog
search uses a stricter maximum page size of `50`.

## Decimal Values

`REST_FRAMEWORK["COERCE_DECIMAL_TO_STRING"]` is set to `False`.

This keeps serializer `DecimalField` values as decimals instead of converting
them to strings inside DRF serializer output. For example, product
`default_price` is serialized as a numeric decimal value instead of `"150.00"`.
