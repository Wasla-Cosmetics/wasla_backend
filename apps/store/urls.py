from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.store.views import AdViewSet, CategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register("ads", AdViewSet, basename="ads")
router.register("categories", CategoryViewSet, basename="categories")
router.register("products", ProductViewSet, basename="products")

urlpatterns = [
    path("", include(router.urls)),
]
