from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User
from apps.store.models import Brand, Category, Product, ProductReview


LOW_STOCK_THRESHOLD = 5


def dashboard_callback(request, context):
    product_metrics = Product.objects.aggregate(
        total_products=Count("id"),
        total_units=Sum("stock_quantity"),
        low_stock_products=Count(
            "id",
            filter=Q(
                stock_quantity__gt=0,
                stock_quantity__lte=LOW_STOCK_THRESHOLD,
            ),
        ),
        out_of_stock_products=Count(
            "id",
            filter=Q(stock_quantity=0),
        ),
        best_sellers=Count(
            "id",
            filter=Q(is_best_seller=True),
        ),
    )

    customer_metrics = User.objects.aggregate(
        total_customers=Count(
            "id",
            filter=Q(is_staff=False),
        ),
        active_customers=Count(
            "id",
            filter=Q(is_staff=False, is_active=True),
        ),
    )

    products_missing_arabic = Product.objects.filter(
        Q(title_ar__isnull=True)
        | Q(title_ar="")
        | Q(description_ar__isnull=True)
        | Q(description_ar="")
    ).count()

    total_reviews = ProductReview.objects.count()

    seller_stats = [
        {
            "title": _("Products"),
            "value": product_metrics["total_products"] or 0,
            "description": _("Products in the catalog"),
            "icon": "inventory_2",
            "tone": "teal",
            "url": reverse("admin:store_product_changelist"),
        },
        {
            "title": _("Inventory Units"),
            "value": product_metrics["total_units"] or 0,
            "description": _("Available product units"),
            "icon": "warehouse",
            "tone": "navy",
            "url": reverse("admin:store_product_changelist"),
        },
        {
            "title": _("Low Stock"),
            "value": product_metrics["low_stock_products"] or 0,
            "description": _("Products with 1–5 units"),
            "icon": "warning",
            "tone": "warning",
            "url": (
                reverse("admin:store_product_changelist")
                + f"?stock_quantity__lte={LOW_STOCK_THRESHOLD}"
            ),
        },
        {
            "title": _("Customers"),
            "value": customer_metrics["total_customers"] or 0,
            "description": _("Registered customer accounts"),
            "icon": "group",
            "tone": "blue",
            "url": reverse("admin:authentication_user_changelist"),
        },
    ]

    low_stock_products = (
        Product.objects.select_related(
            "category",
            "category__branch",
            "category__branch__brand",
        )
        .filter(stock_quantity__lte=LOW_STOCK_THRESHOLD)
        .order_by("stock_quantity", "title")[:8]
    )

    recent_products = Product.objects.select_related("category").order_by(
        "-created_at"
    )[:6]

    recent_reviews = (
        ProductReview.objects.select_related("product", "user")
        .order_by("-created_at")[:6]
    )

    context.update(
        {
            "title": _("Seller Dashboard"),
            "seller_stats": seller_stats,
            "catalog_health": {
                "brands": Brand.objects.count(),
                "categories": Category.objects.count(),
                "out_of_stock": product_metrics["out_of_stock_products"] or 0,
                "best_sellers": product_metrics["best_sellers"] or 0,
                "missing_arabic": products_missing_arabic,
                "reviews": total_reviews,
                "active_customers": customer_metrics["active_customers"] or 0,
            },
            "low_stock_products": low_stock_products,
            "recent_products": recent_products,
            "recent_reviews": recent_reviews,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        }
    )

    return context