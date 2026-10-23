from modeltranslation import settings as modeltranslation_settings
from modeltranslation.utils import build_localized_fieldname


def get_localized_field_names(*field_paths):
    """Return concrete translated field names, including related field paths."""
    localized_fields = []

    for field_path in field_paths:
        *relations, field_name = field_path.split("__")
        for language in modeltranslation_settings.AVAILABLE_LANGUAGES:
            localized_field_name = build_localized_fieldname(field_name, language)
            localized_fields.append("__".join((*relations, localized_field_name)))

    return tuple(localized_fields)
