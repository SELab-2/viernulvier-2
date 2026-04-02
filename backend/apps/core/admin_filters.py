"""Reusable Django admin list filters used across apps.

This module contains a generic, searchable multi-select filter base class
for Django admin changelists.

Design goals
------------
- Reuse one filter implementation across multiple apps.
- Keep query parameters stable and explicit to avoid Django admin ``?e=1``
    redirects caused by unknown lookup parameters.
- Support multi-select (checkboxes) while preserving selected values between
    requests.
- Provide all UI state the generic template needs (open/closed state,
    clear/reset URLs, hidden passthrough params).

How to create a new filter
--------------------------
1) Subclass :class:`SearchableMultiSelectFilter`.
2) Set ``title`` and ``parameter_name``.
3) Optionally set ``search_param`` if you do not want the default
     ``<parameter_name>_q``.
4) Implement ``get_option_queryset()`` to return a list of ``(value, label)``
     tuples.
5) Implement ``filter_queryset(queryset)`` with your filter logic.

Typical usage in a ModelAdmin:

        list_filter = (
                ...,
                MyCustomFilter,
        )
"""

from django.contrib.admin import SimpleListFilter


class SearchableMultiSelectFilter(SimpleListFilter):
    """Base class for searchable multi-select admin filters.

    The class bridges Django's single-value ``SimpleListFilter`` API with a
    multi-value checkbox UI rendered by ``multiselect_search.html``.

    Request params
    --------------
    - ``parameter_name``: repeated checkbox values (e.g. ``tag=1&tag=2``).
    - ``search_param``: optional text query for narrowing visible options.
    - ``open_param``: remembers collapsed/open state after submit.

    Subclass contract
    -----------------
    - ``get_option_queryset()`` must return iterable ``[(value, label), ...]``.
    - ``filter_queryset(queryset)`` must apply selected values to queryset.
    """

    template = "multiselect_search.html"
    search_param = None
    open_param = None
    search_value = ""
    selected_values = ()
    hidden_params = ()
    clear_search_url = "?"
    reset_url = "?"
    is_open = False

    def __init__(self, request: any, params: dict, model: any, model_admin: any) -> None:
        """Initialize filter state and sanitize custom query params.

        Django's changelist only knows about parameters registered via
        ``expected_parameters()``. Custom params that are not consumed can lead
        to ``IncorrectLookupParameters`` and redirect to ``?e=1``.
        Therefore this initializer explicitly pops the custom search/open
        parameters from ``params`` before delegating to ``SimpleListFilter``.
        """
        current_search_param = self.search_param or f"{self.parameter_name}_q"
        current_open_param = self.open_param or f"{self.parameter_name}_open"
        params.pop(current_search_param, None)
        params.pop(current_open_param, None)
        super().__init__(request, params, model, model_admin)
        self.request = request
        self.search_param = current_search_param
        self.open_param = current_open_param
        self.search_value = request.GET.get(self.search_param, "").strip()
        self.selected_values = request.GET.getlist(self.parameter_name)
        self.is_open = request.GET.get(self.open_param) == "1" or bool(self.search_value) or bool(self.selected_values)

        self.hidden_params = [
            {"key": key, "val": value}
            for key, values in request.GET.lists()
            if key not in {self.parameter_name, self.search_param, self.open_param, "e"}
            for value in values
        ]

        qs_without_search = request.GET.copy()
        qs_without_search.pop(self.search_param, None)
        qs_without_search.pop(self.open_param, None)
        qs_without_search.pop("e", None)
        self.clear_search_url = f"?{qs_without_search.urlencode()}" if qs_without_search else "?"

        qs_without_self = request.GET.copy()
        qs_without_self.pop(self.search_param, None)
        qs_without_self.pop(self.parameter_name, None)
        qs_without_self.pop(self.open_param, None)
        qs_without_self.pop("e", None)
        self.reset_url = f"?{qs_without_self.urlencode()}" if qs_without_self else "?"

    def value(self) -> tuple[str, ...]:
        """Return selected values as list, compatible with template usage."""
        return self.selected_values

    def expected_parameters(self) -> list[str]:
        """Declare all query params this filter owns."""
        return [self.parameter_name, self.search_param, self.open_param]

    def get_option_queryset(self) -> list[tuple[str, str]]:
        """Return list of selectable options as ``[(value, label), ...]``."""
        raise NotImplementedError

    def filter_queryset(self, _queryset: any) -> any:
        """Apply selected values to the provided queryset."""
        raise NotImplementedError

    def lookups(self, _request: any, _model_admin: any) -> list[tuple[str, str]]:
        """Django hook: supply choices for the sidebar UI."""
        return self.get_option_queryset()

    def queryset(self, _request: any, queryset: any) -> any:
        """Django hook: return filtered queryset when values are selected."""
        if self.selected_values:
            return self.filter_queryset(queryset)
        return queryset
