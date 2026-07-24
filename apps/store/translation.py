from modeltranslation.translator import TranslationOptions, register

from apps.store.models import Ad, Category, Product


@register(Ad)
class AdTranslationOptions(TranslationOptions):
    fields = ("title", "subtitle")


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("title", "description")
