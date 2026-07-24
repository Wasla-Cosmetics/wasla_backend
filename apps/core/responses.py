from collections.abc import Mapping

from django.utils.translation import gettext as _
from rest_framework import status

EMPTY_VALUES = (None, "", [], {})
ENVELOPE_KEYS = {"status", "message", "data"}
PAGINATION_KEYS = {"count", "next", "previous", "results"}


def build_response(status_code, message=None, data=None, errors=None, pagination=None):
    return {
        "status": status_code,
        "message": message or default_message(status_code),
        "data": data if data is not None else {},
        "errors": errors if errors is not None else {},
        "pagination": pagination,
    }


def default_message(status_code):
    if status_code < status.HTTP_400_BAD_REQUEST:
        return _("Success")
    return _("Error")


def is_enveloped(data):
    return isinstance(data, Mapping) and ENVELOPE_KEYS.issubset(data.keys())


def is_paginated(data):
    return isinstance(data, Mapping) and PAGINATION_KEYS.issubset(data.keys())


def normalize_response_payload(data, status_code):
    if is_enveloped(data):
        return {
            "status": data.get("status", status_code),
            "message": data.get("message") or default_message(status_code),
            "data": data.get("data", {}),
            "errors": data.get("errors", {}),
            "pagination": data.get("pagination"),
        }

    if status_code >= status.HTTP_400_BAD_REQUEST:
        message, errors = extract_error_payload(data, status_code)
        return build_response(
            status_code=status_code,
            message=message,
            data={},
            errors=errors,
        )

    if is_paginated(data):
        return build_response(
            status_code=status_code,
            data=data["results"],
            pagination={
                "count": data["count"],
                "next": data["next"],
                "previous": data["previous"],
            },
        )

    return build_response(status_code=status_code, data=data)


def extract_error_payload(data, status_code):
    if isinstance(data, Mapping) and "detail" in data:
        return str(data["detail"]), {}

    if data in EMPTY_VALUES:
        return default_message(status_code), {}

    if not isinstance(data, Mapping):
        return str(data), {}

    return validation_error_message(status_code), data


def validation_error_message(status_code):
    if status_code == status.HTTP_400_BAD_REQUEST:
        return _("Validation error")
    return default_message(status_code)
