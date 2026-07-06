from apps.authentication.tokens import (
    get_anonymous_token,
    get_anonymous_user,
    get_authenticated_user,
    get_bearer_token,
)


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
