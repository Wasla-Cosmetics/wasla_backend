from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.store.models import Brand, Branch, Category, Product


@override_settings(MEDIA_ROOT=Path("/tmp/wasla_test_media"))
class BrandBranchModelTests(TestCase):
    @staticmethod
    def image(name="image.jpg"):
        return ContentFile(b"file_content", name=name)

    def test_product_inherits_branch_and_brand_through_category(self):
        brand = Brand.objects.create(title="Wasla", image=self.image("brand.jpg"))
        branch = Branch.objects.create(
            brand=brand,
            title="Cairo",
            image=self.image("branch.jpg"),
        )
        category = Category.objects.create(
            branch=branch,
            title="Skin Care",
            image=self.image("category.jpg"),
        )
        product = Product.objects.create(
            category=category,
            title="Cleanser",
            description="Gentle daily cleanser",
            image=self.image("product.jpg"),
            default_price="150.00",
        )

        self.assertEqual(product.category.branch, branch)
        self.assertEqual(product.category.branch.brand, brand)
        self.assertFalse(hasattr(product, "branch_id"))
        self.assertFalse(hasattr(product, "brand_id"))

    def test_category_parent_must_belong_to_same_branch(self):
        brand = Brand.objects.create(title="Wasla")
        cairo = Branch.objects.create(brand=brand, title="Cairo")
        alexandria = Branch.objects.create(brand=brand, title="Alexandria")
        cairo_parent = Category.objects.create(branch=cairo, title="Skin Care")
        invalid_child = Category(
            branch=alexandria,
            parent=cairo_parent,
            title="Face Care",
        )

        with self.assertRaises(ValidationError):
            invalid_child.full_clean()

    def test_populated_brand_and_branch_are_protected_from_deletion(self):
        brand = Brand.objects.create(title="Wasla")
        branch = Branch.objects.create(brand=brand, title="Cairo")
        Category.objects.create(branch=branch, title="Skin Care")

        with self.assertRaises(ProtectedError):
            branch.delete()

        with self.assertRaises(ProtectedError):
            brand.delete()


