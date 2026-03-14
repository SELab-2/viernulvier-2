"""
Tests for media item crop sync logic in apps/imports/scrapers/viernulvier.py

Covers:
- _derive_crop_filename: all extension/fallback branches
- _download_image: success, HTTP errors, 429 retry, connection errors, exhausted retries
- sync_media_item_crops: empty DB, dry run, success (create + update), partial failure,
  all-failure, 304 skip, fetch error, missing external_id, non-list crops payload,
  unwanted crop names filtered, missing crop URL, save/storage error,
  on_progress callback, ImportLog states, log messages
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, Mock

import pytest
import requests

from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import (
    _derive_crop_filename,
    _download_image,
    sync_media_item_crops,
)
from tests.factories.media_library import MediaItemFactory

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(status: int, content: bytes = b"", ok: bool = None, headers: dict = None):
    """Build a minimal mock requests.Response."""
    r = Mock()
    r.status_code = status
    r.ok = ok if ok is not None else (status < 400)
    r.content = content
    hdr = headers or {}
    r.headers = Mock()
    r.headers.get = lambda k, default=None: hdr.get(k, default)
    return r


def _foto_item(external_id="/api/v1/media/items/1"):
    """Create a saved foto MediaItem and return it."""
    return MediaItemFactory(
        type="foto",
        external_id=external_id,
    )


def _crop_payload(names=("hd_ready", "FE3_header"), url="https://cdn.example.com/img.jpg"):
    """Return a crops list with the given names."""
    return [{"name": n, "url": url} for n in names]


def _patch_fetch(monkeypatch, item_data):
    """Patch _fetch_with_retry to always return (item_data, None)."""
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda session, url, *args, **kwargs: (item_data, None),
    )


def _patch_session(monkeypatch):
    """Patch _build_session to return a no-op mock session."""
    session = MagicMock()
    monkeypatch.setattr(viernulvier, "_build_session", lambda: session)
    return session


def _patch_download(monkeypatch, return_value=b"fake-image-bytes"):
    """Patch _download_image to return a fixed byte string (or None)."""
    monkeypatch.setattr(viernulvier, "_download_image", lambda *args, **kwargs: return_value)


def _patch_storage(monkeypatch, saved_path="media_crops/2024/01/img.jpg"):
    """Patch MediaItemCrop's ImageField storage to avoid real filesystem writes."""
    from apps.media_library.models import MediaItemCrop

    image_field = MediaItemCrop._meta.get_field("image")
    mock_storage = MagicMock()
    mock_storage.save.return_value = saved_path
    monkeypatch.setattr(image_field, "storage", mock_storage)
    return mock_storage


# ---------------------------------------------------------------------------
# _derive_crop_filename
# ---------------------------------------------------------------------------


