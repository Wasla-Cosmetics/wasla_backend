from collections.abc import Mapping
from rest_framework.views import exception_handler
from rest_framework import status


def flatten_errors(errors):
    if isinstance(errors, list):
        if not errors:
            return errors
        return flatten_errors(errors[0])

    if not isinstance(errors, Mapping):
        return errors

    flattened = {}

    for key, value in errors.items():
        if isinstance(value, Mapping):
            flattened[key] = flatten_errors(value)
        elif isinstance(value, list):
            flattened[key] = flatten_errors(value[0])
        else:
            flattened[key] = value

    return flattened


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response and response.status_code == status.HTTP_400_BAD_REQUEST:
        response.data = flatten_errors(response.data)

    return response
