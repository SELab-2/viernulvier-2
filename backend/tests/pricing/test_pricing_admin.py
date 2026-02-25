from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from apps.languages.models import Language
from apps.pricing.admin import (
    PriceAdmin,
    PriceRankAdmin,
    PriceTranslationAdmin,
    PriceRankTranslationAdmin,
)
from apps.pricing.models import Price, PriceRank, PriceTranslation, PriceRankTranslation


class PricingAdminConfigTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()

    def test_price_admin_config(self):
        admin_obj = PriceAdmin(Price, self.site)

        self.assertIn("type", admin_obj.list_filter)
        self.assertIn("visibility", admin_obj.list_filter)
        self.assertIn("membership", admin_obj.list_filter)
        self.assertIn("cineville_box", admin_obj.list_filter)

        self.assertIn("id", admin_obj.search_fields)

        self.assertEqual(admin_obj.ordering, ("sort_order",))
        self.assertTrue(admin_obj.inlines) 

    def test_price_rank_admin_config(self):
        admin_obj = PriceRankAdmin(PriceRank, self.site)

        self.assertEqual(admin_obj.ordering, ("position",))
        self.assertIn("id", admin_obj.search_fields)
        self.assertIn("position", admin_obj.search_fields)
        self.assertTrue(admin_obj.inlines)


class PricingAdminQuerysetOptimizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lang = Language.objects.create(code="en", name="English")
        cls.price = Price.objects.create(
            type="Standard",
            visibility="public",
            membership="",
            minimum=None,
            maximum=None,
            step=None,
            sort_order=0,
        )
        cls.rank = PriceRank.objects.create(position=1, sold_out_buffer=0)

        cls.price_tr = PriceTranslation.objects.create(
            price=cls.price, language=cls.lang, description="Standard ticket"
        )
        cls.rank_tr = PriceRankTranslation.objects.create(
            price_rank=cls.rank, language=cls.lang, description="First rank"
        )

    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()

    def test_price_translation_admin_get_queryset_select_related(self):
        admin_obj = PriceTranslationAdmin(PriceTranslation, self.site)
        request = self.factory.get("/admin/")
        qs = admin_obj.get_queryset(request)

        with self.assertNumQueries(1):
            obj = qs.get(pk=self.price_tr.pk)
            _ = obj.price.id
            _ = obj.language.code

    def test_price_rank_translation_admin_get_queryset_select_related(self):
        admin_obj = PriceRankTranslationAdmin(PriceRankTranslation, self.site)
        request = self.factory.get("/admin/")

        qs = admin_obj.get_queryset(request)

        with self.assertNumQueries(1):
            obj = qs.get(pk=self.rank_tr.pk)
            _ = obj.price_rank.id
            _ = obj.language.code