class BrandBranchMigrationTests(TransactionTestCase):
    migrate_from = ("store", "0004_product_compare_at_price_and_more")
    migrate_to = ("store", "0005_branch_brand_category_branch_branch_brand")

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps
        Category = old_apps.get_model("store", "Category")
        Product = old_apps.get_model("store", "Product")
        category = Category.objects.create(
            title="Legacy Category",
            title_en="Legacy Category",
            title_ar="فئة قديمة",
            image="default.jpeg",
            lft=1,
            rght=2,
            tree_id=1,
            level=0,
        )
        Product.objects.create(
            category=category,
            title="Legacy Product",
            title_en="Legacy Product",
            title_ar="منتج قديم",
            description="Legacy description",
            description_en="Legacy description",
            description_ar="وصف قديم",
            image="default.jpeg",
            default_price="10.00",
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.apps = executor.loader.project_state([self.migrate_to]).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_catalog_is_assigned_to_default_hierarchy(self):
        Brand = self.apps.get_model("store", "Brand")
        Branch = self.apps.get_model("store", "Branch")
        Category = self.apps.get_model("store", "Category")
        Product = self.apps.get_model("store", "Product")

        category = Category.objects.get(title_en="Legacy Category")
        product = Product.objects.get(title_en="Legacy Product")

        self.assertEqual(Brand.objects.get().title_en, "Wasla")
        self.assertEqual(Branch.objects.get().title_en, "Main Branch")
        self.assertEqual(category.branch_id, Branch.objects.get().id)
        self.assertEqual(product.category_id, category.id)


@override_settings(MEDIA_ROOT=Path("/tmp/wasla_test_media"))
class BrandBranchApiTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="+201000000301",
            email="catalog-admin@example.com",
            full_name="Catalog Admin",
            password="NileBridgePass123!",
        )
        self.brand = Brand.objects.create(
            title_en="Luma",
            title_ar="لوما",
        )
        self.branch = Branch.objects.create(
            brand=self.brand,
            title_en="Cairo",
            title_ar="القاهرة",
        )

    def auth_headers(self):
        token = RefreshToken.for_user(self.admin)
        return {"HTTP_AUTHORIZATION": f"Bearer {token.access_token}"}

    def test_public_lists_localize_brand_and_branch_responses(self):
        brand_response = self.client.get(
            reverse("brands-list"),
            HTTP_ACCEPT_LANGUAGE="ar",
        )
        branch_response = self.client.get(
            reverse("branches-list"),
            HTTP_ACCEPT_LANGUAGE="all",
        )

        self.assertEqual(brand_response.status_code, status.HTTP_200_OK)
        brand = next(
            item for item in brand_response.data["data"] if item["id"] == self.brand.id
        )
        self.assertEqual(brand["title"], "لوما")
        self.assertNotIn("title_en", brand)
        self.assertEqual(branch_response.status_code, status.HTTP_200_OK)
        branch = next(
            item
            for item in branch_response.data["data"]
            if item["id"] == self.branch.id
        )
        self.assertEqual(branch["title_en"], "Cairo")
        self.assertEqual(branch["title_ar"], "القاهرة")
        self.assertEqual(branch["brand"]["title_en"], "Luma")
        self.assertEqual(branch["brand"]["title_ar"], "لوما")

    def test_admin_can_create_complete_catalog_hierarchy(self):
        brand_response = self.client.post(
            reverse("brands-list"),
            {"title": "New Brand"},
            **self.auth_headers(),
            format="json",
        )
        branch_response = self.client.post(
            reverse("branches-list"),
            {"brand_id": brand_response.data["data"]["id"], "title": "Giza"},
            **self.auth_headers(),
            format="json",
        )
        category_response = self.client.post(
            reverse("categories-list"),
            {
                "branch_id": branch_response.data["data"]["id"],
                "title": "Hair Care",
                "parent": None,
            },
            **self.auth_headers(),
            format="json",
        )
        product_response = self.client.post(
            reverse("products-list"),
            {
                "category_id": category_response.data["data"]["id"],
                "title": "Hair Oil",
                "description": "Nourishing hair oil",
                "default_price": "200.00",
            },
            **self.auth_headers(),
            format="json",
        )

        self.assertEqual(brand_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(branch_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(category_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(product_response.status_code, status.HTTP_201_CREATED)
        category = product_response.data["data"]["category"]
        self.assertEqual(category["branch"]["title"], "Giza")
        self.assertEqual(category["branch"]["brand"]["title"], "New Brand")

    def test_non_admin_cannot_create_brand_or_branch(self):
        for route, payload in (
            ("brands-list", {"title": "Blocked Brand"}),
            ("branches-list", {"brand_id": self.brand.id, "title": "Blocked"}),
        ):
            with self.subTest(route=route):
                response = self.client.post(reverse(route), payload, format="json")
                self.assertIn(
                    response.status_code,
                    (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
                )

    def test_api_rejects_cross_branch_category_parent(self):
        other_branch = Branch.objects.create(brand=self.brand, title="Alexandria")
        parent = Category.objects.create(branch=self.branch, title="Skin Care")

        response = self.client.post(
            reverse("categories-list"),
            {
                "branch_id": other_branch.id,
                "title": "Face Care",
                "parent": parent.id,
            },
            **self.auth_headers(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("parent", response.data["errors"])

    def test_populated_brand_and_branch_delete_return_conflict(self):
        Category.objects.create(branch=self.branch, title="Skin Care")

        branch_response = self.client.delete(
            reverse("branches-detail", args=[self.branch.id]),
            **self.auth_headers(),
        )
        brand_response = self.client.delete(
            reverse("brands-detail", args=[self.brand.id]),
            **self.auth_headers(),
        )

        self.assertEqual(branch_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(brand_response.status_code, status.HTTP_409_CONFLICT)

    def test_filters_match_titles_in_any_language_and_hierarchy_ids(self):
        category = Category.objects.create(
            branch=self.branch,
            title_en="Skin Care",
            title_ar="العناية بالبشرة",
        )
        product = Product.objects.create(
            category=category,
            title_en="Cleanser",
            title_ar="غسول",
            description_en="Gentle cleanser",
            description_ar="غسول لطيف",
            default_price="100.00",
        )

        cases = (
            ("brands-list", {"title": "لوما"}, self.brand.id),
            ("branches-list", {"brand_title": "لوما"}, self.branch.id),
            ("categories-list", {"branch_title": "القاهرة"}, category.id),
            ("categories-list", {"brand": self.brand.id}, category.id),
            ("products-list", {"brand_title": "لوما"}, product.id),
            ("products-list", {"branch": self.branch.id}, product.id),
        )

        for route, query, expected_id in cases:
            with self.subTest(route=route, query=query):
                response = self.client.get(
                    reverse(route),
                    query,
                    HTTP_ACCEPT_LANGUAGE="en",
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["pagination"]["count"], 1)
                self.assertEqual(response.data["data"][0]["id"], expected_id)
