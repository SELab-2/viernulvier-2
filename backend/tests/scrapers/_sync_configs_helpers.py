"""Shared helpers/constants for sync_viernulvier config and command tests."""

from django.db import models as django_models

from apps.events.models import Event, EventPrice
from apps.genres.models import Genre
from apps.imports.management.commands.sync_viernulvier import (
    EVENT_CONFIG,
    EVENT_PRICE_CONFIG,
    GENRE_CONFIG,
    HALL_CONFIG,
    LOCATION_CONFIG,
    MEDIA_GALLERY_CONFIG,
    MEDIA_ITEM_CONFIG,
    PRICE_CONFIG,
    PRICE_RANK_CONFIG,
    PRODUCTION_CONFIG,
    SPACE_CONFIG,
    SYNC_STEPS,
    TAG_CONFIG,
    UITDATABASE_TYPE_CONFIG,
)
from apps.locations.models import Hall, Location, Space
from apps.media_library.models import MediaGallery, MediaItem
from apps.pricing.models import Price, PriceRank
from apps.productions.models import Production, UitDatabaseType
from apps.tags.models import Tag


def get_model_field_names(model):
    """Get concrete, non-auto Django model field names."""
    return {
        field.name for field in model._meta.get_fields() if isinstance(field, django_models.Field) and not field.auto_created
    }


ALL_CONFIGS = [
    UITDATABASE_TYPE_CONFIG,
    GENRE_CONFIG,
    TAG_CONFIG,
    LOCATION_CONFIG,
    SPACE_CONFIG,
    HALL_CONFIG,
    MEDIA_GALLERY_CONFIG,
    MEDIA_ITEM_CONFIG,
    PRICE_CONFIG,
    PRICE_RANK_CONFIG,
    PRODUCTION_CONFIG,
    EVENT_CONFIG,
    EVENT_PRICE_CONFIG,
]

BASE_CONFIGS = [
    UITDATABASE_TYPE_CONFIG,
    GENRE_CONFIG,
    TAG_CONFIG,
    LOCATION_CONFIG,
]

CONFIGS_WITH_TRANSLATIONS = [
    GENRE_CONFIG,
    TAG_CONFIG,
    LOCATION_CONFIG,
    SPACE_CONFIG,
    HALL_CONFIG,
    MEDIA_ITEM_CONFIG,
    PRICE_CONFIG,
    PRICE_RANK_CONFIG,
    PRODUCTION_CONFIG,
]

CONFIGS_AND_MODELS = [
    (UITDATABASE_TYPE_CONFIG, UitDatabaseType),
    (GENRE_CONFIG, Genre),
    (TAG_CONFIG, Tag),
    (LOCATION_CONFIG, Location),
    (MEDIA_GALLERY_CONFIG, MediaGallery),
    (MEDIA_ITEM_CONFIG, MediaItem),
    (PRICE_CONFIG, Price),
    (PRICE_RANK_CONFIG, PriceRank),
    (PRODUCTION_CONFIG, Production),
    (EVENT_CONFIG, Event),
    (EVENT_PRICE_CONFIG, EventPrice),
]

VALUE_TRANSFORM_CONFIGS = [
    (TAG_CONFIG, Tag),
    (LOCATION_CONFIG, Location),
    (HALL_CONFIG, Hall),
]

FK_RESOLVER_CONFIGS = []

EXTERNAL_ID_CONFIGS = [
    ("UitDatabaseType", UitDatabaseType, UITDATABASE_TYPE_CONFIG),
    ("Genre", Genre, GENRE_CONFIG),
    ("Tag", Tag, TAG_CONFIG),
    ("Location", Location, LOCATION_CONFIG),
    ("Space", Space, SPACE_CONFIG),
    ("Hall", Hall, HALL_CONFIG),
    ("MediaGallery", MediaGallery, MEDIA_GALLERY_CONFIG),
    ("MediaItem", MediaItem, MEDIA_ITEM_CONFIG),
    ("Price", Price, PRICE_CONFIG),
    ("PriceRank", PriceRank, PRICE_RANK_CONFIG),
    ("Production", Production, PRODUCTION_CONFIG),
    ("Event", Event, EVENT_CONFIG),
    ("EventPrice", EventPrice, EVENT_PRICE_CONFIG),
]

DEFINED_CONFIGS = [config for _, _, config in EXTERNAL_ID_CONFIGS]

REQUIRED_CONFIG_ATTRIBUTES = [
    "field_map",
    "lookup_field",
    "api_id_key",
    "value_transforms",
    "fk_resolvers",
    "translations",
    "m2m",
]

TRANSLATION_REQUIRED_ATTRIBUTES = [
    "api_key",
    "model",
    "parent_fk",
    "flat_field",
    "language_fk",
]

M2M_REQUIRED_ATTRIBUTES = [
    "api_key",
    "related_model",
    "through_model",
    "parent_fk",
    "related_fk",
    "related_lookup_field",
]

SYNC_STEP_NAMES = [name for name, *_ in SYNC_STEPS]
SYNC_STEP_ENDPOINTS = [endpoint for *_, endpoint in SYNC_STEPS]
