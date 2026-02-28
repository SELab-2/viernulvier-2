"""
ViewSets for the Tags app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.

Tags are classification labels attached to productions. They support
localised fields (name, short description, URL title) resolved per request
via the ``Accept-Language`` header.
"""

from drf_spectacular.utils import extend_schema

from apps.core.views import ApiModelViewSet

from .models import Tag
from .schemas import tag_schema
from .serializers import TagSerializer

_TAG = "Tags"  # Reusable tag for all tag-related endpoints in the OpenAPI docs


@extend_schema(tags=[_TAG])
@tag_schema
class TagViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Tag objects.

    A tag is a classification label that can be attached to productions.
    Tags support localised fields (name, short description, URL title)
    resolved from the ``Accept-Language`` header via ``TranslatableSerializerMixin``.

    Queryset strategy
    -----------------
    ``prefetch_related("translations")`` loads all translations for each tag
    in a single additional query, preventing N+1 queries when the serializer
    resolves localised fields across a list response.
    """

    serializer_class = TagSerializer
    queryset = Tag.objects.prefetch_related("translations")