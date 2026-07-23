from rest_framework.pagination import PageNumberPagination


class OptionalPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100
    is_paginated_query_param = "is_paginated"
    disabled_values = {"0", "false", "no", "off"}

    def paginate_queryset(self, queryset, request, view=None):
        is_paginated = request.query_params.get(self.is_paginated_query_param)

        if is_paginated is not None and is_paginated.lower() in self.disabled_values:
            return None

        return super().paginate_queryset(queryset, request, view)
