"""
Tests for the media-item crop section of the Viernulvier scraper.

Covers every line of:
  - _derive_crop_filename
  - _download_image
  - sync_media_item_crops

Run with:
    pytest apps/imports/scrapers/tests/test_viernulvier_crops.py -v
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
import requests
from django.core.exceptions import FieldDoesNotExist

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    ScraperError,
    _derive_crop_filename,
    _download_image,
    sync_media_item_crops,
)

# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------


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
    r = Mock()
    r.status_code = status
    r.ok = status < 400
    r.headers = Mock()
    header_dict = headers or {}
    r.headers.get = lambda k, d=None: header_dict.get(k, d)
    return r


# ============================================================================
# _derive_crop_filename
# ============================================================================


class TestDeriveCropFilename:
    def test_basic_path_and_jpg_extension(self):
        """/api/v1/media/items/310 + .jpg url -> api_v1_media_items_310_hd_ready.jpg"""
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/310",
            "https://cdn.example.com/images/photo.jpg",
        )
        assert result == "api_v1_media_items_310_hd_ready.jpg"

    def test_extension_extracted_from_png_url(self):
        result = _derive_crop_filename(
            "FE3_header",
            "/api/v1/media/items/42",
            "https://cdn.example.com/images/banner.png",
        )
        assert result.endswith(".png")
        assert "FE3_header" in result

    def test_query_string_stripped_before_extension_extraction(self):
        """Query params after ? are ignored when detecting the extension."""
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/5",
            "https://cdn.example.com/photo.jpeg?w=800&h=600",
        )
        assert result.endswith(".jpeg")

    def test_extension_too_long_falls_back_to_jpg(self):
        """Extension with more than 5 chars (e.g. a CDN hash) falls back to .jpg."""
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/9",
            "https://cdn.example.com/images/abc123def456",  # no dot -> falls back
        )
        assert result.endswith(".jpg")

    def test_non_alpha_extension_falls_back_to_jpg(self):
        """Extension containing digits (like .123) falls back to .jpg."""
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/7",
            "https://cdn.example.com/file.12345",
        )
        assert result.endswith(".jpg")

    def test_url_segment_without_dot_falls_back_to_jpg(self):
        """A URL path that has no dot at all falls back to .jpg."""
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/8",
            "https://cdn.example.com/images/nondotted",
        )
        assert result.endswith(".jpg")

    def test_leading_slash_stripped_from_external_id(self):
        """Leading slash on external_id is stripped before slugifying."""
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/10",
            "https://cdn.example.com/img.jpg",
        )
        # Must NOT start with underscore
        assert not result.startswith("_")
        assert result.startswith("api")

    def test_slashes_in_external_id_replaced_by_underscores(self):
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/310",
            "https://cdn.example.com/img.jpg",
        )
        assert "/" not in result

    def test_crop_name_included_in_filename(self):
        result = _derive_crop_filename(
            "FE3_header",
            "/api/v1/media/items/99",
            "https://cdn.example.com/img.jpg",
        )
        assert "FE3_header" in result

    def test_extension_longer_than_5_chars_falls_back(self):
        """Any extension longer than 5 chars (including the dot) falls back to .jpg."""
        # ".webp2" is 6 chars -> fallback
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/1",
            "https://cdn.example.com/img.webp2",
        )
        assert result.endswith(".jpg")

    def test_webp_extension_is_kept(self):
        """.webp is exactly 5 chars - border case that should be kept."""
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/1",
            "https://cdn.example.com/img.webp",
        )
        assert result.endswith(".webp")


# ============================================================================
# _download_image
# ============================================================================


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

    def test_returns_bytes_on_success(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.return_value = _make_ok_response(b"pixels")

        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result == b"pixels"

    def test_returns_none_on_non_ok_status(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.return_value = _make_status_response(404)

        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None

    def test_returns_none_on_request_exception(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.side_effect = requests.RequestException("ssl error")

        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None

    def test_connection_error_retries_then_succeeds(self, monkeypatch):
        def responses(url, n):
            if n == 1:
                raise requests.ConnectionError("down")
            return _make_ok_response(b"data")

        session, count = self._patched_session(monkeypatch, responses)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result == b"data"
        assert count[0] == 2

    def test_timeout_retries_then_succeeds(self, monkeypatch):
        def responses(url, n):
            if n == 1:
                raise requests.Timeout()
            return _make_ok_response(b"ok")

        session, _ = self._patched_session(monkeypatch, responses)
        assert _download_image(session, "https://cdn.example.com/img.jpg") == b"ok"

    def test_connection_error_all_retries_exhausted_returns_none(self, monkeypatch, caplog):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.side_effect = requests.ConnectionError("always down")

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None
        assert any("Image download failed" in r.message for r in caplog.records)

    def test_timeout_all_retries_exhausted_returns_none(self, monkeypatch, caplog):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.side_effect = requests.Timeout()

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None

    def test_429_with_retry_after_waits_then_succeeds(self, monkeypatch):
        sleep_calls = []
        monkeypatch.setattr(viernulvier.time, "sleep", lambda t: sleep_calls.append(t))
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

    def test_429_all_retries_exhausted_returns_none(self, monkeypatch, caplog):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.return_value = _make_status_response(429, {})

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None
        assert any("Rate limited" in r.message for r in caplog.records)

    def test_429_without_retry_after_uses_backoff(self, monkeypatch):
        sleep_calls = []
        monkeypatch.setattr(viernulvier.time, "sleep", lambda t: sleep_calls.append(t))
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

    def test_server_error_non_ok_non_429_logs_and_returns_none(self, monkeypatch, caplog):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = Mock()
        session.get.return_value = _make_status_response(500)

        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None
        assert any("HTTP 500" in r.message for r in caplog.records)

    def test_fallthrough_return_none_when_max_retries_set_to_minus_one(self, monkeypatch):
        """The unreachable `return None` after the retry loop is hit when MAX_RETRIES=-1.

        With MAX_RETRIES=-1 the for-loop body never executes, so the function
        falls through to the bare `return None` at the bottom.
        """
        monkeypatch.setattr(viernulvier, "MAX_RETRIES", -1)
        session = Mock()  # .get should never be called

        result = _download_image(session, "https://cdn.example.com/img.jpg")

        assert result is None
        session.get.assert_not_called()

    def test_connection_error_retry_warning_logged(self, monkeypatch, caplog):
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


# ============================================================================
# sync_media_item_crops
# ============================================================================


def _patch_crop_dependencies(
    monkeypatch,
    *,
    foto_items: list,
    fetch_results: dict | None = None,
    download_result: bytes | None = b"image-data",
    synced_crop_names: set | None = None,
    generate_filename_result: str = "media/crops/item_hd_ready.jpg",
    storage_save_result: str = "media/crops/item_hd_ready.jpg",
):
    """
    Patch all external dependencies of sync_media_item_crops in one call.

    fetch_results: maps external_id -> (item_data, etag) tuple.
    download_result: bytes returned by _download_image (None simulates failure).
    """
    from apps.media_library import models as media_models

    if synced_crop_names is None:
        synced_crop_names = {"hd_ready", "FE3_header"}

    # --- MediaItem queryset ---
    mock_qs = Mock()
    mock_qs.values.return_value = foto_items
    monkeypatch.setattr(
        media_models.MediaItem.objects,
        "filter",
        lambda **_kw: mock_qs,
    )

    # --- _build_session (returns a dummy session; _download_image is patched separately) ---
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())

    # --- _fetch_with_retry ---
    def fake_fetch(session, url, etag=None, params=None):
        if fetch_results and url in fetch_results:
            return fetch_results[url]
        # Default: single crop
        return (
            {
                "crops": [
                    {"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"},
                ]
            },
            None,
        )

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch)

    # --- _download_image ---
    monkeypatch.setattr(viernulvier, "_download_image", lambda _session, _url: download_result)

    # --- MediaItemCrop ---
    mock_crop_model = Mock()
    mock_crop_model.SYNCED_CROP_NAMES = synced_crop_names

    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = generate_filename_result
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = storage_save_result
    mock_crop_model._meta = Mock()
    mock_crop_model._meta.get_field.return_value = mock_image_field
    mock_crop_model.objects.update_or_create.return_value = (Mock(), True)

    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_model)

    return mock_crop_model


@pytest.mark.django_db
def test_sync_crops_no_foto_items_returns_zero(monkeypatch):
    """When there are no foto MediaItems, sync returns 0 immediately."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = []
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)

    result = sync_media_item_crops()

    assert result == 0


