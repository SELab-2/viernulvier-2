"""Router for API v1.

All current viewsets are registered here. When a breaking change is
needed, create ``api/v2/urls.py``, import the unchanged viewsets from
this module, and register only the new/changed ones on a fresh router.

    from api.v1.urls import router as v1_router
    # re-use everything except the one that changed
"""

from rest_framework.routers import DefaultRouter

from apps.blogs.views import BlogViewSet
from apps.events.views import EventViewSet
from apps.genres.views import GenreViewSet
from apps.import_log.views import ImportLogViewSet
from apps.languages.views import LanguageViewSet
from apps.locations.views import HallViewSet, LocationViewSet, SpaceViewSet
from apps.media_files.views import MediaFileViewSet
from apps.media_library.views import MediaGalleryViewSet, MediaItemViewSet
from apps.pricing.views import PriceRankViewSet, PriceViewSet
from apps.productions.views import ProductionViewSet
from apps.tags.views import TagViewSet

router = DefaultRouter()

# Reference / taxonomy
router.register(r"languages", LanguageViewSet, basename="language")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"genres", GenreViewSet, basename="genre")
router.register(r"price-ranks", PriceRankViewSet, basename="price-rank")
router.register(r"prices", PriceViewSet, basename="price")

# Location hierarchy
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"spaces", SpaceViewSet, basename="space")
router.register(r"halls", HallViewSet, basename="hall")

# Core content
router.register(r"productions", ProductionViewSet, basename="production")
router.register(r"events", EventViewSet, basename="event")

# Media
router.register(r"media", MediaFileViewSet, basename="media-file")
router.register(r"media-galleries", MediaGalleryViewSet, basename="media-gallery")
router.register(r"media-items", MediaItemViewSet, basename="media-item")

# Blogs
router.register(r"blogs", BlogViewSet, basename="blog")

# Import pipeline
router.register(r"import-logs", ImportLogViewSet, basename="import-log")

urlpatterns = router.urls
