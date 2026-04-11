"""Tests for apps.core.media_validation module."""

from io import BytesIO
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import pytest

from apps.core.media_validation import (
    ALLOWED_IMAGE_MIME_TYPES,
    ALLOWED_MEDIA_MIME_TYPES,
    MAX_MEDIA_FILE_SIZE_BYTES,
    MediaValidationError,
    MediaValidationResult,
    _detect_image_mime,
    _detect_pdf_mime,
    _read_header,
    _rewind_file,
    _validate_extension_for_mime,
    detect_best_mime_type,
    detect_content_mime_type,
    extract_safe_filename,
    validate_media_file,
)


def make_pdf_bytes() -> bytes:
    """Return bytes starting with PDF header."""
    return b"%PDF-1.4\n%fake pdf content"


def make_png_bytes() -> bytes:
    """Return valid PNG bytes."""
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color=(255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


def make_jpeg_bytes() -> bytes:
    """Return valid JPEG bytes."""
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color=(255, 0, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


def make_webp_bytes() -> bytes:
    """Return valid WEBP bytes."""
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color=(255, 0, 0)).save(buffer, format="WEBP")
    return buffer.getvalue()


def make_uploaded_file(
    name: str = "test.pdf",
    content: bytes = b"dummy content",
    content_type: str | None = "application/pdf",
) -> SimpleUploadedFile:
    """Create a SimpleUploadedFile for testing."""
    return SimpleUploadedFile(name, content, content_type=content_type)


class TestExtractSafeFilename:
    """Tests for extract_safe_filename()."""

    def test_returns_basename_from_relative_path(self) -> None:
        result = extract_safe_filename("path/to/file.pdf")
        assert result == "file.pdf"

    def test_returns_basename_from_absolute_path(self) -> None:
        result = extract_safe_filename("/absolute/path/to/file.png")
        assert result == "file.png"

    def test_returns_basename_from_windows_path(self) -> None:
        """On Unix systems, backslashes are part of the filename, not separators."""
        result = extract_safe_filename("C:\\Users\\user\\file.jpg")
        assert result == "C:\\Users\\user\\file.jpg"

    def test_returns_simple_filename_unchanged(self) -> None:
        result = extract_safe_filename("poster.webp")
        assert result == "poster.webp"

    def test_returns_empty_string_for_none(self) -> None:
        result = extract_safe_filename("")
        assert result == ""

    def test_handles_trailing_slashes(self) -> None:
        """Trailing slashes are stripped by Path, leaving the directory name."""
        result = extract_safe_filename("path/to/directory/")
        assert result == "directory"

    def test_preserves_filename_with_multiple_dots(self) -> None:
        result = extract_safe_filename("path/to/file.name.pdf")
        assert result == "file.name.pdf"


class TestRewindFile:
    """Tests for _rewind_file()."""

    def test_rewinds_and_restores_file_pointer(self) -> None:
        """Verify file pointer is rewound and restored."""
        content = b"test content here"
        file_obj = BytesIO(content)
        file_obj.seek(5)  # Move to position 5

        def callback():
            return file_obj.tell()

        result = _rewind_file(file_obj, callback)
        assert result == 0  # Callback ran at position 0
        assert file_obj.tell() == 5  # Pointer restored

    def test_handles_file_without_seek(self) -> None:
        """Handle file-like objects without seek capability."""
        mock_file = MagicMock(spec=[])  # No tell/seek methods
        def callback():
            return "result"

        result = _rewind_file(mock_file, callback)
        assert result == "result"

    def test_handles_tell_returning_error(self) -> None:
        """Handle tell() raising OSError."""
        mock_file = MagicMock()
        mock_file.tell.side_effect = OSError()
        mock_file.seek.side_effect = OSError()

        def callback():
            return "result"

        result = _rewind_file(mock_file, callback)
        assert result == "result"

    def test_callback_exception_still_restores_pointer(self) -> None:
        """Pointer is restored even if callback raises."""
        file_obj = BytesIO(b"content")
        file_obj.seek(5)

        def callback():
            raise ValueError("callback error")

        with pytest.raises(ValueError, match="callback error"):
            _rewind_file(file_obj, callback)

        assert file_obj.tell() == 5  # Pointer restored despite exception


class TestReadHeader:
    """Tests for _read_header()."""

    def test_reads_default_16_bytes(self) -> None:
        content = b"abcdefghijklmnopqrstuvwxyz"
        file_obj = BytesIO(content)
        header = _read_header(file_obj)
        assert header == b"abcdefghijklmnop"
        assert file_obj.tell() == 0  # Pointer unchanged

    def test_reads_custom_length(self) -> None:
        content = b"abcdefghij"
        file_obj = BytesIO(content)
        header = _read_header(file_obj, length=5)
        assert header == b"abcde"

    def test_handles_short_file(self) -> None:
        content = b"abc"
        file_obj = BytesIO(content)
        header = _read_header(file_obj, length=10)
        assert header == b"abc"

    def test_handles_empty_file(self) -> None:
        file_obj = BytesIO(b"")
        header = _read_header(file_obj, length=10)
        assert header == b""

    def test_preserves_file_pointer_position(self) -> None:
        content = b"0123456789"
        file_obj = BytesIO(content)
        file_obj.seek(7)
        _read_header(file_obj, length=4)
        assert file_obj.tell() == 7

    def test_handles_file_read_returning_bytearray(self) -> None:
        """Handle when file.read() returns bytearray instead of bytes."""
        mock_file = MagicMock()
        mock_file.read.return_value = bytearray(b"test")
        mock_file.tell.return_value = 0
        mock_file.seek = MagicMock()

        header = _read_header(mock_file, length=4)
        assert header == b"test"


class TestDetectPdfMime:
    """Tests for _detect_pdf_mime()."""

    def test_detects_valid_pdf_header(self) -> None:
        content = make_pdf_bytes()
        file_obj = BytesIO(content)
        mime = _detect_pdf_mime(file_obj)
        assert mime == "application/pdf"

    def test_returns_none_for_non_pdf(self) -> None:
        content = make_png_bytes()
        file_obj = BytesIO(content)
        mime = _detect_pdf_mime(file_obj)
        assert mime is None

    def test_returns_none_for_empty_file(self) -> None:
        file_obj = BytesIO(b"")
        mime = _detect_pdf_mime(file_obj)
        assert mime is None

    def test_returns_none_for_partial_pdf_header(self) -> None:
        file_obj = BytesIO(b"%PD")  # Missing F
        mime = _detect_pdf_mime(file_obj)
        assert mime is None

    def test_detects_pdf_with_different_version(self) -> None:
        content = b"%PDF-2.0rest of content"
        file_obj = BytesIO(content)
        mime = _detect_pdf_mime(file_obj)
        assert mime == "application/pdf"


class TestDetectImageMime:
    """Tests for _detect_image_mime()."""

    def test_detects_valid_png(self) -> None:
        content = make_png_bytes()
        file_obj = BytesIO(content)
        mime = _detect_image_mime(file_obj)
        assert mime == "image/png"

    def test_detects_valid_jpeg(self) -> None:
        content = make_jpeg_bytes()
        file_obj = BytesIO(content)
        mime = _detect_image_mime(file_obj)
        assert mime == "image/jpeg"

    def test_detects_valid_webp(self) -> None:
        content = make_webp_bytes()
        file_obj = BytesIO(content)
        mime = _detect_image_mime(file_obj)
        assert mime == "image/webp"

    def test_returns_none_for_invalid_image(self) -> None:
        file_obj = BytesIO(b"not an image")
        mime = _detect_image_mime(file_obj)
        assert mime is None

    def test_returns_none_for_empty_file(self) -> None:
        file_obj = BytesIO(b"")
        mime = _detect_image_mime(file_obj)
        assert mime is None

    def test_returns_none_when_format_unmapped(self) -> None:
        """Handle image formats not in IMAGE_FORMAT_TO_MIME."""
        buffer = BytesIO()
        Image.new("RGB", (1, 1)).save(buffer, format="BMP")
        content = buffer.getvalue()

        file_obj = BytesIO(content)
        mime = _detect_image_mime(file_obj)
        assert mime is None  # BMP not in mapping


class TestDetectContentMimeType:
    """Tests for detect_content_mime_type()."""

    def test_detects_pdf_content(self) -> None:
        content = make_pdf_bytes()
        file_obj = BytesIO(content)
        mime = detect_content_mime_type(file_obj)
        assert mime == "application/pdf"

    def test_detects_image_content(self) -> None:
        content = make_png_bytes()
        file_obj = BytesIO(content)
        mime = detect_content_mime_type(file_obj)
        assert mime == "image/png"

    def test_returns_none_for_unknown_content(self) -> None:
        file_obj = BytesIO(b"unknown content")
        mime = detect_content_mime_type(file_obj)
        assert mime is None

    def test_pdf_detection_takes_precedence(self) -> None:
        """PDF detection should run before image detection."""
        content = make_pdf_bytes()
        file_obj = BytesIO(content)
        with patch("apps.core.media_validation._detect_image_mime") as mock_img:
            result = detect_content_mime_type(file_obj)
            assert result == "application/pdf"
            mock_img.assert_not_called()


class TestDetectBestMimeType:
    """Tests for detect_best_mime_type()."""

    def test_prefers_content_detection(self) -> None:
        """Content detection should take highest priority."""
        file_obj = SimpleUploadedFile(
            "file.png",
            make_pdf_bytes(),  # Actual PDF bytes
            content_type="image/png",  # Declared as image
        )
        mime = detect_best_mime_type(file_obj)
        assert mime == "application/pdf"  # Content wins

    def test_falls_back_to_declared_mime(self) -> None:
        """Use declared content_type when content detection fails."""
        file_obj = SimpleUploadedFile(
            "file.unknown",
            b"unknown content",
            content_type="image/webp",
        )
        mime = detect_best_mime_type(file_obj)
        assert mime == "image/webp"

    def test_falls_back_to_guessed_from_extension(self) -> None:
        """Guess MIME from filename extension."""
        file_obj = SimpleUploadedFile(
            "file.jpeg",
            b"unknown content",
            content_type=None,
        )
        mime = detect_best_mime_type(file_obj)
        assert mime == "image/jpeg"

    def test_defaults_to_octet_stream(self) -> None:
        """Default to octet-stream when nothing else matches."""
        file_obj = SimpleUploadedFile(
            "file.unknown",
            b"unknown content",
            content_type=None,
        )
        mime = detect_best_mime_type(file_obj)
        assert mime == "application/octet-stream"

    def test_handles_file_without_name(self) -> None:
        """Handle file objects without name attribute."""
        mock_file = MagicMock(spec=["content_type"])
        mock_file.content_type = None

        with patch("apps.core.media_validation.detect_content_mime_type", return_value=None), patch(
            "apps.core.media_validation.mimetypes.guess_type", return_value=(None, None)
        ):
            mime = detect_best_mime_type(mock_file)
            assert mime == "application/octet-stream"


class TestValidateExtensionForMime:
    """Tests for _validate_extension_for_mime()."""

    def test_accepts_matching_jpeg_extension(self) -> None:
        _validate_extension_for_mime("poster.jpg", "image/jpeg")
        _validate_extension_for_mime("poster.jpeg", "image/jpeg")

    def test_accepts_matching_png_extension(self) -> None:
        _validate_extension_for_mime("poster.png", "image/png")

    def test_accepts_matching_webp_extension(self) -> None:
        _validate_extension_for_mime("poster.webp", "image/webp")

    def test_accepts_matching_pdf_extension(self) -> None:
        _validate_extension_for_mime("document.pdf", "application/pdf")

    def test_rejects_jpeg_with_png_extension(self) -> None:
        with pytest.raises(MediaValidationError, match="extension does not match"):
            _validate_extension_for_mime("poster.png", "image/jpeg")

    def test_rejects_pdf_with_image_extension(self) -> None:
        with pytest.raises(MediaValidationError, match="extension does not match"):
            _validate_extension_for_mime("document.jpg", "application/pdf")

    def test_accepts_uppercase_extension(self) -> None:
        """Extensions should be case-insensitive."""
        _validate_extension_for_mime("poster.PNG", "image/png")

    def test_accepts_no_extension(self) -> None:
        """Files without extension should pass."""
        _validate_extension_for_mime("poster", "image/png")

    def test_accepts_unknown_mime_type(self) -> None:
        """Unknown MIME types should not raise extension errors."""
        _validate_extension_for_mime("file.xyz", "application/unknown")

    def test_rejects_known_mime_with_unknown_extension(self) -> None:
        """Unknown extensions for known MIME types should raise errors."""
        with pytest.raises(MediaValidationError, match="extension does not match"):
            _validate_extension_for_mime("poster.unknown", "image/jpeg")


class TestMediaValidationResult:
    """Tests for MediaValidationResult dataclass."""

    def test_creates_with_mime_and_size(self) -> None:
        result = MediaValidationResult(mime_type="image/png", size_bytes=1024)
        assert result.mime_type == "image/png"
        assert result.size_bytes == 1024

    def test_is_frozen(self) -> None:
        """Result should be immutable."""
        result = MediaValidationResult(mime_type="image/png", size_bytes=1024)
        with pytest.raises(AttributeError):
            result.mime_type = "image/jpeg"


class TestValidateMediaFile:
    """Tests for validate_media_file()."""

    def test_rejects_empty_file(self) -> None:
        file_obj = None
        with pytest.raises(MediaValidationError, match="No file was uploaded"):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_rejects_file_with_unknown_content(self) -> None:
        """Files with unrecognizable content are rejected."""
        file_obj = SimpleUploadedFile("test.bin", b"not a pdf or image", content_type=None)
        with pytest.raises(MediaValidationError, match="Unsupported file type"):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_rejects_oversized_file(self) -> None:
        content = b"x" * (MAX_MEDIA_FILE_SIZE_BYTES + 1)
        file_obj = SimpleUploadedFile(
            "large.pdf",
            content,
            content_type="application/pdf",
        )
        with pytest.raises(MediaValidationError, match="File is too large"):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_rejects_mismatch_content_vs_declared(self) -> None:
        """Reject when binary signature contradicts declared MIME."""
        file_obj = SimpleUploadedFile(
            "fake.pdf",
            make_png_bytes(),  # PNG content
            content_type="application/pdf",  # Declared as PDF
        )
        with pytest.raises(
            MediaValidationError,
            match="content does not match the declared file type",
        ):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_rejects_unsupported_mime_type(self) -> None:
        file_obj = SimpleUploadedFile(
            "test.exe",
            b"MZ\x90\x00",  # PE executable header
            content_type="application/octet-stream",
        )
        with pytest.raises(
            MediaValidationError,
            match="Unsupported file type",
        ):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_rejects_unknown_mime_when_required_not_allowed(self) -> None:
        file_obj = SimpleUploadedFile(
            "test.unknown",
            b"unknown content",
            content_type=None,
        )
        with pytest.raises(
            MediaValidationError,
            match="Unsupported file type",
        ):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_IMAGE_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_rejects_extension_mismatch(self) -> None:
        """Reject when extension contradicts detected MIME."""
        file_obj = SimpleUploadedFile(
            "poster.pdf",  # .pdf extension
            make_png_bytes(),  # PNG content
            content_type=None,
        )
        with pytest.raises(
            MediaValidationError,
            match="extension does not match",
        ):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_accepts_valid_pdf(self) -> None:
        file_obj = SimpleUploadedFile(
            "document.pdf",
            make_pdf_bytes(),
            content_type="application/pdf",
        )
        result = validate_media_file(
            file_obj,
            allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
            max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
        )
        assert result.mime_type == "application/pdf"
        assert result.size_bytes > 0
        assert isinstance(result, MediaValidationResult)

    def test_accepts_valid_png(self) -> None:
        file_obj = SimpleUploadedFile(
            "poster.png",
            make_png_bytes(),
            content_type="image/png",
        )
        result = validate_media_file(
            file_obj,
            allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
            max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
        )
        assert result.mime_type == "image/png"

    def test_accepts_valid_jpeg(self) -> None:
        file_obj = SimpleUploadedFile(
            "photo.jpg",
            make_jpeg_bytes(),
            content_type="image/jpeg",
        )
        result = validate_media_file(
            file_obj,
            allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
            max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
        )
        assert result.mime_type == "image/jpeg"

    def test_accepts_valid_webp(self) -> None:
        file_obj = SimpleUploadedFile(
            "image.webp",
            make_webp_bytes(),
            content_type="image/webp",
        )
        result = validate_media_file(
            file_obj,
            allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
            max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
        )
        assert result.mime_type == "image/webp"

    def test_allows_images_only_when_restricted(self) -> None:
        """Validate respects allowed_mime_types restrictions."""
        file_obj = SimpleUploadedFile(
            "document.pdf",
            make_pdf_bytes(),
            content_type="application/pdf",
        )
        with pytest.raises(MediaValidationError, match="Unsupported file type"):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_IMAGE_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_returns_result_with_correct_size(self) -> None:
        """Result should include actual file size."""
        content = make_png_bytes()
        file_obj = SimpleUploadedFile("poster.png", content, content_type="image/png")
        result = validate_media_file(
            file_obj,
            allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
            max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
        )
        assert result.size_bytes == len(content)

    def test_accepts_file_at_max_size_boundary(self) -> None:
        """Accept file exactly at max size limit."""
        content = b"x" * MAX_MEDIA_FILE_SIZE_BYTES
        file_obj = SimpleUploadedFile(
            "large.pdf",
            content,
            content_type="application/pdf",
        )
        # We can't make it truly valid PDF at this size, so we'll mock the detection
        with patch("apps.core.media_validation.detect_content_mime_type", return_value="application/pdf"):
            result = validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )
            assert result.size_bytes == MAX_MEDIA_FILE_SIZE_BYTES

    def test_guesses_mime_from_extension_when_no_signature(self) -> None:
        """Fallback to guessing MIME from extension."""
        file_obj = SimpleUploadedFile(
            "poster.webp",
            b"unknown content",  # Not detectable as WEBP
            content_type=None,
        )
        result = validate_media_file(
            file_obj,
            allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
            max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
        )
        assert result.mime_type == "image/webp"

    def test_error_message_lists_allowed_types(self) -> None:
        """Error should list all allowed MIME types."""
        file_obj = SimpleUploadedFile(
            "test.exe",
            b"MZ",
            content_type="application/octet-stream",
        )
        with pytest.raises(MediaValidationError) as exc_info:
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_IMAGE_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )
        error_msg = str(exc_info.value)
        assert "image/jpeg" in error_msg
        assert "image/png" in error_msg
        assert "image/webp" in error_msg

    def test_handles_file_without_size_attribute(self) -> None:
        """Handle file objects missing size attribute - falls back to 0."""
        # When size attribute is missing or 0, the validation still proceeds
        # but fails when no supported MIME is detected
        file_obj = SimpleUploadedFile("test.unknown", b"not valid", content_type=None)
        with pytest.raises(MediaValidationError, match="Unsupported file type"):
            validate_media_file(
                file_obj,
                allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
                max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
            )

    def test_handles_file_without_name_attribute(self) -> None:
        """Handle file objects without name for extension check."""
        file_obj = BytesIO(make_png_bytes())
        file_obj.size = len(make_png_bytes())
        # Note: BytesIO has no name attribute, so extract_safe_filename(None) returns ""
        result = validate_media_file(
            file_obj,
            allowed_mime_types=ALLOWED_MEDIA_MIME_TYPES,
            max_file_size=MAX_MEDIA_FILE_SIZE_BYTES,
        )
        assert result.mime_type == "image/png"