@pytest.mark.django_db
def test_sync_crops_params_skip_missing_fields_and_apply_supported_ones(monkeypatch):
    from apps.media_library import models as media_models

    class FakeQuerySet:
        def __init__(self):
            self.filter_calls = []

        def filter(self, **kwargs):
            self.filter_calls.append(kwargs)
            return self

        def values(self, *_args, **_kwargs):
            return []

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)

    def fake_get_field(name):
        if name == "updated_at":
            return Mock()
        raise FieldDoesNotExist(name)

    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", fake_get_field)

    def fake_parse_datetime(value):
        if value == "raise-type":
            raise TypeError("bad type")
        return datetime(2024, 1, 1, tzinfo=timezone.utc)

    monkeypatch.setattr(viernulvier, "parse_datetime", fake_parse_datetime)

    result = sync_media_item_crops(
        params={
            "created_at[after]": "ok",
            "created_at[before]": "ok",
            "updated_at[after]": "ok",
            "updated_at[before]": "ok",
            "updated_at[strictly_after]": "raise-type",
            "updated_at[strictly_before]": "ok",
            "created_at[strictly_after]": "ok",
            "created_at[strictly_before]": "raise-value",
        }
    )

    assert result == 0
    assert {"updated_at__gte": datetime(2024, 1, 1, tzinfo=timezone.utc)} in fake_qs.filter_calls
    assert {"updated_at__lte": datetime(2024, 1, 1, tzinfo=timezone.utc)} in fake_qs.filter_calls
    assert all("created_at" not in next(iter(call)) for call in fake_qs.filter_calls)


