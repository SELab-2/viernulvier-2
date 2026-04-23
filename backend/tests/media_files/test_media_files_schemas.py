"""Tests for apps.media_files.schemas."""

from apps.media_files import schemas
from apps.media_files.serializers import MediaFileSerializer, MediaFileUploadSerializer


def test_response_examples_include_description_and_not_uploaded_by() -> None:
    assert "description" in schemas._MEDIA_FILE_RESPONSE.value
    assert "description" in schemas._MEDIA_FILE_IMAGE_RESPONSE.value
    assert "uploaded_by" not in schemas._MEDIA_FILE_RESPONSE.value
    assert "uploaded_by" not in schemas._MEDIA_FILE_IMAGE_RESPONSE.value


def test_examples_use_filename_field() -> None:
    assert schemas._MEDIA_FILE_RESPONSE.value["filename"] == "season-brochure-2026.pdf"
    assert schemas._MEDIA_FILE_IMAGE_RESPONSE.value["filename"] == "poster-premiere.png"


def test_request_examples_only_include_expected_payloads() -> None:
    assert schemas._MEDIA_FILE_INPUT.value == {
        "file": "<binary file>",
        "description": "Optional context about the file contents.",
    }
    assert schemas._MEDIA_FILE_PARTIAL_INPUT.value == {
        "external_id": "print-archive-2026-001",
        "description": "Final Dutch brochure version for the 2026 season.",
    }
    assert schemas._MEDIA_FILE_PUT_INPUT.value == {
        "file": "<binary file>",
        "description": "Updated file with revised print margins.",
    }


def test_partial_update_example_mentions_description() -> None:
    assert "description" in schemas._MEDIA_FILE_PARTIAL_INPUT.value


def test_schema_objects_reference_expected_serializers() -> None:
    assert schemas.MediaFileSerializer is MediaFileSerializer
    assert schemas.MediaFileUploadSerializer is MediaFileUploadSerializer
    assert schemas.media_file_schema is not None