class TestDeriveCropFilename:
    def test_standard_jpg_url(self):
        result = _derive_crop_filename("hd_ready", "/api/v1/media/items/310", "https://cdn.example.com/image.jpg")
        assert result == "api_v1_media_items_310_hd_ready.jpg"

    def test_png_extension_preserved(self):
        result = _derive_crop_filename("FE3_header", "/api/v1/media/items/42", "https://cdn.example.com/photo.png")
        assert result == "api_v1_media_items_42_FE3_header.png"

    def test_url_with_query_string_strips_query(self):
        """Extension is derived from the path part, not the query string."""
        result = _derive_crop_filename(
            "hd_ready",
            "/api/v1/media/items/99",
            "https://cdn.example.com/image.jpg?token=abc&size=large",
        )
        assert result == "api_v1_media_items_99_hd_ready.jpg"

    def test_cdn_hash_url_without_extension_falls_back_to_jpg(self):
        """CDN URLs that end in a base64 hash (no dot) fall back to .jpg."""
        hash_url = "https://img.viernulvier.gent/xCITfZbBlBVKsd3ltZFSnD5H4RHGLZr28jkObzacjF8"
        result = _derive_crop_filename("cms", "/api/v1/media/items/310", hash_url)
        assert result.endswith(".jpg")
        assert "310" in result
        assert "cms" in result

    def test_long_extension_falls_back_to_jpg(self):
        """Extensions longer than 5 chars (e.g. '.toolong') fall back to .jpg."""
        result = _derive_crop_filename("hd_ready", "/api/v1/media/items/1", "https://cdn.example.com/file.toolong")
        assert result.endswith(".jpg")

    def test_extension_with_non_alpha_falls_back_to_jpg(self):
        """Extensions containing digits (e.g. '.m4v2') fall back to .jpg."""
        result = _derive_crop_filename("hd_ready", "/api/v1/media/items/1", "https://cdn.example.com/file.m4v2")
        assert result.endswith(".jpg")

    def test_leading_slash_stripped_from_external_id(self):
        """Leading and trailing slashes in external_id are stripped before slugifying."""
        result = _derive_crop_filename("hd_ready", "/api/v1/media/items/5/", "https://cdn.example.com/img.jpg")
        assert result.startswith("api_v1_media_items_5")

    def test_slashes_replaced_by_underscores(self):
        result = _derive_crop_filename("hd_ready", "/api/v1/media/items/7", "https://cdn.example.com/img.jpg")
        assert "/" not in result.split("_hd_ready")[0]

    def test_extension_lowercased(self):
        result = _derive_crop_filename("hd_ready", "/api/v1/media/items/8", "https://cdn.example.com/img.JPG")
        assert result.endswith(".jpg")

    def test_absolute_external_id_url(self):
        """Full https:// external_id is also slugified correctly."""
        result = _derive_crop_filename(
            "hd_ready",
            "https://www.viernulvier.gent/api/v1/media/items/310",
            "https://cdn.example.com/img.jpg",
        )
        assert "310" in result
        assert result.endswith(".jpg")


# ---------------------------------------------------------------------------
# _download_image
# ---------------------------------------------------------------------------


