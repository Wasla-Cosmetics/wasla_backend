from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.store.views import (
    AdViewSet,
    BrandViewSet,
    BranchViewSet,
    CategoryViewSet,
    ProductReviewViewSet,
    ProductViewSet,
)

router = DefaultRouter()
router.register("ads", AdViewSet, basename="ads")
router.register("brands", BrandViewSet, basename="brands")
router.register("branches", BranchViewSet, basename="branches")
router.register("categories", CategoryViewSet, basename="categories")
router.register("products", ProductViewSet, basename="products")
router.register("reviews", ProductReviewViewSet, basename="reviews")

urlpatterns = [
    path("", include(router.urls)),
]
