from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.languages.models import Language
from apps.pricing.models import Price, PriceTranslation, PriceRank, PriceRankTranslation
from apps.pricing.views import (
    PriceViewSet,
    PriceTranslationViewSet,
    PriceRankViewSet,
    PriceRankTranslationViewSet,
)

PUB_KEY = "pub-view-test-key"
INT_KEY = "int-view-test-key"


def pub_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {PUB_KEY}"}


def int_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {INT_KEY}"}


def wrong_headers():
    return {"HTTP_AUTHORIZATION": "Api-Key completely-wrong-key"}


class TestPriceViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(PriceViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        self.assertEqual(PriceViewSet.queryset.model, Price)


class TestPriceTranslationViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(PriceTranslationViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        self.assertEqual(PriceTranslationViewSet.queryset.model, PriceTranslation)


class TestPriceRankViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(PriceRankViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        self.assertEqual(PriceRankViewSet.queryset.model, PriceRank)


class TestPriceRankTranslationViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(PriceRankTranslationViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        self.assertEqual(PriceRankTranslationViewSet.queryset.model, PriceRankTranslation)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestPriceViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        PriceTranslation.objects.all().delete()
        Price.objects.all().delete()
        Language.objects.all().delete()

        self.lang_en = Language.objects.create(code="en", name="English", is_active=True)
        self.lang_nl = Language.objects.create(code="nl", name="Nederlands", is_active=True)

        self.p1 = Price.objects.create(
            type="A",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=1,
        )
        self.p2 = Price.objects.create(
            type="B",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=5,
        )
        PriceTranslation.objects.create(price=self.p1, language=self.lang_en, description="A en")
        PriceTranslation.objects.create(price=self.p1, language=self.lang_nl, description="A nl")


    def test_list_public_key(self):
        response = self.client.get("/api/prices/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_internal_key(self):
        response = self.client.get("/api/prices/?ordering=id", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_without_auth(self):
        response = self.client.get("/api/prices/")
        self.assertEqual(response.status_code, 403)

    def test_retrieve_public_key(self):
        response = self.client.get(f"/api/prices/{self.p1.id}/", **pub_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "A")

    def test_retrieve_wrong_key(self):
        response = self.client.get(f"/api/prices/{self.p1.id}/", **wrong_headers())
        self.assertIn(response.status_code, [401, 403])

    def test_create_internal_key(self):
        response = self.client.post(
            "/api/prices/",
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
        self.assertTrue(Price.objects.filter(type="C").exists())

    def test_create_public_key_denied(self):
        response = self.client.post(
            "/api/prices/",
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
        self.assertIn(response.status_code, [401, 403])

    def test_patch_internal_key(self):
        response = self.client.patch(
            f"/api/prices/{self.p1.id}/",
            {"type": "A-updated"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.type, "A-updated")

    def test_delete_internal_key(self):
        response = self.client.delete(f"/api/prices/{self.p1.id}/", **int_headers())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Price.objects.filter(id=self.p1.id).exists())


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestPriceTranslationViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        PriceTranslation.objects.all().delete()
        Price.objects.all().delete()
        Language.objects.all().delete()

        self.lang = Language.objects.create(code="en", name="English", is_active=True)
        self.price = Price.objects.create(
            type="Standard",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
        )
        self.tr = PriceTranslation.objects.create(
            price=self.price, language=self.lang, description="Standard ticket"
        )

    def test_list_public_key(self):
        response = self.client.get("/api/price-translations/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_without_auth(self):
        response = self.client.get("/api/price-translations/")
        self.assertEqual(response.status_code, 403)

    def test_retrieve_public_key(self):
        response = self.client.get(f"/api/price-translations/{self.tr.id}/", **pub_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], "Standard ticket")

    def test_create_internal_key(self):
        response = self.client.post(
            "/api/price-translations/",
            {"price": self.price.id, "language": self.lang.code, "description": "New"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)

    def test_create_public_key_denied(self):
        response = self.client.post(
            "/api/price-translations/",
            {"price": self.price.id, "language": self.lang.code, "description": "New"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, [401, 403])


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestPriceRankViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        PriceRankTranslation.objects.all().delete()
        PriceRank.objects.all().delete()
        Language.objects.all().delete()

        self.lang = Language.objects.create(code="en", name="English", is_active=True)
        self.r1 = PriceRank.objects.create(position=1, sold_out_buffer=0)
        self.r2 = PriceRank.objects.create(position=2, sold_out_buffer=0)
        PriceRankTranslation.objects.create(price_rank=self.r1, language=self.lang, description="R1")

    def test_list_public_key(self):
        response = self.client.get("/api/price-ranks/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_without_auth(self):
        response = self.client.get("/api/price-ranks/")
        self.assertEqual(response.status_code, 403)

    def test_create_internal_key(self):
        response = self.client.post(
            "/api/price-ranks/",
            {"position": 3, "sold_out_buffer": 0},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 201)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestPriceRankTranslationViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        PriceRankTranslation.objects.all().delete()
        PriceRank.objects.all().delete()
        Language.objects.all().delete()

        self.lang = Language.objects.create(code="en", name="English", is_active=True)
        self.rank = PriceRank.objects.create(position=1, sold_out_buffer=0)
        self.tr = PriceRankTranslation.objects.create(
            price_rank=self.rank, language=self.lang, description="First rank"
        )

    def test_list_public_key(self):
        response = self.client.get("/api/price-rank-translations/?ordering=id", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_retrieve_public_key(self):
        response = self.client.get(
            f"/api/price-rank-translations/{self.tr.id}/",
            **pub_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], "First rank")