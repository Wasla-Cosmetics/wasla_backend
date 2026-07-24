from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from modeltranslation.admin import TranslationAdmin

from apps.store.models import Ad, Category, Product, ProductReview


class DraggableTranslationAdmin(TranslationAdmin, DraggableMPTTAdmin):
    pass


@admin.register(Ad)
class AdAdmin(TranslationAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title", "subtitle")
    ordering = ("-created_at",)


@admin.register(Category)
class CategoryAdmin(DraggableTranslationAdmin):
    list_display = ("tree_actions", "indented_title", "parent")
    list_display_links = ("indented_title",)
    search_fields = ("title",)


@admin.register(Product)
class ProductAdmin(TranslationAdmin):
    list_display = (
        "title",
        "category",
        "default_price",
        "stock_quantity",
        "reward_points",
        "is_newest",
        "is_best_seller",
    )
    list_filter = ("category", "is_newest", "is_best_seller")
    search_fields = ("title", "description")


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at", "updated_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__title", "user__phone", "user__full_name", "description")
    readonly_fields = ("created_at", "updated_at")
