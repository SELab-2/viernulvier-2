"""Django management command: sync_viernulvier

Usage:
    python manage.py sync_viernulvier
    python manage.py sync_viernulvier --only productions
    python manage.py sync_viernulvier --since 2024-01-01T00:00:00Z

Path:
    apps/imports/management/commands/sync_viernulvier.py

Required empty files:
    apps/imports/management/__init__.py
    apps/imports/management/commands/__init__.py
"""

from typing import Any, Optional

from django.core.management.base import BaseCommand

from apps.events.models import Event, EventPrice
from apps.genres.models import Genre, GenreUseAs, GenreTranslation
from apps.imports.scrapers.viernulvier import (
    ModelSyncConfig,
    TranslationConfig,
    M2MConfig,
    normalize_url,
    normalize_performer_type,
    sync_viernulvier,
)
from apps.locations.models import (
    Location,
    LocationTranslation,
    Space,
    SpaceTranslation,
    Hall,
    HallTranslation,
)
from apps.media_library.models import (
    MediaGallery,
    MediaItem,
    MediaItemTranslation,
)
from apps.pricing.models import (
    Price,
    PriceTranslation,
    PriceRank,
    PriceRankTranslation,
)
from apps.productions.models import (
    UitDatabaseTheme,
    UitDatabaseType,
    Production,
    ProductionTranslation,
    ProductionGenre,
)
from apps.tags.models import Tag, TagTranslation


# ===========================================================================
# Shared value transforms
# ===========================================================================


