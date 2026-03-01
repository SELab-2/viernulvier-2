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

from apps.core.views import ApiModelViewSet

from .models import Tag, TagTranslation
from .schemas import tag_schema
from .serializers import TagSerializer

_TAG = "Tags"  # Reusable tag for all tag-related endpoints in the OpenAPI docs


@extend_schema(tags=[_TAG])
@tag_schema
class TagViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Tag objects.

    Tags are classification labels attached to productions.

    Translated fields (name, short description, URL title)
    are returned as language-code dictionaries via
    ``TranslatableSerializerMixin``.

    Queryset strategy
    -----------------
    ``prefetch_related("translations")`` loads all translations in a
    single additional query to avoid N+1 lookups.
    """

    serializer_class = TagSerializer
    queryset = Tag.objects.prefetch_related(
        Prefetch(
            "translations",
            queryset=TagTranslation.objects.select_related("language"),
        )
    )