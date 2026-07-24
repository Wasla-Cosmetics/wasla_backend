from rest_framework.response import Response

from apps.authentication.tokens import (
    get_anonymous_token,
    get_anonymous_user,
    get_authenticated_user,
    get_bearer_token,
)
from apps.core.responses import normalize_response_payload


class TokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_token = get_bearer_token(request)
        auth_user = get_authenticated_user(auth_token)

        if auth_token and not auth_user:
            return self.get_response(request)

        anon_token = None if auth_user else get_anonymous_token(request)
        anon_user = get_anonymous_user(anon_token)

        if auth_user:
            request.user = auth_user
        elif anon_user:
            request.user = anon_user

        return self.get_response(request)


class UnifiedAPIResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_template_response(self, request, response):
        self.wrap_response(response)
        return response

    def wrap_response(self, response):
        if isinstance(response, Response) and not response.is_rendered:
            response.data = normalize_response_payload(
                response.data,
                response.status_code,
            )
