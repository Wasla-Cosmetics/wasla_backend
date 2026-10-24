from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.store.admin import AdAdmin, CategoryAdmin, ProductAdmin, ProductReviewAdmin
from apps.store.models import (
    Ad,
    Brand,
    Branch,
    Category,
    Product,
    ProductImage,
    ProductReview,
)
from apps.store.serializers import ProductSerializer


@override_settings(MEDIA_ROOT=Path("/tmp/wasla_test_media"))
class StoreApiTests(APITestCase):
    def setUp(self):
        translation.deactivate()
        self.addCleanup(translation.deactivate)
        self.brand = Brand.objects.create(title="Wasla")
        self.branch = Branch.objects.create(brand=self.brand, title="Main Branch")

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
        parent = Category.objects.create(
            branch=self.branch,
            title="Beauty",
            image=self.image("parent.jpg"),
        )
        Category.objects.create(
            branch=self.branch,
            title="Skin Care",
            image=self.image("child.jpg"),
            parent=parent,
        )

        response = self.client.get(reverse("categories-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        child = next(
            item for item in response.data["data"] if item["title"] == "Skin Care"
        )
        self.assertEqual(child["parent"], parent.id)

    def test_products_endpoint_uses_default_price_not_legacy_price(self):
        category = Category.objects.create(
            branch=self.branch, title="Beauty", image=self.image("category.jpg")
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
        self.assertIsNone(product["compare_at_price"])
        self.assertEqual(product["discount_percentage"], 0)
        self.assertNotIn("price", product)

    def test_products_endpoint_returns_compare_price_and_discount_percentage(self):
        category = Category.objects.create(
            branch=self.branch, title="Beauty", image=self.image("category.jpg")
        )
        Product.objects.create(
            category=category,
            title="Cleanser",
            image=self.image("product.jpg"),
            description="Gentle daily cleanser",
            default_price="150.00",
            compare_at_price="200.00",
        )

        response = self.client.get(reverse("products-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product = response.data["data"][0]
        self.assertEqual(product["default_price"], Decimal("150.00"))
        self.assertEqual(product["compare_at_price"], Decimal("200.00"))
        self.assertEqual(product["discount_percentage"], 25)

    def test_product_serializer_rejects_compare_price_not_above_default_price(self):
        category = Category.objects.create(
            branch=self.branch, title="Beauty", image=self.image("category.jpg")
        )
        serializer = ProductSerializer(
            data={
                "category_id": category.id,
                "title": "Cleanser",
                "description": "Gentle daily cleanser",
                "default_price": "150.00",
                "compare_at_price": "150.00",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("compare_at_price", serializer.errors)

    def test_product_database_rejects_compare_price_not_above_default_price(self):
        category = Category.objects.create(
            branch=self.branch, title="Beauty", image=self.image("category.jpg")
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(
                    category=category,
                    title="Cleanser",
                    description="Gentle daily cleanser",
                    default_price="150.00",
                    compare_at_price="100.00",
                )

    def test_products_endpoint_cannot_disable_pagination(self):
        category = Category.objects.create(
            branch=self.branch, title="Beauty", image=self.image("category.jpg")
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
        self.assertIsNotNone(response.data["pagination"])
        self.assertEqual(response.data["data"][0]["title"], "Cleanser")

    def test_products_endpoint_fetches_categories_and_images_in_fixed_queries(self):
        category = Category.objects.create(
            branch=self.branch, title="Beauty", image=self.image("category.jpg")
        )
        for index in range(5):
            Product.objects.create(
                category=category,
                title=f"Product {index}",
                image=self.image(f"product-{index}.jpg"),
                description="Product description",
                default_price="150.00",
            )

        with self.assertNumQueries(3):
            response = self.client.get(reverse("products-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["count"], 5)

    def test_products_endpoint_returns_additional_images(self):
        category = Category.objects.create(
            branch=self.branch, title="Beauty", image=self.image("category.jpg")
        )
        product = Product.objects.create(
            category=category,
            title="Cleanser",
            image=self.image("primary-product.jpg"),
            description="Gentle daily cleanser",
            default_price="150.00",
        )
        first_image = ProductImage.objects.create(
            product=product,
            image=self.image("additional-product-front.jpg"),
        )
        second_image = ProductImage.objects.create(
            product=product,
            image=self.image("additional-product-back.jpg"),
        )

        response = self.client.get(reverse("products-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized_product = response.data["data"][0]
        self.assertIn("primary-product", serialized_product["image"])
        self.assertEqual(
            [image["id"] for image in serialized_product["images"]],
            [first_image.id, second_image.id],
        )
        self.assertIn(
            "additional-product-front",
            serialized_product["images"][0]["image"],
        )
        self.assertIn(
            "additional-product-back",
            serialized_product["images"][1]["image"],
        )

    def test_ads_list_returns_all_translations_when_requested(self):
        Ad.objects.create(
            title_en="Natural Beauty",
            title_ar="الجمال الطبيعي",
            subtitle_en="Discover selected products",
            subtitle_ar="اكتشف المنتجات المختارة",
            image=self.image("translated-ad.jpg"),
        )

        response = self.client.get(
            reverse("ads-list"),
            HTTP_ACCEPT_LANGUAGE="all",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ad = response.data["data"][0]
        self.assertEqual(ad["title"], "Natural Beauty")
        self.assertEqual(ad["subtitle"], "Discover selected products")
        self.assertEqual(ad["title_en"], "Natural Beauty")
        self.assertEqual(ad["title_ar"], "الجمال الطبيعي")
        self.assertEqual(ad["subtitle_en"], "Discover selected products")
        self.assertEqual(ad["subtitle_ar"], "اكتشف المنتجات المختارة")

    def test_all_language_header_only_changes_list_responses(self):
        ad = Ad.objects.create(
            title_en="Natural Beauty",
            title_ar="الجمال الطبيعي",
            subtitle_en="Discover selected products",
            subtitle_ar="اكتشف المنتجات المختارة",
            image=self.image("translated-ad.jpg"),
        )

        response = self.client.get(
            reverse("ads-detail", args=[ad.id]),
            HTTP_ACCEPT_LANGUAGE="all",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("title_en", response.data["data"])
        self.assertNotIn("title_ar", response.data["data"])

    def test_categories_list_returns_all_translations_when_requested(self):
        Category.objects.create(
            branch=self.branch,
            title_en="Beauty",
            title_ar="الجمال",
            image=self.image("translated-category.jpg"),
        )

        response = self.client.get(
            reverse("categories-list"),
            HTTP_ACCEPT_LANGUAGE="all",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category = response.data["data"][0]
        self.assertEqual(category["title_en"], "Beauty")
        self.assertEqual(category["title_ar"], "الجمال")

    def test_products_list_returns_all_translations_when_requested(self):
        category = Category.objects.create(
            branch=self.branch,
            title_en="Beauty",
            title_ar="الجمال",
            image=self.image("translated-category.jpg"),
        )
        Product.objects.create(
            category=category,
            title_en="Cleanser",
            title_ar="غسول",
            description_en="Gentle daily cleanser",
            description_ar="غسول يومي لطيف",
            image=self.image("translated-product.jpg"),
            default_price="150.00",
        )

        response = self.client.get(
            reverse("products-list"),
            HTTP_ACCEPT_LANGUAGE="all",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product = response.data["data"][0]
        self.assertEqual(product["title"], "Cleanser")
        self.assertEqual(product["description"], "Gentle daily cleanser")
        self.assertEqual(product["title_en"], "Cleanser")
        self.assertEqual(product["title_ar"], "غسول")
        self.assertEqual(product["description_en"], "Gentle daily cleanser")
        self.assertEqual(product["description_ar"], "غسول يومي لطيف")
        self.assertEqual(product["category"]["title_en"], "Beauty")
        self.assertEqual(product["category"]["title_ar"], "الجمال")

    def test_product_title_filter_matches_arabic_with_english_response(self):
        category = Category.objects.create(
            branch=self.branch,
            title_en="Beauty",
            title_ar="الجمال",
            image=self.image("filter-category.jpg"),
        )
        product = Product.objects.create(
            category=category,
            title_en="Cleanser",
            title_ar="غسول",
            description_en="Gentle daily cleanser",
            description_ar="غسول يومي لطيف",
            image=self.image("filter-product.jpg"),
            default_price="150.00",
        )

        response = self.client.get(
            reverse("products-list"),
            {"title": "غسول"},
            HTTP_ACCEPT_LANGUAGE="en",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["count"], 1)
        self.assertEqual(response.data["data"][0]["id"], product.id)
        self.assertEqual(response.data["data"][0]["title"], "Cleanser")

    def test_product_title_filter_matches_english_with_arabic_response(self):
        category = Category.objects.create(
            branch=self.branch,
            title_en="Beauty",
            title_ar="الجمال",
            image=self.image("filter-category.jpg"),
        )
        product = Product.objects.create(
            category=category,
            title_en="Cleanser",
            title_ar="غسول",
            description_en="Gentle daily cleanser",
            description_ar="غسول يومي لطيف",
            image=self.image("filter-product.jpg"),
            default_price="150.00",
        )

        response = self.client.get(
            reverse("products-list"),
            {"title": "clean"},
            HTTP_ACCEPT_LANGUAGE="ar",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["count"], 1)
        self.assertEqual(response.data["data"][0]["id"], product.id)
        self.assertEqual(response.data["data"][0]["title"], "غسول")

    def test_category_title_filter_matches_arabic_with_all_languages_response(self):
        category = Category.objects.create(
            branch=self.branch,
            title_en="Beauty",
            title_ar="الجمال",
            image=self.image("filter-category.jpg"),
        )
        product = Product.objects.create(
            category=category,
            title_en="Cleanser",
            title_ar="غسول",
            description_en="Gentle daily cleanser",
            description_ar="غسول يومي لطيف",
            image=self.image("filter-product.jpg"),
            default_price="150.00",
        )

        response = self.client.get(
            reverse("products-list"),
            {"category_title": "الجمال"},
            HTTP_ACCEPT_LANGUAGE="all",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["count"], 1)
        self.assertEqual(response.data["data"][0]["id"], product.id)
        self.assertEqual(response.data["data"][0]["title_en"], "Cleanser")
        self.assertEqual(response.data["data"][0]["title_ar"], "غسول")


@override_settings(MEDIA_ROOT=Path("/tmp/wasla_test_media"))
class StoreAdminSearchTests(TestCase):
    @staticmethod
    def image(name="image.jpg"):
        return ContentFile(b"file_content", name=name)

    def setUp(self):
        self.request = RequestFactory().get("/admin/")
        self.brand = Brand.objects.create(title="Wasla")
        self.branch = Branch.objects.create(brand=self.brand, title="Main Branch")
        self.ad = Ad.objects.create(
            title_en="Natural Beauty",
            title_ar="الجمال الطبيعي",
            subtitle_en="Discover selected products",
            subtitle_ar="اكتشف المنتجات المختارة",
            image=self.image("admin-ad.jpg"),
        )
        self.category = Category.objects.create(
            branch=self.branch,
            title_en="Beauty",
            title_ar="الجمال",
            image=self.image("admin-category.jpg"),
        )
        self.product = Product.objects.create(
            category=self.category,
            title_en="Cleanser",
            title_ar="غسول",
            description_en="Gentle daily cleanser",
            description_ar="غسول يومي لطيف",
            image=self.image("admin-product.jpg"),
            default_price="150.00",
        )
        self.user = get_user_model().objects.create_user(
            phone="+201000000111",
            email="admin-search@example.com",
            full_name="Admin Search User",
            password="NileBridgePass123!",
            is_active=True,
        )
        self.review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            description="Excellent product.",
        )

    def search(self, admin_class, model, term):
        model_admin = admin_class(model, admin.site)
        queryset, _ = model_admin.get_search_results(
            self.request,
            model.objects.all(),
            term,
        )
        return queryset

    def test_ad_admin_searches_arabic_subtitle(self):
        queryset = self.search(AdAdmin, Ad, "اكتشف")

        self.assertQuerySetEqual(queryset, [self.ad], ordered=False)

    def test_category_admin_searches_arabic_title(self):
        queryset = self.search(CategoryAdmin, Category, "الجمال")

        self.assertQuerySetEqual(queryset, [self.category], ordered=False)

    def test_product_admin_searches_arabic_description(self):
        queryset = self.search(ProductAdmin, Product, "لطيف")

        self.assertQuerySetEqual(queryset, [self.product], ordered=False)

    def test_review_admin_searches_arabic_product_title(self):
        queryset = self.search(ProductReviewAdmin, ProductReview, "غسول")

        self.assertQuerySetEqual(queryset, [self.review], ordered=False)


@override_settings(MEDIA_ROOT=Path("/tmp/wasla_test_media"))
class ProductReviewApiTests(APITestCase):
    @staticmethod
    def image(name="image.jpg"):
        return ContentFile(b"file_content", name=name)

    def setUp(self):
        self.user_model = get_user_model()
        self.brand = Brand.objects.create(title="Wasla")
        self.branch = Branch.objects.create(brand=self.brand, title="Main Branch")
        self.category = Category.objects.create(
            branch=self.branch,
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
        self.assertNotIn("user_id", response.data["data"])
        self.assertNotIn("user_full_name", response.data["data"])
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

    def test_duplicate_review_race_returns_conflict_instead_of_server_error(self):
        ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            description="Good product.",
        )

        with patch("apps.store.serializers.ProductReview.objects.filter") as reviews:
            reviews.return_value.exists.return_value = False
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

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("product_id", response.data["errors"])
        self.assertEqual(ProductReview.objects.count(), 1)

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
