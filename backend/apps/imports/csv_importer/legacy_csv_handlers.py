"""Row handlers for legacy production and event CSV imports."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from apps.events.models import Event
from apps.productions.models import Production, ProductionTranslation

from .legacy_csv_normalize import (
    _event_external_id,
    _normalise_cell,
    _normalise_multiline_text,
    _parse_legacy_datetime,
    _split_genres,
)
from .legacy_csv_relations import _ensure_language, _hall_for_name, _sync_production_genres

logger = logging.getLogger(__name__)


def _import_legacy_production_row(row: dict[str, Any], *, dry_run: bool) -> bool:
    """Import a single production row from legacy CSV data.

    Args:
        row: Dictionary containing the CSV row data.
        dry_run: If True, validate the row without saving to the database.

    Returns:
        True if the row was successfully imported or validated, False otherwise.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    external_id = _normalise_cell(row.get("ID"))
    if not external_id:
        message = f"Missing production ID in legacy CSV row: {row}"
        logger.warning(message)
        raise ValueError(message)

    title = _normalise_cell(row.get("Ondertitel"))
    artist_name = _normalise_cell(row.get("Titel"))
    description = _normalise_multiline_text(row.get("Description1"))
    description_extra = _normalise_multiline_text(row.get("Description2"))
    genres = _split_genres(row.get("Genre"))

    if dry_run:
        return True

    language = _ensure_language()
    production, _ = Production.objects.update_or_create(
        external_id=external_id,
        defaults={
            "attendance_mode": "",
            "performer_type": "",
            "uit_database_theme": None,
            "uit_database_type": None,
            "media_gallery": None,
        },
    )

    ProductionTranslation.objects.update_or_create(
        production=production,
        language=language,
        defaults={
            "supertitle": artist_name,
            "title": title,
            "artist_name": artist_name,
            "tagline": "",
            "teaser": "",
            "description": description,
            "description_short": description[:1000],
            "description_extra": description_extra,
            "description_2": "",
            "video_1": "",
            "video_2": "",
            "meta_title": title,
            "meta_description": description_extra[:500],
        },
    )

    _sync_production_genres(production, genres, language)
    return True


def _import_legacy_event_row(row: dict[str, Any], *, dry_run: bool) -> bool:
    """Import a single event row from legacy CSV data.

    Args:
        row: Dictionary containing the CSV row data.
        dry_run: If True, validate the row without saving to the database.

    Returns:
        True if the row was successfully imported or validated, False otherwise.

    Raises:
        ValueError: If required fields are missing, invalid, or related production not found.
    """
    production_external_id = _normalise_cell(row.get("Production"))
    if not production_external_id:
        raise ValueError(f"Missing production reference in legacy event CSV row: {row}")

    production = Production.objects.filter(external_id=production_external_id).first()
    if production is None:
        raise ValueError(
            f"Production external_id={production_external_id} not found (legacy data may be incomplete or from a different era)",
        )

    starts_at = _parse_legacy_datetime(row.get("Starttime"))
    ends_at = _parse_legacy_datetime(row.get("Endtime"))
    if starts_at and ends_at and ends_at < starts_at:
        ends_at += timedelta(days=1)
    if starts_at and ends_at and ends_at < starts_at:
        ends_at = None

    hall_name = _normalise_cell(row.get("Hall"))

    if dry_run:
        return True

    language = _ensure_language()
    hall = _hall_for_name(hall_name, language)
    external_id = _event_external_id(production_external_id, starts_at, ends_at, hall_name)

    Event.objects.update_or_create(
        external_id=external_id,
        defaults={
            "production": production,
            "hall": hall,
            "starts_at": starts_at,
            "ends_at": ends_at,
        },
    )
    return True