@pytest.mark.django_db
def test_sync_crops_params_are_forwarded_to_api_and_limit_item_fetches(monkeypatch):
    from apps.media_library import models as media_models

    class FakeQuerySet:
        def filter(self, **_kwargs):
            return self

        def values(self, *_args, **_kwargs):
            return [
                {"pk": 1, "external_id": "/api/v1/media/items/1"},
                {"pk": 2, "external_id": "/api/v1/media/items/2"},
            ]

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)

    def fake_get_field(name):
        if name == "updated_at":
            return Mock()
        raise FieldDoesNotExist(name)

    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", fake_get_field)
    monkeypatch.setattr(viernulvier, "parse_datetime", Mock(return_value=None))
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())

    captured = {}

    def fake_fetch_viernulvier(endpoint, params=None, etag_cache=None):
        captured["endpoint"] = endpoint
        captured["params"] = params
        return [{"@id": "/api/v1/media/items/1"}]

    monkeypatch.setattr(viernulvier, "fetch_viernulvier", fake_fetch_viernulvier)

    fetched_urls = []

    def fake_fetch_with_retry(session, url, params=None, etag=None):
        fetched_urls.append(url)
        return ({"crops": []}, None)

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch_with_retry)

    result = sync_media_item_crops(
        params={
            "created_at[after]": "2024-01-01T00:00:00+00:00",
            "updated_at[after]": "2024-01-01T00:00:00+00:00",
        }
    )

    assert result == 0
    assert captured["endpoint"] == "/media/items"
    assert captured["params"] == {"updated_at[after]": "2024-01-01T00:00:00+00:00"}
    assert fetched_urls == ["https://www.viernulvier.gent/api/v1/media/items/1"]


@pytest.mark.django_db
def test_sync_crops_params_skip_filter_when_fake_parse_datetime_raises_valueerror(monkeypatch):
    from apps.media_library import models as media_models

    class FakeQuerySet:
        def __init__(self):
            self.filter_calls = []

        def values(self, *_args, **_kwargs):
            return []

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)
    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", lambda name: Mock() if name == "updated_at" else None)

    def fake_parse_datetime(value):
        if value == "raise-value":
            raise ValueError("bad datetime")

    monkeypatch.setattr(viernulvier, "parse_datetime", fake_parse_datetime)

    result = sync_media_item_crops(params={"updated_at[strictly_before]": "raise-value"})

    assert result == 0
    assert fake_qs.filter_calls == []


