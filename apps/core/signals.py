from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage

DEFAULT_MEDIA_NAME = "default.jpeg"


def ensure_default_media(**kwargs):
    if default_storage.exists(DEFAULT_MEDIA_NAME):
        return

    source = Path(settings.BASE_DIR) / DEFAULT_MEDIA_NAME
    with source.open("rb") as image:
        default_storage.save(DEFAULT_MEDIA_NAME, File(image, name=DEFAULT_MEDIA_NAME))
