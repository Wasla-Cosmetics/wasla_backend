import ast
from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, override_settings

from apps.authentication.models import GuestUser, User
from apps.core.signals import ensure_default_media
from apps.store.models import Ad, Category, Product, ProductImage, ProductReview


class SeedDataCommandTests(TestCase):
    def test_seeds_all_domain_models_with_valid_relationships(self):
        output = StringIO()

        with patch.dict(os.environ, {"ENV": "local"}):
            call_command("seed_data", stdout=output)

        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(GuestUser.objects.count(), 1)
        self.assertEqual(Ad.objects.count(), 2)
        self.assertEqual(Category.objects.count(), 6)
        self.assertEqual(Product.objects.count(), 6)
        self.assertEqual(ProductImage.objects.count(), 12)
        self.assertEqual(ProductReview.objects.count(), 6)
        self.assertTrue(User.objects.filter(is_superuser=True, is_staff=True).exists())
        self.assertTrue(Category.objects.filter(parent__isnull=False).exists())
        self.assertTrue(Product.objects.filter(compare_at_price__isnull=False).exists())
        self.assertFalse(Product.objects.filter(title_en__isnull=True).exists())
        self.assertFalse(Product.objects.filter(title_ar__isnull=True).exists())
        self.assertFalse(Product.objects.filter(description_en__isnull=True).exists())
        self.assertFalse(Product.objects.filter(description_ar__isnull=True).exists())
        self.assertTrue(
            all(product.images.count() == 2 for product in Product.objects.all())
        )
        self.assertTrue(
            all(product.reviews.count() == 1 for product in Product.objects.all())
        )
        self.assertIn("Seed data ready", output.getvalue())

    def test_is_idempotent(self):
        with patch.dict(os.environ, {"ENV": "development"}):
            call_command("seed_data", stdout=StringIO())
            first_counts = self._domain_model_counts()
            call_command("seed_data", stdout=StringIO())

        self.assertEqual(self._domain_model_counts(), first_counts)

    def test_refuses_to_seed_staging_or_production(self):
        for environment in ("staging", "production"):
            with self.subTest(environment=environment), patch.dict(
                os.environ, {"ENV": environment}
            ):
                with self.assertRaisesMessage(
                    CommandError,
                    "seed_data can run only in local or development environments.",
                ):
                    call_command("seed_data", stdout=StringIO())

    @staticmethod
    def _domain_model_counts():
        return {
            model: model.objects.count()
            for model in (
                User,
                GuestUser,
                Ad,
                Category,
                Product,
                ProductImage,
                ProductReview,
            )
        }


class DefaultMediaTests(SimpleTestCase):
    def test_default_media_is_initialized_when_missing(self):
        with TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root
        ):
            ensure_default_media()

            installed_image = Path(media_root) / "default.jpeg"
            source_image = Path(__file__).resolve().parents[2] / "default.jpeg"
            self.assertTrue(installed_image.exists())
            self.assertEqual(installed_image.read_bytes(), source_image.read_bytes())

    def test_existing_default_media_is_not_overwritten(self):
        with TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root
        ):
            installed_image = Path(media_root) / "default.jpeg"
            installed_image.write_bytes(b"custom image")

            ensure_default_media()

            self.assertEqual(installed_image.read_bytes(), b"custom image")


class ArabicCatalogTests(SimpleTestCase):
    def test_every_python_message_has_an_arabic_translation(self):
        project_root = Path(__file__).resolve().parents[2]
        source_messages = set()

        for source_root in (project_root / "apps", project_root / "project"):
            for path in source_root.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "_"
                        and node.args
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)
                    ):
                        source_messages.add(node.args[0].value)

        catalog = self._read_catalog(
            project_root / "locale" / "ar" / "LC_MESSAGES" / "django.po"
        )
        missing = sorted(
            message for message in source_messages if not catalog.get(message)
        )

        self.assertEqual(missing, [], f"Missing Arabic translations: {missing}")

    @staticmethod
    def _read_catalog(path):
        lines = path.read_text(encoding="utf-8").splitlines()
        catalog = {}
        index = 0

        while index < len(lines):
            if not lines[index].startswith("msgid "):
                index += 1
                continue

            msgid_parts = [lines[index][6:]]
            index += 1
            while index < len(lines) and lines[index].startswith('"'):
                msgid_parts.append(lines[index])
                index += 1

            if index >= len(lines) or not lines[index].startswith("msgstr "):
                continue

            msgstr_parts = [lines[index][7:]]
            index += 1
            while index < len(lines) and lines[index].startswith('"'):
                msgstr_parts.append(lines[index])
                index += 1

            msgid = "".join(ast.literal_eval(part) for part in msgid_parts)
            msgstr = "".join(ast.literal_eval(part) for part in msgstr_parts)
            if msgid:
                catalog[msgid] = msgstr

        return catalog
