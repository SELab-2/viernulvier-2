"""Normalization helpers for legacy CSV fields and values."""

from __future__ import annotations

from datetime import UTC
from hashlib import sha256
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.imports.scrapers.viernulvier import clean_string


def _normalise_cell(value: Any) -> str:
    text = clean_string(value)
    if text == "\\N":
        return ""
    return text


def _normalise_multiline_text(value: Any) -> str:
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
    raw = _normalise_cell(value)
    if not raw:
        return []
    return [genre.strip() for genre in raw.split(",") if genre.strip()]


def _parse_legacy_datetime(value: Any) -> Any | None:
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
    payload = "|".join(
        [
            production_id,
            starts_at.isoformat() if starts_at else "",
            ends_at.isoformat() if ends_at else "",
            hall_name.strip().lower(),
        ],
    )
    return f"legacy-event:{sha256(payload.encode('utf-8')).hexdigest()}"
