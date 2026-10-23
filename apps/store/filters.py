from django.db.models import Q
from django_filters import rest_framework as filters

from apps.core.translation import get_localized_field_names
from apps.store.models import Product


def filter_translated_field(queryset, field_path, lookup_expr, value):
    query = Q()
    for localized_field in get_localized_field_names(field_path):
        query |= Q(**{f"{localized_field}__{lookup_expr}": value})

    return queryset.filter(query)


class ProductFilter(filters.FilterSet):
    category_title = filters.CharFilter(
        method="filter_category_title",
    )
    title = filters.CharFilter(method="filter_title")

    def filter_category_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="category__title",
            lookup_expr="exact",
            value=value,
        )

    def filter_title(self, queryset, name, value):
        return filter_translated_field(
            queryset,
            field_path="title",
            lookup_expr="icontains",
            value=value,
        )

    class Meta:
        model = Product
        fields = {
            "is_newest": ["exact"],
            "is_best_seller": ["exact"],
        }
