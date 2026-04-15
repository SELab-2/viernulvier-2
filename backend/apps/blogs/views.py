"""ViewSets for the Blog app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from django.db.models import Min, Prefetch, Q, QuerySet
from django.db.models.functions import Coalesce, Lower

from apps.core.mixins import LanguageAwareMixin
from apps.core.views import ApiModelViewSet
from apps.productions.views import ProductionViewSet

from .filters import BlogFilter
from .models import Blog
from .schemas import blog_schema, extend_schema
from .serializers import BlogSerializer

_TAG = "Blogs"


@extend_schema(tags=[_TAG])
@blog_schema
class BlogViewSet(LanguageAwareMixin, ApiModelViewSet):
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
        with fallback to any available translation. Items without a
        translation are always sorted last, regardless of direction.
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
    search_fields = ["slug", "title_sort", "excerpt_search"]

    def get_queryset(self) -> QuerySet[Blog]:
        """Annotate language-aware title and excerpt fields for ordering and search.

        ``title_sort`` is a single annotation reused for both alphabetical
        ordering (``?ordering=title_sort``) and full-text search
        (``?search=...``). It resolves to the title in the preferred request
        language and falls back to any available translation when none exists
        for that language.

        ``excerpt_search`` follows the same language-preference logic and is
        used only for full-text search.

        Items without any translation at all resolve to NULL and are placed
        last by :class:`~apps.core.ordering.NullsLastOrderingFilter`.
        """
        language_code = self._get_request_language_code()
        queryset = super().get_queryset()

        return queryset.annotate(
            title_sort=Lower(
                Coalesce(
                    Min(
                        "translations__title",
                        filter=Q(translations__language__code=language_code)
                        & ~Q(translations__title=""),
                    ),
                    Min("translations__title", filter=~Q(translations__title="")),
                )
            ),
            excerpt_search=Lower(
                Coalesce(
                    Min(
                        "translations__excerpt",
                        filter=Q(translations__language__code=language_code)
                        & ~Q(translations__excerpt=""),
                    ),
                    Min("translations__excerpt", filter=~Q(translations__excerpt="")),
                )
            ),
        )
