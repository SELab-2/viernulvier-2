"""
This module defines custom pagination classes for the API endpoints.
Each class inherits from Django REST Framework's PageNumberPagination and sets
specific defaults for page size and maximum page size to suit different types
of datasets (small, standard, large). These pagination classes can be used in
views to control how results are paginated when returned to clients.
"""

from rest_framework.pagination import PageNumberPagination


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination class for endpoints that return small datasets.
    """

    page_size = 10  # Default number of items per page for small datasets
    page_size_query_param = (
        "page_size"  # Allow clients to set page size via query parameter
    )
    max_page_size = 50  # Maximum number of items per page to prevent abuse


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for API responses.
    """

    page_size = 20  # Default number of items per page
    page_size_query_param = (
        "page_size"  # Allow clients to set page size via query parameter
    )
    max_page_size = 100  # Maximum number of items per page to prevent abuse


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination class for endpoints that return large datasets.
    """

    page_size = 100  # Default number of items per page for large datasets
    page_size_query_param = (
        "page_size"  # Allow clients to set page size via query parameter
    )
    max_page_size = 500  # Maximum number of items per page to prevent abuse
