from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.store.models import Ad, Category, Product


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
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "Natural Beauty")
        self.assertEqual(
            set(response.data["results"][0].keys()),
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
            item for item in response.data["results"] if item["title"] == "Skin Care"
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
            quantity=10,
            points=5,
            is_newest=True,
        )

        response = self.client.get(reverse("products-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product = response.data["results"][0]
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
        self.assertIsInstance(response.data, list)
        self.assertEqual(response.data[0]["title"], "Cleanser")