def nee_ja_to_bool(value) -> bool:
    """Convert various API truthy/falsy values to bool.

    Supports:
        "ja", "nee"
        "true", "false"
        "1", "0"
        bool values
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"ja", "true", "1"}:
            return True
        if v in {"nee", "false", "0", ""}:
            return False

    return bool(value)


# ===========================================================================
# UITDATABANK THEME
# API: { "@id", "name": "string", "cdb_cat_id": "string" }
# Endpoint: /uitdatabank/themes
# ===========================================================================
UITDATABASE_THEME_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "name": "name",
        "cdb_cat_id": None,  # not in our model
    },
)


# ===========================================================================
# UITDATABANK TYPE
# API: { "@id", "name": "string", "cdb_cat_id": "string" }
# Endpoint: /uitdatabank/types
# ===========================================================================
UITDATABASE_TYPE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "name": "name",
        "cdb_cat_id": None,
    },
)


# ===========================================================================
# GENRE
# API: {
#   "@id", "type": "string",
#   "use_as": "string",          <- plain string, no URL
#   "vendor_id": "string",
#   "name": {"nl": "...", ...},  <- flat dict
#   "slug": {"nl": "...", ...},  <- flat dict, no field in GenreTranslation
#   "description": {"nl": "..."} <- flat dict, no field in GenreTranslation
# }
# Endpoint: /genres
#
# use_as is a plain string (e.g. "genre", "tag").
# fk_resolver creates GenreUseAs via get_or_create.
# ===========================================================================
def _resolve_genre_use_as(raw_value: Any) -> Optional[int]:
    name = str(raw_value).strip() if raw_value else "unknown"
    obj, _ = GenreUseAs.objects.get_or_create(name=name)
    return obj.pk


GENRE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "type": "type",
        "use_as": "use_as",  # FK — resolved via fk_resolver
        "vendor_id": None,
        "name": None,  # flat dict → handled via TranslationConfig
        "slug": None,  # no field in GenreTranslation
        "description": None,  # no field in GenreTranslation
    },
    fk_resolvers={
        "use_as": _resolve_genre_use_as,
    },
    translations=[
        TranslationConfig(
            api_key="name",
            model=GenreTranslation,
            parent_fk="genre",
            flat_field="name",
            language_fk="language_id",
        ),
    ],
)


# ===========================================================================
# TAG
# API: {
#   "@id", "source": "string", "sourceType": "string",
#   "enable": "string",          <- NOT is_enabled, NOT boolean
#   "external": true,            <- NOT is_external
#   "code": "string",
#   "name": {"nl": "...", ...},
#   "short_description": {"nl": "...", ...},
#   "url": "string",
#   "url_title": {"nl": "...", ...},
#   "gallery": "url",
#   "expires_after": 0,
#   "automatically_assigned": true
# }
# Endpoint: /tags
#
# "enable" contains a string (e.g. "ja"/"nee") -> nee_ja_to_bool
# "external" is a boolean -> direct mapping to is_external
# TagTranslation has: name, short_description, url_title
# ===========================================================================
TAG_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "source": "source",
        "sourceType": "source_type",  # camelCase in API, snake_case in model
        "enable": "is_enabled",  # API: "enable"  →  model: "is_enabled"
        "external": "is_external",  # API: "external"  →  model: "is_external"
        "url": "url",
        "type": "type",
        # Skip
        "code": None,
        "name": None,  # flat dict → TranslationConfig
        "short_description": None,  # flat dict → TranslationConfig
        "url_title": None,  # flat dict → TranslationConfig
        "gallery": None,  # no FK on Tag in our model
        "expires_after": None,
        "automatically_assigned": None,
    },
    value_transforms={
        "is_enabled": nee_ja_to_bool,
    },
    translations=[
        TranslationConfig(
            api_key="name",
            model=TagTranslation,
            parent_fk="tag",
            flat_field="name",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="short_description",
            model=TagTranslation,
            parent_fk="tag",
            flat_field="short_description",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="url_title",
            model=TagTranslation,
            parent_fk="tag",
            flat_field="url_title",
            language_fk="language_id",
        ),
    ],
)


# ===========================================================================
# LOCATION
# API: {
#   "@id", "name": {"nl": "...", ...},
#   "code": "string", "street": "string", "number": "string",
#   "postal_code": "string", "city": "string",
#   "phone_1": "string", "phone_2": "string",
#   "own_location": "nee",   <- "nee"/"ja" string → is_own_location bool
#   "country": "string",
#   "uitdatabank_id": "string",
#   "spaces": ["url", ...]   <- list of URLs, no FK on Location
# }
# Endpoint: /locations
# ===========================================================================
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
        "own_location": "is_own_location",  # API: "own_location"  →  model: "is_own_location"
        # Skip
        "name": None,  # flat dict → TranslationConfig
        "code": None,
        "uitdatabank_id": None,
        "spaces": None,  # reverse relation, not on Location
    },
    value_transforms={
        "is_own_location": nee_ja_to_bool,
    },
    translations=[
        TranslationConfig(
            api_key="name",
            model=LocationTranslation,
            parent_fk="location",
            flat_field="name",
            language_fk="language_id",
        ),
    ],
)


# ===========================================================================
# SPACE
# API: {
#   "@id", "vendor_id": "string",
#   "name": {"nl": "...", ...},
#   "location": "url",   <- FK to Location
#   "halls": ["url", ...]
# }
# Endpoint: /spaces
# ===========================================================================
SPACE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "location": "location",  # FK to Location
        # Skip
        "vendor_id": None,
        "name": None,  # flat dict → TranslationConfig
        "halls": None,  # reverse relation
    },
    translations=[
        TranslationConfig(
            api_key="name",
            model=SpaceTranslation,
            parent_fk="space",
            flat_field="name",
            language_fk="language_id",
        ),
    ],
)


# ===========================================================================
# HALL
# API: {
#   "@id", "vendor_id": "string", "box_office_id": "string",
#   "seat_selection": "nee",   <- "nee"/"ja" string → bool
#   "open_seating": "nee",     <- "nee"/"ja" string → bool
#   "name": {"nl": "...", ...},
#   "remark": {"nl": "...", ...},
#   "space": "url"   <- FK to Space
# }
# Endpoint: /halls
# ===========================================================================
HALL_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "space": "space",  # FK to Space
        "seat_selection": "seat_selection",
        "open_seating": "open_seating",
        # Skip
        "vendor_id": None,
        "box_office_id": None,
        "name": None,  # flat dict → TranslationConfig
        "remark": None,  # flat dict → TranslationConfig
    },
    value_transforms={
        "seat_selection": nee_ja_to_bool,
        "open_seating": nee_ja_to_bool,
    },
    translations=[
        TranslationConfig(
            api_key="name",
            model=HallTranslation,
            parent_fk="hall",
            flat_field="name",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="remark",
            model=HallTranslation,
            parent_fk="hall",
            flat_field="remark",
            language_fk="language_id",
        ),
    ],
)


# ===========================================================================
# MEDIA GALLERY
# API: { "@id", "name": "string", "items": ["url", ...] }
# Endpoint: /media/galleries
# ===========================================================================
MEDIA_GALLERY_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "name": "name",  # plain string, no flat dict
        "items": None,  # reverse relation
    },
)


# ===========================================================================
# MEDIA ITEM
# API: {
#   "@id", "type": "string", "original_filename": "string",
#   "position": 0, "width": 0, "height": 0, "format": "string",
#   "gallery": "url",   <- FK to MediaGallery
#   "title": {"nl": "...", ...},
#   "description": {"nl": "...", ...},
#   "credits": {"nl": "...", ...},
#   "link": {"nl": "...", ...}
# }
# Endpoint: /media/items
# ===========================================================================
MEDIA_ITEM_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "type": "type",
        "original_filename": "original_filename",
        "position": "position",
        "width": "width",
        "height": "height",
        "format": "format",
        "gallery": "gallery",  # FK to MediaGallery
        # Skip — flat dicts → TranslationConfigs
        "title": None,
        "description": None,
        "credits": None,
        "link": None,
    },
    translations=[
        TranslationConfig(
            api_key="title",
            model=MediaItemTranslation,
            parent_fk="media_item",
            flat_field="title",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="description",
            model=MediaItemTranslation,
            parent_fk="media_item",
            flat_field="description",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="credits",
            model=MediaItemTranslation,
            parent_fk="media_item",
            flat_field="credits",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="link",
            model=MediaItemTranslation,
            parent_fk="media_item",
            flat_field="link",
            language_fk="language_id",
        ),
    ],
)


# ===========================================================================
# PRICE
# API: {
#   "@id", "type": "string", "visibility": "string",
#   "code": "string",
#   "description": {"nl": "...", ...},
#   "minimum": 0, "maximum": 0, "step": 0,
#   "order": 0,                <- model: sort_order
#   "auto_select_combo": true,
#   "include_in_price_range": true,
#   "cineville_box": true,
#   "membership": "string"
# }
# Endpoint: /prices
# ===========================================================================
PRICE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "type": "type",
        "visibility": "visibility",
        "membership": "membership",
        "minimum": "minimum",
        "maximum": "maximum",
        "step": "step",
        "order": "sort_order",  # API: "order"  →  model: "sort_order"
        "cineville_box": "cineville_box",
        # Skip
        "code": None,
        "description": None,  # flat dict → TranslationConfig
        "auto_select_combo": None,
        "include_in_price_range": None,
    },
    translations=[
        TranslationConfig(
            api_key="description",
            model=PriceTranslation,
            parent_fk="price",
            flat_field="description",
            language_fk="language_id",
        ),
    ],
)


# ===========================================================================
# PRICE RANK
# API: {
#   "@id",
#   "description": {"nl": "...", ...},
#   "code": "string",
#   "position": 0,
#   "sold_out_buffer": 0
# }
# Endpoint: /prices/ranks
# ===========================================================================
PRICE_RANK_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "position": "position",
        "sold_out_buffer": "sold_out_buffer",
        # Skip
        "code": None,
        "description": None,  # flat dict → TranslationConfig
    },
    translations=[
        TranslationConfig(
            api_key="description",
            model=PriceRankTranslation,
            parent_fk="price_rank",
            flat_field="description",
            language_fk="language_id",
        ),
    ],
)


# ===========================================================================
# PRODUCTION
# API: {
#   "@id", "vendor_id", "box_office_id", "performer_field", "performer_type",
#   "attendance_mode",
#   "supertitle": {"nl": "...", ...},   <- flat dict
#   "title": {"nl": "...", ...},        <- flat dict
#   "artist": {"nl": "...", ...},       <- flat dict (model: artist_name)
#   "meta_title": {"nl": "...", ...},
#   "meta_description": {"nl": "...", ...},
#   "tagline": {"nl": "...", ...},
#   "teaser": {"nl": "...", ...},
#   "description": {"nl": "...", ...},
#   "description_extra": {"nl": "...", ...},
#   "description_2": {"nl": "...", ...},
#   "description_short": {"nl": "...", ...},
#   "video_1": {"nl": "...", ...},
#   "video_2": {"nl": "...", ...},
#   "quote", "quote_source", "programme", "info",
#   "eticket_info", "custom_data"        <- no fields in our model
#   "genres": ["url", ...],              <- M2M via ProductionGenre
#   "events": ["url", ...],              <- reverse relation, skip
#   "media_gallery": "url",              <- FK to MediaGallery
#   "review_gallery": "url",             <- no field in our model
#   "poster_gallery": "url",             <- no field in our model
#   "uitdatabank_keywords": ["url", ...],<- no field in our model
#   "uitdatabank_theme": "url",          <- FK to UitDatabaseTheme
#   "uitdatabank_type": "url"            <- FK to UitDatabaseType
# }
# Endpoint: /productions
#
# NOTE: the API has NO "tags" field on productions.
# ProductionTag relations exist only in our database, not in the API.
# ===========================================================================
PRODUCTION_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "attendance_mode": "attendance_mode",
        "performer_type": "performer_type",
        "uitdatabank_theme": "uit_database_theme",  # FK → UitDatabaseTheme
        "uitdatabank_type": "uit_database_type",  # FK → UitDatabaseType
        "media_gallery": "media_gallery",  # FK → MediaGallery
        # Skip — no field in our model
        "vendor_id": None,
        "box_office_id": None,
        "performer_field": None,
        "review_gallery": None,
        "poster_gallery": None,
        "uitdatabank_keywords": None,
        "events": None,
        "genres": None,  # M2M → handled via M2MConfig
        # Skip all flat dict fields — handled via TranslationConfigs
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
    value_transforms={
        "performer_type": normalize_performer_type
    },
    translations=[
        TranslationConfig(
            api_key="supertitle",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="supertitle",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="title",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="title",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="artist",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="artist_name",
            language_fk="language_id",
        ),  # API: "artist" → model: "artist_name"
        TranslationConfig(
            api_key="tagline",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="tagline",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="teaser",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="teaser",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="description",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="description",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="description_short",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="description_short",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="description_extra",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="description_extra",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="description_2",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="description_2",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="meta_title",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="meta_title",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="meta_description",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="meta_description",
            language_fk="language_id",
        ),
        TranslationConfig(
            api_key="video_1",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="video_1",
            language_fk="language_id",
            value_transforms={"video_1": normalize_url},
        ),
        TranslationConfig(
            api_key="video_2",
            model=ProductionTranslation,
            parent_fk="production",
            flat_field="video_2",
            language_fk="language_id",
            value_transforms={"video_2": normalize_url},
        ),
    ],
    m2m=[
        # genres is a list of URLs → ProductionGenre through table
        # NO tags — the API does not return tags on productions
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


# ===========================================================================
# EVENT
# API: {
#   "@id", "starts_at", "ends_at", "intermission_at", "doors_at",
#   "box_office_id", "vendor_id", "max_tickets_per_order",
#   "uitdatabank_id", "secure", "sms_verification",
#   "production": {},     <- embedded object with "@id"
#   "status": "url",      <- no Status model in our schema
#   "hall": "url",        <- FK to Hall (nullable)
#   "prices": ["url", ...], <- EventPrice relations, synced separately
#   "info": {"nl": "...", ...},
#   "eticket_info": {"nl": "...", ...},
#   "external_order_url": {"nl": "...", ...}
# }
# Endpoint: /events
#
# EventPrice is NOT synchronized here — use the /events/prices endpoint.
# ===========================================================================
def _is_not_longterm(item: dict) -> bool:
    """Filter function to exclude longterm productions based on the production's @id containing "/longterm/"."""
    production = item.get("production") or {}
    api_id = production.get("@id", "") if isinstance(production, dict) else str(production)
    return "/longterm/" not in api_id

