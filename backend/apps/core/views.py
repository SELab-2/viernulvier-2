"""
Base ViewSet classes for the core app.

All app-level ViewSets inherit from one of the two classes defined here:

- :class:`ApiModelViewSet`    - full CRUD, access gated by key scope.
- :class:`ApiReadOnlyViewSet` - list + retrieve only, no write routes registered.

Both classes wire up :class:`~apps.core.authentications.ApiKeyAuthentication`
and :class:`~apps.core.permissions.ApiKeyPermission` as their authentication
and permission classes. These are also set as the global DRF defaults in
``settings/base.py``, but specifying them explicitly here provides a clear
in-code contract and makes the classes self-contained when read in isolation.

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

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .authentications import ApiKeyAuthentication
from .permissions import ApiKeyPermission


class ApiModelViewSet(ModelViewSet):
    """
    Base ViewSet for full CRUD operations.

    Registers all standard DRF routes:
    ``list``, ``create``, ``retrieve``, ``update``, ``partial_update``,
    and ``destroy``.

    Access control is enforced by :class:`~apps.core.permissions.ApiKeyPermission`:

    - **Internal key** -> all routes are accessible.
    - **Public key**   -> only ``list`` and ``retrieve`` (safe methods).
    - **No valid key** -> ``HTTP 401`` from the authenticator or ``HTTP 403``
      from the permission class.

    Subclasses must define ``serializer_class`` and ``queryset``. Use
    ``select_related`` and ``prefetch_related`` on the queryset to avoid
    N+1 queries on list responses.
    """

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [ApiKeyPermission]


class ApiReadOnlyViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    Base ViewSet for read-only access.

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

    Subclasses must define ``serializer_class`` and ``queryset``.
    """

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [ApiKeyPermission]
