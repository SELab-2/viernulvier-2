"""OpenAPI schema decorators and examples for the Blog app."""

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view

from apps.core.openapi import (
    DELETE_ERRORS,
    ITEM_ERRORS,
    MUTATE_ERRORS,
    READ_ERRORS,
    RESPONSE_204_DELETED,
    WRITE_ERRORS,
)

from .serializers import BlogSerializer

# ===========================================================================
# Blog - examples
# ===========================================================================

_BLOG_RESPONSE = OpenApiExample(
    "Blog - Full Response",
    summary="Complete blog post with all translations",
    value={
        "id": 42,
        "slug": "i-love-techno-2024",
        "published_at": "2024-11-15T10:00:00Z",
        "cover_image": "/media/blog_covers/i-love-techno-2024.jpg",
        "title": {
            "nl": "I Love Techno 2024: Een Terugblik",
            "en": "I Love Techno 2024: A Retrospective",
        },
        "body": {
            "nl": "<p>Een uitgebreide terugblik op het evenement...</p>",
            "en": "<p>An extensive look back at the event...</p>",
        },
        "excerpt": {
            "nl": "Een korte samenvatting van het evenement",
            "en": "A brief summary of the event",
        },
        "display_title": "I Love Techno 2024: Een Terugblik",
        "display_excerpt": "Een korte samenvatting van het evenement",
        "productions": [
            {
                "id": 101,
                "attendance_mode": "offline",
                "performer_type": "group",
                "first_event_start": "2025-09-15T19:30:00Z",
                "last_event_end": "2025-11-02T21:30:00Z",
                "media_gallery": {"id": 706, "name": "home", "media_items": []},
                "uit_database_type": {"id": 7, "name": "Voorstelling"},
                "display_title": "Collectief Morgen - De Laatste Avond",
                "display_artist_name": "Collectief Morgen",
                "title": {"nl": "Collectief Morgen - De Laatste Avond"},
                "artist_name": {"nl": "Collectief Morgen"},
                "tagline": {"nl": "Een ode aan vergankelijkheid"},
                "teaser": {"nl": "Een indringende voorstelling over verlies en hoop."},
                "description": {"nl": "Volledige beschrijving van de productie..."},
                "tags": [],
                "genres": [],
            }
        ],
    },
    response_only=True,
)

_BLOG_LIST_RESPONSE = OpenApiExample(
    "Blog - List Response",
    summary="Full blog post for list views",
    value={
        "id": 42,
        "slug": "vooruit-100-years",
        "published_at": "2024-03-20T14:30:00Z",
        "cover_image": "/media/blog_covers/vooruit-100.jpg",
        "title": {
            "nl": "100 Jaar Vooruit",
            "en": "100 Years of Vooruit",
        },
        "excerpt": {
            "nl": "Een historisch overzicht",
            "en": "A historical overview",
        },
        "body": {
            "nl": "<p>Een historisch overzicht van Vooruit...</p>",
            "en": "<p>A historical overview of Vooruit...</p>",
        },
        "display_title": "100 Jaar Vooruit",
        "display_excerpt": "Een historisch overzicht",
        "productions": [
            {
                "id": 50,
                "attendance_mode": "offline",
                "performer_type": "group",
                "first_event_start": None,
                "last_event_end": None,
                "media_gallery": {"id": 800, "name": "home", "media_items": []},
                "uit_database_type": None,
                "display_title": "Vooruit 100 Jaar",
                "display_artist_name": "Vooruit",
                "title": {"nl": "Vooruit 100 Jaar"},
                "artist_name": {"nl": "Vooruit"},
                "tagline": {},
                "teaser": {},
                "description": {},
                "tags": [],
                "genres": [],
            }
        ],
    },
    response_only=True,
)

_BLOG_INPUT = OpenApiExample(
    "Blog - Request Body",
    summary="Payload for creating a new blog post with inline translations",
    description=(
        "Only `slug` is required. You can optionally provide `translations_data` "
        "to create translations inline. Use `production_ids` to link productions."
    ),
    value={
        "slug": "summer-festival-2025",
        "published_at": "2025-06-01T08:00:00Z",
        "cover_image": "/media/blog_covers/summer-2025.jpg",
        "production_ids": [200, 201],
        "translations_data": [
            {
                "language_id": 1,
                "title": "Zomerfestival 2025",
                "body": "<p>Een geweldig festival...</p>",
                "excerpt": "Het beste zomerfestival ooit",
            },
            {
                "language_id": 2,
                "title": "Summer Festival 2025",
                "body": "<p>An amazing festival...</p>",
                "excerpt": "The best summer festival ever",
            },
        ],
    },
    request_only=True,
)

