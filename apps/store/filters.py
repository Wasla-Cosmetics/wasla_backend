from django.db.models import Q
from django_filters import rest_framework as filters

from apps.core.translation import get_localized_field_names
from apps.store.models import Brand, Branch, Category, Product


def filter_translated_field(queryset, field_path, lookup_expr, value):
    query = Q()
    for localized_field in get_localized_field_names(field_path):
        query |= Q(**{f"{localized_field}__{lookup_expr}": value})

    return queryset.filter(query)


class TranslatedTitleFilterSet(filters.FilterSet):
    title = filters.CharFilter(method="filter_title")

    def filter_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="title",
            lookup_expr="icontains",
            value=value,
        )


class BrandFilter(TranslatedTitleFilterSet):
    class Meta:
        model = Brand
        fields = []


class BranchFilter(TranslatedTitleFilterSet):
    brand_title = filters.CharFilter(method="filter_brand_title")

    def filter_brand_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="brand__title",
            lookup_expr="icontains",
            value=value,
        )

    class Meta:
        model = Branch
        fields = {"brand": ["exact"]}


class CategoryFilter(TranslatedTitleFilterSet):
    brand = filters.NumberFilter(field_name="branch__brand_id")
    branch_title = filters.CharFilter(method="filter_branch_title")
    brand_title = filters.CharFilter(method="filter_brand_title")

    def filter_branch_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="branch__title",
            lookup_expr="icontains",
            value=value,
        )

    def filter_brand_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="branch__brand__title",
            lookup_expr="icontains",
            value=value,
        )

    class Meta:
        model = Category
        fields = {"branch": ["exact"]}


class ProductFilter(TranslatedTitleFilterSet):
    branch = filters.NumberFilter(field_name="category__branch_id")
    brand = filters.NumberFilter(field_name="category__branch__brand_id")
    category_title = filters.CharFilter(
        method="filter_category_title",
    )
    branch_title = filters.CharFilter(method="filter_branch_title")
    brand_title = filters.CharFilter(method="filter_brand_title")

    def filter_category_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="category__title",
            lookup_expr="exact",
            value=value,
        )

    def filter_branch_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="category__branch__title",
            lookup_expr="icontains",
            value=value,
        )

    def filter_brand_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="category__branch__brand__title",
            lookup_expr="icontains",
            value=value,
        )

    class Meta:
        model = Product
        fields = {
            "category": ["exact"],
            "is_newest": ["exact"],
            "is_best_seller": ["exact"],
        }
