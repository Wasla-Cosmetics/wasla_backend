from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey


class Ad(models.Model):
    title = models.CharField(_("title"), max_length=200)
    subtitle = models.TextField(_("subtitle"), blank=True)
    image = models.ImageField(_("image"), upload_to="ads/")
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("ad")
        verbose_name_plural = _("ads")

    def __str__(self):
        return self.title


class Category(MPTTModel):
    title = models.CharField(_("title"), max_length=255)
    image = models.ImageField(_("image"), upload_to="categories/")
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        verbose_name=_("parent"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class MPTTMeta:
        order_insertion_by = ["title"]

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.title


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE,
        verbose_name=_("category"),
    )
    title = models.CharField(_("title"), max_length=255)
    image = models.ImageField(_("image"), upload_to="products/")
    description = models.TextField(_("description"))
    stock_quantity = models.PositiveIntegerField(
        _("stock quantity"), default=0, validators=[MinValueValidator(0)]
    )
    reward_points = models.PositiveIntegerField(
        _("reward points"), default=0, validators=[MinValueValidator(0)]
    )
    default_price = models.DecimalField(
        _("default price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
    )
    is_newest = models.BooleanField(_("newest"), default=False)
    is_best_seller = models.BooleanField(_("best seller"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["title"]

    def __str__(self):
        return self.title


class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="reviews",
        on_delete=models.CASCADE,
        verbose_name=_("product"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="product_reviews",
        on_delete=models.CASCADE,
        verbose_name=_("user"),
    )
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    description = models.TextField(_("description"))
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("product review")
        verbose_name_plural = _("product reviews")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_product_review_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.product} - {self.rating}"
