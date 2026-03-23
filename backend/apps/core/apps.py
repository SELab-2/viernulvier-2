"""
App configuration for the Core app.

Connects cache invalidation signals for all models that have cached
read endpoints. Signals are registered centrally here to avoid
spreading signal logic across individual app configurations.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"

    def ready(self):
        from apps.core.signals import connect_cache_invalidation
        from apps.events.models import Event
        from apps.genres.models import Genre, GenreUseAs
        from apps.languages.models import Language
        from apps.locations.models import Hall, Location, Space
        from apps.media_library.models import MediaGallery, MediaItem
        from apps.pricing.models import Price, PriceRank
        from apps.productions.models import Production
        from apps.tags.models import Tag

        connect_cache_invalidation(Event,       "/api/v1/events/")
        connect_cache_invalidation(Production,  "/api/v1/productions/")
        connect_cache_invalidation(Location,    "/api/v1/locations/")
        connect_cache_invalidation(Space,       "/api/v1/spaces/")
        connect_cache_invalidation(Hall,        "/api/v1/halls/")
        connect_cache_invalidation(MediaGallery,"/api/v1/media-galleries/")
        connect_cache_invalidation(MediaItem,   "/api/v1/media-items/")
        connect_cache_invalidation(Price,       "/api/v1/prices/")
        connect_cache_invalidation(PriceRank,   "/api/v1/price-ranks/")
        connect_cache_invalidation(Genre,       "/api/v1/genres/")
        connect_cache_invalidation(GenreUseAs,  "/api/v1/genre-use-as/")
        connect_cache_invalidation(Language,    "/api/v1/languages/")
        connect_cache_invalidation(Tag,         "/api/v1/tags/")