class TestDownloadImage:
    def _session(self, responses):
        """Build a mock session whose .get() cycles through responses."""
        session = Mock()
        call_count = [0]

        def fake_get(url, timeout=None, stream=None):
            idx = min(call_count[0], len(responses) - 1)
            call_count[0] += 1
            r = responses[idx]
            if isinstance(r, Exception):
                raise r
            return r

        session.get.side_effect = fake_get
        return session

    def test_success_returns_bytes(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session([_make_response(200, content=b"imagedata")])
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result == b"imagedata"

    def test_http_error_returns_none(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session([_make_response(404, ok=False)])
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result is None

    def test_500_returns_none_immediately(self, monkeypatch):
        """Non-429 HTTP errors are not retried — returns None on first failure."""
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session([_make_response(500, ok=False)])
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result is None

    def test_connection_error_retries_then_succeeds(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session(
            [
                requests.ConnectionError("down"),
                _make_response(200, content=b"ok"),
            ]
        )
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result == b"ok"

    def test_connection_error_all_retries_exhausted_returns_none(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session([requests.ConnectionError("always down")] * (viernulvier.MAX_RETRIES + 2))
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result is None

    def test_timeout_retries_then_succeeds(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session(
            [
                requests.Timeout(),
                _make_response(200, content=b"data"),
            ]
        )
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result == b"data"

    def test_generic_request_exception_returns_none_immediately(self, monkeypatch):
        """Non-retryable RequestException returns None without sleeping."""
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session([requests.RequestException("ssl error")])
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result is None

    def test_429_with_retry_after_waits_then_succeeds(self, monkeypatch):
        sleep_calls = []
        monkeypatch.setattr(viernulvier.time, "sleep", lambda t: sleep_calls.append(t))
        r429 = _make_response(429, ok=False, headers={"Retry-After": "3"})
        session = self._session([r429, _make_response(200, content=b"img")])
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result == b"img"
        assert 3.0 in sleep_calls

    def test_429_all_retries_exhausted_returns_none(self, monkeypatch):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        r429 = _make_response(429, ok=False, headers={})
        session = self._session([r429] * (viernulvier.MAX_RETRIES + 2))
        result = _download_image(session, "https://cdn.example.com/img.jpg")
        assert result is None

    def test_logs_error_on_exhausted_connection_errors(self, monkeypatch, caplog):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session([requests.ConnectionError("down")] * (viernulvier.MAX_RETRIES + 2))
        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        _download_image(session, "https://cdn.example.com/img.jpg")
        assert any("Image download failed" in r.message for r in caplog.records)

    def test_logs_error_on_http_failure(self, monkeypatch, caplog):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        session = self._session([_make_response(403, ok=False)])
        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        _download_image(session, "https://cdn.example.com/img.jpg")
        assert any("HTTP 403" in r.message for r in caplog.records)

    def test_logs_error_on_rate_limit_exhaustion(self, monkeypatch, caplog):
        monkeypatch.setattr(viernulvier.time, "sleep", lambda *_: None)
        r429 = _make_response(429, ok=False, headers={})
        session = self._session([r429] * (viernulvier.MAX_RETRIES + 2))
        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)
        _download_image(session, "https://cdn.example.com/img.jpg")
        assert any("Rate limited" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# sync_media_item_crops - empty DB
# ---------------------------------------------------------------------------


class TestSyncCropsEmptyDatabase:
    def test_returns_zero_when_no_foto_items(self, monkeypatch):
        _patch_session(monkeypatch)
        result = sync_media_item_crops()
        assert result == 0

    def test_creates_success_import_log_when_no_foto_items(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _patch_session(monkeypatch)
        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.status == ImportLog.Status.SUCCESS
        assert log.records_total == 0
        assert log.records_imported == 0
        assert log.records_failed == 0
        assert log.finished_at is not None

    def test_does_not_crash_when_no_foto_items(self, monkeypatch):
        _patch_session(monkeypatch)
        # Must not raise even with zero items
        sync_media_item_crops()

    def test_non_foto_items_ignored(self, monkeypatch):
        """Video and audio items must NOT be processed."""
        from apps.import_log.models import ImportLog

        MediaItemFactory(type="video", external_id="/api/v1/media/items/1")
        MediaItemFactory(type="audio", external_id="/api/v1/media/items/2")

        _patch_session(monkeypatch)
        result = sync_media_item_crops()

        assert result == 0
        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.records_total == 0


# ---------------------------------------------------------------------------
# sync_media_item_crops - dry run
# ---------------------------------------------------------------------------


class TestSyncCropsDryRun:
    def test_dry_run_returns_would_save_count(self, monkeypatch):
        _foto_item("/api/v1/media/items/1")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload()})

        result = sync_media_item_crops(dry_run=True)

        # 1 item × 2 wanted crops = 2
        assert result == 2

    def test_dry_run_does_not_write_db_rows(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/1")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload()})

        sync_media_item_crops(dry_run=True)

        assert MediaItemCrop.objects.count() == 0

    def test_dry_run_does_not_download_images(self, monkeypatch):
        _foto_item("/api/v1/media/items/1")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload()})

        download_calls = []
        monkeypatch.setattr(
            viernulvier,
            "_download_image",
            lambda *a, **k: download_calls.append(a) or b"bytes",
        )

        sync_media_item_crops(dry_run=True)

        assert download_calls == []

    def test_dry_run_logs_would_save_messages(self, monkeypatch, caplog):
        _foto_item("/api/v1/media/items/1")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload()})
        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        sync_media_item_crops(dry_run=True)

        assert any("DRY RUN" in r.message for r in caplog.records)

    def test_dry_run_import_log_records_total(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/1")
        _foto_item("/api/v1/media/items/2")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload()})

        sync_media_item_crops(dry_run=True)

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.records_total == 2


# ---------------------------------------------------------------------------
# sync_media_item_crops - successful saves
# ---------------------------------------------------------------------------


