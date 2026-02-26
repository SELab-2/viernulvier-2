from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.languages.models import Language
from apps.pricing.models import Price, PriceTranslation, PriceRank, PriceRankTranslation
from apps.pricing.views import (
    PriceViewSet,
    PriceRankViewSet
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


class TestPriceRankViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self):
        self.assertTrue(issubclass(PriceRankViewSet, ApiModelViewSet))

    def test_queryset_model(self):
        self.assertEqual(PriceRankViewSet.queryset.model, PriceRank)


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
