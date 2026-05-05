"""ViewSets for the Tags app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

Tags are classification labels used for filtering and categorising productions.
They support localised fields (name, excerpt, short_description, url_title).

Translation Format
------------------
All translated fields are returned as dictionaries mapping language codes
to their values (e.g., {"nl": "...", "en": "..."}).
"""

from django.db.models import Max, Min, OuterRef, Prefetch, Subquery
from drf_spectacular.utils import extend_schema

from apps.core.views import ApiModelViewSet
from apps.media_library.models import MediaItemCrop

from .filters import TagFilter
from .models import Tag, TagTranslation
from .schemas import tag_schema
from .serializers import TagSerializer

_TAG = "Tags"


@extend_schema(tags=[_TAG])
@tag_schema
class TagViewSet(ApiModelViewSet):
    """CRUD endpoints for Tag objects.

    Tags are classification labels attached to productions. They support
    localised names and descriptions via the ``TagTranslation`` model.

    Filtering
    ---------
    ``?type=theme``
        Substring match on the internal type / category.
    ``?source=uitdatabank``
        Substring match on the originating system identifier.
    ``?is_enabled=true``
        Only active (enabled) tags.
    ``?name=contemporary``
        Substring match across all translated tag names.
    ``?excerpt=contemporary arts``
        Substring match across all translated tag excerpts.
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
        Full-text search across ``type``, ``source``,
        and translated tag names.
    """

    serializer_class = TagSerializer
    queryset = (
        Tag.objects.annotate(
            first_production_start=Min("productions__events__starts_at"),
            last_production_end=Max("productions__events__ends_at"),
            fallback_crop_path=Subquery(
                MediaItemCrop.objects.filter(
                    media_item__gallery__productions__tags=OuterRef("pk"),
                )
                .order_by(
                    "-media_item__gallery__productions__id",
                    "media_item__position",
                    "id",
                )
                .values("image")[:1]
            ),
        )
        .prefetch_related(
            Prefetch(
                "translations",
                queryset=TagTranslation.objects.select_related("language"),
            )
        )
        .order_by("id")
    )

    filterset_class = TagFilter
    ordering_fields = ["id", "type", "source", "is_enabled"]
    ordering = ["id"]
    search_fields = ["type", "source", "translations__name"]
