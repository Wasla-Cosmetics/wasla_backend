from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import APIException
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import IsAdminOrReadOnly, IsReviewOwnerOrAdminOrReadOnly
from apps.store.filters import ProductFilter
from apps.store.models import Ad, Category, Product, ProductReview
from apps.store.serializers import (
    AdSerializer,
    CategorySerializer,
    ProductReviewSerializer,
    ProductSerializer,
)


class ReviewAlreadyExists(APIException):
    status_code = 409
    default_detail = {"product_id": _("You already reviewed this product.")}
    default_code = "review_already_exists"


class AdViewSet(ModelViewSet):
    queryset = Ad.objects.all().order_by("id")
    serializer_class = AdSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related("category").prefetch_related("images")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter


class ProductReviewViewSet(ModelViewSet):
    queryset = ProductReview.objects.select_related("product", "user")
    serializer_class = ProductReviewSerializer
    permission_classes = [IsReviewOwnerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product", "user"]

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
