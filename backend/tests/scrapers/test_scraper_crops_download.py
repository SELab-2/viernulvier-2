"""Tests for crop download and filename helper behavior."""

from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest
import requests

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import _derive_crop_filename, _download_image


def _make_ok_response(content: bytes = b"img-bytes", status: int = 200):
    """Return a mock requests.Response with .ok=True and .content set."""
    r = Mock()
    r.status_code = status
    r.ok = True
    r.content = content
    r.headers = Mock()
    r.headers.get = Mock(return_value=None)
    return r


def _make_status_response(status: int, headers: dict | None = None):
    """Return a mock response for a non-success or custom HTTP status."""
    r = Mock()
    r.status_code = status
    r.ok = status < 400
    r.headers = Mock()
    header_dict = headers or {}
    r.headers.get = lambda k, d=None: header_dict.get(k, d)
    return r


class TestDownloadImage:
    def _patched_session(self, monkeypatch, responses_fn):
        """Return a Mock session whose .get() calls responses_fn(url, call_n)."""
        call_count = [0]
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()

        def fake_get(url, timeout=None, stream=None):
            call_count[0] += 1
            return responses_fn(url, call_count[0])

        session.get.side_effect = fake_get
        return session, call_count

    def test_returns_bytes_on_success(self, monkeypatch) -> None:
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.return_value = _make_ok_response(b"pixels")

        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result == b"pixels"

    def test_returns_none_on_non_ok_status(self, monkeypatch) -> None:
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.return_value = _make_status_response(404)

        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None

    def test_returns_none_on_request_exception(self, monkeypatch) -> None:
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.side_effect = requests.RequestException("ssl error")

        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None

    def test_connection_error_retries_then_succeeds(self, monkeypatch) -> None:
        def responses(url, n):
            if n == 1:
                raise requests.ConnectionError("down")
            return _make_ok_response(b"data")

        session, count = self._patched_session(monkeypatch, responses)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result == b"data"
        assert count[0] == 2

    def test_timeout_retries_then_succeeds(self, monkeypatch) -> None:
        def responses(url, n):
            if n == 1:
                raise requests.Timeout
            return _make_ok_response(b"ok")

        session, _ = self._patched_session(monkeypatch, responses)
        assert _download_image(session, "https://cdn.example.com/img.jpg") == b"ok"

    def test_connection_error_all_retries_exhausted_returns_none(self, monkeypatch, caplog) -> None:
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.side_effect = requests.ConnectionError("always down")

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None
        assert any("Image download failed" in r.message for r in caplog.records)

    def test_timeout_all_retries_exhausted_returns_none(self, monkeypatch, caplog) -> None:
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.side_effect = requests.Timeout()

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None

    def test_429_with_retry_after_waits_then_succeeds(self, monkeypatch) -> None:
        sleep_calls = []
        monkeypatch.setattr(viernulvier.time, "sleep", sleep_calls.append)
        call_count = [0]
        session = Mock()

        def fake_get(url, timeout=None, stream=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return _make_status_response(429, {"Retry-After": "10"})
            return _make_ok_response(b"img")

        session.get.side_effect = fake_get
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result == b"img"
        assert 10.0 in sleep_calls

    def test_429_all_retries_exhausted_returns_none(self, monkeypatch, caplog) -> None:
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.return_value = _make_status_response(429, {})

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None
        assert any("Rate limited" in r.message for r in caplog.records)

    def test_429_without_retry_after_uses_backoff(self, monkeypatch) -> None:
        sleep_calls = []
        monkeypatch.setattr(viernulvier.time, "sleep", sleep_calls.append)
        call_count = [0]
        session = Mock()

        def fake_get(url, timeout=None, stream=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return _make_status_response(429, {})
            return _make_ok_response(b"ok")

        session.get.side_effect = fake_get
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result == b"ok"
        # Some backoff sleep must have been called (not the fixed 10s from Retry-After)
        assert sleep_calls

    def test_server_error_non_ok_non_429_logs_and_returns_none(self, monkeypatch, caplog) -> None:
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.return_value = _make_status_response(500)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None
        assert any("HTTP 500" in r.message for r in caplog.records)

    def test_fallthrough_return_none_when_max_retries_set_to_minus_one(self, monkeypatch) -> None:
        """The unreachable `return None` after the retry loop is hit when MAX_RETRIES=-1.

        With MAX_RETRIES=-1 the for-loop body never executes, so the function
        falls through to the bare `return None` at the bottom.
        """
        monkeypatch.setattr(viernulvier, "MAX_RETRIES", -1)
        session = Mock()  # .get should never be called

        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None
        session.get.assert_not_called()

    def test_connection_error_retry_warning_logged(self, monkeypatch, caplog) -> None:
        """A connection error that succeeds on retry logs a warning."""
        call_count = [0]
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()

        def fake_get(url, timeout=None, stream=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise requests.ConnectionError("flaky")
            return _make_ok_response(b"data")

        session.get.side_effect = fake_get
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
        _download_image(session, "https://cdn.example.com/img.jpg")

        assert any("Image download error" in r.message for r in caplog.records)


@pytest.mark.parametrize(
    ("crop_name", "external_id", "url", "expected_suffix"),
    [
        ("hd_ready", "/api/v1/media/items/310", "https://cdn.example.com/images/photo.jpg", ".jpg"),
        ("FE3_header", "/api/v1/media/items/42", "https://cdn.example.com/images/banner.png", ".png"),
        ("hd_ready", "/api/v1/media/items/5", "https://cdn.example.com/photo.jpeg?w=800&h=600", ".jpeg"),
        ("hd_ready", "/api/v1/media/items/9", "https://cdn.example.com/images/abc123def456", ".jpg"),
        ("hd_ready", "/api/v1/media/items/7", "https://cdn.example.com/file.12345", ".jpg"),
        ("hd_ready", "/api/v1/media/items/8", "https://cdn.example.com/images/nondotted", ".jpg"),
        ("hd_ready", "/api/v1/media/items/1", "https://cdn.example.com/img.webp2", ".jpg"),
        ("hd_ready", "/api/v1/media/items/1", "https://cdn.example.com/img.webp", ".webp"),
    ],
)
def test_derive_crop_filename_extension_handling(crop_name, external_id, url, expected_suffix) -> None:
    assert _derive_crop_filename(crop_name, external_id, url).endswith(expected_suffix)


def test_derive_crop_filename_basic_format() -> None:
    result = _derive_crop_filename(
        "hd_ready",
        "/api/v1/media/items/310",
        "https://cdn.example.com/images/photo.jpg",
    )
    assert result == "api_v1_media_items_310_hd_ready.jpg"


def test_derive_crop_filename_external_id_and_crop_are_embedded() -> None:
    result = _derive_crop_filename(
        "FE3_header",
        "/api/v1/media/items/99",
        "https://cdn.example.com/img.jpg",
    )
    assert result.startswith("api")
    assert not result.startswith("_")
    assert "/" not in result
    assert "FE3_header" in result
