import ast
from datetime import timedelta
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.authentication.models import GuestUser, User
from apps.core.signals import ensure_default_media
from apps.store.models import (
    Ad,
    Brand,
    Branch,
    Category,
    Product,
    ProductImage,
    ProductReview,
)


class SeedDataCommandTests(TestCase):
    def test_seeds_all_domain_models_with_valid_relationships(self):
        output = StringIO()

        with patch.dict(os.environ, {"ENV": "local"}):
            call_command("seed_data", stdout=output)

        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(GuestUser.objects.count(), 1)
        self.assertEqual(Ad.objects.count(), 2)
        self.assertEqual(Brand.objects.count(), 1)
        self.assertEqual(Branch.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 6)
        self.assertEqual(Product.objects.count(), 6)
        self.assertEqual(ProductImage.objects.count(), 12)
        self.assertEqual(ProductReview.objects.count(), 6)
        self.assertTrue(User.objects.filter(is_superuser=True, is_staff=True).exists())
        self.assertTrue(Category.objects.filter(parent__isnull=False).exists())
        self.assertFalse(Category.objects.filter(branch__isnull=True).exists())
        self.assertFalse(
            Product.objects.filter(category__branch__brand__isnull=True).exists()
        )
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

    def test_refreshes_expired_seed_guest_session(self):
        guest = GuestUser.objects.create(
            session_key="seed-guest-session",
            expires_at=timezone.now() - timedelta(days=1),
        )

        with patch.dict(os.environ, {"ENV": "local"}):
            call_command("seed_data", stdout=StringIO())

        guest.refresh_from_db()
        self.assertGreater(guest.expires_at, timezone.now())

    def test_does_not_write_custom_password_to_command_output(self):
        output = StringIO()
        custom_password = "PrivateSeedPassword123!"

        with patch.dict(os.environ, {"ENV": "local"}):
            call_command("seed_data", password=custom_password, stdout=output)

        self.assertNotIn(custom_password, output.getvalue())

    def test_keeps_same_named_categories_in_other_branches(self):
        other_brand = Brand.objects.create(title_en="Other Brand")
        other_branch = Branch.objects.create(
            brand=other_brand,
            title_en="Other Branch",
        )
        other_category = Category.objects.create(
            branch=other_branch,
            title_en="Skincare",
        )

        with patch.dict(os.environ, {"ENV": "local"}):
            call_command("seed_data", stdout=StringIO())

        other_category.refresh_from_db()
        self.assertEqual(other_category.branch, other_branch)
        self.assertTrue(
            Category.objects.filter(
                branch__brand__title_en="Wasla",
                branch__title_en="Main Branch",
                title_en="Skincare",
            ).exists()
        )

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
                Brand,
                Branch,
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


class HealthCheckTests(TestCase):
    def test_returns_service_unavailable_when_database_is_unreachable(self):
        with patch(
            "django.db.backends.utils.CursorWrapper.execute",
            side_effect=OperationalError("database unavailable"),
        ):
            response = self.client.get("/health/")

        self.assertEqual(response.status_code, 503)


class DeploymentConfigurationTests(SimpleTestCase):
    def test_default_host_ports_do_not_overlap_between_environments(self):
        project_root = Path(__file__).resolve().parents[2]
        workflow = (project_root / ".github/workflows/deploy.yaml").read_text()

        expected_defaults = (
            'django_port="${DEV_DJANGO_PORT:-8000}"',
            'django_port="${STAGE_DJANGO_PORT:-8001}"',
            'django_port="${MASTER_DJANGO_PORT:-8002}"',
            'postgres_host_port="${DEV_POSTGRES_HOST_PORT:-5432}"',
            'postgres_host_port="${STAGE_POSTGRES_HOST_PORT:-5433}"',
            'postgres_host_port="${MASTER_POSTGRES_HOST_PORT:-5434}"',
        )

        for expected_default in expected_defaults:
            with self.subTest(expected_default=expected_default):
                self.assertIn(expected_default, workflow)

    def test_local_environment_template_does_not_override_deployed_security_defaults(
        self,
    ):
        project_root = Path(__file__).resolve().parents[2]
        environment_template = (project_root / ".env.example").read_text()

        for setting_name in (
            "SECURE_SSL_REDIRECT",
            "SECURE_HSTS_SECONDS",
            "SECURE_HSTS_INCLUDE_SUBDOMAINS",
            "SECURE_HSTS_PRELOAD",
        ):
            with self.subTest(setting_name=setting_name):
                self.assertNotIn(f"{setting_name}=", environment_template)


