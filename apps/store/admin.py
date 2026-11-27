from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin, TabularInline

from apps.core.translation import get_localized_field_names
from apps.store.forms import ProductAdminForm
from apps.store.models import (
    Ad,
    Branch,
    Brand,
    Category,
    Product,
    ProductImage,
    ProductReview,
)


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    tab = False
    show_count = True
    fields = ("image",)

    verbose_name = _("Additional product image")
    verbose_name_plural = _("Additional product images")


@admin.register(Brand)
class BrandAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = get_localized_field_names("title")
    ordering = ("title",)
    list_per_page = 25


@admin.register(Branch)
class BranchAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = (
        "title",
        "brand",
        "created_at",
        "updated_at",
    )
    list_filter = ("brand",)
    search_fields = (
        *get_localized_field_names("title"),
        *get_localized_field_names("brand__title"),
    )
    list_select_related = ("brand",)
    ordering = ("brand", "title")
    list_per_page = 25
    list_filter_submit = True


@admin.register(Ad)
class AdAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = (
        "title",
        "created_at",
        "updated_at",
    )
    search_fields = get_localized_field_names("title", "subtitle")
    ordering = ("-created_at",)
    list_per_page = 25


@admin.register(Category)
class CategoryAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = (
        "category_tree",
        "branch",
        "parent",
        "created_at",
    )
    list_display_links = ("category_tree",)
    list_filter = (
        "branch__brand",
        "branch",
    )
    search_fields = (
        *get_localized_field_names("title"),
        *get_localized_field_names("branch__title"),
        *get_localized_field_names("branch__brand__title"),
    )
    list_per_page = 50
    list_filter_submit = True

    @admin.display(description=_("Category"), ordering="tree_id")
    def category_tree(self, obj: Category) -> str:
        indentation = "— " * obj.level
        return f"{indentation}{obj.title}"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return (
            super()
            .get_queryset(request)
            .select_related("branch", "branch__brand", "parent")
            .order_by("tree_id", "lft")
        )


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    form = ProductAdminForm
    change_form_template = "admin/store/product/change_form.html"
    warn_unsaved_form = True

    inlines = (ProductImageInline,)
    list_display = (
        "product_thumbnail",
        "title",
        "category",
        "default_price",
        "compare_at_price",
        "discount_percentage",
        "stock_quantity",
        "reward_points",
        "is_newest",
        "is_best_seller",
    )
    list_filter = (
        "category__branch__brand",
        "category__branch",
        "category",
        "is_newest",
        "is_best_seller",
        "created_at",
    )
    search_fields = (
        *get_localized_field_names("title", "description"),
        *get_localized_field_names("category__title"),
        *get_localized_field_names("category__branch__title"),
        *get_localized_field_names("category__branch__brand__title"),
    )
    readonly_fields = (
        "discount_percentage",
        "created_at",
        "updated_at",
    )
    list_select_related = (
        "category",
        "category__branch",
        "category__branch__brand",
    )
    list_per_page = 25
    list_filter_submit = True
    list_fullwidth = True

    @admin.display(description=_("Image"))
    def product_thumbnail(self, obj: Product) -> str | SafeString:
        if not obj.image:
            return "—"

        return format_html(
            '<img src="{}" alt="{}" '
            'style="width:42px;height:42px;object-fit:cover;'
            'border-radius:8px;" />',
            obj.image.url,
            obj.title,
        )


@admin.register(ProductReview)
class ProductReviewAdmin(ModelAdmin):
    list_display = (
        "product",
        "user",
        "rating",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "rating",
        "created_at",
    )
    search_fields = (
        *get_localized_field_names("product__title"),
        "user__phone",
        "user__full_name",
        "description",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    list_select_related = (
        "product",
        "user",
    )
    ordering = ("-created_at",)
    list_per_page = 25
    list_filter_submit = True
