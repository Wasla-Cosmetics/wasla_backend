from django.core.validators import MinValueValidator
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
    quantity = models.PositiveIntegerField(
        _("quantity"), default=0, validators=[MinValueValidator(0)]
    )
    points = models.PositiveIntegerField(
        _("points"), default=0, validators=[MinValueValidator(0)]
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