class TestSyncCropsSuccess:
    def test_creates_crop_rows_for_wanted_variants(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        item = _foto_item("/api/v1/media/items/10")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready", "FE3_header"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        count = sync_media_item_crops()

        assert count == 2
        assert MediaItemCrop.objects.filter(media_item=item).count() == 2
        names = set(MediaItemCrop.objects.filter(media_item=item).values_list("name", flat=True))
        assert names == {"hd_ready", "FE3_header"}

    def test_unwanted_crop_variants_not_stored(self, monkeypatch):
        """cms, thumbnail, etc. must be silently ignored."""
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/11")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["cms", "thumbnail", "inleiding"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        count = sync_media_item_crops()

        assert count == 0
        assert MediaItemCrop.objects.count() == 0

    def test_updates_existing_crop_instead_of_creating_duplicate(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        item = _foto_item("/api/v1/media/items/20")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)

        # Run twice
        sync_media_item_crops()
        sync_media_item_crops()

        # Still only one row
        assert MediaItemCrop.objects.filter(media_item=item, name="hd_ready").count() == 1

    def test_returns_correct_count_for_multiple_items(self, monkeypatch):
        for i in range(3):
            _foto_item(f"/api/v1/media/items/{i}")

        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        count = sync_media_item_crops()

        # 3 items × 1 wanted crop = 3
        assert count == 3

    def test_import_log_success_status(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/30")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.status == ImportLog.Status.SUCCESS
        assert log.records_imported == 1
        assert log.records_failed == 0
        assert log.finished_at >= log.started_at

    def test_image_path_stored_in_crop_row(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        item = _foto_item("/api/v1/media/items/40")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch, "media_crops/2024/01/test_hd_ready.jpg")

        sync_media_item_crops()

        crop = MediaItemCrop.objects.get(media_item=item, name="hd_ready")
        assert str(crop.image) == "media_crops/2024/01/test_hd_ready.jpg"

    def test_storage_save_called_with_image_bytes(self, monkeypatch):
        _foto_item("/api/v1/media/items/50")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch, b"real-image-data")
        storage = _patch_storage(monkeypatch)

        sync_media_item_crops()

        assert storage.save.called
        # The ContentFile content must match the downloaded bytes
        args = storage.save.call_args
        content_file = args[0][1]
        assert content_file.read() == b"real-image-data"

    def test_logs_created_debug_message(self, monkeypatch, caplog):
        _foto_item("/api/v1/media/items/60")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)
        caplog.set_level(logging.DEBUG, logger=viernulvier.logger.name)

        sync_media_item_crops()

        assert any("Created" in r.message and "hd_ready" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# sync_media_item_crops - 304 Not Modified
# ---------------------------------------------------------------------------


class TestSyncCrops304:
    def test_304_skips_item_without_error(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/100")
        _patch_session(monkeypatch)
        # _fetch_with_retry returns (None, ...) on 304
        monkeypatch.setattr(
            viernulvier,
            "_fetch_with_retry",
            lambda session, url, *args, **kwargs: (None, "some-etag"),
        )

        count = sync_media_item_crops()

        assert count == 0
        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.status == ImportLog.Status.SUCCESS
        assert log.records_failed == 0

    def test_304_calls_on_progress(self, monkeypatch):
        _foto_item("/api/v1/media/items/101")
        _patch_session(monkeypatch)
        monkeypatch.setattr(
            viernulvier,
            "_fetch_with_retry",
            lambda session, url, *args, **kwargs: (None, None),
        )

        calls = []
        sync_media_item_crops(on_progress=lambda saved, total: calls.append((saved, total)))

        assert calls == [(1, 1)]


# ---------------------------------------------------------------------------
# sync_media_item_crops - fetch errors
# ---------------------------------------------------------------------------


class TestSyncCropsFetchErrors:
    def test_scraper_error_increments_error_count(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/200")
        _patch_session(monkeypatch)
        monkeypatch.setattr(
            viernulvier,
            "_fetch_with_retry",
            lambda *a, **k: (_ for _ in ()).throw(viernulvier.ScraperError("API down")),
        )

        count = sync_media_item_crops()

        assert count == 0
        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.records_failed == 1
        assert log.status == ImportLog.Status.FAILED

    def test_fetch_error_message_stored_in_log(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/201")
        _patch_session(monkeypatch)

        def raise_error(session, url, *args, **kwargs):
            raise viernulvier.ScraperError("connection timeout")

        monkeypatch.setattr(viernulvier, "_fetch_with_retry", raise_error)

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert "connection timeout" in log.error_message

    def test_fetch_error_logs_error_message(self, monkeypatch, caplog):
        _foto_item("/api/v1/media/items/202")
        _patch_session(monkeypatch)

        def raise_error(session, url, *args, **kwargs):
            raise viernulvier.ScraperError("boom")

        monkeypatch.setattr(viernulvier, "_fetch_with_retry", raise_error)
        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        sync_media_item_crops()

        assert any("Failed to fetch media item" in r.message for r in caplog.records)

    def test_one_fetch_error_does_not_stop_other_items(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        fail_item = _foto_item("/api/v1/media/items/203")
        ok_item = _foto_item("/api/v1/media/items/204")

        _patch_session(monkeypatch)
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        def selective_fetch(session, url, *args, **kwargs):
            if "203" in url:
                raise viernulvier.ScraperError("item 203 failed")
            return ({"crops": _crop_payload(["hd_ready"])}, None)

        monkeypatch.setattr(viernulvier, "_fetch_with_retry", selective_fetch)

        count = sync_media_item_crops()

        assert count == 1
        assert MediaItemCrop.objects.filter(media_item=ok_item).count() == 1
        assert MediaItemCrop.objects.filter(media_item=fail_item).count() == 0


# ---------------------------------------------------------------------------
# sync_media_item_crops - missing external_id
# ---------------------------------------------------------------------------


class TestSyncCropsMissingExternalId:
    def test_item_without_external_id_counted_as_error(self, monkeypatch):
        from apps.import_log.models import ImportLog

        MediaItemFactory(type="foto", external_id=None)
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": []})

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.records_failed == 1

    def test_item_without_external_id_logs_warning(self, monkeypatch, caplog):
        MediaItemFactory(type="foto", external_id=None)
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": []})
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        sync_media_item_crops()

        assert any("no external_id" in r.message for r in caplog.records)

    def test_item_without_external_id_calls_on_progress(self, monkeypatch):
        MediaItemFactory(type="foto", external_id=None)
        _patch_session(monkeypatch)
        calls = []

        sync_media_item_crops(on_progress=lambda s, t: calls.append((s, t)))

        assert calls == [(1, 1)]


# ---------------------------------------------------------------------------
# sync_media_item_crops - non-list crops payload
# ---------------------------------------------------------------------------


class TestSyncCropsNonListPayload:
    def test_dict_crops_value_skipped_gracefully(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/300")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": {"unexpected": "dict"}})

        count = sync_media_item_crops()

        assert count == 0
        assert MediaItemCrop.objects.count() == 0

    def test_no_crops_key_in_response_produces_no_rows(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/301")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"title": "no crops key"})

        count = sync_media_item_crops()

        assert count == 0
        assert MediaItemCrop.objects.count() == 0

    def test_non_dict_crop_entry_skipped(self, monkeypatch):
        """Individual crop entries that are not dicts are silently skipped."""
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/302")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": ["not-a-dict", None, 42]})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        count = sync_media_item_crops()

        assert count == 0
        assert MediaItemCrop.objects.count() == 0


# ---------------------------------------------------------------------------
# sync_media_item_crops - missing crop URL
# ---------------------------------------------------------------------------


class TestSyncCropsMissingUrl:
    def test_crop_without_url_skipped_with_warning(self, monkeypatch, caplog):
        _foto_item("/api/v1/media/items/400")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": [{"name": "hd_ready", "url": ""}]})
        caplog.set_level(logging.WARNING, logger=viernulvier.logger.name)

        count = sync_media_item_crops()

        assert count == 0
        assert any("no URL" in r.message for r in caplog.records)

    def test_crop_without_url_field_skipped(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/401")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": [{"name": "hd_ready"}]})

        sync_media_item_crops()

        assert MediaItemCrop.objects.count() == 0


# ---------------------------------------------------------------------------
# sync_media_item_crops - download failures
# ---------------------------------------------------------------------------


class TestSyncCropsDownloadFailures:
    def test_download_failure_increments_error_count(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/500")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch, return_value=None)  # simulate failure

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.records_failed == 1

    def test_download_failure_does_not_create_db_row(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/501")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch, return_value=None)

        sync_media_item_crops()

        assert MediaItemCrop.objects.count() == 0

    def test_download_failure_error_message_in_log(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/502")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch, return_value=None)

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert "Download failed" in log.error_message

    def test_one_download_fails_other_crop_still_saved(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        item = _foto_item("/api/v1/media/items/503")
        _patch_session(monkeypatch)
        _patch_fetch(
            monkeypatch,
            {
                "crops": [
                    {"name": "hd_ready", "url": "https://cdn.example.com/ok.jpg"},
                    {"name": "FE3_header", "url": "https://cdn.example.com/fail.jpg"},
                ]
            },
        )
        _patch_storage(monkeypatch)

        def selective_download(session, url):
            if "fail" in url:
                return None
            return b"good-bytes"

        monkeypatch.setattr(viernulvier, "_download_image", selective_download)

        count = sync_media_item_crops()

        assert count == 1
        assert MediaItemCrop.objects.filter(media_item=item, name="hd_ready").exists()
        assert not MediaItemCrop.objects.filter(media_item=item, name="FE3_header").exists()


# ---------------------------------------------------------------------------
# sync_media_item_crops - storage / save errors
# ---------------------------------------------------------------------------


class TestSyncCropsSaveErrors:
    def test_storage_exception_increments_error_count(self, monkeypatch):
        from apps.import_log.models import ImportLog
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/600")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)

        # Make storage.save raise
        image_field = MediaItemCrop._meta.get_field("image")
        mock_storage = MagicMock()
        mock_storage.save.side_effect = OSError("disk full")
        monkeypatch.setattr(image_field, "storage", mock_storage)

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.records_failed == 1

    def test_storage_exception_logged(self, monkeypatch, caplog):
        from apps.media_library.models import MediaItemCrop

        _foto_item("/api/v1/media/items/601")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)

        image_field = MediaItemCrop._meta.get_field("image")
        mock_storage = MagicMock()
        mock_storage.save.side_effect = OSError("disk full")
        monkeypatch.setattr(image_field, "storage", mock_storage)
        caplog.set_level(logging.ERROR, logger=viernulvier.logger.name)

        sync_media_item_crops()

        assert any("Error saving crop" in r.message for r in caplog.records)

    def test_save_error_does_not_stop_next_item(self, monkeypatch):
        from apps.media_library.models import MediaItemCrop

        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)

        image_field = MediaItemCrop._meta.get_field("image")
        call_count = [0]
        mock_storage = MagicMock()

        def selective_save(upload_name, content_file):
            call_count[0] += 1
            if call_count[0] == 1:
                raise OSError("disk full on first item")
            return f"media_crops/{call_count[0]}.jpg"

        mock_storage.save.side_effect = selective_save
        monkeypatch.setattr(image_field, "storage", mock_storage)

        count = sync_media_item_crops()

        assert count == 1
        assert MediaItemCrop.objects.count() == 1


# ---------------------------------------------------------------------------
# sync_media_item_crops - on_progress callback
# ---------------------------------------------------------------------------


class TestSyncCropsOnProgress:
    def test_on_progress_called_once_per_media_item(self, monkeypatch):
        for i in range(3):
            _foto_item(f"/api/v1/media/items/{i}")

        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        calls = []
        sync_media_item_crops(on_progress=lambda s, t: calls.append((s, t)))

        assert len(calls) == 3
        totals = {t for _, t in calls}
        assert totals == {3}

    def test_on_progress_called_with_ascending_index(self, monkeypatch):
        for i in range(2):
            _foto_item(f"/api/v1/media/items/{i}")

        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        calls = []
        sync_media_item_crops(on_progress=lambda s, t: calls.append(s))

        assert calls == [1, 2]

    def test_on_progress_called_even_on_304(self, monkeypatch):
        _foto_item("/api/v1/media/items/1")
        _patch_session(monkeypatch)
        monkeypatch.setattr(viernulvier, "_fetch_with_retry", lambda *a, **k: (None, None))

        calls = []
        sync_media_item_crops(on_progress=lambda s, t: calls.append((s, t)))

        assert calls == [(1, 1)]

    def test_on_progress_called_on_fetch_error(self, monkeypatch):
        _foto_item("/api/v1/media/items/1")
        _patch_session(monkeypatch)

        def raise_error(*a, **k):
            raise viernulvier.ScraperError("boom")

        monkeypatch.setattr(viernulvier, "_fetch_with_retry", raise_error)

        calls = []
        sync_media_item_crops(on_progress=lambda s, t: calls.append((s, t)))

        assert calls == [(1, 1)]


# ---------------------------------------------------------------------------
# sync_media_item_crops - ImportLog states
# ---------------------------------------------------------------------------


class TestSyncCropsImportLog:
    def test_partial_success_when_some_downloads_fail(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/700")
        _patch_session(monkeypatch)
        _patch_fetch(
            monkeypatch,
            {
                "crops": [
                    {"name": "hd_ready", "url": "https://cdn.example.com/ok.jpg"},
                    {"name": "FE3_header", "url": "https://cdn.example.com/bad.jpg"},
                ]
            },
        )
        _patch_storage(monkeypatch)

        def selective_download(session, url):
            return None if "bad" in url else b"bytes"

        monkeypatch.setattr(viernulvier, "_download_image", selective_download)

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.status == ImportLog.Status.PARTIAL_SUCCESS
        assert log.records_imported == 1
        assert log.records_failed == 1

    def test_failed_status_when_all_downloads_fail(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/800")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready", "FE3_header"])})
        _patch_download(monkeypatch, return_value=None)

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.status == ImportLog.Status.FAILED
        assert log.records_imported == 0

    def test_import_log_timestamps_sequential(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _foto_item("/api/v1/media/items/900")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.finished_at >= log.started_at

    def test_import_log_records_total_equals_foto_item_count(self, monkeypatch):
        from apps.import_log.models import ImportLog

        for i in range(4):
            _foto_item(f"/api/v1/media/items/{i}")

        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": []})

        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.records_total == 4

    def test_source_field_is_correct(self, monkeypatch):
        from apps.import_log.models import ImportLog

        _patch_session(monkeypatch)
        sync_media_item_crops()

        log = ImportLog.objects.get(source="viernulvier:media_item_crops")
        assert log.source == "viernulvier:media_item_crops"

    def test_completion_logged(self, monkeypatch, caplog):
        _foto_item("/api/v1/media/items/1")
        _patch_session(monkeypatch)
        _patch_fetch(monkeypatch, {"crops": _crop_payload(["hd_ready"])})
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)
        caplog.set_level(logging.INFO, logger=viernulvier.logger.name)

        sync_media_item_crops()

        assert any("Crop sync complete" in r.message and "saved=1" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# sync_media_item_crops - external_id URL construction
# ---------------------------------------------------------------------------


class TestSyncCropsUrlConstruction:
    def test_relative_external_id_prepends_base_domain(self, monkeypatch):
        """Relative external_ids like /api/v1/media/items/X must be prepended with BASE_DOMAIN."""
        _foto_item("/api/v1/media/items/999")
        _patch_session(monkeypatch)
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        fetched_urls = []

        def capturing_fetch(session, url, *args, **kwargs):
            fetched_urls.append(url)
            return ({"crops": []}, None)

        monkeypatch.setattr(viernulvier, "_fetch_with_retry", capturing_fetch)

        sync_media_item_crops()

        assert fetched_urls
        assert fetched_urls[0].startswith("https://www.viernulvier.gent")
        assert "999" in fetched_urls[0]

    def test_absolute_external_id_used_as_is(self, monkeypatch):
        """If external_id is already a full URL it should not be double-prepended."""
        _foto_item("https://www.viernulvier.gent/api/v1/media/items/888")
        _patch_session(monkeypatch)
        _patch_download(monkeypatch)
        _patch_storage(monkeypatch)

        fetched_urls = []

        def capturing_fetch(session, url, *args, **kwargs):
            fetched_urls.append(url)
            return ({"crops": []}, None)

        monkeypatch.setattr(viernulvier, "_fetch_with_retry", capturing_fetch)

        sync_media_item_crops()

        assert fetched_urls[0] == "https://www.viernulvier.gent/api/v1/media/items/888"
