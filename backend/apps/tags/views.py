"""
ViewSets for the Tags app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

Tags are classification labels used for filtering and categorising productions.
They support localised fields (name, short_description, url_title).

Translation Format
------------------
All translated fields are returned as dictionaries mapping language codes
to their values (e.g., {"nl": "...", "en": "..."}).
"""

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema

from apps.core.cache_mixin import cache_read_actions
from apps.core.views import ApiModelViewSet

from .filters import TagFilter
from .models import Tag, TagTranslation
from .schemas import tag_schema
from .serializers import TagSerializer

_TAG = "Tags"


@cache_read_actions()
@extend_schema(tags=[_TAG])
@tag_schema
class TagViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Tag objects.

    Tags are classification labels attached to productions. They support
    localised names and descriptions via the ``TagTranslation`` model.

    Filtering
    ---------
    ``?type=theme``
        Substring match on the internal type / category.
    ``?source=uitdatabank``
        Substring match on the originating system identifier.
    ``?source_type=targetAudience``
        Substring match on the source sub-classification.
    ``?is_external=true``
        Only tags imported from an external system.
    ``?is_enabled=true``
        Only active (enabled) tags.
    ``?name=contemporary``
        Substring match across all translated tag names.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=type`` / ``?ordering=-type``
        Alphabetical by internal type.
    ``?ordering=source`` / ``?ordering=-source``
        Alphabetical by originating system.
    ``?ordering=id`` / ``?ordering=-id``
        By creation order (default ascending).

    Search
    ------
    ``?search=contemporary``
        Full-text search across ``type``, ``source``, ``source_type``,
        and translated tag names.
    """

    serializer_class = TagSerializer
    queryset = Tag.objects.prefetch_related(
        Prefetch(
            "translations",
            queryset=TagTranslation.objects.select_related("language"),
        )
    ).order_by("id")

    filterset_class = TagFilter
    ordering_fields = ["id", "type", "source", "is_enabled", "is_external"]
    ordering = ["id"]
    search_fields = ["type", "source", "source_type", "translations__name"]
