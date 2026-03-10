"""
Tests for apps/productions/views.py - ProductionViewSet

Covers:
- ViewSet inherits from ApiModelViewSet
- Queryset model is Production
- Serializer class is ProductionSerializer
- Queryset has prefetch_related for translations, tags, uit_database_theme, uit_database_type
- GET  /api/productions/        - public key ✓, internal key ✓
- GET  /api/productions/<id>/   - public key ✓, internal key ✓
- POST /api/productions/        - internal key ✓, public key ✗
- PUT  /api/productions/<id>/   - internal key ✓, public key ✗
- PATCH /api/productions/<id>/  - internal key ✓, public key ✗
- DELETE /api/productions/<id>/ - internal key ✓, public key ✗
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
from tests.factories.language import LanguageFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionTranslationFactory,
    UitDatabaseThemeFactory,
    UitDatabaseTypeFactory,
)

PUB_KEY = "pub-production-view-test-key"
INT_KEY = "int-production-view-test-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def int_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {INT_KEY}"}


def pub_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {PUB_KEY}"}


def wrong_headers():
    return {"HTTP_AUTHORIZATION": "Api-Key completely-wrong-key"}


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestProductionViewSetClass(TestCase):
    """Verify ViewSet class-level configuration."""

    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(ProductionViewSet, ApiModelViewSet))

    def test_queryset_model_is_production(self):
        self.assertEqual(ProductionViewSet.queryset.model, Production)

    def test_serializer_class_is_production_serializer(self):
        self.assertEqual(ProductionViewSet.serializer_class, ProductionSerializer)

    def test_queryset_has_prefetch_for_tags(self):
        queryset = ProductionViewSet().get_queryset()
        lookups = queryset._prefetch_related_lookups
        lookup_names = [lookup.prefetch_through if hasattr(lookup, "prefetch_through") else lookup for lookup in lookups]
        self.assertIn("tags", lookup_names)


# ---------------------------------------------------------------------------
# GET /api/productions/ - list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetList(TestCase):
    def setUp(self):
        self.client = APIClient()
        Production.objects.all().delete()
        self.production_a = ProductionFactory.create(attendance_mode="offline")
        self.production_b = ProductionFactory.create(attendance_mode="online")

    def test_list_with_public_key_returns_200(self):
        response = self.client.get("/api/productions/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_with_internal_key_returns_200(self):
        response = self.client.get("/api/productions/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_without_auth_header_returns_403(self):
        response = self.client.get("/api/productions/")
        self.assertIn(response.status_code, (401, 403))

    def test_list_with_wrong_key_returns_403(self):
        response = self.client.get("/api/productions/", **wrong_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_list_returns_all_productions(self):
        response = self.client.get("/api/productions/", **pub_headers())
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_response_contains_expected_fields(self):
        response = self.client.get("/api/productions/", **pub_headers())
        item = response.data["results"][0]
        expected_fields = {
            "id",
            "attendance_mode",
            "performer_type",
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
        self.assertEqual(set(item.keys()), expected_fields)

    def test_list_returns_empty_list_when_no_productions(self):
        Production.objects.all().delete()
        response = self.client.get("/api/productions/", **pub_headers())
        self.assertEqual(response.data["results"], [])


# ---------------------------------------------------------------------------
# GET /api/productions/<id>/ - detail
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetDetail(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.production = ProductionFactory.create(attendance_mode="offline", performer_type="solo")

    def test_detail_with_public_key_returns_200(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_detail_with_internal_key_returns_200(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_detail_without_auth_header_returns_403(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/")
        self.assertIn(response.status_code, (401, 403))

    def test_detail_with_wrong_key_returns_403(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **wrong_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_detail_returns_correct_id(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertEqual(response.data["id"], self.production.pk)

    def test_detail_returns_correct_attendance_mode(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertEqual(response.data["attendance_mode"], "offline")

    def test_detail_returns_correct_performer_type(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertEqual(response.data["performer_type"], "solo")

    def test_detail_returns_404_for_nonexistent_id(self):
        response = self.client.get("/api/productions/99999999/", **pub_headers())
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# POST /api/productions/ - create
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetCreate(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {"attendance_mode": "offline", "performer_type": "group"}

    def test_create_with_internal_key_returns_201(self):
        response = self.client.post("/api/productions/", self.payload, **int_headers())
        self.assertEqual(response.status_code, 201)

    def test_create_with_public_key_returns_403(self):
        response = self.client.post("/api/productions/", self.payload, **pub_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_create_without_auth_returns_403(self):
        response = self.client.post("/api/productions/", self.payload)
        self.assertIn(response.status_code, (401, 403))

    def test_create_with_wrong_key_returns_403(self):
        response = self.client.post("/api/productions/", self.payload, **wrong_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_create_persists_production_to_database(self):
        count_before = Production.objects.count()
        self.client.post("/api/productions/", self.payload, **int_headers())
        self.assertEqual(Production.objects.count(), count_before + 1)

    def test_create_returns_created_production_data(self):
        response = self.client.post("/api/productions/", self.payload, **int_headers())
        self.assertEqual(response.data["attendance_mode"], "offline")
        self.assertEqual(response.data["performer_type"], "group")


# ---------------------------------------------------------------------------
# PUT /api/productions/<id>/ - full update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetUpdate(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.production = ProductionFactory.create(attendance_mode="offline", performer_type="solo")
        self.payload = {"attendance_mode": "online", "performer_type": "group"}

    def test_put_with_internal_key_returns_200(self):
        response = self.client.put(f"/api/productions/{self.production.pk}/", self.payload, **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_put_with_public_key_returns_403(self):
        response = self.client.put(f"/api/productions/{self.production.pk}/", self.payload, **pub_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_put_without_auth_returns_403(self):
        response = self.client.put(f"/api/productions/{self.production.pk}/", self.payload)
        self.assertIn(response.status_code, (401, 403))

    def test_put_updates_attendance_mode(self):
        self.client.put(f"/api/productions/{self.production.pk}/", self.payload, **int_headers())
        self.production.refresh_from_db()
        self.assertEqual(self.production.attendance_mode, "online")


# ---------------------------------------------------------------------------
# PATCH /api/productions/<id>/ - partial update
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetPartialUpdate(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.production = ProductionFactory.create(attendance_mode="offline", performer_type="solo")

    def test_patch_with_internal_key_returns_200(self):
        response = self.client.patch(
            f"/api/productions/{self.production.pk}/",
            {"attendance_mode": "online"},
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_with_public_key_returns_403(self):
        response = self.client.patch(
            f"/api/productions/{self.production.pk}/",
            {"attendance_mode": "online"},
            **pub_headers(),
        )
        self.assertIn(response.status_code, (401, 403))

    def test_patch_without_auth_returns_403(self):
        response = self.client.patch(f"/api/productions/{self.production.pk}/", {"attendance_mode": "online"})
        self.assertIn(response.status_code, (401, 403))

    def test_patch_only_updates_specified_field(self):
        self.client.patch(
            f"/api/productions/{self.production.pk}/",
            {"attendance_mode": "online"},
            **int_headers(),
        )
        self.production.refresh_from_db()
        self.assertEqual(self.production.attendance_mode, "online")
        self.assertEqual(self.production.performer_type, "solo")  # unchanged


# ---------------------------------------------------------------------------
# DELETE /api/productions/<id>/ - destroy
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetDelete(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.production = ProductionFactory.create()

    def test_delete_with_internal_key_returns_204(self):
        response = self.client.delete(f"/api/productions/{self.production.pk}/", **int_headers())
        self.assertEqual(response.status_code, 204)

    def test_delete_with_public_key_returns_403(self):
        response = self.client.delete(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_delete_without_auth_returns_403(self):
        response = self.client.delete(f"/api/productions/{self.production.pk}/")
        self.assertIn(response.status_code, (401, 403))

    def test_delete_with_wrong_key_returns_403(self):
        response = self.client.delete(f"/api/productions/{self.production.pk}/", **wrong_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_delete_removes_production_from_database(self):
        pk = self.production.pk
        self.client.delete(f"/api/productions/{pk}/", **int_headers())
        self.assertFalse(Production.objects.filter(pk=pk).exists())


# ---------------------------------------------------------------------------
# Response structure - nested and translated fields
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetResponseStructure(TestCase):
    """Verify that nested and translated fields are correctly represented in API responses."""

    def setUp(self):
        self.client = APIClient()
        self.nl = LanguageFactory.create(code="nl", name="Dutch")
        self.theme = UitDatabaseThemeFactory.create(name="Drama")
        self.db_type = UitDatabaseTypeFactory.create(name="Theater")
        self.production = ProductionFactory.create(
            uit_database_theme=self.theme,
            uit_database_type=self.db_type,
            attendance_mode="offline",
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

    def test_detail_contains_nested_uit_database_theme(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertEqual(response.data["uit_database_theme"]["name"], "Drama")

    def test_detail_contains_nested_uit_database_type(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertEqual(response.data["uit_database_type"]["name"], "Theater")

    def test_detail_title_is_translated_dict(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertIsInstance(response.data["title"], dict)
        self.assertIn("nl", response.data["title"])

    def test_detail_title_nl_value_is_correct(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertEqual(response.data["title"]["nl"], "Test Titel")

    def test_detail_description_nl_value_is_correct(self):
        response = self.client.get(f"/api/productions/{self.production.pk}/", **pub_headers())
        self.assertEqual(response.data["description"]["nl"], "Test Beschrijving")

    def test_detail_title_is_empty_dict_without_translations(self):
        production_no_trans = ProductionFactory.create()
        response = self.client.get(f"/api/productions/{production_no_trans.pk}/", **pub_headers())
        self.assertEqual(response.data["title"], {})


# ---------------------------------------------------------------------------
# N+1 guard - prefetch translations
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestProductionViewSetPrefetch(TestCase):
    """Ensure translations are prefetched and do not cause N+1 queries on list."""

    def setUp(self):
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

    def test_list_with_translations_executes_bounded_queries(self):
        with self.assertNumQueries(6):
            response = self.client.get("/api/productions/", **pub_headers())
        self.assertEqual(response.status_code, 200)
