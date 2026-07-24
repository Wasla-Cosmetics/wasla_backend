from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.store.models import Ad, Category, Product, ProductReview


@override_settings(MEDIA_ROOT=Path("/tmp/wasla_test_media"))
class StoreApiTests(APITestCase):
    @staticmethod
    def image(name="image.jpg"):
        return ContentFile(b"file_content", name=name)

    def test_ads_endpoint_returns_ads(self):
        Ad.objects.create(
            title="Natural Beauty",
            subtitle="Discover selected products",
            image=self.image("active.jpg"),
        )
        Ad.objects.create(
            title="Summer Sale",
            image=self.image("sale.jpg"),
        )

        response = self.client.get(reverse("ads-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Success")
        self.assertEqual(response.data["errors"], {})
        self.assertEqual(response.data["pagination"]["count"], 2)
        self.assertEqual(response.data["data"][0]["title"], "Natural Beauty")
        self.assertEqual(
            set(response.data["data"][0].keys()),
            {"id", "title", "subtitle", "image"},
        )

    def test_category_endpoint_exposes_parent(self):
        parent = Category.objects.create(title="Beauty", image=self.image("parent.jpg"))
        Category.objects.create(
            title="Skin Care", image=self.image("child.jpg"), parent=parent
        )

        response = self.client.get(reverse("categories-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        child = next(
            item for item in response.data["data"] if item["title"] == "Skin Care"
        )
        self.assertEqual(child["parent"], parent.id)

    def test_products_endpoint_uses_default_price_not_legacy_price(self):
        category = Category.objects.create(
            title="Beauty", image=self.image("category.jpg")
        )
        Product.objects.create(
            category=category,
            title="Cleanser",
            image=self.image("product.jpg"),
            description="Gentle daily cleanser",
            default_price="150.00",
            stock_quantity=10,
            reward_points=5,
            is_newest=True,
        )

        response = self.client.get(reverse("products-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product = response.data["data"][0]
        self.assertEqual(product["default_price"], Decimal("150.00"))
        self.assertNotIn("price", product)

    def test_products_endpoint_can_disable_pagination(self):
        category = Category.objects.create(
            title="Beauty", image=self.image("category.jpg")
        )
        Product.objects.create(
            category=category,
            title="Cleanser",
            image=self.image("product.jpg"),
            description="Gentle daily cleanser",
            default_price="150.00",
        )

        response = self.client.get(reverse("products-list"), {"is_paginated": "false"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["data"], list)
        self.assertIsNone(response.data["pagination"])
        self.assertEqual(response.data["data"][0]["title"], "Cleanser")


@override_settings(MEDIA_ROOT=Path("/tmp/wasla_test_media"))
class ProductReviewApiTests(APITestCase):
    @staticmethod
    def image(name="image.jpg"):
        return ContentFile(b"file_content", name=name)

    def setUp(self):
        self.user_model = get_user_model()
        self.category = Category.objects.create(
            title="Beauty",
            image=self.image("category.jpg"),
        )
        self.product = Product.objects.create(
            category=self.category,
            title="Cleanser",
            image=self.image("product.jpg"),
            description="Gentle daily cleanser",
            default_price="150.00",
        )
        self.user = self.user_model.objects.create_user(
            phone="+201000000101",
            email="reviewer@example.com",
            full_name="Review User",
            password="NileBridgePass123!",
            is_active=True,
        )

    def auth_headers(self, user=None):
        token = RefreshToken.for_user(user or self.user)
        return {"HTTP_AUTHORIZATION": f"Bearer {token.access_token}"}

    def test_authenticated_user_can_create_product_review(self):
        response = self.client.post(
            reverse("reviews-list"),
            {
                "product_id": self.product.id,
                "rating": 5,
                "description": "Excellent product.",
            },
            **self.auth_headers(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductReview.objects.count(), 1)
        self.assertEqual(response.data["data"]["product"], self.product.id)
        self.assertEqual(response.data["data"]["user_id"], self.user.id)
        self.assertEqual(response.data["data"]["rating"], 5)
        self.assertIn("created_at", response.data["data"])
        self.assertIn("updated_at", response.data["data"])

    def test_reviews_can_be_read_publicly(self):
        ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            description="Good product.",
        )

        response = self.client.get(reverse("reviews-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"][0]["rating"], 4)
        self.assertEqual(response.data["pagination"]["count"], 1)

    def test_guest_user_cannot_create_product_review(self):
        response = self.client.post(
            reverse("reviews-list"),
            {
                "product_id": self.product.id,
                "rating": 5,
                "description": "Excellent product.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_review_rating_must_be_between_one_and_five(self):
        response = self.client.post(
            reverse("reviews-list"),
            {
                "product_id": self.product.id,
                "rating": 6,
                "description": "Invalid rating.",
            },
            **self.auth_headers(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rating", response.data["errors"])

    def test_user_cannot_review_same_product_twice(self):
        ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            description="Good product.",
        )

        response = self.client.post(
            reverse("reviews-list"),
            {
                "product_id": self.product.id,
                "rating": 5,
                "description": "Second review.",
            },
            **self.auth_headers(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("product_id", response.data["errors"])

    def test_only_review_owner_can_update_review(self):
        other_user = self.user_model.objects.create_user(
            phone="+201000000102",
            email="other-reviewer@example.com",
            full_name="Other Review User",
            password="NileBridgePass123!",
            is_active=True,
        )
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            description="Good product.",
        )

        response = self.client.patch(
            reverse("reviews-detail", args=[review.id]),
            {"description": "Trying to edit another user review."},
            **self.auth_headers(other_user),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(
            reverse("reviews-detail", args=[review.id]),
            {"description": "Updated review."},
            **self.auth_headers(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["description"], "Updated review.")
