from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    name = "apps.core"

    def ready(self):
        from apps.core.signals import ensure_default_media

        post_migrate.connect(
            ensure_default_media,
            sender=self,
            dispatch_uid="apps.core.ensure_default_media",
        )
