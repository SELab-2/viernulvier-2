"""Tests for the admin dashboard template tag helpers."""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.core.templatetags import admin_dashboard
from apps.productions.models import ProductionTag
from tests.factories.production import ProductionFactory
from tests.factories.tag import TagFactory


class TestAdminDashboardTemplateTag(TestCase):
    """Coverage for ``apps.core.templatetags.admin_dashboard``."""

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get("/admin/")
        request.user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="secret123",
        )
        return request

    def test_model_admin_helpers_return_urls_for_registered_models(self) -> None:
        """Helper methods should resolve add/changelist URLs for registered models."""
        changelist = admin_dashboard._model_admin_url(ProductionFactory._meta.model)
        add_url = admin_dashboard._model_admin_add_url(ProductionFactory._meta.model)

        assert changelist == reverse("admin:productions_production_changelist")
        assert add_url == reverse("admin:productions_production_add")

    def test_model_admin_helpers_return_none_for_missing_admin_routes(self) -> None:
        """Helper methods should return ``None`` when the model has no admin route."""
        assert admin_dashboard._model_admin_url(ProductionTag) is None
        assert admin_dashboard._model_admin_add_url(ProductionTag) is None

    def test_dashboard_cards_returns_empty_list_without_request_in_context(self) -> None:
        """Tag should fail closed when no request is available in template context."""
        assert admin_dashboard.dashboard_cards({}) == []

    def test_dashboard_cards_skips_unavailable_or_forbidden_cards(self) -> None:
        """Tag should skip entries with missing admin, denied permissions, or missing URL."""
        TagFactory.create_batch(2)
        request = self._request()

        denied_module_admin = Mock()
        denied_module_admin.has_module_permission.return_value = False

        denied_view_admin = Mock()
        denied_view_admin.has_module_permission.return_value = True
        denied_view_admin.has_view_or_change_permission.return_value = False

        allowed_admin = Mock()
        allowed_admin.has_module_permission.return_value = True
        allowed_admin.has_view_or_change_permission.return_value = True
        allowed_admin.has_add_permission.return_value = False

        specs = (
            admin_dashboard.DashboardCardSpec(
                title="No admin",
                description="Skipped when model has no admin registration.",
                model=ProductionTag,
            ),
            admin_dashboard.DashboardCardSpec(
                title="No module permission",
                description="Skipped when module permission is denied.",
                model=ProductionFactory._meta.model,
            ),
            admin_dashboard.DashboardCardSpec(
                title="No view permission",
                description="Skipped when view permission is denied.",
                model=admin_dashboard.Event,
            ),
            admin_dashboard.DashboardCardSpec(
                title="No changelist URL",
                description="Skipped when changelist URL cannot be reversed.",
                model=admin_dashboard.Blog,
            ),
            admin_dashboard.DashboardCardSpec(
                title="Allowed",
                description="Should be rendered.",
                model=admin_dashboard.Tag,
            ),
        )

        registry_by_model = {
            ProductionTag: None,
            ProductionFactory._meta.model: denied_module_admin,
            admin_dashboard.Event: denied_view_admin,
            admin_dashboard.Blog: allowed_admin,
            admin_dashboard.Tag: allowed_admin,
        }

        with (
            patch.object(admin_dashboard, "CARD_SPECS", specs),
            patch.object(admin_dashboard.admin.site, "_registry", registry_by_model),
            patch.object(
                admin_dashboard,
                "_model_admin_url",
                side_effect=lambda model: "/admin/tags/tag/" if model is admin_dashboard.Tag else None,
            ),
        ):
            cards = admin_dashboard.dashboard_cards({"request": request})

        assert len(cards) == 1
        assert cards[0]["title"] == "Allowed"
        assert cards[0]["count"] == 2
        assert cards[0]["url"] == "/admin/tags/tag/"
        assert cards[0]["add_url"] is None

    def test_dashboard_cards_includes_add_url_when_add_is_allowed(self) -> None:
        """Tag should include add URL when model admin allows adding."""
        ProductionFactory.create_batch(2)
        request = self._request()

        specs = (
            admin_dashboard.DashboardCardSpec(
                title="Productions",
                description="Core catalogue entries and metadata.",
                model=ProductionFactory._meta.model,
            ),
        )

        with patch.object(admin_dashboard, "CARD_SPECS", specs):
            cards = admin_dashboard.dashboard_cards({"request": request})

        assert len(cards) == 1
        assert cards[0]["count"] == 2
        assert cards[0]["url"] == reverse("admin:productions_production_changelist")
        assert cards[0]["add_url"] == reverse("admin:productions_production_add")

    def test_build_multiselect_options_without_facets(self) -> None:
        class DummySpec:
            lookup_choices = [("a", "Alpha"), ("b", "Beta")]
            selected_values = ("b",)

        class DummyChangeList:
            add_facets = False

        options = admin_dashboard._build_multiselect_options(DummyChangeList(), DummySpec())

        assert options == [
            {"value": "a", "label": "Alpha", "selected": False, "count": None},
            {"value": "b", "label": "Beta", "selected": True, "count": None},
        ]

    def test_build_multiselect_options_with_facets(self) -> None:
        class DummySpec:
            lookup_choices = [("a", "Alpha"), ("b", "Beta")]
            selected_values = ()

            def get_facet_queryset(self, _cl):
                return {"0__c": 4, "1__c": 2}

        class DummyChangeList:
            add_facets = True

        options = admin_dashboard._build_multiselect_options(DummyChangeList(), DummySpec())

        assert options == [
            {"value": "a", "label": "Alpha", "selected": False, "count": 4},
            {"value": "b", "label": "Beta", "selected": False, "count": 2},
        ]

    def test_multiselect_options_tag_passthrough(self) -> None:
        class DummySpec:
            lookup_choices = [("a", "Alpha")]
            selected_values = ()

            def get_facet_queryset(self, _cl):
                return {"0__c": 1}

        class DummyChangeList:
            add_facets = True

        assert admin_dashboard.multiselect_options(DummyChangeList(), DummySpec()) == [
            {"value": "a", "label": "Alpha", "selected": False, "count": 1}
        ]
