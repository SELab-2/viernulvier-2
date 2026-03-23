"""
ViewSets for the Language app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.cache_mixin import cache_read_actions
from apps.core.views import ApiModelViewSet

from .filters import LanguageFilter
from .models import Language
from .schemas import extend_schema, language_schema
from .serializers import LanguageSerializer

_TAG = "Languages"


@cache_read_actions()
@extend_schema(tags=[_TAG])
@language_schema
class LanguageViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Language objects.

    Languages are identified by their ISO 639-1 ``code`` (e.g. ``en``, ``nl``)
    instead of a numeric primary key, so the URL lookup field is ``code``.

    Access rules
    ------------
    - **Public key**   -> read-only (``list``, ``retrieve``).
    - **Internal key** -> full CRUD.

    Filtering
    ---------
    ``?code=nl``
        Exact ISO 639-1 code lookup (case-insensitive).
    ``?name=dutch``
        Substring match on the display name.
    ``?is_active=true``
        Only active (or inactive) languages.
    ``?external_id=abc-123``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=code`` / ``?ordering=-code``
        Alphabetical by ISO code (default).
    ``?ordering=name`` / ``?ordering=-name``
        Alphabetical by display name.

    Search
    ------
    ``?search=nl``
        Full-text search across ``code`` and ``name``.
    """

    queryset = Language.objects.order_by("code")
    serializer_class = LanguageSerializer
    lookup_field = "code"

    filterset_class = LanguageFilter
    ordering_fields = ["code", "name"]
    ordering = ["code"]
    search_fields = ["code", "name"]
