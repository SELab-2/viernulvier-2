from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.core.ordering import NullsLastOrderingFilter


class TestNullsLastOrderingFilter(SimpleTestCase):
    def setUp(self) -> None:
        self.filter = NullsLastOrderingFilter()
        self.request = MagicMock()
        self.view = MagicMock()

    def test_filter_queryset_returns_original_queryset_when_no_ordering(self) -> None:
        queryset = MagicMock()
        self.filter.get_ordering = MagicMock(return_value=None)

        result = self.filter.filter_queryset(self.request, queryset, self.view)

        assert result is queryset
        queryset.order_by.assert_not_called()

    def test_filter_queryset_applies_nulls_last_for_ascending_and_descending(self) -> None:
        queryset = MagicMock()
        ordered_queryset = MagicMock()
        queryset.order_by.return_value = ordered_queryset
        self.filter.get_ordering = MagicMock(return_value=["title_sort", "-published_at"])

        result = self.filter.filter_queryset(self.request, queryset, self.view)

        assert result is ordered_queryset
        queryset.order_by.assert_called_once()
