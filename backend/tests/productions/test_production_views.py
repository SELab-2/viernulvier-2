"""
Tests for apps/productions/views.py - ProductionViewSet

Covers:
- ViewSet inherits from ApiModelViewSet
- Queryset model is Production
- Serializer class is ProductionSerializer
- Queryset has prefetch_related for translations, tags, uit_database_type
- GET  /api/v1/productions/        - public key ✓, internal key ✓
- GET  /api/v1/productions/<id>/   - public key ✓, internal key ✓
- POST /api/v1/productions/        - internal key ✓, public key ✗
- PUT  /api/v1/productions/<id>/   - internal key ✓, public key ✗
- PATCH /api/v1/productions/<id>/  - internal key ✓, public key ✗
- DELETE /api/v1/productions/<id>/ - internal key ✓, public key ✗
- All methods rejected without auth header
- All methods rejected with a completely wrong key
- Response structure / fields on list and detail
- Translations are prefetched (N+1 guard)
"""

from datetime import UTC, datetime

from django.db import connection
from django.db.models import Min
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.productions.models import Production
from apps.productions.serializers import ProductionSerializer
from apps.productions.views import ProductionViewSet
from tests.factories.blog import BlogFactory, BlogTranslationFactory
from tests.factories.event import EventFactory
from tests.factories.language import LanguageFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionTagFactory,
    ProductionTagTranslationFactory,
    ProductionTranslationFactory,
    UitDatabaseTypeFactory,
)
from tests.factories.tag import TagFactory
from tests.helpers.api import internal_headers as int_headers
from tests.helpers.api import public_headers as pub_headers
from tests.helpers.api import wrong_headers

PUB_KEY = "pub-production-view-test-key"
INT_KEY = "int-production-view-test-key"


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestProductionViewSetClass(TestCase):
    """Verify ViewSet class-level configuration."""

    def test_inherits_from_api_model_viewset(self) -> None:
        assert issubclass(ProductionViewSet, ApiModelViewSet)

    def test_queryset_model_is_production(self) -> None:
        assert ProductionViewSet.queryset.model == Production

    def test_serializer_class_is_production_serializer(self) -> None:
        assert ProductionViewSet.serializer_class == ProductionSerializer