@pytest.mark.django_db
def test_sync_crops_params_skip_filter_when_fake_get_field_raises_fielddoesnotexist(monkeypatch):
    from apps.media_library import models as media_models

    class FakeQuerySet:
        def __init__(self):
            self.filter_calls = []

        def filter(self, **kwargs):
            self.filter_calls.append(kwargs)
            return self

        def values(self, *_args, **_kwargs):
            return []

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)

    def fake_get_field(name):
        if name == "updated_at":
            return Mock()
        raise FieldDoesNotExist(name)

    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", fake_get_field)

    parse_dt = Mock(return_value=datetime(2024, 1, 1, tzinfo=timezone.utc))
    monkeypatch.setattr(viernulvier, "parse_datetime", parse_dt)

    result = sync_media_item_crops(
        params={
            "created_at[before]": "2024-01-01T00:00:00+00:00",
            "updated_at[before]": "2024-01-01T00:00:00+00:00",
        }
    )

    assert result == 0
    assert fake_qs.filter_calls == [{"updated_at__lte": datetime(2024, 1, 1, tzinfo=timezone.utc)}]
    parse_dt.assert_called_once_with("2024-01-01T00:00:00+00:00")


@pytest.mark.django_db
def test_sync_crops_params_ignores_non_matching_param_key(monkeypatch):
    from apps.media_library import models as media_models

    class FakeQuerySet:
        def __init__(self):
            self.filter_calls = []

        def values(self, *_args, **_kwargs):
            return []

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)

    meta_get_field = Mock(side_effect=AssertionError("get_field should not be called for invalid param keys"))
    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", meta_get_field)

    parse_dt = Mock(side_effect=AssertionError("parse_datetime should not be called for invalid param keys"))
    monkeypatch.setattr(viernulvier, "parse_datetime", parse_dt)

    result = sync_media_item_crops(params={"invalid[param]": "2024-01-01T00:00:00+00:00"})

    assert result == 0
    assert fake_qs.filter_calls == []
    meta_get_field.assert_not_called()
    parse_dt.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_params_skips_filter_when_datetime_is_none(monkeypatch):
    from apps.media_library import models as media_models

    class FakeQuerySet:
        def __init__(self):
            self.filter_calls = []

        def values(self, *_args, **_kwargs):
            return []

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)
    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", lambda name: Mock() if name == "updated_at" else None)

    parse_dt = Mock(return_value=None)
    monkeypatch.setattr(viernulvier, "parse_datetime", parse_dt)

    result = sync_media_item_crops(params={"updated_at[after]": "not-a-datetime"})

    assert result == 0
    assert fake_qs.filter_calls == []
    parse_dt.assert_called_once_with("not-a-datetime")


@pytest.mark.django_db
def test_sync_crops_params_skips_filter_when_datetime_raises_valueerror(monkeypatch):
    from apps.media_library import models as media_models

    class FakeQuerySet:
        def __init__(self):
            self.filter_calls = []

        def values(self, *_args, **_kwargs):
            return []

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)

    def fake_get_field(_name):
        return Mock()

    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", fake_get_field)

    parse_dt = Mock(side_effect=ValueError("bad datetime"))
    monkeypatch.setattr(viernulvier, "parse_datetime", parse_dt)

    result = sync_media_item_crops(params={"updated_at[before]": "raise-value"})

    assert result == 0
    assert fake_qs.filter_calls == []
    parse_dt.assert_called_once_with("raise-value")


@pytest.mark.django_db
def test_sync_crops_no_foto_items_creates_success_import_log(monkeypatch):
    """Empty foto list creates a SUCCESS ImportLog with all-zero counters."""
    from apps.import_log.models import ImportLog
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = []
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_total == 0
    assert log.records_imported == 0
    assert log.records_failed == 0


