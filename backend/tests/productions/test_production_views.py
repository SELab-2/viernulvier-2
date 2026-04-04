"""
Tests for apps/productions/views.py - ProductionViewSet

Covers:
- ViewSet inherits from ApiModelViewSet
- Queryset model is Production
- Serializer class is ProductionSerializer
- Queryset has prefetch_related for translations, tags, uit_database_theme, uit_database_type
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

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.productions.models import Production
from apps.productions.serializers import ProductionSerializer
from apps.productions.views import ProductionViewSet
from tests.factories.event import EventFactory
from tests.factories.language import LanguageFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionTagFactory,
    ProductionTagTranslationFactory,
    ProductionTranslationFactory,
    UitDatabaseThemeFactory,
    UitDatabaseTypeFactory,
)
from tests.factories.tag import TagFactory

PUB_KEY = "pub-production-view-test-key"
INT_KEY = "int-production-view-test-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def wrong_headers():
    return {"HTTP_X_API_KEY": "completely-wrong-key"}


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
            "media_gallery",
            "uit_database_theme",
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
        }
        assert set(item.keys()) == expected_fields

    def test_list_returns_empty_list_when_no_productions(self) -> None:
        Production.objects.all().delete()
        response = self.client.get("/api/v1/productions/", **pub_headers())
        assert response.data["results"] == []


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
        self.theme = UitDatabaseThemeFactory.create(name="Drama")
        self.db_type = UitDatabaseTypeFactory.create(name="Theater")
        self.production = ProductionFactory.create(
            uit_database_theme=self.theme,
            uit_database_type=self.db_type,
            attendance_mode="offline",
        )
        self.event1 = EventFactory.create(production=self.production)
        self.event2 = EventFactory.create(production=self.production)
        ProductionTranslationFactory.create(
            production=self.production,
            language=self.nl,
            title="Test Titel",
            description="Test Beschrijving",
            teaser="",
            artist_name="",
            tagline="",
        )

    def test_detail_contains_nested_uit_database_theme(self) -> None:
        response = self.client.get(f"/api/v1/productions/{self.production.pk}/", **pub_headers())
        assert response.data["uit_database_theme"]["name"] == "Drama"

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
        }


# ---------------------------------------------------------------------------
# N+1 guard - prefetch translations
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetPrefetch(TestCase):
    """Ensure translations are prefetched and do not cause N+1 queries on list."""

    def setUp(self) -> None:
        self.client = APIClient()
        nl = LanguageFactory.create(code="nl", name="Dutch")
        en = LanguageFactory.create(code="en", name="English")
        for _ in range(5):
            p = ProductionFactory.create()
            ProductionTranslationFactory.create(
                production=p,
                language=nl,
                title="NL Titel",
                description="",
                teaser="",
                artist_name="",
                tagline="",
            )
            ProductionTranslationFactory.create(
                production=p,
                language=en,
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
        assert "description" in data["tags"][0]

    def test_tag_description_nl_is_correct_in_detail(self) -> None:
        data = self._detail().data
        assert data["tags"][0]["description"]["nl"] == "Context voor dit thema."

    def test_tag_description_in_list_response(self) -> None:
        response = self.client.get("/api/v1/productions/", **pub_headers())
        tags = response.data["results"][0]["tags"]
        assert "description" in tags[0]
        assert tags[0]["description"]["nl"] == "Context voor dit thema."

    def test_tag_without_translation_has_empty_description_dict(self) -> None:
        other_production = ProductionFactory.create()
        other_tag = TagFactory.create(type="mood")
        ProductionTagFactory.create(production=other_production, tag=other_tag)

        response = self.client.get(f"/api/v1/productions/{other_production.pk}/", **pub_headers())
        assert response.data["tags"][0]["description"] == {}


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetTagTranslationPrefetch(TestCase):
    """N+1 guard: tag translations must be prefetched, not fetched per tag per production."""

    def setUp(self) -> None:
        self.client = APIClient()
        nl = LanguageFactory.create(code="nl")
        en = LanguageFactory.create(code="en")

        for _ in range(5):
            production = ProductionFactory.create()
            for tag_type in ("theme", "mood"):
                tag = TagFactory.create(type=tag_type)
                pt = ProductionTagFactory.create(production=production, tag=tag)
                ProductionTagTranslationFactory.create(production_tag=pt, language=nl, description="NL")
                ProductionTagTranslationFactory.create(production_tag=pt, language=en, description="EN")

    def test_list_with_tag_translations_executes_bounded_queries(self) -> None:
        # Baseline from the existing N+1 test is 7 queries for 5 productions
        # with translation prefetch. Adding tag translation prefetch must not
        # grow this number linearly with the number of tags or productions.
        with self.assertNumQueries(9):
            response = self.client.get("/api/v1/productions/", **pub_headers())
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 5
        # Spot-check that description data is present and correct
        for item in results:
            for tag in item["tags"]:
                assert "nl" in tag["description"]
                assert "en" in tag["description"]
