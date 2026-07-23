from django_filters import rest_framework as filters
from apps.store.models import Product


class ProductFilter(filters.FilterSet):
    category_title = filters.CharFilter(
        lookup_expr="exact",
        field_name="category__title",
    )
    title = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Product
        fields = {
            "is_newest": ["exact"],
            "is_best_seller": ["exact"],
        }
