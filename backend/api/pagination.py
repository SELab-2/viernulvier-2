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

    # Default number of items per page for small datasets
    page_size = 10
    # Allow clients to set page size via query parameter
    page_size_query_param = "page_size"
    # Maximum number of items per page to prevent abuse
    max_page_size = 50


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for API responses.
    """

    # Default number of items per page
    page_size = 20
    # Allow clients to set page size via query parameter
    page_size_query_param = "page_size"
    # Maximum number of items per page to prevent abuse
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination class for endpoints that return large datasets.
    """

    # Default number of items per page for large datasets
    page_size = 100
    # Allow clients to set page size via query parameter
    page_size_query_param = "page_size"
    # Maximum number of items per page to prevent abuse
    max_page_size = 500