EVENT_CONFIG = ModelSyncConfig(
    item_filter=_is_not_longterm,
    field_map={
        "@id": "external_id",
        "production": "production",  # FK → Production (embedded object with @id)
        "hall": "hall",  # FK → Hall (nullable, URL string)
        "starts_at": "starts_at",
        "ends_at": "ends_at",
        # Skip
        "intermission_at": None,
        "doors_at": None,
        "box_office_id": None,
        "vendor_id": None,
        "max_tickets_per_order": None,
        "uitdatabank_id": None,
        "secure": None,
        "sms_verification": None,
        "status": None,  # no Status model in our schema
        "prices": None,  # sync separately via /events/prices
        "info": None,  # no translation model for events
        "eticket_info": None,
        "external_order_url": None,
    },
)


# ===========================================================================
# EVENT PRICE
# API: {
#   "@id",
#   "event": "url",        <- FK to Event
#   "price": "url",        <- FK to PriceRank
#   "amount": 0,
#   "available": 0,
#   "expires_at": "datetime",
#   "created_at": "datetime",
#   "updated_at": "datetime",
#   "contingent_id": "string",    <- no field in our model
#   "box_office_id": "string",   <- no field in our model
#   "rank": 0                   <- no field in our model
# }
# Endpoint: /events/prices
#
EVENT_PRICE_CONFIG = ModelSyncConfig(
    field_map={
        "@id": "external_id",
        "event": "event",  # FK → Event
        "price": "price",  # FK → Price
        "rank": "price_rank", # FK → PriceRank
        "amount": "amount",
        "available": "available",
        "expires_at": None,
        "created_at": None,
        "updated_at": None,
        "contingent_id": None,
        "box_office_id": None,
        "rank": None,
    }
)


