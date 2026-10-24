from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.core.pagination import StandardPageNumberPagination
from apps.core.permissions import IsAdminOrReadOnly, IsReviewOwnerOrAdminOrReadOnly
from apps.core.serializers import AllLanguagesModelSerializer
from apps.store.filters import BrandFilter, BranchFilter, CategoryFilter, ProductFilter
from apps.store.models import Ad, Brand, Branch, Category, Product, ProductReview
from apps.store.search import hydrate_search_results, search_catalog
from apps.store.serializers import (
    AdSerializer,
    BrandSerializer,
    BranchSerializer,
    CatalogSearchQuerySerializer,
    CatalogSearchResultSerializer,
    CategorySerializer,
    ProductReviewSerializer,
    ProductSerializer,
)
from apps.store.throttles import CatalogSearchRateThrottle


class ReviewAlreadyExists(APIException):
    status_code = 409
    default_detail = {"product_id": _("You already reviewed this product.")}
    default_code = "review_already_exists"


class CatalogResourceInUse(APIException):
    status_code = 409
    default_detail = _("This catalog resource is in use and cannot be deleted.")
    default_code = "catalog_resource_in_use"


class ProtectedDestroyMixin:
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise CatalogResourceInUse() from exc


class CatalogSearchPagination(StandardPageNumberPagination):
    max_page_size = 50


class CatalogSearchView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CatalogSearchRateThrottle]
    pagination_class = CatalogSearchPagination

    def get(self, request):
        query_serializer = CatalogSearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        search_rows = search_catalog(
            query_serializer.validated_data["q"],
            query_serializer.validated_data["types"],
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(search_rows, request, view=self)
        results = hydrate_search_results(page)
        serializer = CatalogSearchResultSerializer(
            results,
            many=True,
            context={
                "request": request,
                "view": self,
                "include_all_languages": (
                    request.headers.get("Accept-Language", "").strip().lower()
                    == AllLanguagesModelSerializer.all_languages_header_value
                ),
            },
        )
        return paginator.get_paginated_response(serializer.data)


class AdViewSet(ModelViewSet):
    queryset = Ad.objects.all().order_by("id")
    serializer_class = AdSerializer
    permission_classes = [IsAdminOrReadOnly]


class BrandViewSet(ProtectedDestroyMixin, ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BrandFilter


class BranchViewSet(ProtectedDestroyMixin, ModelViewSet):
    queryset = Branch.objects.select_related("brand")
    serializer_class = BranchSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BranchFilter


class CategoryViewSet(ProtectedDestroyMixin, ModelViewSet):
    queryset = Category.objects.select_related("branch__brand")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related(
        "category__branch__brand"
    ).prefetch_related("images")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter


class ProductReviewViewSet(ModelViewSet):
    queryset = ProductReview.objects.select_related("product")
    serializer_class = ProductReviewSerializer
    permission_classes = [IsReviewOwnerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product"]

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(user=self.request.user)
        except IntegrityError as exc:
            product = serializer.validated_data["product"]
            if ProductReview._base_manager.filter(
                product=product,
                user=self.request.user,
            ).exists():
                raise ReviewAlreadyExists() from exc
            raise
