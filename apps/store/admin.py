from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin

from apps.store.models import Ad, Category, Product


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title", "subtitle")
    ordering = ("-created_at",)


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "parent")
    list_display_links = ("indented_title",)
    search_fields = ("title",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "default_price",
        "quantity",
        "points",
        "is_newest",
        "is_best_seller",
    )
    list_filter = ("category", "is_newest", "is_best_seller")
    search_fields = ("title", "description")
