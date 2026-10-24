# Store App

The `store` app contains catalog and storefront models.

Catalog ownership follows one chain:

```text
Brand → Branch → Category → Product
```

A product stores only its category. Its branch and brand are derived through
that category, so ownership cannot drift between duplicate foreign keys.

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

### Brand

Customer-facing catalog owner:

- translated `title`
- `image`
- `created_at`
- `updated_at`

Deleting a brand that still has branches is rejected with HTTP `409` by the
API.

### Branch

Catalog branch belonging to one brand:

- `brand`
- translated `title`
- `image`
- `created_at`
- `updated_at`

Deleting a branch that still has categories is rejected with HTTP `409`.

### Category

Tree-based product category using `django-mptt`:

- `title`
- `image`
- `branch`
- `parent`
- `created_at`
- `updated_at`

Categories are ordered inside the tree by `title`. A category and its parent
and child nodes must all belong to the same branch.

A category cannot be moved below itself or one of its descendants. Deleting a
category that still has child categories or products is rejected with HTTP
`409`, preventing accidental catalog cascades.

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
The default price cannot be negative. These price rules are enforced by both
API validation and database constraints. The API calculates
`discount_percentage`; clients do not submit or store it:

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
The database also enforces the supported rating range and one-review-per-user
rule, so direct writes cannot bypass the API validation.

## API Routes

Store routes are mounted under:

```http
/api/store/
```

Available viewsets:

| Resource | Collection route | Detail route | Write access |
| --- | --- | --- | --- |
| Ads | `/api/store/ads/` | `/api/store/ads/{id}/` | Admin |
| Brands | `/api/store/brands/` | `/api/store/brands/{id}/` | Admin |
| Branches | `/api/store/branches/` | `/api/store/branches/{id}/` | Admin |
| Categories | `/api/store/categories/` | `/api/store/categories/{id}/` | Admin |
| Products | `/api/store/products/` | `/api/store/products/{id}/` | Admin |
| Reviews | `/api/store/reviews/` | `/api/store/reviews/{id}/` | Authenticated owner or admin |

Collections support `GET` and `POST`; detail routes support `GET`, `PUT`,
`PATCH`, and `DELETE`. Reads are public. Catalog writes require an admin.
Branch writes use `brand_id`, category writes use `branch_id`, and product
writes use `category_id`. Uploaded images require `multipart/form-data`.

Reads nest the ownership chain, for example:

```json
{
  "id": 42,
  "title": "Cleanser",
  "category": {
    "id": 7,
    "title": "Face Care",
    "branch": {
      "id": 3,
      "title": "Cairo",
      "brand": {
        "id": 1,
        "title": "Wasla"
      }
    }
  }
}
```

Review reads are public, but creating a review requires a user.
Updating or deleting a review is limited to the review owner or admin users.
Concurrent attempts to create the same review return HTTP `409` rather than a
server error.

Create a review with `product_id`, `rating`, and `description`. Review lists can
be filtered by exact `product` ID. Filtering by reviewer identity is
intentionally unsupported because public output omits the reviewer identity.
A review's product cannot be changed after creation.

## Global Catalog Search

The public search endpoint searches the customer-facing catalog:

```http
GET /api/search/?q=rose
```

It searches every configured translation, independently of the response
language:

- Product `title` and `description`
- Category `title`
- Brand `title`
- Branch `title`
- Ad `title` and `subtitle`

User accounts, guest sessions, reviews, OTPs, tokens, and other internal
records are intentionally excluded. Each result has a `type` value of
`product`, `category`, `brand`, `branch`, or `ad`, followed by that model's
normal API fields.

The `q` parameter is required after whitespace is trimmed and must contain
between 2 and 100 characters. Restrict a request to one or more public result
types with a comma-separated allowlist:

```http
GET /api/search/?q=rose&types=product,brand,branch,ad
```

Unknown result types return HTTP `400`. Results are ranked by exact title,
title prefix, partial title, then description or subtitle match. Ties are
stable, with products before categories, brands, branches, and ads.

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

## Localized Responses

Send `Accept-Language: en` or `Accept-Language: ar` for one localized value.
On catalog collection routes and global search, `Accept-Language: all` keeps
the normal field and adds suffixed values such as `title_en` and `title_ar`.
Detail and write responses retain the single-language shape.

## Filtering

Brand, branch, category, and product lists support ownership and translated
title filters:

```http
GET /api/store/brands/?title=وصلة
GET /api/store/branches/?brand=1
GET /api/store/branches/?brand_title=wasla
GET /api/store/branches/?title=القاهرة
GET /api/store/categories/?branch=3
GET /api/store/categories/?brand=1
GET /api/store/categories/?branch_title=cairo
GET /api/store/categories/?brand_title=وصلة
GET /api/store/products/?title=cleanser
GET /api/store/products/?category=7
GET /api/store/products/?branch=3
GET /api/store/products/?brand=1
GET /api/store/products/?category_title=Beauty
GET /api/store/products/?branch_title=القاهرة
GET /api/store/products/?brand_title=wasla
GET /api/store/products/?is_newest=true
GET /api/store/products/?is_best_seller=true
```

Translated title filters inspect all configured languages independently of
`Accept-Language`, so English and Arabic filter values work with `en`, `ar`,
or `all` responses. The product `category_title` filter remains an exact
match; the other title filters are case-insensitive partial matches.

Filters can be combined with pagination query parameters:

```http
GET /api/store/products/?is_newest=true&page_size=20
```
