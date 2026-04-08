"""Normalization helpers for legacy CSV fields and values."""

from __future__ import annotations

from datetime import UTC
from hashlib import sha256
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.imports.scrapers.viernulvier import clean_string


def _normalise_cell(value: Any) -> str:
    r"""Clean and normalize a single CSV cell value.

    Removes whitespace and replaces the legacy null marker '\\N' with empty string.

    Args:
        value: The value to normalize.

    Returns:
        The normalized string value.
    """
    text = clean_string(value)
    if text == "\\N":
        return ""
    return text


def _normalise_multiline_text(value: Any) -> str:
    """Clean and normalize multiline text from a CSV cell.

    Removes escape sequences, extra whitespace, and empty lines.

    Args:
        value: The multiline value to normalize.

    Returns:
        The normalized text with lines joined by newlines.
    """
    text = _normalise_cell(value)
    if not text:
        return ""

    cleaned_lines = []
    for line in text.replace("\\\r\n", "\n").replace("\\\n", "\n").splitlines():
        stripped = line.strip()
        if not stripped or stripped == "\\":
            continue
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines).strip()


def _split_genres(value: Any) -> list[str]:
    """Split a comma-separated genre string into individual genre labels.

    Args:
        value: The comma-separated genre value.

    Returns:
        List of individual genre labels, with whitespace trimmed.
    """
    raw = _normalise_cell(value)
    if not raw:
        return []
    return [genre.strip() for genre in raw.split(",") if genre.strip()]


def _parse_legacy_datetime(value: Any) -> Any | None:
    """Parse a datetime string from legacy CSV data.

    Handles special cases like null markers, zero timestamps, and epoch dates.
    Converts naive datetimes to timezone-aware datetimes in UTC.

    Args:
        value: The datetime string to parse.

    Returns:
        A timezone-aware datetime object, or None if the value is invalid or a null marker.
    """
    text = _normalise_cell(value)
    if not text or text.startswith("0000-") or text == "1970-01-01 00:00:00":
        return None

    try:
        parsed = parse_datetime(text)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, UTC)
    return parsed


def _event_external_id(production_id: str, starts_at: Any | None, ends_at: Any | None, hall_name: str) -> str:
    """Generate a deterministic external ID for a legacy event.

    Creates a SHA256 hash-based ID from production ID, start/end times, and hall name.

    Args:
        production_id: The external ID of the production.
        starts_at: The event start datetime, or None.
        ends_at: The event end datetime, or None.
        hall_name: The name of the hall where the event takes place.

    Returns:
        A unique string ID in the format 'legacy-event:{sha256_hash}'.
    """
    payload = "|".join(
        [
            production_id,
            starts_at.isoformat() if starts_at else "",
            ends_at.isoformat() if ends_at else "",
            hall_name.strip().lower(),
        ],
    )
    return f"legacy-event:{sha256(payload.encode('utf-8')).hexdigest()}"