class SettingsSelectionTests(SimpleTestCase):
    @staticmethod
    def import_settings(**overrides):
        project_root = Path(__file__).resolve().parents[2]
        environment = {
            **os.environ,
            "DATABASE_TYPE": "sqlite3",
            "SQLITE_NAME": ":memory:",
            **overrides,
        }
        return subprocess.run(
            [sys.executable, "-c", "import project.settings"],
            cwd=project_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_unknown_environment_fails_closed(self):
        result = self.import_settings(ENV="prodution")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ENV must be one of", result.stderr)

    def test_deployed_email_otp_requires_real_smtp_backend(self):
        result = self.import_settings(
            ENV="production",
            SECRET_KEY="production-secret-key-with-more-than-fifty-characters-12345",
            ALLOWED_HOSTS="api.example.com",
            TRUSTED_PROXY_COUNT="1",
            AUTH_OTP_DELIVERY_BACKEND=(
                "apps.authentication.otp.EmailOtpDeliveryBackend"
            ),
            EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
            EMAIL_HOST="smtp.example.com",
            EMAIL_HOST_USER="smtp-user",
            EMAIL_HOST_PASSWORD="smtp-password",
            EMAIL_USE_TLS="True",
            EMAIL_USE_SSL="False",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SMTP email backend", result.stderr)

    def test_deployed_email_otp_accepts_complete_smtp_configuration(self):
        result = self.import_settings(
            ENV="production",
            SECRET_KEY="production-secret-key-with-more-than-fifty-characters-12345",
            ALLOWED_HOSTS="api.example.com",
            TRUSTED_PROXY_COUNT="1",
            AUTH_OTP_DELIVERY_BACKEND=(
                "apps.authentication.otp.EmailOtpDeliveryBackend"
            ),
            EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
            EMAIL_HOST="smtp.example.com",
            EMAIL_HOST_USER="smtp-user",
            EMAIL_HOST_PASSWORD="smtp-password",
            EMAIL_USE_TLS="True",
            EMAIL_USE_SSL="False",
            DEFAULT_FROM_EMAIL="otp@example.com",
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_deployed_email_otp_requires_configured_sender_address(self):
        result = self.import_settings(
            ENV="production",
            SECRET_KEY="production-secret-key-with-more-than-fifty-characters-12345",
            ALLOWED_HOSTS="api.example.com",
            TRUSTED_PROXY_COUNT="1",
            AUTH_OTP_DELIVERY_BACKEND=(
                "apps.authentication.otp.EmailOtpDeliveryBackend"
            ),
            EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
            EMAIL_HOST="smtp.example.com",
            EMAIL_HOST_USER="smtp-user",
            EMAIL_HOST_PASSWORD="smtp-password",
            EMAIL_USE_TLS="True",
            EMAIL_USE_SSL="False",
            DEFAULT_FROM_EMAIL="no-reply@wasla.local",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DEFAULT_FROM_EMAIL", result.stderr)

    def test_deployed_settings_reject_unsupported_otp_backend(self):
        result = self.import_settings(
            ENV="production",
            SECRET_KEY="production-secret-key-with-more-than-fifty-characters-12345",
            ALLOWED_HOSTS="api.example.com",
            TRUSTED_PROXY_COUNT="1",
            AUTH_OTP_DELIVERY_BACKEND="custom.otp.Backend",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("supported OTP delivery backend", result.stderr)


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
