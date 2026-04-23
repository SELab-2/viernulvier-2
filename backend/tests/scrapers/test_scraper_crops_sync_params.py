"""Param-filter and API-scoping tests for `sync_media_item_crops`."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

from django.core.exceptions import FieldDoesNotExist
import pytest

from apps.import_log.models import ImportLog
from apps.imports.scrapers import viernulvier
from apps.imports.scrapers.viernulvier import sync_media_item_crops
from apps.media_library import models as media_models


@pytest.mark.django_db
def test_sync_crops_params_skip_missing_fields_and_apply_supported_ones(monkeypatch) -> None:
    class FakeQuerySet:
        def __init__(self) -> None:
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
        return datetime(2024, 1, 1, tzinfo=UTC)

    monkeypatch.setattr(viernulvier, "parse_datetime", fake_parse_datetime)
    monkeypatch.setattr(viernulvier, "fetch_viernulvier", lambda **_kw: [])

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
    assert {"updated_at__gte": datetime(2024, 1, 1, tzinfo=UTC)} in fake_qs.filter_calls
    assert {"updated_at__lte": datetime(2024, 1, 1, tzinfo=UTC)} in fake_qs.filter_calls
    assert all("created_at" not in next(iter(call)) for call in fake_qs.filter_calls)


@pytest.mark.django_db
def test_sync_crops_params_are_forwarded_to_api_and_limit_item_fetches(monkeypatch) -> None:
    class FakeQuerySet:
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
    monkeypatch.setattr(viernulvier, "_build_session", Mock)

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
    assert captured["params"] == {
        "created_at[after]": "2024-01-01T00:00:00+00:00",
        "updated_at[after]": "2024-01-01T00:00:00+00:00",
    }
    assert fetched_urls == ["https://www.viernulvier.gent/api/v1/media/items/1"]


@pytest.mark.django_db
def test_sync_crops_params_skip_non_image_api_items(monkeypatch) -> None:
    class FakeQuerySet:
        def values(self, *_args, **_kwargs):
            return []

    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: FakeQuerySet())
    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", lambda name: Mock() if name == "updated_at" else None)
    monkeypatch.setattr(viernulvier, "parse_datetime", Mock(return_value=None))
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [
            {"@id": "/api/v1/media/items/vid-1", "type": "video"},
            {"@id": "/api/v1/media/items/img-1", "type": "foto"},
        ],
    )

    fetched_urls = []

    def fake_fetch_with_retry(session, url, params=None, etag=None):
        fetched_urls.append(url)
        return ({"crops": []}, None)

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch_with_retry)

    result = sync_media_item_crops(params={"updated_at[after]": "2024-01-01T00:00:00+00:00"})

    assert result == 0
    assert fetched_urls == ["https://www.viernulvier.gent/api/v1/media/items/img-1"]


@pytest.mark.django_db
def test_sync_crops_params_skip_api_items_without_external_id(monkeypatch) -> None:
    class FakeQuerySet:
        def filter(self, **_kwargs):
            return self

        def values(self, *_args, **_kwargs):
            return [{"pk": 1, "external_id": "/api/v1/media/items/1"}]

    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: FakeQuerySet())

    def fake_get_field(_name):
        return Mock()

    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", fake_get_field)
    monkeypatch.setattr(viernulvier, "parse_datetime", Mock(return_value=datetime(2024, 1, 1, tzinfo=UTC)))
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [{"@id": "", "type": "foto"}],
    )

    result = sync_media_item_crops(params={"updated_at[after]": "2024-01-01T00:00:00+00:00"})

    assert result == 0


@pytest.mark.django_db
def test_sync_crops_params_skip_non_dict_api_items(monkeypatch) -> None:
    class FakeQuerySet:
        def values(self, *_args, **_kwargs):
            return []

    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: FakeQuerySet())
    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", lambda name: Mock() if name == "updated_at" else None)
    monkeypatch.setattr(viernulvier, "parse_datetime", Mock(return_value=None))
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [
            "not-a-dict",
            {"@id": "/api/v1/media/items/img-2", "type": "foto"},
        ],
    )

    fetched_urls = []

    def fake_fetch_with_retry(session, url, params=None, etag=None):
        fetched_urls.append(url)
        return ({"crops": []}, None)

    monkeypatch.setattr(viernulvier, "_fetch_with_retry", fake_fetch_with_retry)

    result = sync_media_item_crops(params={"updated_at[after]": "2024-01-01T00:00:00+00:00"})

    assert result == 0
    assert fetched_urls == ["https://www.viernulvier.gent/api/v1/media/items/img-2"]


@pytest.mark.django_db
def test_sync_crops_params_fetch_error_marks_import_log_failed(monkeypatch) -> None:
    class FakeQuerySet:
        def values(self, *_args, **_kwargs):
            return []

    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: FakeQuerySet())
    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", lambda name: Mock() if name == "updated_at" else None)
    monkeypatch.setattr(viernulvier, "parse_datetime", Mock(return_value=None))

    monkeypatch.setattr(viernulvier, "fetch_viernulvier", Mock(side_effect=RuntimeError("api down")))

    with pytest.raises(RuntimeError, match="api down"):
        sync_media_item_crops(params={"updated_at[after]": "2024-01-01T00:00:00+00:00"})

    log = ImportLog.objects.latest("started_at")
    assert log.status == ImportLog.Status.FAILED
    assert log.error_message == "api down"
    assert log.finished_at is not None


@pytest.mark.django_db
def test_sync_crops_params_upserts_missing_media_item_dependency(monkeypatch) -> None:
    monkeypatch.setattr(viernulvier, "_build_session", Mock)
    monkeypatch.setattr(
        viernulvier,
        "fetch_viernulvier",
        lambda **_kw: [{"@id": "/api/v1/media/items/42", "type": "foto"}],
    )
    monkeypatch.setattr(
        viernulvier,
        "_fetch_with_retry",
        lambda *_a, **_kw: (
            {
                "type": "foto",
                "original_filename": "missing.jpg",
                "position": 0,
                "format": "jpg",
                "crops": [{"name": "hd_ready", "url": "https://cdn.example.com/img.jpg"}],
            },
            None,
        ),
    )
    monkeypatch.setattr(viernulvier, "_download_image", lambda *_a: b"img")

    media_upsert = Mock(return_value=(Mock(pk=4242), True))
    monkeypatch.setattr(media_models.MediaItem.objects, "update_or_create", media_upsert)

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

    result = sync_media_item_crops(params={"updated_at[after]": "2024-01-01T00:00:00+00:00"})

    assert result == 1
    media_upsert.assert_called_once()
    mock_crop_cls.objects.update_or_create.assert_called_once_with(
        media_item_id=4242,
        name="hd_ready",
        defaults={"image": "crops/img.jpg"},
    )


@pytest.mark.django_db
def test_sync_crops_params_skip_filter_when_fake_parse_datetime_raises_valueerror(monkeypatch) -> None:
    class FakeQuerySet:
        def __init__(self) -> None:
            self.filter_calls = []

        def values(self, *_args, **_kwargs):
            return []

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)
    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", lambda name: Mock() if name == "updated_at" else None)

    def fake_parse_datetime(value) -> None:
        if value == "raise-value":
            raise ValueError("bad datetime")

    monkeypatch.setattr(viernulvier, "parse_datetime", fake_parse_datetime)
    monkeypatch.setattr(viernulvier, "fetch_viernulvier", lambda **_kw: [])

    result = sync_media_item_crops(params={"updated_at[strictly_before]": "raise-value"})

    assert result == 0
    assert fake_qs.filter_calls == []


@pytest.mark.django_db
def test_sync_crops_params_skip_filter_when_fake_get_field_raises_fielddoesnotexist(monkeypatch) -> None:
    class FakeQuerySet:
        def __init__(self) -> None:
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

    parse_dt = Mock(return_value=datetime(2024, 1, 1, tzinfo=UTC))
    monkeypatch.setattr(viernulvier, "parse_datetime", parse_dt)
    monkeypatch.setattr(viernulvier, "fetch_viernulvier", lambda **_kw: [])

    result = sync_media_item_crops(
        params={
            "created_at[before]": "2024-01-01T00:00:00+00:00",
            "updated_at[before]": "2024-01-01T00:00:00+00:00",
        }
    )

    assert result == 0
    assert fake_qs.filter_calls == [{"updated_at__lte": datetime(2024, 1, 1, tzinfo=UTC)}]
    parse_dt.assert_called_once_with("2024-01-01T00:00:00+00:00")


@pytest.mark.django_db
def test_sync_crops_params_ignores_non_matching_param_key(monkeypatch) -> None:
    class FakeQuerySet:
        def __init__(self) -> None:
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
def test_sync_crops_params_skips_filter_when_datetime_is_none(monkeypatch) -> None:
    class FakeQuerySet:
        def __init__(self) -> None:
            self.filter_calls = []

        def values(self, *_args, **_kwargs):
            return []

    fake_qs = FakeQuerySet()
    monkeypatch.setattr(media_models.MediaItem.objects, "filter", lambda **_kw: fake_qs)
    monkeypatch.setattr(media_models.MediaItem._meta, "get_field", lambda name: Mock() if name == "updated_at" else None)

    parse_dt = Mock(return_value=None)
    monkeypatch.setattr(viernulvier, "parse_datetime", parse_dt)
    monkeypatch.setattr(viernulvier, "fetch_viernulvier", lambda **_kw: [])

    result = sync_media_item_crops(params={"updated_at[after]": "not-a-datetime"})

    assert result == 0
    assert fake_qs.filter_calls == []
    parse_dt.assert_called_once_with("not-a-datetime")


@pytest.mark.django_db
def test_sync_crops_params_skips_filter_when_datetime_raises_valueerror(monkeypatch) -> None:
    class FakeQuerySet:
        def __init__(self) -> None:
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
    monkeypatch.setattr(viernulvier, "fetch_viernulvier", lambda **_kw: [])

    result = sync_media_item_crops(params={"updated_at[before]": "raise-value"})

    assert result == 0
    assert fake_qs.filter_calls == []
    parse_dt.assert_called_once_with("raise-value")
