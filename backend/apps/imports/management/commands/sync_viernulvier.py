"""Django management command: sync_viernulvier

Fetches all configured endpoints from the Viernulvier / Peppered API and
upserts the results into the local database.

Usage examples:
    python manage.py sync_viernulvier
    python manage.py sync_viernulvier --only productions
    python manage.py sync_viernulvier --dry-run
    python manage.py sync_viernulvier --created-after 2024-01-01T00:00:00Z
    python manage.py sync_viernulvier --starts-after 2024-06-01T00:00:00Z --only events

File path:
    apps/imports/management/commands/sync_viernulvier.py
"""

import time
from typing import Any, Callable, Optional

from django.core.management.base import BaseCommand

from apps.events.models import Event, EventPrice
from apps.genres.models import Genre, GenreUseAs, GenreTranslation
from apps.imports.scrapers.viernulvier import (
    M2MConfig,
    ModelSyncConfig,
    TranslationConfig,
    nee_ja_to_bool,
    normalize_performer_type,
    normalize_url,
    sync_viernulvier,
    clean_vendor_id
)
from apps.locations.models import (
    Hall,
    HallTranslation,
    Location,
    LocationTranslation,
    Space,
    SpaceTranslation,
)
from apps.media_library.models import MediaGallery, MediaItem, MediaItemTranslation
from apps.pricing.models import Price, PriceRank, PriceRankTranslation, PriceTranslation
from apps.productions.models import (
    Production,
    ProductionGenre,
    ProductionTranslation,
    UitDatabaseTheme,
    UitDatabaseType,
)
from apps.tags.models import Tag, TagTranslation

# tqdm is optional — degrade gracefully to a simple counter if not installed
try:
    from tqdm import tqdm as _tqdm

    def _make_progress_bar(name: str, total: int):  # type: ignore[return]
        """Return a tqdm bar or a no-op context manager."""
        return _tqdm(total=total, desc=name, unit="records", leave=False)

except ImportError:
    _tqdm = None  # type: ignore[assignment]

    def _make_progress_bar(name: str, total: int):  # type: ignore[return]
        return None


# ---------------------------------------------------------------------------
# FK resolvers
# ---------------------------------------------------------------------------


def _resolve_genre_use_as(raw_value: Any) -> Optional[int]:
    """Resolve the GenreUseAs FK by name, creating the row if needed."""
    name = str(raw_value).strip() if raw_value else "unknown"
    obj, _ = GenreUseAs.objects.get_or_create(name=name)
    return obj.pk


# ---------------------------------------------------------------------------
# Sync configurations
# ---------------------------------------------------------------------------

UITDATABASE_THEME_CONFIG = ModelSyncConfig(
    field_map={"@id": "external_id", "name": "name", "cdb_cat_id": None},
)

UITDATABASE_TYPE_CONFIG = ModelSyncConfig(
    field_map={"@id": "external_id", "name": "name", "cdb_cat_id": None},
)

GENRE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "type": "type",
        "use_as": "use_as",
        "vendor_id": "vendor_id",
        "name": None,        # flat dict → TranslationConfig
        "slug": None,        # no field in GenreTranslation
        "description": None, # no field in GenreTranslation
    },
    fk_resolvers={"use_as": _resolve_genre_use_as},
    value_transforms={"vendor_id": clean_vendor_id},
    translations=[
        TranslationConfig("name", GenreTranslation, "genre", "name", "language_id"),
    ],
)

TAG_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "source": "source",
        "sourceType": "source_type",   # camelCase → snake_case
        "enable": "is_enabled",        # API: "enable" string → model: bool
        "external": "is_external",
        "url": "url",
        "type": "type",
        "code": None,
        "name": None,
        "short_description": None,
        "url_title": None,
        "gallery": None,
        "expires_after": None,
        "automatically_assigned": None,
    },
    value_transforms={"is_enabled": nee_ja_to_bool},
    translations=[
        TranslationConfig("name", TagTranslation, "tag", "name", "language_id"),
        TranslationConfig("short_description", TagTranslation, "tag", "short_description", "language_id"),
        TranslationConfig("url_title", TagTranslation, "tag", "url_title", "language_id"),
    ],
)

