"""ViewSets for the Blog app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from django.conf import settings
from django.db.models import Min, Prefetch, Q, QuerySet
from django.db.models.functions import Coalesce

from apps.core.views import ApiModelViewSet
from apps.productions.views import ProductionViewSet

from .filters import BlogFilter
from .models import Blog
from .schemas import blog_schema, extend_schema
from .serializers import BlogSerializer

_TAG = "Blogs"


@extend_schema(tags=[_TAG])
@blog_schema
class BlogViewSet(ApiModelViewSet):
    """CRUD endpoints for Blog objects.

    Blogs are CMS-managed content pages that can be linked to productions.
    Each blog supports multiple translations and can be published or kept as a draft.

    Filtering
    ---------
    ``?slug=techno``
        Substring match on the slug.
    ``?title=festival``
        Substring match across translated blog titles (all languages).
    ``?published=true``
        Show only published posts (with a non-null ``published_at``).
    ``?published=false``
        Show only drafts (with a null ``published_at``).
    ``?production=42``
        Show posts linked to a specific production.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=published_at`` / ``?ordering=-published_at``
        By publication date (default: newest first).
    ``?ordering=title_sort`` / ``?ordering=-title_sort``
        Alphabetical by title in the preferred request language,
        with fallback to any available translation.
    ``?ordering=slug`` / ``?ordering=-slug``
        Alphabetical by slug.
    ``?ordering=id`` / ``?ordering=-id``
        By creation order.

    Search
    ------
    ``?search=techno``
        Full-text search across ``slug`` plus preferred-language
        ``title`` and ``excerpt`` values, with fallback to any
        available translation.
    Production links are returned as full nested production objects.
    """

    queryset = Blog.objects.prefetch_related(
        "translations__language",
        Prefetch("productions", queryset=ProductionViewSet.queryset),
    ).order_by("-published_at", "-id")
    serializer_class = BlogSerializer

    filterset_class = BlogFilter
    ordering_fields = ["id", "slug", "published_at", "title_sort"]
    ordering = ["-published_at", "-id"]
    search_fields = ["slug", "title_search", "excerpt_search"]

    def _get_request_language_code(self) -> str:
        """Resolve the preferred language from query params/header with sane fallback."""
        raw = self.request.query_params.get("lang") or self.request.headers.get("Accept-Language", "")
        candidate = raw.split(",", 1)[0].split(";", 1)[0].strip().lower()
        if candidate:
            return candidate.split("-", 1)[0]
        return (getattr(settings, "LANGUAGE_CODE", "en") or "en").split("-", 1)[0].lower()

    def get_queryset(self) -> QuerySet[Blog]:
        """Annotate language-aware title/search fields for this request."""
        language_code = self._get_request_language_code()
        queryset = super().get_queryset()

        return queryset.annotate(
            title_sort=Coalesce(
                Min("translations__title", filter=Q(translations__language__code=language_code)),
                Min("translations__title"),
            ),
            title_search=Coalesce(
                Min("translations__title", filter=Q(translations__language__code=language_code)),
                Min("translations__title"),
            ),
            excerpt_search=Coalesce(
                Min("translations__excerpt", filter=Q(translations__language__code=language_code)),
                Min("translations__excerpt"),
            ),
        )