@pytest.mark.django_db
def test_sync_crops_item_without_external_id_skipped(monkeypatch, caplog):
    """MediaItem rows with no external_id are skipped and counted as errors."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": ""}],
    )

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("no external_id" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_none_external_id_skipped(monkeypatch, caplog):
    """MediaItem rows with external_id=None are also skipped."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": None}],
    )

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("no external_id" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_fetch_failure_logged_as_error(monkeypatch, caplog):
    """A ScraperError during individual item fetch is logged and counted as error."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (_ for _ in ()).throw(ScraperError("API down")),
    )

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("Failed to fetch media item" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_304_not_modified_skips_item(monkeypatch):
    """A 304 (fetch returns None) means no crops to process - item is silently skipped."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(viernulvier, "_fetch_with_retry", lambda *_a, **_kw: (None, None))

    result = sync_media_item_crops()

    assert result == 0


@pytest.mark.django_db
def test_sync_crops_non_list_crops_field_skipped(monkeypatch, caplog):
    """When API crops field is not a list, the item is silently skipped."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": "not-a-list"}, None),
    )

    caplog.set_level(logging.DEBUG, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("Unexpected crops format" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_crop_not_in_wanted_set_skipped(monkeypatch):
    """Crop names not in SYNCED_CROP_NAMES are silently ignored."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "unknown_variant", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_qs2 = Mock()
    mock_qs2.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]

    from apps.media_library import models as mm

    monkeypatch.setattr(mm, "MediaItemCrop", mock_crop_cls)

    result = sync_media_item_crops()

    assert result == 0
    mock_crop_cls.objects.update_or_create.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_crop_missing_url_warns_and_skips(monkeypatch, caplog):
    """A crop dict without a url key is skipped with a warning."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": ""}]}, None),
    )

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    from apps.media_library import models as mm

    monkeypatch.setattr(mm, "MediaItemCrop", mock_crop_cls)

    caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("has no URL" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_download_failure_counted_as_error(monkeypatch, caplog):
    """When _download_image returns None the crop is counted as an error."""
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,  # simulate download failure
    )

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    mock_crop_cls.objects.update_or_create.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_successful_save_returns_count(monkeypatch):
    """A successful crop save increments the saved counter."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=b"image-bytes",
    )

    result = sync_media_item_crops()

    assert result == 1


@pytest.mark.django_db
def test_sync_crops_creates_import_log_success(monkeypatch):
    """A fully successful run produces a SUCCESS ImportLog."""
    from apps.import_log.models import ImportLog

    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_imported == 1
    assert log.records_failed == 0


@pytest.mark.django_db
def test_sync_crops_partial_success_import_log(monkeypatch):
    """One crop saved + one failed produces a PARTIAL_SUCCESS ImportLog."""
    from apps.import_log.models import ImportLog
    from apps.media_library import models as media_models

    # Two items; first succeeds, second has bad external_id (empty -> error)
    mock_qs = Mock()
    mock_qs.values.return_value = [
        {"pk": 1, "external_id": "/api/v1/media/items/1"},
        {"pk": 2, "external_id": ""},  # will be skipped as error
    ]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"data")

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "crops/img.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), True)
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.PARTIAL_SUCCESS
    assert log.records_imported == 1
    assert log.records_failed == 1


@pytest.mark.django_db
def test_sync_crops_all_failed_import_log(monkeypatch):
    """All items failing produces a FAILED ImportLog."""
    from apps.import_log.models import ImportLog

    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,  # download always fails
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.FAILED
    assert log.records_imported == 0
    assert log.records_failed == 1


@pytest.mark.django_db
def test_sync_crops_dry_run_does_not_write(monkeypatch):
    """dry_run=True logs intentions but writes neither images nor DB rows."""
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    result = sync_media_item_crops(dry_run=True)

    assert result == 1  # "would save"
    mock_crop_cls.objects.update_or_create.assert_not_called()
    mock_crop_cls._meta.get_field.return_value.storage.save.assert_not_called()


@pytest.mark.django_db
def test_sync_crops_dry_run_logs_intended_save(monkeypatch, caplog):
    """dry_run mode logs what would be saved for each crop."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops(dry_run=True)

    assert any("[DRY RUN]" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_on_progress_called_per_item(monkeypatch):
    """on_progress callback receives (idx, total) for every processed item."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[
            {"pk": 1, "external_id": "/api/v1/media/items/1"},
            {"pk": 2, "external_id": "/api/v1/media/items/2"},
        ],
        fetch_results={
            "https://www.viernulvier.gent/api/v1/media/items/1": (
                {"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/a.jpg"}]},
                None,
            ),
            "https://www.viernulvier.gent/api/v1/media/items/2": (
                {"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/b.jpg"}]},
                None,
            ),
        },
    )

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert len(calls) == 2
    assert calls[0] == (1, 2)
    assert calls[1] == (2, 2)


