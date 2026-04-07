"""Importer for the legacy Viernulvier CSV exports bundled with the project."""

from __future__ import annotations

import csv
from datetime import UTC, timedelta
from hashlib import sha256
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

from apps.events.models import Event
from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from apps.import_log.models import ImportLog
from apps.imports.scrapers.viernulvier import clean_string
from apps.imports.scrapers.viernulvier_import_log import finalize_import_log
from apps.languages.models import Language
from apps.locations.models import Hall, HallTranslation
from apps.productions.models import Production, ProductionGenre, ProductionTranslation

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LEGACY_PRODUCTION_ORIGINAL_CSV = PACKAGE_ROOT / "Productions - output.csv"
LEGACY_PRODUCTION_CSV = PACKAGE_ROOT / "Productions - converted.csv"
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


def _iter_csv_rows(csv_path: Path) -> Iterable[dict[str, Any]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing headers in {csv_path.name}")
        yield from reader


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing headers in {csv_path.name}")
        return sum(1 for _ in reader)


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
        raise ValueError(
            f"Production external_id={production_external_id} not found (legacy data may be incomplete or from a different era)"
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


def _import_legacy_csv_rows(
    *,
    source_name: str,
    rows: Iterable[dict[str, Any]],
    row_handler: Any,
    partial_error_label: str,
    failed_error_label: str,
    dry_run: bool,
    total_rows: int | None = None,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> int:
    import_log = ImportLog.objects.create(
        source=f"legacy_csv:{source_name}",
        status=ImportLog.Status.IN_PROGRESS,
        started_at=timezone.now(),
    )

    saved = 0
    total = 0
    try:
        for row in rows:
            total += 1
            try:
                with transaction.atomic():
                    saved_row = row_handler(row, dry_run=dry_run)
            except Exception as exc:
                logger.exception("Legacy CSV row import failed for %s at row %s", source_name, total)
                import_log.status = ImportLog.Status.FAILED
                import_log.finished_at = timezone.now()
                import_log.records_total = total
                import_log.records_imported = saved
                import_log.records_failed = 1
                import_log.error_message = f"Row {total}: {exc}"
                import_log.save()
                raise

            if saved_row:
                saved += 1
            if progress_callback:
                progress_callback(total, total_rows)
    except Exception as exc:
        if import_log.status != ImportLog.Status.FAILED:
            import_log.status = ImportLog.Status.FAILED
            import_log.finished_at = timezone.now()
            import_log.records_total = total
            import_log.records_imported = saved
            import_log.records_failed = 0
            import_log.error_message = str(exc)
            import_log.save()
        raise

    finalize_import_log(
        import_log=import_log,
        total=total,
        imported=saved,
        errors=0,
        error_messages=[],
        timezone_module=timezone,
        partial_error_label=partial_error_label,
        failed_error_label=failed_error_label,
    )
    return saved


def _import_legacy_csv_file(
    csv_path: Path,
    *,
    row_handler: Any,
    partial_error_label: str,
    failed_error_label: str,
    dry_run: bool,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> int:
    total_rows = _count_csv_rows(csv_path) if progress_callback else None
    return _import_legacy_csv_rows(
        source_name=csv_path.name,
        rows=_iter_csv_rows(csv_path),
        row_handler=row_handler,
        partial_error_label=partial_error_label,
        failed_error_label=failed_error_label,
        dry_run=dry_run,
        total_rows=total_rows,
        progress_callback=progress_callback,
    )


def import_legacy_csv_file(
    csv_path: Path | str,
    *,
    dry_run: bool = False,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> int:
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
            progress_callback=progress_callback,
        )
    if kind == "events":
        return _import_legacy_csv_file(
            path,
            row_handler=_import_legacy_event_row,
            partial_error_label="event rows failed",
            failed_error_label="event rows failed",
            dry_run=dry_run,
            progress_callback=progress_callback,
        )
    raise ValueError(f"Unsupported CSV kind: {kind}")


def import_bundled_legacy_csv_files(
    *,
    dry_run: bool = False,
    base_dir: Path | None = None,
    only: str | None = None,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> int:
    """Import the legacy CSV files bundled with the backend package."""
    root = base_dir or PACKAGE_ROOT
    productions_original_path = root / LEGACY_PRODUCTION_ORIGINAL_CSV.name
    productions_fallback_path = root / LEGACY_PRODUCTION_CSV.name
    productions_path = productions_original_path if productions_original_path.exists() else productions_fallback_path
    events_path = root / LEGACY_EVENT_CSV.name

    csv_paths: list[Path]
    if only == "productions":
        csv_paths = [productions_path]
    elif only == "events":
        csv_paths = [events_path]
    else:
        csv_paths = [productions_path, events_path]

    total_rows = sum(_count_csv_rows(csv_path) for csv_path in csv_paths) if progress_callback else None
    processed_offset = 0
    imported_total = 0

    for csv_path in csv_paths:
        file_processed = 0

        def _file_progress(processed: int, _total: int | None, *, offset: int = processed_offset) -> None:
            nonlocal file_processed
            file_processed = processed
            if progress_callback:
                progress_callback(offset + processed, total_rows)

        imported_total += import_legacy_csv_file(
            csv_path,
            dry_run=dry_run,
            progress_callback=_file_progress if progress_callback else None,
        )
        processed_offset += file_processed

    return imported_total
