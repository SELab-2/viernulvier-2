"""Base ViewSet classes for the core app.

All app-level ViewSets inherit from one of the two classes defined here:

- :class:`ApiModelViewSet`    - full CRUD, access gated by key scope.
- :class:`ApiReadOnlyViewSet` - list + retrieve only, no write routes registered.

Both classes wire up :class:`~apps.core.authentications.ApiKeyAuthentication`
and :class:`~apps.core.permissions.ApiKeyPermission` as their authentication
and permission classes. These are also set as the global DRF defaults in
``settings/base.py``, but specifying them explicitly here provides a clear
in-code contract and makes the classes self-contained when read in isolation.

Both classes also apply :class:`~apps.core.ordering.NullsLastOrderingFilter`
as their ordering backend, which ensures that items without a value for the
sorted field (e.g. no title translation, no event date) always appear last,
regardless of whether the sort direction is ascending or descending.

Read endpoints are cached for a short period. The cache is applied only to
``list`` and ``retrieve`` handlers, so write routes are never cached.

Access matrix
-------------
+------------------+---------------------+---------------------+
| ``request.auth`` | ApiModelViewSet     | ApiReadOnlyViewSet  |
+==================+=====================+=====================+
| ``"internal"``   | Full CRUD           | List + Retrieve     |
+------------------+---------------------+---------------------+
| ``"public"``     | List + Retrieve     | List + Retrieve     |
+------------------+---------------------+---------------------+
| ``None`` / other | 401 / 403           | 401 / 403           |
+------------------+---------------------+---------------------+
"""

from collections.abc import Callable
from typing import Any

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.core.ordering import NullsLastOrderingFilter

from .authentications import ApiKeyAuthentication
from .permissions import ApiKeyPermission

CACHE_TTL_API = 60 * 15
API_CACHE_KEY_PREFIX = "api"
API_CACHE_VARY_HEADERS = ("Accept-Language",)


def cache_api_view(timeout: int = CACHE_TTL_API) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache an API handler while keeping language-aware responses separate.

    Django's ``cache_page`` caches per URL, including query parameters. The
    additional ``Vary: Accept-Language`` ensures endpoints with language-aware
    ordering/search annotations do not reuse a response generated for another
    preferred language.
    """

    def decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
        return cache_page(timeout, key_prefix=API_CACHE_KEY_PREFIX)(vary_on_headers(*API_CACHE_VARY_HEADERS)(view_func))

    return decorator


@method_decorator(cache_api_view(), name="list")
@method_decorator(cache_api_view(), name="retrieve")
class ApiModelViewSet(ModelViewSet):
    """Base ViewSet for full CRUD operations.

    Registers all standard DRF routes:
    ``list``, ``create``, ``retrieve``, ``update``, ``partial_update``,
    and ``destroy``.

    Access control is enforced by :class:`~apps.core.permissions.ApiKeyPermission`:

    - **Internal key** -> all routes are accessible.
    - **Public key**   -> only ``list`` and ``retrieve`` (safe methods).
    - **No valid key** -> ``HTTP 401`` from the authenticator or ``HTTP 403``
      from the permission class.

    Ordering is handled by :class:`~apps.core.NullsLastOrderingFilter`
    instead of DRF's default ``OrderingFilter``. The behaviour is identical
    except that NULL values (e.g. items without a title translation or without
    an event date) are always sorted last, regardless of sort direction.

    Subclasses must define ``serializer_class`` and ``queryset``. Use
    ``select_related`` and ``prefetch_related`` on the queryset to avoid
    N+1 queries on list responses.
    """

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [ApiKeyPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, NullsLastOrderingFilter]


@method_decorator(cache_api_view(), name="list")
@method_decorator(cache_api_view(), name="retrieve")
class ApiReadOnlyViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Base ViewSet for read-only access.

    Only the ``list`` and ``retrieve`` routes are registered - write
    routes (``create``, ``update``, ``partial_update``, ``destroy``) are
    excluded at the class level by not including the corresponding DRF
    mixins. This means they return ``HTTP 405 Method Not Allowed`` even
    for internal keys, not just ``HTTP 403``.

    Use this base class for resources that must never be mutated via the
    API regardless of key scope, such as audit logs, computed statistics,
    or external reference data. The architectural exclusion makes the intent
    explicit and prevents accidental registration of write routes in the
    URL router.

    Ordering is handled by :class:`~apps.core.NullsLastOrderingFilter`
    instead of DRF's default ``OrderingFilter``. The behaviour is identical
    except that NULL values (e.g. items without a title translation or without
    an event date) are always sorted last, regardless of sort direction.

    Subclasses must define ``serializer_class`` and ``queryset``.
    """

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [ApiKeyPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, NullsLastOrderingFilter]