@pytest.mark.django_db
def test_sync_crops_save_exception_counted_as_error(monkeypatch, caplog):
    """An unexpected exception during update_or_create is caught and counted as error."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"data")

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "crops/img.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.side_effect = RuntimeError("db crash")
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
    result = sync_media_item_crops()

    assert result == 0
    assert any("Error saving crop" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_save_exception_added_to_error_messages(monkeypatch):
    """Exceptions during save are captured in the ImportLog error_message."""
    from apps.import_log.models import ImportLog
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"data")

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "crops/img.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.side_effect = RuntimeError("db crash")
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.error_message is not None
    assert "db crash" in log.error_message


@pytest.mark.django_db
def test_sync_crops_external_id_as_absolute_url_used_directly(monkeypatch):
    """external_id already starting with http is used as-is (not prefixed)."""
    from apps.media_library import models as media_models

    captured_urls = []
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "https://www.viernulvier.gent/api/v1/media/items/99"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())

    def fake_fetch(session, url, **_kw):
        captured_urls.append(url)
        return ({"crops": []}, None)

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch)

    sync_media_item_crops()

    assert captured_urls[0] == "https://www.viernulvier.gent/api/v1/media/items/99"


@pytest.mark.django_db
def test_sync_crops_external_id_as_relative_path_prefixed_with_base_domain(monkeypatch):
    """Relative external_id is prefixed with BASE_DOMAIN before fetching."""
    from apps.media_library import models as media_models

    captured_urls = []
    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/10"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())

    def fake_fetch(session, url, **_kw):
        captured_urls.append(url)
        return ({"crops": []}, None)

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch)

    sync_media_item_crops()

    assert captured_urls[0].startswith("https://")
    assert "/api/v1/media/items/10" in captured_urls[0]


@pytest.mark.django_db
def test_sync_crops_multiple_items_and_crops_counted_correctly(monkeypatch):
    """Two items, each with two wanted crops -> four total crops saved."""
    from apps.media_library import models as media_models

    items_data = [
        {"pk": 1, "external_id": "/api/v1/media/items/1"},
        {"pk": 2, "external_id": "/api/v1/media/items/2"},
    ]
    mock_qs = Mock()
    mock_qs.values.return_value = items_data
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            {
                "crops": [
                    {"name": "hd_ready", "url": "https://cdn.example.com/hd.jpg"},
                    {"name": "FE3_header", "url": "https://cdn.example.com/fe3.jpg"},
                ]
            },
            None,
        ),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"img")

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready", "FE3_header"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "crops/img.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), True)
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    result = sync_media_item_crops()

    assert result == 4  # 2 items × 2 crops each


@pytest.mark.django_db
def test_sync_crops_crop_dict_not_dict_skipped(monkeypatch):
    """Non-dict entries inside the crops list are silently ignored."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            # Mix of valid and non-dict crops
            {
                "crops": [
                    "not-a-dict",
                    42,
                    None,
                    {"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"},
                ]
            },
            None,
        ),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"img")

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "crops/img.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), True)
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    result = sync_media_item_crops()

    assert result == 1  # Only the valid dict crop was processed


@pytest.mark.django_db
def test_sync_crops_logs_created_or_updated_debug(monkeypatch, caplog):
    """Created vs Updated status is logged at DEBUG level."""
    mock_crop_cls = _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), False)  # updated

    caplog.set_level(logging.DEBUG, logger=viernulvier.logger.name)
    sync_media_item_crops()

    assert any("Updated" in r.message or "Created" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_import_log_source_is_correct(monkeypatch):
    """The ImportLog source is set to 'viernulvier:media_item_crops'."""
    from apps.import_log.models import ImportLog

    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[],
    )
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = []
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.source == "viernulvier:media_item_crops"


@pytest.mark.django_db
def test_sync_crops_import_log_timestamps_sequential(monkeypatch):
    """finished_at >= started_at in the ImportLog."""
    from apps.import_log.models import ImportLog

    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert log.finished_at >= log.started_at


