from math import ceil

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

from apps.core.responses import build_response


class StandardPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        page_size = self.get_page_size(self.request)

        return Response(
            build_response(
                status_code=status.HTTP_200_OK,
                data=data,
                pagination={
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "page": self.page.number,
                    "page_size": page_size,
                    "total_pages": ceil(self.page.paginator.count / page_size),
                },
            )
        )
