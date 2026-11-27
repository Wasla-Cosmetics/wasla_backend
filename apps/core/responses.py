from collections.abc import Mapping
from typing import Any

from django.utils.translation import gettext as _
from rest_framework import status

EMPTY_VALUES: tuple[object, ...] = (None, "", [], {})
ENVELOPE_KEYS = {"status", "message", "data"}


def build_response(
    status_code: int,
    message: object | None = None,
    data: Any = None,
    errors: Any = None,
    pagination: Any = None,
) -> dict[str, Any]:
    return {
        "status": status_code,
        "message": message or default_message(status_code),
        "data": data if data is not None else {},
        "errors": errors if errors is not None else {},
        "pagination": pagination,
    }


def default_message(status_code: int) -> str:
    if status_code < status.HTTP_400_BAD_REQUEST:
        return _("Success")
    return _("Error")


def is_enveloped(data: object) -> bool:
    return isinstance(data, Mapping) and ENVELOPE_KEYS.issubset(data.keys())


def normalize_response_payload(data: Any, status_code: int) -> dict[str, Any]:
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

    return build_response(status_code=status_code, data=data)


def extract_error_payload(data: Any, status_code: int) -> tuple[object, Any]:
    if isinstance(data, Mapping) and "detail" in data:
        return str(data["detail"]), {}

    if data in EMPTY_VALUES:
        return default_message(status_code), {}

    if not isinstance(data, Mapping):
        return str(data), {}

    return validation_error_message(status_code), data


def validation_error_message(status_code: int) -> str:
    if status_code == status.HTTP_400_BAD_REQUEST:
        return _("Validation error")
    return default_message(status_code)
