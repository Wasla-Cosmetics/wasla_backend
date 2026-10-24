from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase, override_settings

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
