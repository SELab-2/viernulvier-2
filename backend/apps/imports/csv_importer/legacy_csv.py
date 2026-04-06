"""Importer for the legacy Viernulvier CSV exports bundled with the project."""

from __future__ import annotations

import csv
from datetime import UTC, timedelta
from hashlib import sha256
import logging
from pathlib import Path
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

from apps.events.models import Event
from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from apps.import_log.models import ImportLog
from apps.imports.scrapers.viernulvier import clean_string
from apps.imports.scrapers.viernulvier_import_log import append_limited_error, finalize_import_log
from apps.languages.models import Language
from apps.locations.models import Hall, HallTranslation
from apps.productions.models import Production, ProductionGenre, ProductionTranslation

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LEGACY_PRODUCTION_ORIGINAL_CSV = PACKAGE_ROOT / "Productions - output-orig.csv"
LEGACY_PRODUCTION_CSV = PACKAGE_ROOT / "Productions - output.csv"
LEGACY_EVENT_CSV = PACKAGE_ROOT / "Events - voorstellingen.csv"
LEGACY_LANGUAGE_CODE = "nl"
LEGACY_LANGUAGE_NAME = "Dutch"
LEGACY_LANGUAGE_ACTIVE = True
LEGACY_PRODUCTION_FIELDNAMES = ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"]
LEGACY_PRODUCTION_HEADERS = set(LEGACY_PRODUCTION_FIELDNAMES)
LEGACY_EVENT_HEADERS = {"Starttime", "Endtime", "Hall", "Production"}


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
    if not text or text in {"0000-00-00 00:00:00", "1970-01-01 00:00:00"}:
        return None

    parsed = parse_datetime(text)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, UTC)
    return parsed


def _append_legacy_production_continuation(current_row: dict[str, Any], continuation_row: dict[str, Any]) -> None:
    """Merge a malformed continuation row into the previous production row."""
    chunks = [
        _normalise_multiline_text(continuation_row.get("Titel")),
        _normalise_multiline_text(continuation_row.get("Ondertitel")),
        _normalise_multiline_text(continuation_row.get("Description1")),
        _normalise_multiline_text(continuation_row.get("Description2")),
    ]
    continuation_text = "\n".join(chunk for chunk in chunks if chunk).strip()
    if not continuation_text:
        return

    base = _normalise_multiline_text(current_row.get("Description1"))
    current_row["Description1"] = f"{base}\n{continuation_text}".strip() if base else continuation_text


def _convert_legacy_production_csv(source_path: Path, destination_path: Path) -> None:
    """Convert the original production export into a clean CSV that can be imported directly."""
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing headers in {source_path.name}")

        cleaned_rows: list[dict[str, Any]] = []
        current_row: dict[str, Any] | None = None
        for raw_row in reader:
            row = {field: raw_row.get(field, "") for field in LEGACY_PRODUCTION_FIELDNAMES}
            production_id = _normalise_cell(row.get("ID"))
            if production_id:
                if current_row is not None:
                    cleaned_rows.append(current_row)
                current_row = row
                continue

            if current_row is not None:
                _append_legacy_production_continuation(current_row, row)

        if current_row is not None:
            cleaned_rows.append(current_row)

    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEGACY_PRODUCTION_FIELDNAMES)
        writer.writeheader()
        writer.writerows(cleaned_rows)


def _resolve_production_csv_path(root: Path) -> Path:
    """Resolve the production CSV path, converting the original raw export when available."""
    original_path = root / LEGACY_PRODUCTION_ORIGINAL_CSV.name
    formatted_path = root / LEGACY_PRODUCTION_CSV.name
    if original_path.exists():
        _convert_legacy_production_csv(original_path, formatted_path)
        return formatted_path
    return formatted_path


def _ensure_language() -> Language:
    language, _ = Language.objects.get_or_create(
        code=LEGACY_LANGUAGE_CODE,
        defaults={"name": LEGACY_LANGUAGE_NAME, "is_active": LEGACY_LANGUAGE_ACTIVE},
    )
    return language


def _ensure_genre(label: str, language: Language) -> Genre:
    genre_use_as, _ = GenreUseAs.objects.get_or_create(name="genre")
    genre_type = slugify(label)[:50] or label.strip().lower().replace(" ", "_")[:50] or "genre"

    translation = (
        GenreTranslation.objects.select_related("genre")
        .filter(language=language, name=label[:50], genre__use_as=genre_use_as)
        .order_by("genre_id")
        .first()
    )
    if translation:
        return translation.genre

    genre = Genre.objects.filter(type=genre_type, use_as=genre_use_as).order_by("id").first()
    if genre is None:
        genre = Genre.objects.create(type=genre_type, use_as=genre_use_as)

    GenreTranslation.objects.update_or_create(genre=genre, language=language, defaults={"name": label[:50]})
    return genre


