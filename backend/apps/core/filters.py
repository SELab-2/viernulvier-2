"""
Base filter classes for the core app.

``BaseModelFilter`` is the shared abstract FilterSet that every app-level
FilterSet should inherit from. It provides filtering on the ``external_id``
field, which is present on every model that inherits from
:class:`~apps.core.models.BaseModel`.

Convention
----------
All app-level FilterSets follow the same pattern::

    class MyModelFilter(BaseModelFilter):
        ...

        class Meta:
            model = MyModel
            fields = [..., "external_id"]
"""

import django_filters


class BaseModelFilter(django_filters.FilterSet):
    """
    Abstract base FilterSet for all models that inherit from ``BaseModel``.

    Provides filtering on the ``external_id`` field that is present on every
    model in the project. App-level FilterSets inherit from this class and
    extend it with model-specific filters.

    Supported query parameters
    --------------------------
    ``external_id``
        Case-insensitive exact match on the external identifier
        (e.g. ``?external_id=abc-123``).
    """

    external_id = django_filters.CharFilter(lookup_expr="iexact")