LOCATION_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "street": "street",
        "number": "number",
        "postal_code": "postal_code",
        "city": "city",
        "country": "country",
        "phone_1": "phone_1",
        "phone_2": "phone_2",
        "own_location": "is_own_location",  # API: string → model: bool
        "name": None,
        "code": None,
        "uitdatabank_id": None,
        "spaces": None,  # reverse relation, not a FK on Location
    },
    value_transforms={"is_own_location": nee_ja_to_bool},
    translations=[
        TranslationConfig("name", LocationTranslation, "location", "name", "language_id"),
    ],
)

SPACE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "location": "location",  # FK → Location
        "vendor_id": None,
        "name": None,
        "halls": None,  # reverse relation
    },
    translations=[
        TranslationConfig("name", SpaceTranslation, "space", "name", "language_id"),
    ],
)

HALL_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "space": "space",  # FK → Space
        "seat_selection": "seat_selection",
        "open_seating": "open_seating",
        "vendor_id": None,
        "box_office_id": None,
        "name": None,
        "remark": None,
    },
    value_transforms={
        "seat_selection": nee_ja_to_bool,
        "open_seating": nee_ja_to_bool,
    },
    translations=[
        TranslationConfig("name", HallTranslation, "hall", "name", "language_id"),
        TranslationConfig("remark", HallTranslation, "hall", "remark", "language_id"),
    ],
)

MEDIA_GALLERY_CONFIG = ModelSyncConfig(
    field_map={"@id": "external_id", "name": "name", "items": None},
)

MEDIA_ITEM_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "type": "type",
        "original_filename": "original_filename",
        "position": "position",
        "width": "width",
        "height": "height",
        "format": "format",
        "gallery": "gallery",  # FK → MediaGallery
        "title": None,
        "description": None,
        "credits": None,
        "link": None,
    },
    translations=[
        TranslationConfig("title", MediaItemTranslation, "media_item", "title", "language_id"),
        TranslationConfig("description", MediaItemTranslation, "media_item", "description", "language_id"),
        TranslationConfig("credits", MediaItemTranslation, "media_item", "credits", "language_id"),
        TranslationConfig("link", MediaItemTranslation, "media_item", "link", "language_id"),
    ],
)

PRICE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "type": "type",
        "visibility": "visibility",
        "membership": "membership",
        "minimum": "minimum",
        "maximum": "maximum",
        "step": "step",
        "order": "sort_order",  # API: "order" → model: "sort_order"
        "cineville_box": "cineville_box",
        "code": None,
        "description": None,
        "auto_select_combo": None,
        "include_in_price_range": None,
    },
    translations=[
        TranslationConfig("description", PriceTranslation, "price", "description", "language_id"),
    ],
)

PRICE_RANK_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "position": "position",
        "sold_out_buffer": "sold_out_buffer",
        "code": None,
        "description": None,
    },
    translations=[
        TranslationConfig("description", PriceRankTranslation, "price_rank", "description", "language_id"),
    ],
)

PRODUCTION_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "attendance_mode": "attendance_mode",
        "performer_type": "performer_type",
        "uitdatabank_theme": "uit_database_theme",  # FK → UitDatabaseTheme
        "uitdatabank_type": "uit_database_type",    # FK → UitDatabaseType
        "media_gallery": "media_gallery",            # FK → MediaGallery
        # Not in our model
        "vendor_id": None,
        "box_office_id": None,
        "performer_field": None,
        "review_gallery": None,
        "poster_gallery": None,
        "uitdatabank_keywords": None,
        "events": None,   # reverse relation
        "genres": None,   # M2M → handled via M2MConfig below
        # Flat dicts → TranslationConfigs below
        "supertitle": None,
        "title": None,
        "artist": None,
        "meta_title": None,
        "meta_description": None,
        "tagline": None,
        "teaser": None,
        "description": None,
        "description_extra": None,
        "description_2": None,
        "description_short": None,
        "video_1": None,
        "video_2": None,
        "quote": None,
        "quote_source": None,
        "programme": None,
        "info": None,
        "eticket_info": None,
        "custom_data": None,
    },
    value_transforms={"performer_type": normalize_performer_type},
    translations=[
        TranslationConfig("supertitle", ProductionTranslation, "production", "supertitle", "language_id"),
        TranslationConfig("title", ProductionTranslation, "production", "title", "language_id"),
        # API uses "artist"; model uses "artist_name"
        TranslationConfig("artist", ProductionTranslation, "production", "artist_name", "language_id"),
        TranslationConfig("tagline", ProductionTranslation, "production", "tagline", "language_id"),
        TranslationConfig("teaser", ProductionTranslation, "production", "teaser", "language_id"),
        TranslationConfig("description", ProductionTranslation, "production", "description", "language_id"),
        TranslationConfig("description_short", ProductionTranslation, "production", "description_short", "language_id"),
        TranslationConfig("description_extra", ProductionTranslation, "production", "description_extra", "language_id"),
        TranslationConfig("description_2", ProductionTranslation, "production", "description_2", "language_id"),
        TranslationConfig("meta_title", ProductionTranslation, "production", "meta_title", "language_id"),
        TranslationConfig("meta_description", ProductionTranslation, "production", "meta_description", "language_id"),
        TranslationConfig(
            "video_1", ProductionTranslation, "production", "video_1", "language_id",
            value_transforms={"video_1": normalize_url},
        ),
        TranslationConfig(
            "video_2", ProductionTranslation, "production", "video_2", "language_id",
            value_transforms={"video_2": normalize_url},
        ),
    ],
    m2m=[
        M2MConfig(
            api_key="genres",
            related_model=Genre,
            through_model=ProductionGenre,
            parent_fk="production",
            related_fk="genre",
            related_lookup_field="external_id",
            extra_fields={"position": "position"},
        ),
    ],
)


