from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from apps.core.models import TimeStampedModel


class Brand(TimeStampedModel):
    title = models.CharField(_("title"), max_length=255)
    image = models.ImageField(
        _("image"),
        upload_to="brands/",
        default="default.jpeg",
        blank=True,
    )

    class Meta:
        verbose_name = _("brand")
        verbose_name_plural = _("brands")
        ordering = ["title"]

    def __str__(self):
        return self.title


class Branch(TimeStampedModel):
    brand = models.ForeignKey(
        Brand,
        related_name="branches",
        on_delete=models.PROTECT,
        verbose_name=_("brand"),
    )
    title = models.CharField(_("title"), max_length=255)
    image = models.ImageField(
        _("image"),
        upload_to="branches/",
        default="default.jpeg",
        blank=True,
    )

    class Meta:
        verbose_name = _("branch")
        verbose_name_plural = _("branches")
        ordering = ["title"]

    def __str__(self):
        return self.title


class Ad(TimeStampedModel):
    title = models.CharField(_("title"), max_length=200)
    subtitle = models.TextField(_("subtitle"), blank=True)
    image = models.ImageField(
        _("image"),
        upload_to="ads/",
        default="default.jpeg",
        blank=True,
    )

    class Meta:
        verbose_name = _("ad")
        verbose_name_plural = _("ads")

    def __str__(self):
        return self.title


class Category(MPTTModel, TimeStampedModel):
    branch = models.ForeignKey(
        Branch,
        related_name="categories",
        on_delete=models.PROTECT,
        verbose_name=_("branch"),
    )
    title = models.CharField(_("title"), max_length=255)
    image = models.ImageField(
        _("image"),
        upload_to="categories/",
        default="default.jpeg",
        blank=True,
    )
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        verbose_name=_("parent"),
    )

    class MPTTMeta:
        order_insertion_by = ["title"]

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def clean(self):
        super().clean()
        if (
            self.parent_id
            and self.branch_id
            and self.parent.branch_id != self.branch_id
        ):
            raise ValidationError(
                {"parent": _("Category and parent must belong to the same branch.")}
            )

        if (
            self.pk
            and self.branch_id
            and self.subcategories.exclude(branch_id=self.branch_id).exists()
        ):
            raise ValidationError(
                {"branch": _("Category and children must belong to the same branch.")}
            )

    def __str__(self):
        return self.title


class Product(TimeStampedModel):
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE,
        verbose_name=_("category"),
    )
    title = models.CharField(_("title"), max_length=255)
    image = models.ImageField(
        _("image"),
        upload_to="products/",
        default="default.jpeg",
        blank=True,
    )
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
    compare_at_price = models.DecimalField(
        _("compare-at price"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
    )
    is_newest = models.BooleanField(_("newest"), default=False)
    is_best_seller = models.BooleanField(_("best seller"), default=False)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["title"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(compare_at_price__isnull=True)
                    | models.Q(compare_at_price__gt=models.F("default_price"))
                ),
                name="compare_at_price_above_default_price",
            ),
        ]

    @property
    def discount_percentage(self):
        if self.compare_at_price is None:
            return 0

        discount = self.compare_at_price - self.default_price
        return round((discount / self.compare_at_price) * 100)

    def __str__(self):
        return self.title


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE,
        verbose_name=_("product"),
    )
    image = models.ImageField(_("image"), upload_to="products/")

    class Meta:
        verbose_name = _("product image")
        verbose_name_plural = _("product images")
        ordering = ["id"]

    def __str__(self):
        return f"{self.product} - {self.id}"


class ProductReview(TimeStampedModel):
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
