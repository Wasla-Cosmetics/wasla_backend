import importlib.util
import re
import subprocess
import sys
from pathlib import Path

from django.core.management import CommandError, call_command
from django.core.management.commands.startapp import Command as DjangoStartAppCommand
from django.utils.translation import gettext_lazy as _


class Command(DjangoStartAppCommand):
    help = _(
        "Create a Django app, fix its dotted app path, and register it in LOCAL_APPS. "
        "A plain name creates the app at project root. A path creates it at that path. "
        "Examples: startapp orders, startapp apps/orders, startapp orders apps/orders."
    )

    def handle(self, **options):
        app_name, app_dir, app_path = self._resolve_app_target(
            options["name"], options.get("directory")
        )
        self._validate_app_name(app_name)
        self._validate_app_path(app_path)

        apps_file = app_dir / "apps.py"
        if apps_file.exists():
            raise CommandError(_("App already exists: %(path)s") % {"path": app_dir})

        self._ensure_parent_packages(app_dir)
        app_dir.mkdir(parents=True, exist_ok=True)
        super().handle(**{**options, "name": app_name, "directory": str(app_dir)})

        class_name = self._config_class_name(app_name)
        config_path = f"{app_path}.apps.{class_name}"

        self._fix_app_config(apps_file, app_name, app_path)
        self._register_app(config_path)
        self._run_black(app_dir)
        call_command("check")

        self.stdout.write(
            self.style.SUCCESS(
                _("Created and registered app: %(app_path)s") % {"app_path": app_path}
            )
        )

    def _validate_app_name(self, app_name):
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", app_name):
            raise CommandError(
                _("Invalid app name: %(app_name)s. Use a valid Python identifier.")
                % {"app_name": app_name}
            )

    def _resolve_app_target(self, name, directory):
        if directory:
            app_name = name
            app_dir = Path(directory)
        else:
            raw_target = Path(name)
            if len(raw_target.parts) > 1:
                app_dir = raw_target
                app_name = app_dir.name
            else:
                app_name = name
                app_dir = Path(app_name)

        if app_dir.is_absolute() or ".." in app_dir.parts:
            raise CommandError(_("App path must be a relative package path."))

        app_path = ".".join(app_dir.parts)
        return app_name, app_dir, app_path

    def _validate_app_path(self, app_path):
        for part in app_path.split("."):
            self._validate_app_name(part)

    def _ensure_parent_packages(self, app_dir):
        current = Path()
        for part in app_dir.parts[:-1]:
            current = current / part
            current.mkdir(exist_ok=True)
            init_file = current / "__init__.py"
            init_file.touch(exist_ok=True)

    def _config_class_name(self, app_name):
        return "".join(part.capitalize() for part in app_name.split("_")) + "Config"

    def _fix_app_config(self, apps_file, app_name, app_path):
        apps_text = apps_file.read_text()
        apps_text = apps_text.replace(f"name = '{app_name}'", f'name = "{app_path}"')
        apps_text = apps_text.replace(f'name = "{app_name}"', f'name = "{app_path}"')
        apps_file.write_text(apps_text)

    def _register_app(self, config_path):
        settings_file = Path("project/settings/local.py")
        settings_text = settings_file.read_text()
        if config_path in settings_text:
            return

        lines = settings_text.splitlines(keepends=True)
        start_index = self._find_local_apps_start(lines)

        for index in range(start_index + 1, len(lines)):
            if lines[index].strip() == "]":
                lines.insert(index, f'    "{config_path}",\n')
                settings_file.write_text("".join(lines))
                return

        raise CommandError(
            _("Could not find end of LOCAL_APPS in project/settings/local.py")
        )

    def _find_local_apps_start(self, lines):
        for index, line in enumerate(lines):
            if line.startswith("LOCAL_APPS = ["):
                return index
        raise CommandError(_("Could not find LOCAL_APPS in project/settings/local.py"))

    def _run_black(self, app_dir):
        if importlib.util.find_spec("black") is None:
            return
        subprocess.run(
            [sys.executable, "-m", "black", str(app_dir), "project/settings/local.py"],
            check=True,
        )