# ===========================================================================
# Sync steps in required order
# Leaf models (no FK's to other models) ALWAYS come first.
# ===========================================================================

SYNC_STEPS = [
    # name                  model               config                      endpoint
    (
        "uitdatabank_themes",
        UitDatabaseTheme,
        UITDATABASE_THEME_CONFIG,
        "/uitdatabank/themes",
    ),
    (
        "uitdatabank_types",
        UitDatabaseType,
        UITDATABASE_TYPE_CONFIG,
        "/uitdatabank/types",
    ),
    ("genres", Genre, GENRE_CONFIG, "/genres"),
    ("tags", Tag, TAG_CONFIG, "/tags"),
    ("locations", Location, LOCATION_CONFIG, "/locations"),
    ("spaces", Space, SPACE_CONFIG, "/spaces"),
    ("halls", Hall, HALL_CONFIG, "/halls"),
    ("media_galleries", MediaGallery, MEDIA_GALLERY_CONFIG, "/media/galleries"),
    ("media_items", MediaItem, MEDIA_ITEM_CONFIG, "/media/items"),
    ("prices", Price, PRICE_CONFIG, "/prices"),
    ("price_ranks", PriceRank, PRICE_RANK_CONFIG, "/prices/ranks"),
    ("productions", Production, PRODUCTION_CONFIG, "/productions"),
    ("events", Event, EVENT_CONFIG, "/events"),
    ("event_prices", EventPrice, EVENT_PRICE_CONFIG, "/events/prices"),
]


