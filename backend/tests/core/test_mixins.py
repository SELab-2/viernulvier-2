from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from apps.core.mixins import LanguageAwareMixin


class _DummyLanguageAware(LanguageAwareMixin):
    pass


class TestLanguageAwareMixin(SimpleTestCase):
    def setUp(self) -> None:
        self.view = _DummyLanguageAware()

    def _set_request(self, query_params: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> None:
        self.view.request = SimpleNamespace(
            query_params=query_params or {},
            headers=headers or {},
        )

    def test_uses_lang_query_param_when_present(self) -> None:
        self._set_request(query_params={"lang": "nl-BE"})

        assert self.view._get_request_language_code() == "nl"

    def test_uses_accept_language_when_lang_query_param_missing(self) -> None:
        self._set_request(headers={"Accept-Language": "fr-BE,fr;q=0.9,en;q=0.8"})

        assert self.view._get_request_language_code() == "fr"

    @override_settings(LANGUAGE_CODE="de-DE")
    def test_falls_back_to_settings_language_code_when_no_request_language(self) -> None:
        self._set_request()

        assert self.view._get_request_language_code() == "de"

    @override_settings(LANGUAGE_CODE="")
    def test_falls_back_to_en_when_settings_language_code_is_empty(self) -> None:
        self._set_request()

        assert self.view._get_request_language_code() == "en"