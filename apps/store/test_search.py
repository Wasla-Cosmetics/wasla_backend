from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.store.models import Ad, Brand, Branch, Category, Product
from apps.store.throttles import CatalogSearchRateThrottle


@override_settings(MEDIA_ROOT=Path("/tmp/wasla_test_media"))
class CatalogSearchApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.brand = Brand.objects.create(title="Wasla")
        self.branch = Branch.objects.create(brand=self.brand, title="Main Branch")

    @staticmethod
    def image(name="image.jpg"):
        return ContentFile(b"file_content", name=name)

    def create_category(self, title_en="Beauty", title_ar="الجمال"):
        return Category.objects.create(
            branch=self.branch,
            title_en=title_en,
            title_ar=title_ar,
            image=self.image(f"category-{Category.objects.count()}.jpg"),
        )

    def create_product(
        self,
        *,
        category=None,
        title_en="Cleanser",
        title_ar="غسول",
        description_en="Gentle daily cleanser",
        description_ar="غسول يومي لطيف",
    ):
        return Product.objects.create(
            category=category or self.create_category(),
            title_en=title_en,
            title_ar=title_ar,
            description_en=description_en,
            description_ar=description_ar,
            image=self.image(f"product-{Product.objects.count()}.jpg"),
            default_price="150.00",
        )

    def test_search_matches_every_supported_model_and_language(self):
        category = self.create_category(
            title_en="Rose Care",
            title_ar="العناية بالورد",
        )
        product = self.create_product(
            category=category,
            title_en="Facial Oil",
            title_ar="زيت الوجه",
            description_en="Made with rose extract",
            description_ar="مصنوع من مستخلص الورد",
        )
        ad = Ad.objects.create(
            title_en="Weekend Offer",
            title_ar="عرض نهاية الأسبوع",
            subtitle_en="Save on the rose collection",
            subtitle_ar="وفر على مجموعة الورد",
            image=self.image("rose-ad.jpg"),
        )

        response = self.client.get(
            reverse("catalog-search"),
            {"q": "الورد"},
            HTTP_ACCEPT_LANGUAGE="en",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["count"], 3)
        results = {
            (result["type"], result["id"]): result for result in response.data["data"]
        }
        self.assertEqual(results[("category", category.id)]["title"], "Rose Care")
        self.assertEqual(results[("product", product.id)]["title"], "Facial Oil")
        self.assertEqual(results[("ad", ad.id)]["title"], "Weekend Offer")

    def test_search_localizes_output_without_limiting_match_language(self):
        product = self.create_product()

        response = self.client.get(
            reverse("catalog-search"),
            {"q": "clean"},
            HTTP_ACCEPT_LANGUAGE="ar",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["count"], 1)
        result = response.data["data"][0]
        self.assertEqual(result["id"], product.id)
        self.assertEqual(result["title"], "غسول")
        self.assertNotIn("title_en", result)
        self.assertNotIn("title_ar", result)

    def test_search_returns_all_translations_when_requested(self):
        product = self.create_product()

        response = self.client.get(
            reverse("catalog-search"),
            {"q": "غسول"},
            HTTP_ACCEPT_LANGUAGE="all",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data["data"][0]
        self.assertEqual(result["id"], product.id)
        self.assertEqual(result["title"], "Cleanser")
        self.assertEqual(result["title_en"], "Cleanser")
        self.assertEqual(result["title_ar"], "غسول")
        self.assertEqual(result["description_en"], "Gentle daily cleanser")
        self.assertEqual(result["description_ar"], "غسول يومي لطيف")
        self.assertEqual(result["category"]["title_en"], "Beauty")
        self.assertEqual(result["category"]["title_ar"], "الجمال")

    def test_search_types_parameter_uses_a_fixed_public_allowlist(self):
        category = self.create_category(title_en="Special", title_ar="مميز")
        product = self.create_product(
            category=category,
            title_en="Special Product",
            title_ar="منتج مميز",
        )
        ad = Ad.objects.create(
            title_en="Special Offer",
            title_ar="عرض مميز",
            image=self.image("special-ad.jpg"),
        )
        get_user_model().objects.create_user(
            phone="+201000009999",
            email="special@example.com",
            full_name="Special Private User",
            password="NileBridgePass123!",
            is_active=True,
        )

        response = self.client.get(
            reverse("catalog-search"),
            {"q": "special", "types": "product,ad"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["count"], 2)
        self.assertEqual(
            {(result["type"], result["id"]) for result in response.data["data"]},
            {("product", product.id), ("ad", ad.id)},
        )
        self.assertNotIn("category", {item["type"] for item in response.data["data"]})

        invalid_response = self.client.get(
            reverse("catalog-search"),
            {"q": "special", "types": "product,user"},
        )
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("types", invalid_response.data["errors"])

    def test_search_ranks_exact_title_before_prefix_and_secondary_text(self):
        category = self.create_category(title_en="Catalog", title_ar="الفهرس")
        exact = self.create_product(
            category=category,
            title_en="Rose",
            title_ar="ورد",
            description_en="Exact title",
            description_ar="عنوان مطابق",
        )
        prefix = self.create_product(
            category=category,
            title_en="Rose Oil",
            title_ar="زيت الورد",
            description_en="Prefix title",
            description_ar="عنوان يبدأ بالكلمة",
        )
        secondary = self.create_product(
            category=category,
            title_en="Body Oil",
            title_ar="زيت الجسم",
            description_en="Contains rose extract",
            description_ar="يحتوي على مستخلص الورد",
        )

        response = self.client.get(reverse("catalog-search"), {"q": "rose"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["id"] for item in response.data["data"]],
            [exact.id, prefix.id, secondary.id],
        )

    def test_search_validates_query_length(self):
        for query_params in ({}, {"q": "x"}, {"q": "x" * 101}):
            with self.subTest(query_params=query_params):
                response = self.client.get(reverse("catalog-search"), query_params)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("q", response.data["errors"])

    def test_search_page_size_is_capped_at_fifty(self):
        for index in range(51):
            self.create_category(
                title_en=f"Searchable {index:02d}",
                title_ar=f"قابل للبحث {index:02d}",
            )

        response = self.client.get(
            reverse("catalog-search"),
            {"q": "searchable", "page_size": 100},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pagination"]["count"], 51)
        self.assertEqual(response.data["pagination"]["page_size"], 50)
        self.assertEqual(len(response.data["data"]), 50)

    @patch.object(
        CatalogSearchRateThrottle,
        "THROTTLE_RATES",
        {"catalog_search": "2/minute"},
    )
    def test_search_is_throttled_by_client_ip(self):
        for _ in range(2):
            response = self.client.get(reverse("catalog-search"), {"q": "nothing"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse("catalog-search"), {"q": "nothing"})

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
