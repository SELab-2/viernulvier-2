"""Pagination classes for the viernulvier_archive API.

Three preset classes cover the full range of response sizes. Select the
right one per viewset via ``pagination_class``, or rely on the project
default (``StandardResultsSetPagination``) configured in
``settings.REST_FRAMEWORK``.

    Small    - lookups, dropdowns, short reference lists  (max 50)
    Standard - default for most resources                 (max 100)
    Large    - bulk exports, import logs                  (max 500)

Clients control the page size via ``?page_size=N``, capped at the class
maximum to prevent runaway queries.
"""

from rest_framework.pagination import PageNumberPagination


class SmallResultsSetPagination(PageNumberPagination):
    """For short reference lists such as languages, price ranks, or tags."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class StandardResultsSetPagination(PageNumberPagination):
    """Default pagination for most API resources."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """For bulk or export-oriented endpoints such as import logs."""

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500