def _is_not_longterm(item: dict) -> bool:
    """Filter out long-term productions (they use a different sync flow)."""
    production = item.get("production") or {}
    api_id = production.get("@id", "") if isinstance(production, dict) else str(production)
    return "/longterm/" not in api_id


EVENT_CONFIG = ModelSyncConfig(
    item_filter=_is_not_longterm,
    field_map={
        "@id": "external_id",
        "production": "production",  # FK → Production (embedded object with @id)
        "hall": "hall",              # FK → Hall (nullable)
        "starts_at": "starts_at",
        "ends_at": "ends_at",
        # Not in our model
        "intermission_at": None,
        "doors_at": None,
        "box_office_id": None,
        "vendor_id": None,
        "max_tickets_per_order": None,
        "uitdatabank_id": None,
        "secure": None,
        "sms_verification": None,
        "status": None,
        "prices": None,            # synced separately via /events/prices
        "info": None,
        "eticket_info": None,
        "external_order_url": None,
    },
)

EVENT_PRICE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "event": "event",          # FK → Event
        "price": "price",          # FK → Price
        "rank": "price_rank",      # FK → PriceRank (API: "rank" → model: "price_rank")
        "amount": "amount",
        "available": "available",
        "expires_at": None,
        "created_at": None,
        "updated_at": None,
        "contingent_id": None,
        "box_office_id": None,
    },
)

# ---------------------------------------------------------------------------
# Sync steps — order matters: leaf models (no FKs) must come first
# ---------------------------------------------------------------------------

SYNC_STEPS = [
    ("uitdatabank_themes", UitDatabaseTheme, UITDATABASE_THEME_CONFIG, "/uitdatabank/themes"),
    ("uitdatabank_types",  UitDatabaseType,  UITDATABASE_TYPE_CONFIG,  "/uitdatabank/types"),
    ("genres",             Genre,            GENRE_CONFIG,             "/genres"),
    ("tags",               Tag,              TAG_CONFIG,               "/tags"),
    ("locations",          Location,         LOCATION_CONFIG,          "/locations"),
    ("spaces",             Space,            SPACE_CONFIG,             "/spaces"),
    ("halls",              Hall,             HALL_CONFIG,              "/halls"),
    ("media_galleries",    MediaGallery,     MEDIA_GALLERY_CONFIG,     "/media/galleries"),
    ("media_items",        MediaItem,        MEDIA_ITEM_CONFIG,        "/media/items"),
    ("prices",             Price,            PRICE_CONFIG,             "/prices"),
    ("price_ranks",        PriceRank,        PRICE_RANK_CONFIG,        "/prices/ranks"),
    ("productions",        Production,       PRODUCTION_CONFIG,        "/productions"),
    ("events",             Event,            EVENT_CONFIG,             "/events"),
    ("event_prices",       EventPrice,       EVENT_PRICE_CONFIG,       "/events/prices"),
]


# ---------------------------------------------------------------------------
# Management command
# ---------------------------------------------------------------------------