_BLOG_PARTIAL_INPUT = OpenApiExample(
    "Blog - Partial Request Body",
    summary="Update specific fields and optionally replace all translations",
    description=(
        "When updating, you can change any field. If you provide `translations_data`, "
        "it will REPLACE all existing translations with the new ones."
    ),
    value={
        "published_at": "2025-06-15T12:00:00Z",
        "production_ids": [200, 201, 202],
        "translations_data": [
            {
                "language_id": 1,
                "title": "Bijgewerkte Titel",
                "body": "<p>Bijgewerkte inhoud...</p>",
                "excerpt": "Nieuwe samenvatting",
            },
        ],
    },
    request_only=True,
)


# ===========================================================================
# Blog - per-action schemas
# ===========================================================================

_BLOG_LIST = extend_schema(
    summary="List all blog posts",
    description=(
        "Returns a paginated list of all **Blog** posts.\n\n"
        "Each blog response includes the full `body` translation dictionary and nested production objects."
    ),
    responses={200: BlogSerializer, **READ_ERRORS},
    examples=[_BLOG_LIST_RESPONSE],
)

_BLOG_RETRIEVE = extend_schema(
    summary="Retrieve a blog post",
    description=(
        "Returns the full representation of a single **Blog** post identified "
        "by its primary key, including all translations and linked productions."
    ),
    responses={200: BlogSerializer, **ITEM_ERRORS},
    examples=[_BLOG_RESPONSE],
)

_BLOG_CREATE = extend_schema(
    summary="Create a blog post",
    description=(
        "Creates a new **Blog** post in the archive.\n\n"
        "- The `slug` field must be unique and use `kebab-case` (e.g. `i-love-techno-2024`).\n"
        "- Optionally provide `translations_data` to create translations inline.\n"
        "  Each translation needs: `language_id`, `title`, `body`, and optionally `excerpt`.\n"
        "- Use `production_ids` to link the post to one or more productions.\n"
        "- If `published_at` is null, the post is considered a draft.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=BlogSerializer,
    responses={201: BlogSerializer, **WRITE_ERRORS},
    examples=[_BLOG_INPUT, _BLOG_RESPONSE],
)

_BLOG_UPDATE = extend_schema(
    summary="Replace a blog post",
    description=(
        "Fully replaces an existing **Blog** post. All writable fields must be supplied.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=BlogSerializer,
    responses={200: BlogSerializer, **MUTATE_ERRORS},
    examples=[_BLOG_INPUT, _BLOG_RESPONSE],
)

_BLOG_PARTIAL_UPDATE = extend_schema(
    summary="Partially update a blog post",
    description=(
        "Updates one or more fields of an existing **Blog** post without "
        "requiring a full payload.\n\n"
        "**Important:** If you provide `translations_data`, it will **replace** all "
        "existing translations. To preserve existing translations, omit this field.\n\n"
        "> **Requires an internal API key.**"
    ),
    request=BlogSerializer,
    responses={200: BlogSerializer, **MUTATE_ERRORS},
    examples=[_BLOG_PARTIAL_INPUT, _BLOG_RESPONSE],
)

_BLOG_DESTROY = extend_schema(
    summary="Delete a blog post",
    description=(
        "Permanently removes a **Blog** post from the archive.\n\n"
        "> **Warning:** All associated translations are also deleted. "
        "This action is irreversible.\n\n"
        "> **Requires an internal API key.**"
    ),
    responses={204: RESPONSE_204_DELETED, **DELETE_ERRORS},
)


# ===========================================================================
# Assembled decorator - imported and applied in views.py
# ===========================================================================

blog_schema = extend_schema_view(
    list=_BLOG_LIST,
    retrieve=_BLOG_RETRIEVE,
    create=_BLOG_CREATE,
    update=_BLOG_UPDATE,
    partial_update=_BLOG_PARTIAL_UPDATE,
    destroy=_BLOG_DESTROY,
)
