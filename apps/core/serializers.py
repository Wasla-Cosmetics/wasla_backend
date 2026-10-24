from modeltranslation.translator import translator
from modeltranslation.utils import get_translation_fields
from rest_framework import serializers


class AllLanguagesModelSerializer(serializers.ModelSerializer):
    all_languages_header_value = "all"

    def get_field_names(self, declared_fields, model_info):
        field_names = list(super().get_field_names(declared_fields, model_info))
        if not self._should_include_all_languages():
            return field_names

        translation_options = translator.get_options_for_model(self.Meta.model)
        for field_name in get_translation_fields(*translation_options.fields):
            if field_name not in field_names:
                field_names.append(field_name)

        return field_names

    def _should_include_all_languages(self):
        if self.context.get("include_all_languages"):
            return True

        request = self.context.get("request")
        view = self.context.get("view")
        if request is None or getattr(view, "action", None) != "list":
            return False

        accept_language = request.headers.get("Accept-Language", "")
        return accept_language.strip().lower() == self.all_languages_header_value