class Command(BaseCommand):
    help = "Sync Viernulvier / Peppered API data into the local database"

    # Maps CLI filter prefixes to API field names
    FILTER_FIELDS = {
        "created": "created_at",
        "updated": "updated_at",
        "starts":  "starts_at",
        "ends":    "ends_at",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            type=str,
            metavar="STEP",
            help=(
                "Run only this sync step. "
                f"Choices: {', '.join(name for name, *_ in SYNC_STEPS)}"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Fetch and parse data but do not write anything to the database.",
        )

        # Generate --created-after, --created-before, --created-after-x, ... etc.
        for prefix in self.FILTER_FIELDS:
            for bound in ("after", "before"):
                name = f"--{prefix}-{bound}"
                parser.add_argument(
                    name,
                    type=str,
                    metavar="DATETIME",
                    help=(
                        f"Only sync records where {self.FILTER_FIELDS[prefix]} is {bound} "
                        "this timestamp, e.g. 2024-01-01T00:00:00Z"
                    ),
                )
                # Exclusive variant (strictly after/before)
                parser.add_argument(
                    f"{name}-x",
                    type=str,
                    metavar="DATETIME",
                    help=(
                        f"Only sync records where {self.FILTER_FIELDS[prefix]} is strictly "
                        f"{bound} this timestamp (exclusive), e.g. 2024-01-01T00:00:00Z"
                    ),
                )

    def handle(self, *args, **options):
        only: Optional[str] = options.get("only")
        dry_run: bool = options.get("dry_run", False)

        # Build API query parameters from filter flags
        params = {}
        for prefix, api_field in self.FILTER_FIELDS.items():
            for bound in ("after", "before"):
                value = options.get(f"{prefix}_{bound}")
                if value:
                    params[f"{api_field}[{bound}]"] = value
                strict = options.get(f"{prefix}_{bound}_x")
                if strict:
                    params[f"{api_field}[strictly_{bound}]"] = strict

        steps_to_run = [
            (name, model, config, endpoint)
            for name, model, config, endpoint in SYNC_STEPS
            if only is None or name == only
        ]

        if only and not steps_to_run:
            self.stderr.write(
                self.style.ERROR(
                    f"Unknown step '{only}'. "
                    f"Choices: {', '.join(n for n, *_ in SYNC_STEPS)}"
                )
            )
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing will be written\n"))

        # Share one ETag cache across all steps so unchanged endpoints return 304
        etag_cache: dict = {}
        total_saved = 0
        wall_start = time.monotonic()

        for name, model, config, endpoint in steps_to_run:
            self.stdout.write(f"→ {name} ", ending="")
            self.stdout.flush()

            step_start = time.monotonic()
            try:
                saved = sync_viernulvier(
                    model=model,
                    config=config,
                    endpoint=endpoint,
                    params=params,
                    dry_run=dry_run,
                    etag_cache=etag_cache,
                    on_progress=self._make_progress_callback(name),
                )
                elapsed = time.monotonic() - step_start
                total_saved += saved
                label = "would save" if dry_run else "records"
                self.stdout.write(self.style.SUCCESS(f"✓ {saved} {label} ({elapsed:.1f}s)"))
            except Exception as exc:
                elapsed = time.monotonic() - step_start
                self.stdout.write(self.style.ERROR(f"✗ FAILED after {elapsed:.1f}s: {exc}"))

        total_elapsed = time.monotonic() - wall_start
        suffix = " [DRY RUN]" if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone{suffix}. Total: {total_saved} records in {total_elapsed:.1f}s"
            )
        )

    def _make_progress_callback(self, name: str) -> Callable[[int, int], None]:
        """Return an on_progress callback that drives a tqdm bar (if available)."""
        state: dict = {"bar": None}

        def on_progress(saved: int, total: int) -> None:
            if _tqdm is None:
                # tqdm not installed — emit a simple line every 500 records
                if saved % 500 == 0 or saved == total:
                    self.stdout.write(f"  {name}: {saved}/{total}\r", ending="")
                    self.stdout.flush()
                return

            if state["bar"] is None:
                state["bar"] = _tqdm(
                    total=total,
                    desc=f"  {name}",
                    unit="records",
                    leave=False,
                )

            bar = state["bar"]
            bar.n = saved
            bar.refresh()

            if saved >= total:
                bar.close()
                state["bar"] = None

        return on_progress