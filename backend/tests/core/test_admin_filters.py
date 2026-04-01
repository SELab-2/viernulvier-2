from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
import pytest

from apps.core.admin import BaseAdmin
from apps.core.admin_filters import SearchableMultiSelectFilter
from apps.languages.models import Language
from tests.factories.language import LanguageFactory


class DummyLanguageCodeFilter(SearchableMultiSelectFilter):
    title = "Language code"
    parameter_name = "code"

    def get_option_queryset(self):
        queryset = Language.objects.order_by("code")
        if self.search_value:
            queryset = queryset.filter(code__icontains=self.search_value)
        return [(language.code, language.code.upper()) for language in queryset]

    def filter_queryset(self, queryset):
        return queryset.filter(code__in=self.selected_values)


class TestSearchableMultiSelectFilter(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.model_admin = BaseAdmin(User, admin.site)
        LanguageFactory(code="nl", name="Dutch")
        LanguageFactory(code="en", name="English")

    def _build_filter(self, query_string):
        request = self.factory.get(f"/admin/languages/language/?{query_string}")
        params = request.GET.copy()
        return DummyLanguageCodeFilter(request, params, Language, self.model_admin), params

    def test_expected_parameters_include_value_search_and_open(self) -> None:
        filter_instance, _ = self._build_filter("")
        assert filter_instance.expected_parameters() == ["code", "code_q", "code_open"]

    def test_init_pops_custom_search_and_open_params_from_admin_params(self) -> None:
        filter_instance, params = self._build_filter("code_q=n&code_open=1&code=nl")
        assert filter_instance.search_param not in params
        assert filter_instance.open_param not in params
        assert "code" not in params

    def test_hidden_params_keep_non_filter_query_args(self) -> None:
        filter_instance, _ = self._build_filter("code=nl&o=1&p=2")
        assert filter_instance.hidden_params == [{"key": "o", "val": "1"}, {"key": "p", "val": "2"}]

    def test_clear_search_url_removes_only_search_state(self) -> None:
        filter_instance, _ = self._build_filter("code=nl&code_q=nl&code_open=1&o=3")
        assert filter_instance.clear_search_url == "?code=nl&o=3"

    def test_reset_url_removes_filter_selection_and_search_state(self) -> None:
        filter_instance, _ = self._build_filter("code=nl&code_q=nl&code_open=1&o=3")
        assert filter_instance.reset_url == "?o=3"

    def test_queryset_applies_selected_values(self) -> None:
        filter_instance, _ = self._build_filter("code=nl")
        queryset = filter_instance.queryset(filter_instance.request, Language.objects.order_by("code"))
        assert list(queryset.values_list("code", flat=True)) == ["nl"]

    def test_queryset_returns_unfiltered_when_nothing_selected(self) -> None:
        filter_instance, _ = self._build_filter("")
        queryset = filter_instance.queryset(filter_instance.request, Language.objects.order_by("code"))
        assert list(queryset.values_list("code", flat=True)) == ["en", "nl"]

    def test_lookups_applies_search_branch(self) -> None:
        filter_instance, _ = self._build_filter("code_q=n")
        lookups = filter_instance.lookups(filter_instance.request, self.model_admin)
        assert lookups == [("en", "EN"), ("nl", "NL")]

    def test_value_returns_selected_values_list(self) -> None:
        filter_instance, _ = self._build_filter("code=nl&code=en")
        assert filter_instance.value() == ["nl", "en"]

    def test_base_get_option_queryset_raises_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError):
            SearchableMultiSelectFilter.get_option_queryset(object())

    def test_base_filter_queryset_raises_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError):
            SearchableMultiSelectFilter.filter_queryset(object(), Language.objects.all())
