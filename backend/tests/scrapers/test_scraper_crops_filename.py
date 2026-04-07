"""Tests for `_derive_crop_filename`."""

from __future__ import annotations

import pytest

from apps.imports.scrapers.viernulvier import _derive_crop_filename


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
