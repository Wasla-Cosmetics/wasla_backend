from rest_framework.response import Response

from apps.core.responses import normalize_response_payload


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