@pytest.mark.django_db
def test_sync_crops_fetch_error_message_captured_in_import_log(monkeypatch):
    """ScraperError messages during fetch are included in the ImportLog error_message."""
    from apps.import_log.models import ImportLog
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (_ for _ in ()).throw(ScraperError("network timeout")),
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert "network timeout" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_crops_summary_logged_on_completion(monkeypatch, caplog):
    """'Crop sync complete' with saved= and errors= is logged after running."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops()

    assert any("Crop sync complete" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_dry_run_summary_has_dry_run_suffix(monkeypatch, caplog):
    """The completion log includes '[DRY RUN]' suffix when dry_run=True."""
    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
    )

    caplog.set_level(logging.INFO, logger=viernulvier.logger.name)
    sync_media_item_crops(dry_run=True)

    assert any("[DRY RUN]" in r.message and "Crop sync complete" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_sync_crops_download_error_message_captured(monkeypatch):
    """Download failures are captured in the ImportLog error_message."""
    from apps.import_log.models import ImportLog

    _patch_crop_dependencies(
        monkeypatch,
        foto_items=[{"pk": 1, "external_id": "/api/v1/media/items/1"}],
        download_result=None,
    )

    sync_media_item_crops()

    log = ImportLog.objects.latest("started_at")
    assert "Download failed" in (log.error_message or "")


@pytest.mark.django_db
def test_sync_crops_storage_save_called_with_image_bytes(monkeypatch):
    """The storage backend's save() is called with a ContentFile wrapping the downloaded bytes."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"raw-pixels")

    storage_save_calls = []

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_storage = Mock()

    def capture_save(upload_name, content_file):
        storage_save_calls.append((upload_name, content_file.read()))
        return upload_name

    mock_storage.save.side_effect = capture_save
    mock_image_field.storage = mock_storage
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field
    mock_crop_cls.objects.update_or_create.return_value = (Mock(), True)
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    sync_media_item_crops()

    assert storage_save_calls
    assert storage_save_calls[0][1] == b"raw-pixels"


# ============================================================================
# on_progress called in every early-exit branch
# ============================================================================


@pytest.mark.django_db
def test_on_progress_called_when_external_id_missing(monkeypatch):
    """on_progress is invoked even when an item is skipped due to missing external_id."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": ""}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_on_progress_called_after_fetch_scraper_error(monkeypatch):
    """on_progress is invoked after a ScraperError on the individual item fetch."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (_ for _ in ()).throw(ScraperError("boom")),
    )

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_on_progress_called_after_304_not_modified(monkeypatch):
    """on_progress is invoked when the item fetch returns None (304 Not Modified)."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(viernulvier, "_fetch_with_retry", lambda *_a, **_kw: (None, None))

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_on_progress_called_after_non_list_crops(monkeypatch):
    """on_progress is invoked when the crops field is not a list."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 1, "external_id": "/api/v1/media/items/1"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": "not-a-list"}, None),
    )

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 1)]


@pytest.mark.django_db
def test_on_progress_covers_all_four_early_exit_branches_in_one_run(monkeypatch):
    """Four items, each triggering a different early-exit; on_progress fired for all four."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [
        {"pk": 1, "external_id": ""},  # branch: no external_id
        {"pk": 2, "external_id": "/api/v1/media/items/2"},  # branch: ScraperError
        {"pk": 3, "external_id": "/api/v1/media/items/3"},  # branch: 304 (None)
        {"pk": 4, "external_id": "/api/v1/media/items/4"},  # branch: non-list crops
    ]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())

    calls = []
    sync_media_item_crops(on_progress=lambda idx, total: calls.append((idx, total)))

    assert calls == [(1, 4), (2, 4), (3, 4), (4, 4)]


@pytest.mark.django_db
def test_sync_crops_update_or_create_receives_correct_kwargs(monkeypatch):
    """update_or_create is called with media_item_id, name, and defaults={image:...}."""
    from apps.media_library import models as media_models

    mock_qs = Mock()
    mock_qs.values.return_value = [{"pk": 42, "external_id": "/api/v1/media/items/42"}]
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_: mock_qs)
    monkeypatch.setattr(viernulvier, "_build_session", lambda: Mock())
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: ({"crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}]}, None),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"data")

    uoc_calls = []

    mock_crop_cls = Mock()
    mock_crop_cls.SYNCED_CROP_NAMES = {"hd_ready"}
    mock_image_field = Mock()
    mock_image_field.generate_filename.return_value = "crops/img.jpg"
    mock_image_field.storage = Mock()
    mock_image_field.storage.save.return_value = "saved/path.jpg"
    mock_crop_cls._meta = Mock()
    mock_crop_cls._meta.get_field.return_value = mock_image_field

    def capture_uoc(**kwargs):
        uoc_calls.append(kwargs)
        return (Mock(), True)

    mock_crop_cls.objects.update_or_create.side_effect = capture_uoc
    monkeypatch.setattr(media_models, "MediaItemCrop", mock_crop_cls)

    sync_media_item_crops()

    assert uoc_calls
    call_kw = uoc_calls[0]
    assert call_kw["media_item_id"] == 42
    assert call_kw["name"] == "hd_ready"
    assert call_kw["defaults"] == {"image": "saved/path.jpg"}
