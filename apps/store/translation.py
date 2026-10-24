from modeltranslation.translator import TranslationOptions, register

from apps.store.models import Ad, Brand, Branch, Category, Product


@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Branch)
class BranchTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Ad)
class AdTranslationOptions(TranslationOptions):
    fields = ("title", "subtitle")


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("title", "description")
