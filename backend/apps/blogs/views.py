"""ViewSets for the Blog app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from django.db.models import Prefetch

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
    ``?ordering=slug`` / ``?ordering=-slug``
        Alphabetical by slug.
    ``?ordering=id`` / ``?ordering=-id``
        By creation order.

    Search
    ------
    ``?search=techno``
        Full-text search across ``slug`` and translated ``title`` fields.
    Production links are returned as full nested production objects.
    """

    queryset = Blog.objects.prefetch_related(
        "translations__language",
        Prefetch("productions", queryset=ProductionViewSet.queryset),
    ).order_by("-published_at", "-id")
    serializer_class = BlogSerializer

    filterset_class = BlogFilter
    ordering_fields = ["id", "slug", "published_at"]
    ordering = ["-published_at", "-id"]
    search_fields = ["slug", "translations__title"]
