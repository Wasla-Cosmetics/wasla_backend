# Store App

The `store` app contains catalog and storefront models.

## Models

### Ad

Simple promotional ad model:

- `title`
- `subtitle`
- `image`
- `created_at`
- `updated_at`

The ad model intentionally stays simple. Hero/banner-specific fields are not
part of this model.

### Category

Tree-based product category using `django-mptt`:

- `title`
- `image`
- `parent`
- `created_at`
- `updated_at`

Categories are ordered inside the tree by `title`.

### Product

Catalog product model:

- `category`
- `title`
- `image` as the primary product image
- `description`
- `stock_quantity`
- `reward_points`
- `default_price` as the current selling price
- `compare_at_price` as an optional higher reference price
- `discount_percentage` calculated from the two prices
- `is_newest`
- `is_best_seller`
- `created_at`
- `updated_at`

Products are ordered by `title`.

When `compare_at_price` is provided, it must be greater than `default_price`.
The API calculates `discount_percentage`; clients do not submit or store it:

```json
{
  "default_price": 150.0,
  "compare_at_price": 200.0,
  "discount_percentage": 25
}
```

Without a compare-at price, `compare_at_price` is `null` and
`discount_percentage` is `0`.

Product API responses also contain a read-only `images` array with the
product's additional images:

```json
{
  "image": "http://localhost:8000/media/products/primary.jpg",
  "images": [
    {
      "id": 1,
      "image": "http://localhost:8000/media/products/front.jpg"
    },
    {
      "id": 2,
      "image": "http://localhost:8000/media/products/back.jpg"
    }
  ]
}
```

### ProductImage

Additional image belonging to one product:

- `product`
- `image`
- `created_at`
- `updated_at`

Deleting a product deletes its additional images. Additional images are
ordered by ID and can be managed inline on the product page in Django admin.
There is no separate public product-image endpoint.

### ProductReview

Customer review for a product:

- `product`
- `user`
- `rating` from 1 to 5
- `description`
- `created_at`
- `updated_at`

Each user can review a product once.
Public review responses intentionally omit reviewer IDs and names.

## API Routes

Store routes are mounted under:

```http
/api/store/
```

Available viewsets:

```http
GET /api/store/ads/
GET /api/store/categories/
GET /api/store/products/
GET /api/store/reviews/
POST /api/store/reviews/
```

Write operations require admin permissions. Read operations are public.
Review reads are public, but creating a review requires a user.
Updating or deleting a review is limited to the review owner or admin users.
Concurrent attempts to create the same review return HTTP `409` rather than a
server error.

## Global Catalog Search

The public search endpoint searches the customer-facing catalog:

```http
GET /api/search/?q=rose
```

It searches every configured translation, independently of the response
language:

- Product `title` and `description`
- Category `title`
- Ad `title` and `subtitle`

User accounts, guest sessions, reviews, OTPs, tokens, and other internal
records are intentionally excluded. Each result has a `type` value of
`product`, `category`, or `ad`, followed by that model's normal API fields.

The `q` parameter is required after whitespace is trimmed and must contain
between 2 and 100 characters. Restrict a request to one or more public result
types with a comma-separated allowlist:

```http
GET /api/search/?q=rose&types=product,ad
```

Unknown result types return HTTP `400`. Results are ranked by exact title,
title prefix, partial title, then description or subtitle match. Ties are
stable, with products before categories before ads.

Search uses the standard response envelope and page-number pagination. Its
`page_size` is capped at `50`, even when a larger value is requested.

`Accept-Language` controls only the serialized output. For example, an Arabic
query can return an English response:

```http
GET /api/search/?q=ورد
Accept-Language: en
```

Use `Accept-Language: all` to include every translation field in each result.
The endpoint is IP-throttled using `CATALOG_SEARCH_THROTTLE_RATE`, which
defaults to `30/minute`.

## Filtering

Products support filters:

```http
GET /api/store/products/?title=cleanser
GET /api/store/products/?category_title=Beauty
GET /api/store/products/?is_newest=true
GET /api/store/products/?is_best_seller=true
```

`title` is a case-insensitive partial match. `category_title` is an exact
match. Both translated filters inspect all configured languages independently
of `Accept-Language`, so English and Arabic filter values work with `en`, `ar`,
or `all` responses.

Filters can be combined with pagination query parameters:

```http
GET /api/store/products/?is_newest=true&page_size=20
```