# ---------------------------------------------------------------------------
# GET /api/v1/productions/ - list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetList(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Production.objects.all().delete()
        self.production_a = ProductionFactory.create(attendance_mode="offline")
        self.production_b = ProductionFactory.create(attendance_mode="online")
        EventFactory.create(
            production=self.production_a,
            starts_at=datetime(2025, 1, 1, tzinfo=UTC),
            ends_at=datetime(2025, 1, 1, 22, tzinfo=UTC),
        )
        EventFactory.create(
            production=self.production_b,
            starts_at=datetime(2025, 2, 1, tzinfo=UTC),
            ends_at=datetime(2025, 2, 1, 22, tzinfo=UTC),
        )

    def test_list_with_public_key_returns_200(self) -> None:
        response = self.client.get("/api/v1/productions/", **pub_headers())
        assert response.status_code == 200

    def test_list_with_internal_key_returns_200(self) -> None:
        response = self.client.get("/api/v1/productions/", **int_headers())
        assert response.status_code == 200

    def test_list_without_auth_header_returns_403(self) -> None:
        response = self.client.get("/api/v1/productions/")
        assert response.status_code in (401, 403)

    def test_list_with_wrong_key_returns_403(self) -> None:
        response = self.client.get("/api/v1/productions/", **wrong_headers())
        assert response.status_code in (401, 403)

    def test_list_returns_all_productions(self) -> None:
        response = self.client.get("/api/v1/productions/", **pub_headers())
        assert len(response.data["results"]) == 2

    def test_list_response_contains_expected_fields(self) -> None:
        response = self.client.get("/api/v1/productions/", **pub_headers())
        item = response.data["results"][0]
        expected_fields = {
            "id",
            "attendance_mode",
            "performer_type",
            "first_event_start",
            "last_event_end",
            "media_gallery",
            "uit_database_type",
            "title",
            "description",
            "teaser",
            "artist_name",
            "tagline",
            "tags",
            "genres",
            "display_title",
            "display_artist_name",
            "video_1",
            "video_2",
        }
        assert set(item.keys()) == expected_fields

    def test_list_returns_empty_list_when_no_productions(self) -> None:
        Production.objects.all().delete()
        response = self.client.get("/api/v1/productions/", **pub_headers())
        assert response.data["results"] == []


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionLandingStatsAction(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_landing_stats_returns_aggregated_counts(self) -> None:
        prod_a = ProductionFactory.create()
        prod_b = ProductionFactory.create()

        series_tag_a = TagFactory.create()
        series_tag_b = TagFactory.create()
        ProductionTagFactory.create(production=prod_a, tag=series_tag_a)
        ProductionTagFactory.create(production=prod_b, tag=series_tag_b)

        EventFactory.create(
            production=prod_a,
            starts_at=datetime(2021, 3, 14, 20, 0, tzinfo=UTC),
            ends_at=datetime(2021, 3, 14, 22, 0, tzinfo=UTC),
        )
        EventFactory.create(
            production=prod_b,
            starts_at=datetime(2024, 5, 7, 19, 0, tzinfo=UTC),
            ends_at=datetime(2024, 5, 7, 21, 0, tzinfo=UTC),
        )
        EventFactory.create(
            production=prod_b,
            starts_at=None,
            ends_at=datetime(2025, 1, 1, 0, 30, tzinfo=UTC),
        )

        BlogFactory.create(published_at=datetime(2024, 1, 12, 10, 0, tzinfo=UTC))
        BlogFactory.create(published_at=datetime(2024, 2, 2, 10, 0, tzinfo=UTC))
        BlogFactory.create(published_at=None)

        response = self.client.get("/api/v1/productions/landing-stats/", **pub_headers())

        assert response.status_code == 200
        assert response.data == {
            "productions": 2,
            "series": 2,
            "years": 3,
            "blogs": 2,
        }

    def test_landing_stats_allows_public_and_internal_keys(self) -> None:
        public_response = self.client.get("/api/v1/productions/landing-stats/", **pub_headers())
        internal_response = self.client.get("/api/v1/productions/landing-stats/", **int_headers())

        assert public_response.status_code == 200
        assert internal_response.status_code == 200

    def test_landing_stats_rejects_unauthorized_requests(self) -> None:
        response_without_key = self.client.get("/api/v1/productions/landing-stats/")
        response_wrong_key = self.client.get("/api/v1/productions/landing-stats/", **wrong_headers())

        assert response_without_key.status_code in (401, 403)
        assert response_wrong_key.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /api/v1/productions/<id>/ - detail
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetDetail(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.production = ProductionFactory.create(attendance_mode="offline", performer_type="solo")

    def test_detail_with_public_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.status_code == 200

    def test_detail_with_internal_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **int_headers())
        assert response.status_code == 200

    def test_detail_without_auth_header_returns_403(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/")
        assert response.status_code in (401, 403)

    def test_detail_with_wrong_key_returns_403(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **wrong_headers())
        assert response.status_code in (401, 403)

    def test_detail_returns_correct_id(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.data["id"] == self.production.pk

    def test_detail_returns_correct_attendance_mode(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.data["attendance_mode"] == "offline"

    def test_detail_returns_correct_performer_type(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.data["performer_type"] == "solo"

    def test_detail_returns_404_for_nonexistent_id(self) -> None:
        response = self.client.get("/api/v1/productions/99999999/", **pub_headers())
        assert response.status_code == 404

    def test_retrieve_with_include_related_no_n_plus_one(self) -> None:
        """Related productions and their translations must not cause N+1 queries."""
        nl = LanguageFactory.create(code="nl", name="Dutch")
        en = LanguageFactory.create(code="en", name="English")
        tag = TagFactory.create(type="theme")
        ProductionTagFactory.create(production=self.production, tag=tag)

        def create_related(index: int) -> Production:
            related = ProductionFactory.create()
            ProductionTranslationFactory.create(
                production=related,
                language=nl,
                title=f"Gerelateerde productie {index}",
                description="",
                teaser="",
                artist_name=f"Artiest {index}",
                tagline="",
            )
            ProductionTranslationFactory.create(
                production=related,
                language=en,
                title=f"Related production {index}",
                description="",
                teaser="",
                artist_name=f"Artist {index}",
                tagline="",
            )
            production_tag = ProductionTagFactory.create(production=related, tag=tag)
            ProductionTagTranslationFactory.create(
                production_tag=production_tag,
                language=nl,
                description=f"Context {index}",
            )
            return related

        create_related(1)
        url = f"/api/v1/productions/{self.production.pk}/?include=related"

        with CaptureQueriesContext(connection) as one_related_queries:
            response = self.client.get(url, **pub_headers())

        assert response.status_code == 200
        assert len(response.data["related"]) == 1
        assert len(response.data["related"][0]["productions"]) == 1

        for index in range(2, 6):
            create_related(index)

        with CaptureQueriesContext(connection) as five_related_queries:
            response = self.client.get(url, **pub_headers())

        assert response.status_code == 200
        assert len(response.data["related"]) == 1
        assert len(response.data["related"][0]["productions"]) == 5
        assert len(five_related_queries) == len(one_related_queries)


# ---------------------------------------------------------------------------
# POST /api/v1/productions/ - create
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetCreate(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.payload = {"attendance_mode": "offline", "performer_type": "group"}

    def test_create_with_internal_key_returns_201(self) -> None:
        response = self.client.post("/api/v1/productions/", self.payload, **int_headers())
        assert response.status_code == 201

    def test_create_with_public_key_returns_403(self) -> None:
        response = self.client.post("/api/v1/productions/", self.payload, **pub_headers())
        assert response.status_code in (401, 403)

    def test_create_without_auth_returns_403(self) -> None:
        response = self.client.post("/api/v1/productions/", self.payload)
        assert response.status_code in (401, 403)

    def test_create_with_wrong_key_returns_403(self) -> None:
        response = self.client.post("/api/v1/productions/", self.payload, **wrong_headers())
        assert response.status_code in (401, 403)

    def test_create_persists_production_to_database(self) -> None:
        count_before = Production.objects.count()
        self.client.post("/api/v1/productions/", self.payload, **int_headers())
        assert Production.objects.count() == count_before + 1

    def test_create_returns_created_production_data(self) -> None:
        response = self.client.post("/api/v1/productions/", self.payload, **int_headers())
        assert response.data["attendance_mode"] == "offline"
        assert response.data["performer_type"] == "group"


# ---------------------------------------------------------------------------
# PUT /api/v1/productions/<id>/ - full update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetUpdate(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.production = ProductionFactory.create(attendance_mode="offline", performer_type="solo")
        self.payload = {"attendance_mode": "online", "performer_type": "group"}

    def test_put_with_internal_key_returns_200(self) -> None:
        response = self.client.put(f"/api/v1/productions/{self.production.pk}/", self.payload, **int_headers())
        assert response.status_code == 200

    def test_put_with_public_key_returns_403(self) -> None:
        response = self.client.put(f"/api/v1/productions/{self.production.pk}/", self.payload, **pub_headers())
        assert response.status_code in (401, 403)

    def test_put_without_auth_returns_403(self) -> None:
        response = self.client.put(f"/api/v1/productions/{self.production.pk}/", self.payload)
        assert response.status_code in (401, 403)

    def test_put_updates_attendance_mode(self) -> None:
        self.client.put(f"/api/v1/productions/{self.production.pk}/", self.payload, **int_headers())
        self.production.refresh_from_db()
        assert self.production.attendance_mode == "online"


# ---------------------------------------------------------------------------
# PATCH /api/v1/productions/<id>/ - partial update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetPartialUpdate(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.production = ProductionFactory.create(attendance_mode="offline", performer_type="solo")

    def test_patch_with_internal_key_returns_200(self) -> None:
        response = self.client.patch(
            f"/api/v1/productions/{self.production.pk}/",
            {"attendance_mode": "online"},
            **int_headers(),
        )
        assert response.status_code == 200

    def test_patch_with_public_key_returns_403(self) -> None:
        response = self.client.patch(
            f"/api/v1/productions/{self.production.pk}/",
            {"attendance_mode": "online"},
            **pub_headers(),
        )
        assert response.status_code in (401, 403)

    def test_patch_without_auth_returns_403(self) -> None:
        response = self.client.patch(f"/api/v1/productions/{self.production.pk}/", {"attendance_mode": "online"})
        assert response.status_code in (401, 403)

    def test_patch_only_updates_specified_field(self) -> None:
        self.client.patch(
            f"/api/v1/productions/{self.production.pk}/",
            {"attendance_mode": "online"},
            **int_headers(),
        )
        self.production.refresh_from_db()
        assert self.production.attendance_mode == "online"
        assert self.production.performer_type == "solo"  # unchanged


# ---------------------------------------------------------------------------
# DELETE /api/v1/productions/<id>/ - destroy
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetDelete(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.production = ProductionFactory.create()

    def test_delete_with_internal_key_returns_204(self) -> None:
        response = self.client.delete(f"/api/v1/productions/{self.production.pk}/", **int_headers())
        assert response.status_code == 204

    def test_delete_with_public_key_returns_403(self) -> None:
        response = self.client.delete(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.status_code in (401, 403)

    def test_delete_without_auth_returns_403(self) -> None:
        response = self.client.delete(f"/api/v1/productions/{self.production.pk}/")
        assert response.status_code in (401, 403)

    def test_delete_with_wrong_key_returns_403(self) -> None:
        response = self.client.delete(f"/api/v1/productions/{self.production.pk}/", **wrong_headers())
        assert response.status_code in (401, 403)

    def test_delete_removes_production_from_database(self) -> None:
        pk = self.production.pk
        self.client.delete(f"/api/v1/productions/{pk}/", **int_headers())
        assert not Production.objects.filter(pk=pk).exists()


# ---------------------------------------------------------------------------
# Response structure - nested and translated fields
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetResponseStructure(TestCase):
    """Verify that nested and translated fields are correctly represented in API responses."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.db_type = UitDatabaseTypeFactory.create(name="Theater")
        self.production = ProductionFactory.create(
            uit_database_type=self.db_type,
            attendance_mode="offline",
        )
        self.event1 = EventFactory.create(
            production=self.production,
            starts_at=_dt(2025, 2, 10),
            ends_at=_dt(2025, 2, 10, 22),
        )
        self.event2 = EventFactory.create(
            production=self.production,
            starts_at=_dt(2025, 4, 10),
            ends_at=_dt(2025, 4, 10, 22),
        )
        ProductionTranslationFactory.create(
            production=self.production,
            language=self.nl,
            title="Test Titel",
            description="Test Beschrijving",
            teaser="",
            artist_name="",
            tagline="",
        )

    def test_detail_contains_nested_uit_database_type(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.data["uit_database_type"]["name"] == "Theater"

    def test_detail_title_is_translated_dict(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert isinstance(response.data["title"], dict)
        assert "nl" in response.data["title"]

    def test_detail_title_nl_value_is_correct(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.data["title"]["nl"] == "Test Titel"

    def test_detail_description_nl_value_is_correct(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.data["description"]["nl"] == "Test Beschrijving"

    def test_detail_title_is_empty_dict_without_translations(self) -> None:
        production_no_trans = ProductionFactory.create()
        response = self.client.get(f"/api/v1/productions/{production_no_trans.pk}/", **pub_headers())
        assert response.data["title"] == {}

    def test_retrieve_with_include_events_production_has_no_events(self) -> None:
        """events is an empty list when the production has no events."""
        empty_production = ProductionFactory()
        response = self.client.get(
            f"/api/v1/productions/{empty_production.id}/?include=events",
            **pub_headers(),
        )
        assert response.status_code == 200
        assert response.data["events"] == []

    def test_retrieve_with_include_events_lists_related_events(self) -> None:
        """events list contains the event that belongs to the production."""
        response = self.client.get(
            f"/api/v1/productions/{self.production.id}/?include=events",
            **pub_headers(),
        )
        event_ids = [e["id"] for e in response.data["events"]]
        assert self.event1.id in event_ids
        assert self.event2.id in event_ids

    def test_retrieve_with_include_events_contains_events_field(self) -> None:
        """events field is present in response when ?include=events is set."""
        response = self.client.get(
            f"/api/v1/productions/{self.production.id}/?include=events",
            **pub_headers(),
        )
        assert "events" in response.data

    def test_retrieve_without_include_excludes_events_field(self) -> None:
        """events field is absent from response when ?include=events is not set."""
        response = self.client.get(f"/api/v1/productions/{self.production.id}/", **pub_headers())
        assert response.status_code == 200
        assert "events" not in response.data

    def test_retrieve_with_include_events_returns_200(self) -> None:
        """?include=events on retrieve returns a 200."""
        response = self.client.get(
            f"/api/v1/productions/{self.production.id}/?include=events",
            **pub_headers(),
        )
        assert response.status_code == 200

    def test_retrieve_with_include_events_excludes_production_from_nested_event(self) -> None:
        """NestedEventSerializer omits production fields to avoid circular data."""
        response = self.client.get(
            f"/api/v1/productions/{self.production.id}/?include=events",
            **pub_headers(),
        )
        nested_event = response.data["events"][0]
        assert "production" not in nested_event
        assert "production_id" not in nested_event
        assert "production_display" not in nested_event

    def test_retrieve_with_include_related_contains_related_field(self) -> None:
        """related field is present in response when ?include=related is set."""
        response = self.client.get(
            f"/api/v1/productions/{self.production.id}/?include=related",
            **pub_headers(),
        )
        assert response.status_code == 200
        assert "related" in response.data

    def test_retrieve_without_include_excludes_related_field(self) -> None:
        """related field is absent from response when ?include=related is not set."""
        response = self.client.get(f"/api/v1/productions/{self.production.id}/", **pub_headers())
        assert response.status_code == 200
        assert "related" not in response.data

    def test_retrieve_with_include_related_groups_productions_by_tag(self) -> None:
        """related groups productions per tag and excludes the current production."""
        tag = TagFactory.create(type="theme")
        other_a = ProductionFactory.create()
        other_b = ProductionFactory.create()
        ProductionTagFactory.create(production=self.production, tag=tag)
        ProductionTagFactory.create(production=other_a, tag=tag)
        ProductionTagFactory.create(production=other_b, tag=tag)

        response = self.client.get(
            f"/api/v1/productions/{self.production.id}/?include=related",
            **pub_headers(),
        )

        assert response.status_code == 200
        assert len(response.data["related"]) == 1

        related_group = response.data["related"][0]
        assert set(related_group["tag"].keys()) == {"id", "name", "display_name"}
        assert related_group["tag"]["id"] == tag.id
        related_ids = [item["id"] for item in related_group["productions"]]
        assert self.production.id not in related_ids
        assert other_a.id in related_ids
        assert other_b.id in related_ids
        assert set(related_group["productions"][0].keys()) == {
            "id",
            "title",
            "display_title",
            "artist_name",
            "display_artist_name",
            "media_gallery",
            "first_event_start",
            "last_event_end",
            "tags",
            "genres",
        }

    def test_retrieve_with_include_blogs_contains_blogs_field(self) -> None:
        """blogs field is present in response when ?include=blogs is set."""
        blog = BlogFactory(slug="related-blog", published_at=datetime.now(tz=UTC))
        BlogTranslationFactory(blog=blog, language=self.nl, title="Gerelateerde blog", body="Body", excerpt="Excerpt")
        blog.productions.add(self.production)

        response = self.client.get(
            f"/api/v1/productions/{self.production.id}/?include=blogs",
            **pub_headers(),
        )

        assert response.status_code == 200
        assert "blogs" in response.data
        assert len(response.data["blogs"]) == 1
        assert response.data["blogs"][0]["id"] == blog.id
        assert set(response.data["blogs"][0].keys()) == {
            "id",
            "slug",
            "published_at",
            "cover_image",
            "title",
            "excerpt",
            "display_title",
            "display_excerpt",
        }

    def test_retrieve_without_include_excludes_blogs_field(self) -> None:
        """blogs field is absent from response when ?include=blogs is not set."""
        response = self.client.get(f"/api/v1/productions/{self.production.id}/", **pub_headers())
        assert response.status_code == 200
        assert "blogs" not in response.data

    def test_retrieve_with_include_blogs_excludes_unpublished_blogs(self) -> None:
        """Only published blogs are included when ?include=blogs is set."""
        published_blog = BlogFactory(slug="published-blog", published_at=datetime.now(tz=UTC))
        BlogTranslationFactory(
            blog=published_blog,
            language=self.nl,
            title="Published blog",
            body="Body",
            excerpt="Excerpt",
        )
        published_blog.productions.add(self.production)

        draft_blog = BlogFactory(slug="draft-blog", published_at=None)
        BlogTranslationFactory(blog=draft_blog, language=self.nl, title="Draft blog", body="Body", excerpt="Excerpt")
        draft_blog.productions.add(self.production)

        response = self.client.get(
            f"/api/v1/productions/{self.production.id}/?include=blogs",
            **pub_headers(),
        )

        assert response.status_code == 200
        blog_ids = [item["id"] for item in response.data["blogs"]]
        assert published_blog.id in blog_ids
        assert draft_blog.id not in blog_ids


# ---------------------------------------------------------------------------
# N+1 guard - prefetch translations
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetPrefetch(TestCase):
    """Ensure translations are prefetched and do not cause N+1 queries on list."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.en = LanguageFactory.create(code="en", name="English")
        for _ in range(5):
            p = ProductionFactory.create()
            EventFactory.create(
                production=p, starts_at=datetime(2025, 1, 1, tzinfo=UTC), ends_at=datetime(2025, 1, 1, 22, tzinfo=UTC)
            )
            ProductionTranslationFactory.create(
                production=p,
                language=self.nl,
                title="NL Titel",
                description="",
                teaser="",
                artist_name="",
                tagline="",
            )
            ProductionTranslationFactory.create(
                production=p,
                language=self.en,
                title="EN Title",
                description="",
                teaser="",
                artist_name="",
                tagline="",
            )

    def test_list_with_translations_executes_bounded_queries(self) -> None:
        with self.assertNumQueries(7):
            response = self.client.get("/api/v1/productions/", **pub_headers())
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# N+1 guard - prefetch tag translations
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionApiTagDescription(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.nl = LanguageFactory.create(code="nl")
        self.production = ProductionFactory.create()
        EventFactory.create(
            production=self.production,
            starts_at=datetime(2025, 1, 1, tzinfo=UTC),
            ends_at=datetime(2025, 1, 1, 22, tzinfo=UTC),
        )
        self.tag = TagFactory.create(type="theme")
        self.production_tag = ProductionTagFactory.create(production=self.production, tag=self.tag)
        ProductionTagTranslationFactory.create(
            production_tag=self.production_tag,
            language=self.nl,
            description="Context voor dit thema.",
        )

    def _detail(self):
        return self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())

    def test_tag_entry_in_detail_has_description_key(self) -> None:
        data = self._detail().data
        assert "description" not in data["tags"][0]

    def test_tag_description_nl_is_correct_in_detail(self) -> None:
        data = self._detail().data
        # production-scoped description is no longer included on tag payloads
        # and this setup does not create tag-level translations.
        assert data["tags"][0]["name"] == {}

    def test_tag_description_in_list_response(self) -> None:
        response = self.client.get("/api/v1/productions/", **pub_headers())
        tags = response.data["results"][0]["tags"]
        assert "description" not in tags[0]
        assert tags[0]["name"] == {}

    def test_tag_without_translation_has_empty_description_dict(self) -> None:
        other_production = ProductionFactory.create()
        other_tag = TagFactory.create(type="mood")
        ProductionTagFactory.create(production=other_production, tag=other_tag)

        response = self.client.get(f"/api/v1/productions/{other_production.pk}/", **pub_headers())
        assert "description" not in response.data["tags"][0]


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetTagTranslationPrefetch(TestCase):
    """N+1 guard: tag translations must be prefetched, not fetched per tag per production."""

    def setUp(self) -> None:
        self.client = APIClient()
        nl = LanguageFactory.create(code="nl")
        en = LanguageFactory.create(code="en")

        for _ in range(5):
            production = ProductionFactory.create()
            EventFactory.create(
                production=production,
                starts_at=datetime(2025, 1, 1, tzinfo=UTC),
                ends_at=datetime(2025, 1, 1, 22, tzinfo=UTC),
            )
            for tag_type in ("theme", "mood"):
                tag = TagFactory.create(type=tag_type)
                pt = ProductionTagFactory.create(production=production, tag=tag)
                ProductionTagTranslationFactory.create(production_tag=pt, language=nl, description="NL")
                ProductionTagTranslationFactory.create(production_tag=pt, language=en, description="EN")

    def test_list_with_tag_translations_executes_bounded_queries(self) -> None:
        # Baseline from the existing N+1 test is 7 queries for 5 productions
        # with translation prefetch. Adding tag translation prefetch must not
        # grow this number linearly with the number of tags or productions.
        with self.assertNumQueries(7):
            response = self.client.get("/api/v1/productions/", **pub_headers())
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 5
        # Spot-check that through-table description is not exposed anymore
        for item in results:
            for tag in item["tags"]:
                assert "description" not in tag


def _dt(year, month, day, hour=0):
    return datetime(year, month, day, hour, tzinfo=UTC)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionEventDateFieldsInResponse(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Production.objects.all().delete()
        self.production = ProductionFactory.create()
        self.past_event = EventFactory.create(
            production=self.production,
            starts_at=_dt(2025, 9, 15),
            ends_at=_dt(2025, 9, 15, 22),
        )
        self.future_event = EventFactory.create(
            production=self.production,
            starts_at=_dt(2030, 1, 10),
            ends_at=_dt(2030, 1, 10, 22),
        )

    def test_list_contains_first_event_start(self) -> None:
        response = self.client.get("/api/v1/productions/", **pub_headers())
        assert "first_event_start" in response.data["results"][0]

    def test_list_contains_last_event_end(self) -> None:
        response = self.client.get("/api/v1/productions/", **pub_headers())
        assert "last_event_end" in response.data["results"][0]

    def test_detail_contains_first_event_start(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert "first_event_start" in response.data

    def test_detail_contains_last_event_end(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert "last_event_end" in response.data

    def test_detail_with_include_events_omits_future_events(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/?include=events", **pub_headers())
        event_ids = [event["id"] for event in response.data["events"]]
        assert self.past_event.id in event_ids
        assert self.future_event.id not in event_ids

    def test_list_first_event_start_value_is_correct(self) -> None:
        item = self.client.get("/api/v1/productions/", **pub_headers()).data["results"][0]
        parsed = datetime.fromisoformat(item["first_event_start"])
        assert parsed == _dt(2025, 9, 15)

    def test_list_last_event_end_value_is_correct(self) -> None:
        item = self.client.get("/api/v1/productions/", **pub_headers()).data["results"][0]
        parsed = datetime.fromisoformat(item["last_event_end"])
        assert parsed == _dt(2025, 9, 15, 22)

    def test_list_fields_are_null_without_events(self) -> None:
        Production.objects.all().delete()
        production_without_events = ProductionFactory.create()

        results = self.client.get("/api/v1/productions/", **pub_headers()).data["results"]
        assert len(results) == 1
        assert results[0]["id"] == production_without_events.id
        assert results[0]["first_event_start"] is None
        assert results[0]["last_event_end"] is None

    def test_production_with_only_future_events_is_excluded(self) -> None:
        Production.objects.all().delete()
        future_only = ProductionFactory.create()
        EventFactory.create(
            production=future_only,
            starts_at=_dt(2030, 1, 10),
            ends_at=_dt(2030, 1, 10, 22),
        )

        results = self.client.get("/api/v1/productions/", **pub_headers()).data["results"]
        assert len(results) == 0

    def test_patch_with_first_event_start_is_ignored(self) -> None:
        self.client.patch(
            f"/api/v1/productions/{self.production.pk}/",
            {"first_event_start": "2099-01-01T00:00:00Z"},
            **int_headers(),
        )

        val = (
            Production.objects.annotate(first_event_start=Min("events__starts_at"))
            .get(pk=self.production.pk)
            .first_event_start
        )
        assert val == _dt(2025, 9, 15)  # unchanged


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionEventDateOrdering(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Production.objects.all().delete()
        self.p1 = ProductionFactory.create()
        self.p2 = ProductionFactory.create()
        self.p3 = ProductionFactory.create()
        EventFactory.create(production=self.p1, starts_at=_dt(2025, 3, 1), ends_at=_dt(2025, 3, 1, 20))
        EventFactory.create(production=self.p2, starts_at=_dt(2025, 1, 1), ends_at=_dt(2025, 12, 31, 23))
        EventFactory.create(production=self.p3, starts_at=_dt(2025, 6, 1), ends_at=_dt(2025, 6, 1, 18))

    def _ids(self, ordering):
        response = self.client.get("/api/v1/productions/", {"ordering": ordering}, **pub_headers())
        return [r["id"] for r in response.data["results"]]

    def test_order_by_first_event_start_ascending(self) -> None:
        assert self._ids("first_event_start") == [self.p2.pk, self.p1.pk, self.p3.pk]

    def test_order_by_first_event_start_descending(self) -> None:
        assert self._ids("-first_event_start") == [self.p3.pk, self.p1.pk, self.p2.pk]

    def test_order_by_last_event_end_ascending(self) -> None:
        assert self._ids("last_event_end") == [self.p1.pk, self.p3.pk, self.p2.pk]

    def test_order_by_last_event_end_descending(self) -> None:
        assert self._ids("-last_event_end") == [self.p2.pk, self.p3.pk, self.p1.pk]

    def test_ordering_returns_200(self) -> None:
        assert self.client.get("/api/v1/productions/", {"ordering": "first_event_start"}, **pub_headers()).status_code == 200


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionEventDateFilterViaApi(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Production.objects.all().delete()
        self.early = ProductionFactory.create()
        self.late = ProductionFactory.create()
        EventFactory.create(production=self.early, starts_at=_dt(2025, 1, 10), ends_at=_dt(2025, 1, 10, 22))
        EventFactory.create(production=self.late, starts_at=_dt(2025, 10, 10), ends_at=_dt(2025, 10, 10, 22))

    def _results(self, params):
        return self.client.get("/api/v1/productions/", params, **pub_headers()).data["results"]

    def test_after_filter_returns_one_result(self) -> None:
        assert len(self._results({"first_event_start_after": "2025-06-01T00:00:00Z"})) == 1

    def test_after_filter_returns_correct_production(self) -> None:
        assert self._results({"first_event_start_after": "2025-06-01T00:00:00Z"})[0]["id"] == self.late.pk

    def test_before_filter_returns_one_result(self) -> None:
        assert len(self._results({"first_event_start_before": "2025-06-01T00:00:00Z"})) == 1

    def test_before_filter_returns_correct_production(self) -> None:
        assert self._results({"first_event_start_before": "2025-06-01T00:00:00Z"})[0]["id"] == self.early.pk

    def test_impossible_range_returns_empty(self) -> None:
        assert (
            self._results(
                {
                    "first_event_start_after": "2025-08-01T00:00:00Z",
                    "first_event_start_before": "2025-04-01T00:00:00Z",
                }
            )
            == []
        )


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionEventDateAnnotationNPlusOne(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Production.objects.all().delete()
        for _ in range(5):
            p = ProductionFactory.create()
            EventFactory.create(production=p, starts_at=_dt(2025, 1, 1), ends_at=_dt(2025, 6, 1))
            EventFactory.create(production=p, starts_at=_dt(2025, 3, 1), ends_at=_dt(2025, 9, 1))

    def test_annotation_does_not_add_queries(self) -> None:
        with self.assertNumQueries(6):
            response = self.client.get("/api/v1/productions/", **pub_headers())
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["first_event_start"] is not None
            assert item["last_event_end"] is not None


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionLanguageAwareOrderingAndSearch(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Production.objects.all().delete()

        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.en = LanguageFactory.create(code="en", name="English")

        self.prod_alpha_nl = ProductionFactory.create()
        EventFactory.create(
            production=self.prod_alpha_nl,
            starts_at=datetime(2025, 1, 1, tzinfo=UTC),
            ends_at=datetime(2025, 1, 1, 22, tzinfo=UTC),
        )
        ProductionTranslationFactory.create(
            production=self.prod_alpha_nl,
            language=self.nl,
            title="Alpha",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )
        ProductionTranslationFactory.create(
            production=self.prod_alpha_nl,
            language=self.en,
            title="Zulu",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )

        self.prod_alpha_en = ProductionFactory.create()
        EventFactory.create(
            production=self.prod_alpha_en,
            starts_at=datetime(2025, 1, 1, tzinfo=UTC),
            ends_at=datetime(2025, 1, 1, 22, tzinfo=UTC),
        )
        ProductionTranslationFactory.create(
            production=self.prod_alpha_en,
            language=self.nl,
            title="Zulu",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )
        ProductionTranslationFactory.create(
            production=self.prod_alpha_en,
            language=self.en,
            title="Alpha",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )

    def test_ordering_by_title_sort_uses_accept_language(self) -> None:
        response_nl = self.client.get(
            "/api/v1/productions/",
            {"ordering": "title_sort"},
            HTTP_ACCEPT_LANGUAGE="nl",
            **pub_headers(),
        )
        ids_nl = [row["id"] for row in response_nl.data["results"]]
        assert ids_nl[:2] == [self.prod_alpha_nl.id, self.prod_alpha_en.id]

        response_en = self.client.get(
            "/api/v1/productions/",
            {"ordering": "title_sort"},
            HTTP_ACCEPT_LANGUAGE="en",
            **pub_headers(),
        )
        ids_en = [row["id"] for row in response_en.data["results"]]
        assert ids_en[:2] == [self.prod_alpha_en.id, self.prod_alpha_nl.id]

    def test_ordering_by_title_sort_is_case_insensitive(self) -> None:
        prod_lower = ProductionFactory.create()
        EventFactory.create(
            production=prod_lower, starts_at=datetime(2025, 1, 1, tzinfo=UTC), ends_at=datetime(2025, 1, 1, 22, tzinfo=UTC)
        )
        ProductionTranslationFactory.create(
            production=prod_lower,
            language=self.en,
            title="alpha",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )

        prod_upper = ProductionFactory.create()
        EventFactory.create(
            production=prod_upper, starts_at=datetime(2025, 1, 2, tzinfo=UTC), ends_at=datetime(2025, 1, 2, 22, tzinfo=UTC)
        )
        ProductionTranslationFactory.create(
            production=prod_upper,
            language=self.en,
            title="Zulu",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )

        response = self.client.get(
            "/api/v1/productions/",
            {"ordering": "title_sort", "lang": "en"},
            **pub_headers(),
        )
        ids = [row["id"] for row in response.data["results"]]
        assert ids.index(prod_lower.id) < ids.index(prod_upper.id)

    def test_search_uses_accept_language_preferred_translation(self) -> None:
        response_nl = self.client.get(
            "/api/v1/productions/",
            {"search": "Alpha"},
            HTTP_ACCEPT_LANGUAGE="nl",
            **pub_headers(),
        )
        ids_nl = [row["id"] for row in response_nl.data["results"]]
        assert ids_nl == [self.prod_alpha_nl.id]

        response_en = self.client.get(
            "/api/v1/productions/",
            {"search": "Alpha"},
            HTTP_ACCEPT_LANGUAGE="en",
            **pub_headers(),
        )
        ids_en = [row["id"] for row in response_en.data["results"]]
        assert ids_en == [self.prod_alpha_en.id]


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionOrderingEdgeCases(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        Production.objects.all().delete()

        en = LanguageFactory.create(code="en", name="English")
        nl = LanguageFactory.create(code="nl", name="Dutch")

        self.prod_alpha = ProductionFactory.create()
        EventFactory.create(
            production=self.prod_alpha,
            starts_at=_dt(2025, 1, 1),
            ends_at=_dt(2025, 1, 1, 20),
        )
        ProductionTranslationFactory.create(
            production=self.prod_alpha,
            language=en,
            title="Alpha",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )
        ProductionTranslationFactory.create(
            production=self.prod_alpha,
            language=nl,
            title="Zulu",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )

        self.prod_zulu = ProductionFactory.create()
        EventFactory.create(
            production=self.prod_zulu,
            starts_at=_dt(2025, 2, 1),
            ends_at=_dt(2025, 2, 1, 20),
        )
        ProductionTranslationFactory.create(
            production=self.prod_zulu,
            language=en,
            title="Zulu",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )
        ProductionTranslationFactory.create(
            production=self.prod_zulu,
            language=nl,
            title="Alpha",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )

        self.prod_without_translation = ProductionFactory.create()
        EventFactory.create(
            production=self.prod_without_translation,
            starts_at=_dt(2025, 3, 1),
            ends_at=_dt(2025, 3, 1, 20),
        )

        self.prod_blank_en = ProductionFactory.create()
        EventFactory.create(
            production=self.prod_blank_en,
            starts_at=_dt(2025, 4, 1),
            ends_at=_dt(2025, 4, 1, 20),
        )
        ProductionTranslationFactory.create(
            production=self.prod_blank_en,
            language=en,
            title="",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )
        ProductionTranslationFactory.create(
            production=self.prod_blank_en,
            language=nl,
            title="Beta",
            artist_name="",
            tagline="",
            teaser="",
            description="",
        )

        self.prod_early = ProductionFactory.create()
        self.prod_late = ProductionFactory.create()
        self.prod_without_events = ProductionFactory.create()
        EventFactory.create(
            production=self.prod_early,
            starts_at=_dt(2025, 1, 1),
            ends_at=_dt(2025, 1, 1, 20),
        )
        EventFactory.create(
            production=self.prod_late,
            starts_at=_dt(2025, 9, 1),
            ends_at=_dt(2025, 9, 1, 23),
        )

    def _ids(self, params: dict, **headers) -> list[int]:
        response = self.client.get("/api/v1/productions/", params, **headers)
        assert response.status_code == 200
        return [row["id"] for row in response.data["results"]]

    def test_title_sort_places_missing_translation_last_ascending(self) -> None:
        ids = self._ids({"ordering": "title_sort", "lang": "en"}, **pub_headers())

        assert ids.index(self.prod_alpha.id) < ids.index(self.prod_zulu.id)
        assert ids.index(self.prod_without_translation.id) > ids.index(self.prod_alpha.id)
        assert ids.index(self.prod_without_translation.id) > ids.index(self.prod_zulu.id)

    def test_title_sort_places_missing_translation_last_descending(self) -> None:
        ids = self._ids({"ordering": "-title_sort", "lang": "en"}, **pub_headers())

        assert ids.index(self.prod_zulu.id) < ids.index(self.prod_alpha.id)
        assert ids.index(self.prod_without_translation.id) > ids.index(self.prod_alpha.id)
        assert ids.index(self.prod_without_translation.id) > ids.index(self.prod_zulu.id)

    def test_title_sort_ignores_blank_preferred_language_and_uses_fallback(self) -> None:
        ids_asc = self._ids({"ordering": "title_sort", "lang": "en"}, **pub_headers())
        ids_desc = self._ids({"ordering": "-title_sort", "lang": "en"}, **pub_headers())

        assert ids_asc.index(self.prod_alpha.id) < ids_asc.index(self.prod_blank_en.id)
        assert ids_asc.index(self.prod_blank_en.id) < ids_asc.index(self.prod_zulu.id)
        assert ids_asc.index(self.prod_without_translation.id) > ids_asc.index(self.prod_blank_en.id)

        assert ids_desc.index(self.prod_zulu.id) < ids_desc.index(self.prod_blank_en.id)
        assert ids_desc.index(self.prod_blank_en.id) < ids_desc.index(self.prod_alpha.id)
        assert ids_desc.index(self.prod_without_translation.id) > ids_desc.index(self.prod_blank_en.id)

    def test_first_event_start_places_missing_date_last_ascending(self) -> None:
        ids = self._ids({"ordering": "first_event_start"}, **pub_headers())

        assert ids.index(self.prod_early.id) < ids.index(self.prod_late.id)
        assert ids[-1] == self.prod_without_events.id

    def test_first_event_start_places_missing_date_last_descending(self) -> None:
        ids = self._ids({"ordering": "-first_event_start"}, **pub_headers())

        assert ids.index(self.prod_late.id) < ids.index(self.prod_early.id)
        assert ids[-1] == self.prod_without_events.id

    def test_last_event_end_places_missing_date_last_ascending(self) -> None:
        ids = self._ids({"ordering": "last_event_end"}, **pub_headers())

        assert ids.index(self.prod_early.id) < ids.index(self.prod_late.id)
        assert ids[-1] == self.prod_without_events.id

    def test_last_event_end_places_missing_date_last_descending(self) -> None:
        ids = self._ids({"ordering": "-last_event_end"}, **pub_headers())

        assert ids.index(self.prod_late.id) < ids.index(self.prod_early.id)
        assert ids[-1] == self.prod_without_events.id

    def test_lang_query_param_overrides_accept_language_header_for_title_sort(self) -> None:
        ids = self._ids(
            {"ordering": "title_sort", "lang": "en"},
            HTTP_ACCEPT_LANGUAGE="nl",
            **pub_headers(),
        )

        assert ids.index(self.prod_alpha.id) < ids.index(self.prod_zulu.id)
