from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.languages.models import Language
from apps.pricing.models import (
    Price,
    PriceRank,
    PriceRankTranslation,
    PriceTranslation,
)
from apps.pricing.views import PriceRankViewSet, PriceViewSet
from tests.factories.language import LanguageFactory
from tests.factories.pricing import (
    PriceFactory,
    PriceRankFactory,
    PriceRankTranslationFactory,
    PriceTranslationFactory,
)

PUB_KEY = "pub-view-test-key"
INT_KEY = "int-view-test-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def wrong_headers():
    return {"HTTP_X_API_KEY": "completely-wrong-key"}


def results_list(response):
    """Support both paginated and non-paginated responses."""
    return response.data.get("results", response.data)


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestPriceViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        """Test case for test_inherits_from_api_model_viewset."""
        self.assertTrue(issubclass(PriceViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        """Test case for test_queryset_model."""
        self.assertEqual(PriceViewSet.queryset.model, Price)

    def test_serializer_class(self):
        """Test case for test_serializer_class."""
        from apps.pricing.serializers import PriceSerializer

        self.assertEqual(PriceViewSet.serializer_class, PriceSerializer)


class TestPriceRankViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        """Test case for test_inherits_from_api_model_viewset."""
        self.assertTrue(issubclass(PriceRankViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        """Test case for test_queryset_model."""
        self.assertEqual(PriceRankViewSet.queryset.model, PriceRank)

    def test_serializer_class(self):
        """Test case for test_serializer_class."""
        from apps.pricing.serializers import PriceRankSerializer

        self.assertEqual(PriceRankViewSet.serializer_class, PriceRankSerializer)


# ---------------------------------------------------------------------------
# PriceRank N+1 guard
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestPriceRankViewSetPrefetch(TestCase):
    """Ensure price rank list stays bounded when translations exist."""

    def setUp(self):
        self.client = APIClient()
        self.lang_en = LanguageFactory.create(code="en", name="English", is_active=True)
        self.lang_nl = LanguageFactory.create(code="nl", name="Nederlands", is_active=True)

        for idx in range(5):
            rank = PriceRankFactory(position=idx)
            PriceRankTranslationFactory(price_rank=rank, language=self.lang_en, description=f"Rank {idx} en")
            PriceRankTranslationFactory(price_rank=rank, language=self.lang_nl, description=f"Rank {idx} nl")

    def test_price_rank_list_bounded_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/v1/price-ranks/?ordering=id", **pub_headers())

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(results_list(response)), 5)
        self.assertLessEqual(len(ctx), 3)


# ---------------------------------------------------------------------------
# Prices - shared setup mixin
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class _PriceSetupMixin(TestCase):
    def setUp(self):
        self.client = APIClient()

        PriceTranslation.objects.all().delete()
        Price.objects.all().delete()
        Language.objects.all().delete()

        self.lang_en = LanguageFactory.create(code="en", name="English", is_active=True)
        self.lang_nl = LanguageFactory.create(code="nl", name="Nederlands", is_active=True)

        self.p1 = PriceFactory.create(
            type="A",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=1,
            cineville_box=False,
        )
        self.p2 = PriceFactory.create(
            type="B",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=5,
            cineville_box=False,
        )
        PriceTranslationFactory.create(price=self.p1, language=self.lang_en, description="A en")
        PriceTranslationFactory.create(price=self.p1, language=self.lang_nl, description="A nl")

        # extra data to exercise prefetches
        for idx in range(4):
            price = PriceFactory.create(type=f"X{idx}")
            PriceTranslationFactory.create(price=price, language=self.lang_en, description=f"X{idx} en")
            PriceTranslationFactory.create(price=price, language=self.lang_nl, description=f"X{idx} nl")


# ---------------------------------------------------------------------------
# GET /api/v1/prices/ - list
# ---------------------------------------------------------------------------


class TestPriceViewSetList(_PriceSetupMixin):
    def test_list_with_public_key_returns_200(self):
        """Test case for test_list_with_public_key_returns_200."""
        response = self.client.get("/api/v1/prices/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_with_internal_key_also_returns_200(self):
        """Test case for test_list_with_internal_key_also_returns_200."""
        response = self.client.get("/api/v1/prices/?ordering=id", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_returns_prices(self):
        """Test case for test_list_returns_prices."""
        response = self.client.get("/api/v1/prices/?ordering=id", **pub_headers())
        items = results_list(response)
        types = [item["type"] for item in items]
        self.assertIn("A", types)
        self.assertIn("B", types)

    def test_list_response_has_expected_fields(self):
        """Test case for test_list_response_has_expected_fields."""
        response = self.client.get("/api/v1/prices/?ordering=id", **pub_headers())
        item = results_list(response)[0]

        # Core fields from Price model
        self.assertIn("id", item)
        self.assertIn("type", item)
        self.assertIn("visibility", item)
        self.assertIn("membership", item)
        self.assertIn("minimum", item)
        self.assertIn("maximum", item)
        self.assertIn("step", item)
        self.assertIn("sort_order", item)
        self.assertIn("cineville_box", item)

        # Serializer computed field
        self.assertIn("description", item)

    def test_list_without_auth_returns_401(self):
        """Test case for test_list_without_auth_returns_401."""
        response = self.client.get("/api/v1/prices/")
        self.assertEqual(response.status_code, 401)

    def test_list_with_wrong_key_returns_401(self):
        """Test case for test_list_with_wrong_key_returns_401."""
        response = self.client.get("/api/v1/prices/", **wrong_headers())
        self.assertEqual(response.status_code, 401)

    def test_list_prefetches_translations_bounded_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/v1/prices/?ordering=id", **pub_headers())

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(results_list(response)), 4)
        self.assertLessEqual(len(ctx), 10)


# ---------------------------------------------------------------------------
# GET /api/v1/prices/<id>/ - retrieve
# ---------------------------------------------------------------------------


class TestPriceViewSetRetrieve(_PriceSetupMixin):
    def test_retrieve_with_public_key_returns_200(self):
        """Test case for test_retrieve_with_public_key_returns_200."""
        response = self.client.get(f"/api/v1/prices/{self.p1.id}/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_with_internal_key_also_returns_200(self):
        """Test case for test_retrieve_with_internal_key_also_returns_200."""
        response = self.client.get(f"/api/v1/prices/{self.p1.id}/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_returns_correct_price(self):
        """Test case for test_retrieve_returns_correct_price."""
        response = self.client.get(f"/api/v1/prices/{self.p1.id}/", **pub_headers())
        self.assertEqual(response.data["id"], self.p1.id)
        self.assertEqual(response.data["type"], "A")

    def test_retrieve_nonexistent_returns_404(self):
        """Test case for test_retrieve_nonexistent_returns_404."""
        response = self.client.get("/api/v1/prices/999999/", **pub_headers())
        self.assertEqual(response.status_code, 404)

    def test_retrieve_without_auth_returns_401(self):
        """Test case for test_retrieve_without_auth_returns_401."""
        response = self.client.get(f"/api/v1/prices/{self.p1.id}/")
        self.assertEqual(response.status_code, 401)

    def test_retrieve_with_wrong_key_returns_401(self):
        """Test case for test_retrieve_with_wrong_key_returns_401."""
        response = self.client.get(f"/api/v1/prices/{self.p1.id}/", **wrong_headers())
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# POST /api/v1/prices/ - create (internal only)
# ---------------------------------------------------------------------------


class TestPriceViewSetCreate(_PriceSetupMixin):
    def test_create_with_internal_key_returns_201(self):
        """Test case for test_create_with_internal_key_returns_201."""
        response = self.client.post(
            "/api/v1/prices/",
            {
                "type": "C",
                "visibility": "public",
                "membership": "",
                "minimum": None,
                "maximum": None,
                "step": None,
                "sort_order": 10,
                "cineville_box": False,
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)

    def test_create_adds_price_to_db(self):
        """Test case for test_create_adds_price_to_db."""
        self.client.post(
            "/api/v1/prices/",
            {
                "type": "C",
                "visibility": "public",
                "membership": "",
                "minimum": None,
                "maximum": None,
                "step": None,
                "sort_order": 10,
                "cineville_box": False,
            },
            format="json",
            **int_headers(),
        )
        self.assertTrue(Price.objects.filter(type="C").exists())

    def test_create_with_public_key_returns_403(self):
        """Test case for test_create_with_public_key_returns_403."""
        response = self.client.post(
            "/api/v1/prices/",
            {
                "type": "C",
                "visibility": "public",
                "membership": "",
                "minimum": None,
                "maximum": None,
                "step": None,
                "sort_order": 10,
                "cineville_box": False,
            },
            format="json",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_create_without_auth_returns_401(self):
        """Test case for test_create_without_auth_returns_401."""
        response = self.client.post(
            "/api/v1/prices/",
            {
                "type": "C",
                "visibility": "public",
                "sort_order": 10,
                "cineville_box": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_create_with_wrong_key_returns_401(self):
        """Test case for test_create_with_wrong_key_returns_401."""
        response = self.client.post(
            "/api/v1/prices/",
            {
                "type": "C",
                "visibility": "public",
                "sort_order": 10,
                "cineville_box": False,
            },
            format="json",
            **wrong_headers(),
        )
        self.assertEqual(response.status_code, 401)

    def test_create_missing_required_field_returns_422(self):
        """Test case for test_create_missing_required_field_returns_422."""
        response = self.client.post(
            "/api/v1/prices/",
            {
                "visibility": "public",
                "sort_order": 10,
                "cineville_box": False,
            },  # missing type
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 422)


# ---------------------------------------------------------------------------
# PUT /api/v1/prices/<id>/ - full update (internal only)
# ---------------------------------------------------------------------------


class TestPriceViewSetUpdate(_PriceSetupMixin):
    def test_put_with_internal_key_returns_200(self):
        """Test case for test_put_with_internal_key_returns_200."""
        response = self.client.put(
            f"/api/v1/prices/{self.p1.id}/",
            {
                "type": "A-new",
                "visibility": "public",
                "membership": "",
                "minimum": None,
                "maximum": None,
                "step": None,
                "sort_order": 1,
                "cineville_box": False,
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_put_updates_price_in_db(self):
        """Test case for test_put_updates_price_in_db."""
        self.client.put(
            f"/api/v1/prices/{self.p1.id}/",
            {
                "type": "A-new",
                "visibility": "public",
                "membership": "",
                "minimum": None,
                "maximum": None,
                "step": None,
                "sort_order": 1,
                "cineville_box": False,
            },
            format="json",
            **int_headers(),
        )
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.type, "A-new")

    def test_put_with_public_key_returns_403(self):
        """Test case for test_put_with_public_key_returns_403."""
        response = self.client.put(
            f"/api/v1/prices/{self.p1.id}/",
            {
                "type": "A-new",
                "visibility": "public",
                "membership": "",
                "minimum": None,
                "maximum": None,
                "step": None,
                "sort_order": 1,
                "cineville_box": False,
            },
            format="json",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_put_nonexistent_returns_404(self):
        """Test case for test_put_nonexistent_returns_404."""
        response = self.client.put(
            "/api/v1/prices/999999/",
            {
                "type": "X",
                "visibility": "public",
                "membership": "",
                "minimum": None,
                "maximum": None,
                "step": None,
                "sort_order": 0,
                "cineville_box": False,
            },
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# PATCH /api/v1/prices/<id>/ - partial update (internal only)
# ---------------------------------------------------------------------------


class TestPriceViewSetPartialUpdate(_PriceSetupMixin):
    def test_patch_with_internal_key_returns_200(self):
        """Test case for test_patch_with_internal_key_returns_200."""
        response = self.client.patch(
            f"/api/v1/prices/{self.p1.id}/",
            {"type": "A-updated"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_updates_only_specified_fields(self):
        """Test case for test_patch_updates_only_specified_fields."""
        self.client.patch(
            f"/api/v1/prices/{self.p1.id}/",
            {"type": "A-updated"},
            format="json",
            **int_headers(),
        )
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.type, "A-updated")

    def test_patch_with_public_key_returns_403(self):
        """Test case for test_patch_with_public_key_returns_403."""
        response = self.client.patch(
            f"/api/v1/prices/{self.p1.id}/",
            {"type": "A-updated"},
            format="json",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_without_auth_returns_401(self):
        """Test case for test_patch_without_auth_returns_401."""
        response = self.client.patch(
            f"/api/v1/prices/{self.p1.id}/",
            {"type": "A-updated"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_patch_with_wrong_key_returns_401(self):
        """Test case for test_patch_with_wrong_key_returns_401."""
        response = self.client.patch(
            f"/api/v1/prices/{self.p1.id}/",
            {"type": "A-updated"},
            format="json",
            **wrong_headers(),
        )
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# DELETE /api/v1/prices/<id>/ - destroy (internal only)
# ---------------------------------------------------------------------------


class TestPriceViewSetDelete(_PriceSetupMixin):
    def test_delete_with_internal_key_returns_204(self):
        """Test case for test_delete_with_internal_key_returns_204."""
        response = self.client.delete(f"/api/v1/prices/{self.p1.id}/", **int_headers())
        self.assertEqual(response.status_code, 204)

    def test_delete_removes_price_from_db(self):
        """Test case for test_delete_removes_price_from_db."""
        self.client.delete(f"/api/v1/prices/{self.p1.id}/", **int_headers())
        self.assertFalse(Price.objects.filter(id=self.p1.id).exists())

    def test_delete_with_public_key_returns_403(self):
        """Test case for test_delete_with_public_key_returns_403."""
        response = self.client.delete(f"/api/v1/prices/{self.p1.id}/", **pub_headers())
        self.assertEqual(response.status_code, 403)

    def test_delete_without_auth_returns_401(self):
        """Test case for test_delete_without_auth_returns_401."""
        response = self.client.delete(f"/api/v1/prices/{self.p1.id}/")
        self.assertEqual(response.status_code, 401)

    def test_delete_nonexistent_returns_404(self):
        """Test case for test_delete_nonexistent_returns_404."""
        response = self.client.delete("/api/v1/prices/999999/", **int_headers())
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# Price ranks - shared setup mixin
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class _PriceRankSetupMixin(TestCase):
    def setUp(self):
        self.client = APIClient()

        PriceRankTranslation.objects.all().delete()
        PriceRank.objects.all().delete()
        Language.objects.all().delete()

        self.lang = LanguageFactory.create(code="en", name="English", is_active=True)

        self.r1 = PriceRankFactory.create(position=1, sold_out_buffer=0)
        self.r2 = PriceRankFactory.create(position=2, sold_out_buffer=0)
        PriceRankTranslationFactory.create(price_rank=self.r1, language=self.lang, description="R1")


# ---------------------------------------------------------------------------
# GET /api/v1/price-ranks/ - list
# ---------------------------------------------------------------------------


class TestPriceRankViewSetList(_PriceRankSetupMixin):
    def test_list_with_public_key_returns_200(self):
        """Test case for test_list_with_public_key_returns_200."""
        response = self.client.get("/api/v1/price-ranks/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_with_internal_key_also_returns_200(self):
        """Test case for test_list_with_internal_key_also_returns_200."""
        response = self.client.get("/api/v1/price-ranks/?ordering=id", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_returns_ranks(self):
        """Test case for test_list_returns_ranks."""
        response = self.client.get("/api/v1/price-ranks/?ordering=id", **pub_headers())
        items = results_list(response)
        positions = [item["position"] for item in items]
        self.assertIn(1, positions)
        self.assertIn(2, positions)

    def test_list_without_auth_returns_401(self):
        """Test case for test_list_without_auth_returns_401."""
        response = self.client.get("/api/v1/price-ranks/")
        self.assertEqual(response.status_code, 401)

    def test_list_with_wrong_key_returns_401(self):
        """Test case for test_list_with_wrong_key_returns_401."""
        response = self.client.get("/api/v1/price-ranks/", **wrong_headers())
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# POST /api/v1/price-ranks/ - create (internal only)
# ---------------------------------------------------------------------------


class TestPriceRankViewSetCreate(_PriceRankSetupMixin):
    def test_create_with_internal_key_returns_201(self):
        """Test case for test_create_with_internal_key_returns_201."""
        response = self.client.post(
            "/api/v1/price-ranks/",
            {"position": 3, "sold_out_buffer": 0},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)

    def test_create_with_public_key_returns_403(self):
        """Test case for test_create_with_public_key_returns_403."""
        response = self.client.post(
            "/api/v1/price-ranks/",
            {"position": 3, "sold_out_buffer": 0},
            format="json",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_create_duplicate_position_returns_422(self):
        """Test case for test_create_duplicate_position_returns_422."""
        response = self.client.post(
            "/api/v1/price-ranks/",
            {"position": 1, "sold_out_buffer": 0},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 422)
