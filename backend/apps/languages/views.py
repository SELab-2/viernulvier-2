"""
ViewSets for the Language app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.views import ApiModelViewSet

from .models import Language
from .schemas import language_schema, extend_schema
from .serializers import LanguageSerializer

_TAG = (
    "Languages"  # Reusable tag for all language-related endpoints in the OpenAPI docs
)


@extend_schema(tags=[_TAG])
@language_schema
class LanguageViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Language objects.

    Languages are identified by their ISO 639-1 `code` (e.g. `en`, `nl`)
    instead of a numeric primary key, so the URL lookup field is `code`.

    Access rules:
        - Public API key  -> read-only
        - Internal API key -> full CRUD
    """

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    lookup_field = "code"
