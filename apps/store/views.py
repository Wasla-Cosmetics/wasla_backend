from apps.core.permissions import IsAdminOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

from apps.store.models import Ad, Category, Product
from apps.store.serializers import AdSerializer, CategorySerializer, ProductSerializer
from apps.store.filters import ProductFilter


class AdViewSet(ModelViewSet):
    queryset = Ad.objects.all().order_by("id")
    serializer_class = AdSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
