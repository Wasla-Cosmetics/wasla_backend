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
- `image`
- `description`
- `stock_quantity`
- `reward_points`
- `default_price`
- `is_newest`
- `is_best_seller`
- `created_at`
- `updated_at`

Products are ordered by `title`.

### ProductReview

Customer review for a product:

- `product`
- `user`
- `rating` from 1 to 5
- `description`
- `created_at`
- `updated_at`

Each user can review a product once.

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

## Filtering

Products support filters:

```http
GET /api/store/products/?title=cleanser
GET /api/store/products/?category_title=Beauty
GET /api/store/products/?is_newest=true
GET /api/store/products/?is_best_seller=true
```

Filters can be combined with pagination query parameters:

```http
GET /api/store/products/?is_newest=true&page_size=20
```
