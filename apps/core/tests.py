import ast
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings

from apps.core.signals import ensure_default_media


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
