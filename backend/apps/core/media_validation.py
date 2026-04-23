"""Shared helpers for secure media file validation and MIME detection."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import mimetypes
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

MAX_MEDIA_FILE_SIZE_BYTES = 10 * 1024 * 1024

ALLOWED_MEDIA_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}

ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
}

MIME_EXTENSIONS: dict[str, set[str]] = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "application/pdf": {".pdf"},
}

IMAGE_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
}


class MediaValidationError(ValueError):
    """Raised when an uploaded media file does not pass validation."""


@dataclass(frozen=True, slots=True)
class MediaValidationResult:
    """Result payload returned by :func:`validate_media_file`."""

    mime_type: str
    size_bytes: int


def extract_safe_filename(filename: str) -> str:
    """Return a basename-only filename, stripping any client-side path parts."""
    return Path(filename or "").name


def _rewind_file(file_obj: Any, callback: Any) -> Any:
    """Run callback with file pointer rewound and restore previous pointer afterwards."""
    try:
        position = file_obj.tell()
    except (AttributeError, OSError, ValueError):
        position = None

    with suppress(AttributeError, OSError, ValueError):
        file_obj.seek(0)

    try:
        return callback()
    finally:
        if position is not None:
            with suppress(AttributeError, OSError, ValueError):
                file_obj.seek(position)


def _read_header(file_obj: Any, length: int = 16) -> bytes:
    """Read file header bytes without changing the current file pointer."""

    def _reader() -> bytes:
        data = file_obj.read(length)
        if isinstance(data, bytes):
            return data
        return bytes(data or b"")

    return _rewind_file(file_obj, _reader) or b""


def _detect_pdf_mime(file_obj: Any) -> str | None:
    """Return PDF MIME type when the file starts with a PDF signature."""
    header = _read_header(file_obj, length=8)
    if header.startswith(b"%PDF-"):
        return "application/pdf"
    return None


def _detect_image_mime(file_obj: Any) -> str | None:
    """Detect image MIME type from binary content using Pillow.

    Note: We capture the format BEFORE calling verify(), because verify()
    modifies the image state and makes further operations unsafe.
    """

    def _reader() -> str | None:
        try:
            with Image.open(file_obj) as image:
                # Get format BEFORE verify() to avoid state corruption
                image_format = (image.format or "").upper()
                # Verify integrity
                image.verify()
                return IMAGE_FORMAT_TO_MIME.get(image_format)
        except (OSError, UnidentifiedImageError, ValueError, RuntimeError):
            return None

    return _rewind_file(file_obj, _reader)


def _normalize_mime(value: Any) -> str | None:
    """Normalize MIME type by removing parameters and lowercasing.

    Handles MIME types with optional parameters like "image/jpeg; charset=binary".
    Strips whitespace, removes parameters (after semicolon), and converts to lowercase.

    Args:
        value: A MIME type string (possibly with parameters) or None.

    Returns:
        Normalized MIME type (lowercase, no parameters) or None if empty.
    """
    if not value:
        return None
    normalized = str(value).split(";", 1)[0].strip().lower()
    return normalized or None


def detect_content_mime_type(file_obj: Any) -> str | None:
    """Detect MIME type from binary signature when possible."""
    return _detect_pdf_mime(file_obj) or _detect_image_mime(file_obj)


def detect_best_mime_type(file_obj: Any) -> str:
    """Resolve MIME type from content signature, metadata, and extension fallback."""
    content_mime = detect_content_mime_type(file_obj)
    if content_mime:
        return content_mime

    declared_mime = getattr(file_obj, "content_type", None)
    if declared_mime:
        return str(declared_mime)

    guessed_mime, _ = mimetypes.guess_type(getattr(file_obj, "name", ""))
    return guessed_mime or "application/octet-stream"


def _validate_extension_for_mime(filename: str, mime_type: str) -> None:
    """Reject filename extensions that contradict the resolved MIME type."""
    extension = Path(filename).suffix.lower()
    if not extension:
        return

    allowed_extensions = MIME_EXTENSIONS.get(mime_type)
    if allowed_extensions and extension not in allowed_extensions:
        raise MediaValidationError("File extension does not match the uploaded file type.")


def validate_media_file(file_obj: Any, *, allowed_mime_types: set[str], max_file_size: int) -> MediaValidationResult:
    """Validate a media upload and return normalized metadata.

    Validation includes:
    - non-empty file
    - max file size check
    - allowed MIME type check
    - content-type mismatch detection when binary signature is known
    - extension and MIME consistency check
    """
    if not file_obj:
        raise MediaValidationError("No file was uploaded.")

    size = int(getattr(file_obj, "size", 0) or 0)
    if size <= 0:
        raise MediaValidationError("Uploaded file is empty.")
    if size > max_file_size:
        max_size_mb = max_file_size // (1024 * 1024)
        raise MediaValidationError(f"File is too large (max {max_size_mb} MB).")

    content_mime = detect_content_mime_type(file_obj)
    declared_mime = getattr(file_obj, "content_type", None)
    guessed_mime, _ = mimetypes.guess_type(getattr(file_obj, "name", ""))

    # Normalize MIME types before comparison to handle parameters and casing variations
    normalized_content_mime = _normalize_mime(content_mime)
    normalized_declared_mime = _normalize_mime(declared_mime)

    if normalized_content_mime and normalized_declared_mime and normalized_content_mime != normalized_declared_mime:
        raise MediaValidationError("Uploaded file content does not match the declared file type.")

    resolved_mime = content_mime or declared_mime or guessed_mime
    if not resolved_mime or resolved_mime not in allowed_mime_types:
        allowed_list = ", ".join(sorted(allowed_mime_types))
        raise MediaValidationError(f"Unsupported file type. Allowed types: {allowed_list}.")

    safe_filename = extract_safe_filename(getattr(file_obj, "name", ""))
    _validate_extension_for_mime(safe_filename, resolved_mime)

    return MediaValidationResult(mime_type=resolved_mime, size_bytes=size)
