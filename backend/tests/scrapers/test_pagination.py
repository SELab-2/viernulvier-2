"""
Tests for Viernulvier pagination discovery and execution.
"""

from __future__ import annotations

import logging

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import ScraperError, _discover_extra_pages
from tests.scrapers.conftest import _make_ok_response, _make_status_response, _mock_session

# ---------------------------------------------------------------------------
# _discover_extra_pages
# ---------------------------------------------------------------------------


class TestDiscoverExtraPages:
    def test_no_view_key_returns_empty(self) -> None:
        assert _discover_extra_pages({}) == []

    def test_empty_view_returns_empty(self) -> None:
        assert _discover_extra_pages({"view": {}}) == []

    def test_last_url_without_page_param_returns_empty(self) -> None:
        data = {"view": {"last": "https://example.com/api/events"}}
        assert _discover_extra_pages(data) == []

    def test_last_url_with_page_param_returns_pages_2_to_n(self) -> None:
        data = {"view": {"last": "https://www.viernulvier.gent/api/v1/events?page=4"}}
        pages = _discover_extra_pages(data)
        assert len(pages) == 3
        assert all("page=" in p for p in pages)
        assert "page=2" in pages[0]
        assert "page=4" in pages[2]

    def test_relative_last_url_becomes_absolute(self) -> None:
        data = {"view": {"last": "/api/v1/events?page=3"}}
        pages = _discover_extra_pages(data)
        assert all(p.startswith("http") for p in pages)

    def test_single_page_url_returns_empty(self) -> None:
        """If last=page=1, there are no extra pages."""
        data = {"view": {"last": "https://example.com/api/events?page=1"}}
        pages = _discover_extra_pages(data)
        assert pages == []


# ---------------------------------------------------------------------------
# Concurrent Pagination
# ---------------------------------------------------------------------------


class TestConcurrentPagination:
    def test_fetches_all_pages_concurrently(self, monkeypatch) -> None:

        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if "page=2" in url:
                return _make_ok_response({"member": [{"@id": "2"}]})
            if "page=3" in url:
                return _make_ok_response({"member": [{"@id": "3"}]})
            return _make_ok_response(
                {
                    "@context": "ctx",
                    "member": [{"@id": "1"}],
                    "totalItems": 3,
                    "view": {"last": "https://www.viernulvier.gent/api/v1/events?page=3"},
                }
            )

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 3

    def test_page_fetch_error_logged_and_other_pages_returned(self, monkeypatch, caplog) -> None:

        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if "page=2" in url:
                raise ScraperError("page 2 failed")
            return _make_ok_response(
                {
                    "@context": "ctx",
                    "member": [{"@id": "1"}],
                    "totalItems": 2,
                    "view": {"last": "https://www.viernulvier.gent/api/v1/events?page=2"},
                }
            )

        _mock_session(monkeypatch, responses)
        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert any(item["@id"] == "1" for item in result)
        assert any("Page fetch failed" in r.message for r in caplog.records)

    def test_304_on_concurrent_page_silently_skipped(self, monkeypatch) -> None:

        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

        def responses(url, n):
            if "page=2" in url:
                return _make_status_response(304, {})
            return _make_ok_response(
                {
                    "@context": "ctx",
                    "member": [{"@id": "1"}],
                    "totalItems": 2,
                    "view": {"last": "https://www.viernulvier.gent/api/v1/events?page=2"},
                }
            )

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Sequential Fallback (next pages)
# ---------------------------------------------------------------------------


class TestSequentialFallback:
    def test_304_on_next_page_breaks_loop(self, monkeypatch) -> None:

        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        call_count = [0]

        def responses(url, n):
            call_count[0] = n
            if n == 1:
                return _make_ok_response(
                    {
                        "@context": "ctx",
                        "member": [{"@id": "1"}],
                        "view": {"next": "https://www.viernulvier.gent/api/v1/events?page=2"},
                    }
                )
            return _make_status_response(304, {})

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 1

    def test_relative_next_url_made_absolute(self, monkeypatch) -> None:

        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        captured_urls = []

        def responses(url, n):
            captured_urls.append(url)
            if n == 1:
                return _make_ok_response(
                    {
                        "@context": "ctx",
                        "member": [{"@id": "1"}],
                        "view": {"next": "/api/v1/events?page=2"},
                    }
                )
            return _make_ok_response({"member": [{"@id": "2"}]})

        _mock_session(monkeypatch, responses)
        viernulvier.fetch_viernulvier(endpoint="/events")
        assert captured_urls[1].startswith("http")

    def test_list_response_on_next_page_appended(self, monkeypatch) -> None:

        monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
        call_count = [0]

        def responses(url, n):
            call_count[0] = n
            if n == 1:
                return _make_ok_response(
                    {
                        "@context": "ctx",
                        "member": [{"@id": "1"}],
                        "view": {"next": "https://www.viernulvier.gent/api/v1/events?page=2"},
                    }
                )
            return _make_ok_response([{"@id": "2"}, {"@id": "3"}])

        _mock_session(monkeypatch, responses)
        result = viernulvier.fetch_viernulvier(endpoint="/events")
        assert len(result) == 3