# ===========================================================================
# Management command
# ===========================================================================


class Command(BaseCommand):
    help = "Synchronize Viernulvier / Peppered API data to the local database"

    FILTER_FIELDS = {
        "created": "created_at",
        "updated": "updated_at",
        "starts": "starts_at",
        "ends": "ends_at",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            type=str,
            metavar="STAP",
            help=(
                "Synchronize only this step. "
                f"Choices: {', '.join(name for name, *_ in SYNC_STEPS)}"
            ),
        )
        for prefix in self.FILTER_FIELDS.keys():
            for bound in ("after", "before"):
                option_name = f"--{prefix}-{bound}"
                parser.add_argument(
                    option_name,
                    type=str,
                    metavar="DATETIME",
                    help=f"Sync only records with {self.FILTER_FIELDS[prefix]} {bound} this timestamp, e.g. 2024-01-01T00:00:00Z",
                )
                parser.add_argument(
                    f"{option_name}-x",
                    type=str,
                    metavar="DATETIME",
                    help=f"Sync only records with {self.FILTER_FIELDS[prefix]} {bound} this timestamp (exclusive), e.g. 2024-01-01T00:00:00Z",
                )

    def handle(self, *args, **options):
        only = options.get("only")

        params = {}
        for prefix, api_field in self.FILTER_FIELDS.items():
            for bound in ("after", "before"):
                option_key = f"{prefix}_{bound}"
                value = options.get(option_key)
                if value:
                    params[f"{api_field}[{bound}]"] = value

                strict_option_key = f"{option_key}_x"
                strict_value = options.get(strict_option_key)
                if strict_value:
                    params[f"{api_field}[strictly_{bound}]"] = strict_value

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

        total_saved = 0
        for name, model, config, endpoint in steps_to_run:
            self.stdout.write(f"→ {name}...", ending=" ")
            try:
                saved = sync_viernulvier(
                    model=model,
                    config=config,
                    endpoint=endpoint,
                    params=params,
                )
                total_saved += saved
                self.stdout.write(self.style.SUCCESS(f"{saved} records"))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"FAILED: {exc}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Total: {total_saved} records"))
