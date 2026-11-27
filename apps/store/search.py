from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TypedDict

from django.db.models import Case, CharField, F, IntegerField, Q, Value, When

from apps.core.translation import get_localized_field_names
from apps.store.models import Ad, Branch, Brand, Category, Product

CATALOG_SEARCH_TYPES = ("product", "category", "brand", "branch", "ad")


class SearchConfig(TypedDict):
    model: type[Product] | type[Category] | type[Brand] | type[Branch] | type[Ad]
    title_fields: tuple[str, ...]
    secondary_fields: tuple[str, ...]
    type_order: int


SEARCH_CONFIG: dict[str, SearchConfig] = {
    "product": {
        "model": Product,
        "title_fields": ("title",),
        "secondary_fields": ("description",),
        "type_order": 0,
    },
    "category": {
        "model": Category,
        "title_fields": ("title",),
        "secondary_fields": (),
        "type_order": 1,
    },
    "brand": {
        "model": Brand,
        "title_fields": ("title",),
        "secondary_fields": (),
        "type_order": 2,
    },
    "branch": {
        "model": Branch,
        "title_fields": ("title",),
        "secondary_fields": (),
        "type_order": 3,
    },
    "ad": {
        "model": Ad,
        "title_fields": ("title",),
        "secondary_fields": ("subtitle",),
        "type_order": 4,
    },
}


def _lookup_query(field_names: Iterable[str], lookup: str, value: object) -> Q:
    query = Q()
    for field_name in field_names:
        query |= Q(**{f"{field_name}__{lookup}": value})
    return query


def _ranked_queryset(result_type: str, query: str) -> Any:
    config = SEARCH_CONFIG[result_type]
    title_fields = get_localized_field_names(*config["title_fields"])
    secondary_fields = get_localized_field_names(*config["secondary_fields"])
    title_exact = _lookup_query(title_fields, "iexact", query)
    title_prefix = _lookup_query(title_fields, "istartswith", query)
    title_partial = _lookup_query(title_fields, "icontains", query)
    secondary_partial = _lookup_query(secondary_fields, "icontains", query)
    match_query = title_partial | secondary_partial
    rank_cases = [
        When(title_exact, then=Value(400)),
        When(title_prefix, then=Value(300)),
        When(title_partial, then=Value(200)),
    ]
    if secondary_fields:
        rank_cases.append(When(secondary_partial, then=Value(100)))

    return (
        config["model"]
        .objects.filter(match_query)
        .order_by()
        .annotate(
            result_type=Value(result_type, output_field=CharField()),
            type_order=Value(config["type_order"], output_field=IntegerField()),
            search_rank=Case(
                *rank_cases,
                default=Value(0),
                output_field=IntegerField(),
            ),
            object_id=F("id"),
        )
        .values("result_type", "type_order", "search_rank", "object_id")
    )


def search_catalog(query: str, result_types: Sequence[str]) -> Any:
    querysets = [_ranked_queryset(result_type, query) for result_type in result_types]
    combined = querysets[0]
    if len(querysets) > 1:
        combined = combined.union(*querysets[1:], all=True)
    return combined.order_by("-search_rank", "type_order", "object_id")


def hydrate_search_results(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, object]]:
    ids_by_type: dict[str, list[int]] = {
        result_type: [] for result_type in CATALOG_SEARCH_TYPES
    }
    for row in rows:
        ids_by_type[row["result_type"]].append(row["object_id"])

    objects_by_type: dict[str, Mapping[int, object]] = {
        "product": Product.objects.select_related("category__branch__brand")
        .prefetch_related("images")
        .in_bulk(ids_by_type["product"]),
        "category": Category.objects.select_related("branch__brand").in_bulk(
            ids_by_type["category"]
        ),
        "brand": Brand.objects.in_bulk(ids_by_type["brand"]),
        "branch": Branch.objects.select_related("brand").in_bulk(ids_by_type["branch"]),
        "ad": Ad.objects.in_bulk(ids_by_type["ad"]),
    }

    return [
        {
            "type": row["result_type"],
            "object": objects_by_type[row["result_type"]][row["object_id"]],
        }
        for row in rows
    ]