def _sync_production_genres(production: Production, genre_labels: list[str], language: Language) -> None:
    ProductionGenre.objects.filter(production=production).delete()
    links = []
    for position, label in enumerate(genre_labels):
        genre = _ensure_genre(label, language)
        links.append(ProductionGenre(production=production, genre=genre, position=position))
    if links:
        ProductionGenre.objects.bulk_create(links)


def _hall_for_name(name: str, language: Language) -> Hall | None:
    if not name:
        return None

    translation = HallTranslation.objects.select_related("hall").filter(name=name).first()
    if translation:
        return translation.hall

    hall = Hall.objects.create(space=None, seat_selection=False, open_seating=False)
    HallTranslation.objects.create(hall=hall, language=language, name=name)
    return hall


def _event_external_id(production_id: str, starts_at: Any | None, ends_at: Any | None, hall_name: str) -> str:
    payload = "|".join(
        [
            production_id,
            starts_at.isoformat() if starts_at else "",
            ends_at.isoformat() if ends_at else "",
            hall_name.strip().lower(),
        ]
    )
    return f"legacy-event:{sha256(payload.encode('utf-8')).hexdigest()}"


def _import_legacy_production_row(row: dict[str, Any], *, dry_run: bool) -> bool:
    external_id = _normalise_cell(row.get("ID"))
    if not external_id:
        raise ValueError(f"Missing production ID in legacy CSV row: {row}")

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
    production_external_id = _normalise_cell(row.get("Production"))
    if not production_external_id:
        raise ValueError(f"Missing production reference in legacy event CSV row: {row}")

    production = Production.objects.filter(external_id=production_external_id).first()
    if production is None:
        raise ValueError(f"Production external_id={production_external_id} not found for legacy event CSV row: {row}")

    starts_at = _parse_legacy_datetime(row.get("Starttime"))
    ends_at = _parse_legacy_datetime(row.get("Endtime"))
    if starts_at and ends_at and ends_at < starts_at:
        ends_at += timedelta(days=1)

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


def detect_legacy_csv_kind(csv_path: Path | str) -> str:
    """Identify which legacy dataset a CSV file contains."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = {clean_string(header) for header in (reader.fieldnames or []) if header}

    if headers == LEGACY_PRODUCTION_HEADERS:
        return "productions"
    if headers == LEGACY_EVENT_HEADERS:
        return "events"
    raise ValueError(f"Unsupported legacy CSV headers in {path.name}: {sorted(headers)}")


def _import_legacy_csv_file(
    csv_path: Path,
    *,
    row_handler: Any,
    partial_error_label: str,
    failed_error_label: str,
    dry_run: bool,
) -> int:
    import_log = ImportLog.objects.create(
        source=f"legacy_csv:{csv_path.name}",
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone.now(),
    )

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except Exception as exc:
        import_log.status = ImportLog.Status.FAILED
        import_log.finished_at = timezone.now()
        import_log.error_message = str(exc)
        import_log.save()
        raise

    saved = 0
    errors = 0
    error_messages: list[str] = []

    for row in rows:
        try:
            with transaction.atomic():
                saved_row = row_handler(row, dry_run=dry_run)
        except Exception as exc:  # pragma: no cover - exercised through import log assertions in tests
            errors += 1
            append_limited_error(error_messages, str(exc))
            logger.exception("Legacy CSV row import failed for %s", csv_path.name)
        else:
            if saved_row:
                saved += 1

    finalize_import_log(
        import_log=import_log,
        total=len(rows),
        imported=saved,
        errors=errors,
        error_messages=error_messages,
        timezone_module=timezone,
        partial_error_label=partial_error_label,
        failed_error_label=failed_error_label,
    )
    return saved


def import_legacy_csv_file(csv_path: Path | str, *, dry_run: bool = False) -> int:
    """Import a single legacy CSV export into the Django database."""
    path = Path(csv_path)
    kind = detect_legacy_csv_kind(path)
    if kind == "productions":
        return _import_legacy_csv_file(
            path,
            row_handler=_import_legacy_production_row,
            partial_error_label="production rows failed",
            failed_error_label="production rows failed",
            dry_run=dry_run,
        )
    if kind == "events":
        return _import_legacy_csv_file(
            path,
            row_handler=_import_legacy_event_row,
            partial_error_label="event rows failed",
            failed_error_label="event rows failed",
            dry_run=dry_run,
        )
    raise ValueError(f"Unsupported CSV kind: {kind}")


def import_bundled_legacy_csv_files(*, dry_run: bool = False, base_dir: Path | None = None, only: str | None = None) -> int:
    """Import the legacy CSV files bundled with the backend package."""
    root = base_dir or PACKAGE_ROOT
    productions_path = _resolve_production_csv_path(root)

    if only == "productions":
        return import_legacy_csv_file(productions_path, dry_run=dry_run)
    if only == "events":
        return import_legacy_csv_file(root / "Events - voorstellingen.csv", dry_run=dry_run)
    return sum(
        import_legacy_csv_file(csv_path, dry_run=dry_run)
        for csv_path in (productions_path, root / "Events - voorstellingen.csv")
    )
