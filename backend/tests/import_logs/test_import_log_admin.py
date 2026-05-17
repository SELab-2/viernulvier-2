"""
Tests for apps/import_log/admin.py

Covers:
- ImportLogAdmin is registered
- ImportLogAdmin inherits from BaseAdmin
- list_display configuration
- list_filter configuration
- search_fields configuration
- readonly_fields includes all data fields
- has_add_permission returns False for all users
- Functional admin changelist (with superuser)
- Functional admin changeform (with superuser)
- Add view is blocked (returns 403)
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.core.admin import BaseAdmin
from apps.import_log.admin import ImportLogAdmin
from apps.import_log.models import ImportLog
from tests.factories.import_log import ImportLogFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_superuser(username="admin"):
    return User.objects.create_superuser(username=username, password="password", email=f"{username}@example.com")


def make_import_log(**kwargs):
    """Create a persisted ImportLog with stable defaults for tests."""
    defaults = {
        "source": "test_import.json",
        "status": ImportLog.Status.SUCCESS,
        "records_total": 10,
        "records_imported": 10,
        "records_failed": 0,
        "started_at": None,
        "finished_at": None,
        "error_message": None,
    }
    defaults.update(kwargs)
    log = ImportLogFactory.build(**defaults)
    log.save()
    return log


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestImportLogAdminRegistration(TestCase):
    """Verify ImportLogAdmin is registered."""

    def test_import_log_is_registered(self) -> None:
        assert ImportLog in admin.site._registry

    def test_registered_admin_is_import_log_admin(self) -> None:
        assert isinstance(admin.site._registry[ImportLog], ImportLogAdmin)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestImportLogAdminInheritance(TestCase):
    """ImportLogAdmin must extend BaseAdmin."""

    def test_inherits_from_base_admin(self) -> None:
        assert issubclass(ImportLogAdmin, BaseAdmin)

    def test_inherits_from_model_admin(self) -> None:
        assert issubclass(ImportLogAdmin, admin.ModelAdmin)


# ---------------------------------------------------------------------------
# list_display
# ---------------------------------------------------------------------------


class TestImportLogAdminListDisplay(TestCase):
    """Tests for list_display configuration."""

    def setUp(self) -> None:
        self.admin = admin.site._registry[ImportLog]

    def test_list_display_contains_id(self) -> None:
        assert "id" in self.admin.list_display

    def test_list_display_contains_source(self) -> None:
        assert "source" in self.admin.list_display

    def test_list_display_contains_status(self) -> None:
        assert "status" in self.admin.list_display

    def test_list_display_contains_records_total(self) -> None:
        assert "records_total" in self.admin.list_display

    def test_list_display_contains_records_imported(self) -> None:
        assert "records_imported" in self.admin.list_display

    def test_list_display_contains_records_failed(self) -> None:
        assert "records_failed" in self.admin.list_display

    def test_list_display_contains_started_at(self) -> None:
        assert "started_at" in self.admin.list_display

    def test_list_display_contains_finished_at(self) -> None:
        assert "finished_at" in self.admin.list_display


# ---------------------------------------------------------------------------
# list_filter
# ---------------------------------------------------------------------------


class TestImportLogAdminListFilter(TestCase):
    """Tests for list_filter configuration."""

    def setUp(self) -> None:
        self.admin = admin.site._registry[ImportLog]

    def test_list_filter_contains_status(self) -> None:
        assert "status" in self.admin.list_filter


# ---------------------------------------------------------------------------
# search_fields
# ---------------------------------------------------------------------------


class TestImportLogAdminSearchFields(TestCase):
    """Tests for search_fields configuration."""

    def setUp(self) -> None:
        self.admin = admin.site._registry[ImportLog]

    def test_search_fields_contains_source(self) -> None:
        assert "source" in self.admin.search_fields

    def test_search_fields_contains_error_message(self) -> None:
        assert "error_message" in self.admin.search_fields


# ---------------------------------------------------------------------------
# readonly_fields
# ---------------------------------------------------------------------------


class TestImportLogAdminReadonlyFields(TestCase):
    """All data fields must be read-only to protect log integrity."""

    def setUp(self) -> None:
        self.admin = admin.site._registry[ImportLog]

    def test_readonly_fields_contains_source(self) -> None:
        assert "source" in self.admin.readonly_fields

    def test_readonly_fields_contains_status(self) -> None:
        assert "status" in self.admin.readonly_fields

    def test_readonly_fields_contains_records_total(self) -> None:
        assert "records_total" in self.admin.readonly_fields

    def test_readonly_fields_contains_records_imported(self) -> None:
        assert "records_imported" in self.admin.readonly_fields

    def test_readonly_fields_contains_records_failed(self) -> None:
        assert "records_failed" in self.admin.readonly_fields

    def test_readonly_fields_contains_started_at(self) -> None:
        assert "started_at" in self.admin.readonly_fields

    def test_readonly_fields_contains_finished_at(self) -> None:
        assert "finished_at" in self.admin.readonly_fields

    def test_readonly_fields_contains_error_message(self) -> None:
        assert "error_message" in self.admin.readonly_fields


# ---------------------------------------------------------------------------
# has_add_permission
# ---------------------------------------------------------------------------


class TestImportLogAdminAddPermission(TestCase):
    """has_add_permission must always return False."""

    def setUp(self) -> None:
        self.superuser = make_superuser()
        self.factory = RequestFactory()
        self.model_admin = admin.site._registry[ImportLog]

    def _make_request(self, user=None):
        request = self.factory.get("/")
        request.user = user or self.superuser
        return request

    def test_has_add_permission_returns_false_for_superuser(self) -> None:
        assert not self.model_admin.has_add_permission(self._make_request(self.superuser))

    def test_has_add_permission_returns_false_for_regular_user(self) -> None:
        regular = User.objects.create_user(username="regular", password="password")
        assert not self.model_admin.has_add_permission(self._make_request(regular))


# ---------------------------------------------------------------------------
# Functional changelist / changeform tests
# ---------------------------------------------------------------------------


class TestImportLogAdminChangelist(TestCase):
    """Functional tests for ImportLogAdmin via HTTP."""

    def setUp(self) -> None:
        self.superuser = make_superuser("log_admin")
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self) -> None:
        url = reverse("admin:import_log_importlog_changelist")
        assert self.client.get(url).status_code == 200

    def test_changelist_shows_source(self) -> None:
        make_import_log(source="visible_source.xml")
        url = reverse("admin:import_log_importlog_changelist")
        self.assertContains(self.client.get(url), "visible_source.xml")

    def test_changeform_returns_200(self) -> None:
        log = make_import_log()
        url = reverse("admin:import_log_importlog_change", args=[log.pk])
        assert self.client.get(url).status_code == 200

    def test_add_view_is_blocked(self) -> None:
        url = reverse("admin:import_log_importlog_add")
        assert self.client.get(url).status_code == 403

    def test_changelist_filter_by_status_success(self) -> None:
        make_import_log(status=ImportLog.Status.SUCCESS)
        url = reverse("admin:import_log_importlog_changelist")
        assert self.client.get(url, {"status": ImportLog.Status.SUCCESS}).status_code == 200

    def test_changelist_filter_by_status_failed(self) -> None:
        make_import_log(status=ImportLog.Status.FAILED, error_message="timeout")
        url = reverse("admin:import_log_importlog_changelist")
        assert self.client.get(url, {"status": ImportLog.Status.FAILED}).status_code == 200

    def test_changelist_search_by_source(self) -> None:
        url = reverse("admin:import_log_importlog_changelist")
        assert self.client.get(url, {"q": "import"}).status_code == 200

    def test_changelist_search_by_error_message(self) -> None:
        make_import_log(status=ImportLog.Status.FAILED, error_message="connection refused")
        url = reverse("admin:import_log_importlog_changelist")
        assert self.client.get(url, {"q": "connection refused"}).status_code == 200
