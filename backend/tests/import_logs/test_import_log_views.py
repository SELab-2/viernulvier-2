"""
Tests for apps/import_log/views.py

Covers:
- ImportLogViewSet inherits from ApiReadOnlyViewSet
- ImportLogViewSet does NOT inherit from ApiModelViewSet
- Queryset model is ImportLog
- Serializer class is ImportLogSerializer
- GET  /api/v1/import-logs/       - public key ✓, internal key ✓
- GET  /api/v1/import-logs/<id>/  - public key ✓, internal key ✓
- All GET requests rejected without auth header
- All GET requests rejected with a wrong key
- POST /api/v1/import-logs/       - 405 Method Not Allowed (both keys)
- PUT  /api/v1/import-logs/<id>/  - 405 Method Not Allowed (both keys)
- PATCH /api/v1/import-logs/<id>/ - 405 Method Not Allowed (both keys)
- DELETE /api/v1/import-logs/<id>/- 405 Method Not Allowed (both keys)
- Response structure / fields on list and detail
- duration field is present in list and detail responses
- Results are ordered by -started_at (most recent first)
- Pagination is present on list response
"""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet, ApiReadOnlyViewSet
from apps.import_log.models import ImportLog
from apps.import_log.serializers import ImportLogSerializer
from apps.import_log.views import ImportLogViewSet
from tests.factories.import_log import ImportLogFactory
from tests.helpers.api import internal_headers as int_headers
from tests.helpers.api import public_headers as pub_headers
from tests.helpers.api import wrong_headers

PUB_KEY = "pub-import-log-view-test-key"
INT_KEY = "int-import-log-view-test-key"


def make_import_log(**kwargs):
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


def make_finished_log(source="finished.json", duration_seconds=60, **kwargs):
    start = timezone.now()
    return make_import_log(
        source=source,
        started_at=start,
        finished_at=start + timedelta(seconds=duration_seconds),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Class-level tests
# ---------------------------------------------------------------------------


class TestImportLogViewSetClass(TestCase):
    """Verify ViewSet class-level configuration."""

    def test_inherits_from_api_read_only_viewset(self) -> None:
        assert issubclass(ImportLogViewSet, ApiReadOnlyViewSet)

    def test_does_not_inherit_from_api_model_viewset(self) -> None:
        """ImportLogViewSet must be read-only - not a full CRUD viewset."""
        assert not issubclass(ImportLogViewSet, ApiModelViewSet)

    def test_queryset_model_is_import_log(self) -> None:
        assert ImportLogViewSet.queryset.model == ImportLog

    def test_serializer_class_is_import_log_serializer(self) -> None:
        assert ImportLogViewSet.serializer_class == ImportLogSerializer


# ---------------------------------------------------------------------------
# GET /api/v1/import-logs/ - list
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestImportLogViewSetList(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        ImportLog.objects.all().delete()
        self.log_a = make_import_log(source="import_a.json")
        self.log_b = make_import_log(source="import_b.json")

    def test_list_with_public_key_returns_200(self) -> None:
        response = self.client.get("/api/v1/import-logs/", **pub_headers())
        assert response.status_code == 200

    def test_list_with_internal_key_returns_200(self) -> None:
        response = self.client.get("/api/v1/import-logs/", **int_headers())
        assert response.status_code == 200

    def test_list_without_auth_returns_401_or_403(self) -> None:
        response = self.client.get("/api/v1/import-logs/")
        assert response.status_code in (401, 403)

    def test_list_with_wrong_key_returns_401_or_403(self) -> None:
        response = self.client.get("/api/v1/import-logs/", **wrong_headers())
        assert response.status_code in (401, 403)

    def test_list_returns_all_logs(self) -> None:
        response = self.client.get("/api/v1/import-logs/", **pub_headers())
        assert len(response.data["results"]) == 2

    def test_list_response_has_pagination(self) -> None:
        response = self.client.get("/api/v1/import-logs/", **pub_headers())
        assert "results" in response.data
        assert "count" in response.data

    def test_list_response_contains_expected_fields(self) -> None:
        response = self.client.get("/api/v1/import-logs/", **pub_headers())
        item = response.data["results"][0]
        for field in (
            "id",
            "source",
            "status",
            "records_total",
            "records_imported",
            "records_failed",
            "started_at",
            "finished_at",
            "duration",
            "error_message",
        ):
            with self.subTest(field=field):
                assert field in item

    def test_list_duration_is_none_when_timestamps_missing(self) -> None:
        response = self.client.get("/api/v1/import-logs/", **pub_headers())
        item = next(r for r in response.data["results"] if r["source"] == "import_a.json")
        assert item["duration"] is None

    def test_list_duration_is_string_when_timestamps_set(self) -> None:
        ImportLog.objects.all().delete()
        make_finished_log(source="timed.json", duration_seconds=90)
        response = self.client.get("/api/v1/import-logs/", **pub_headers())
        assert isinstance(response.data["results"][0]["duration"], str)


# ---------------------------------------------------------------------------
# GET /api/v1/import-logs/<id>/ - detail
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestImportLogViewSetDetail(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.log = make_import_log(
            source="detail_test.json",
            status=ImportLog.Status.FAILED,
            records_total=50,
            records_imported=30,
            records_failed=20,
            error_message="Parse error on line 42.",
        )

    def test_detail_with_public_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/", **pub_headers())
        assert response.status_code == 200

    def test_detail_with_internal_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/", **int_headers())
        assert response.status_code == 200

    def test_detail_without_auth_returns_401_or_403(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/")
        assert response.status_code in (401, 403)

    def test_detail_with_wrong_key_returns_401_or_403(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/", **wrong_headers())
        assert response.status_code in (401, 403)

    def test_detail_returns_correct_source(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/", **pub_headers())
        assert response.data["source"] == "detail_test.json"

    def test_detail_returns_correct_status(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/", **pub_headers())
        assert response.data["status"] == "FAILED"

    def test_detail_returns_correct_counters(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/", **pub_headers())
        assert response.data["records_total"] == 50
        assert response.data["records_imported"] == 30
        assert response.data["records_failed"] == 20

    def test_detail_returns_error_message(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/", **pub_headers())
        assert response.data["error_message"] == "Parse error on line 42."

    def test_detail_duration_is_none_when_timestamps_missing(self) -> None:
        response = self.client.get(f"/api/v1/import-logs/{self.log.pk}/", **pub_headers())
        assert response.data["duration"] is None

    def test_detail_duration_is_correct_when_timestamps_set(self) -> None:
        start = timezone.now()
        log = make_import_log(
            source="timed_detail.json",
            status=ImportLog.Status.SUCCESS,
            started_at=start,
            finished_at=start + timedelta(seconds=3661),
        )
        response = self.client.get(f"/api/v1/import-logs/{log.pk}/", **pub_headers())
        assert response.data["duration"] == "1:01:01"

    def test_detail_unknown_id_returns_404(self) -> None:
        response = self.client.get("/api/v1/import-logs/999999/", **pub_headers())
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Write methods must return 405 Method Not Allowed
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestImportLogViewSetWriteNotAllowed(TestCase):
    """
    ImportLogViewSet is structurally read-only via ApiReadOnlyViewSet.
    Write methods must return 405 for internal keys (auth passes, method blocked)
    and 403/405 for public keys (auth may fail before method check).
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.log = make_import_log()

    def test_post_with_internal_key_returns_405(self) -> None:
        response = self.client.post(
            "/api/v1/import-logs/",
            {"source": "manual.json", "status": "PENDING"},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 405

    def test_post_with_public_key_returns_403_or_405(self) -> None:
        response = self.client.post(
            "/api/v1/import-logs/",
            {"source": "manual.json"},
            format="json",
            **pub_headers(),
        )
        assert response.status_code in (403, 405)

    def test_post_without_auth_returns_401_or_403(self) -> None:
        response = self.client.post(
            "/api/v1/import-logs/",
            {"source": "manual.json"},
            format="json",
        )
        assert response.status_code in (401, 403)

    def test_put_with_internal_key_returns_405(self) -> None:
        response = self.client.put(
            f"/api/v1/import-logs/{self.log.pk}/",
            {"source": "updated.json", "status": "SUCCESS"},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 405

    def test_put_with_public_key_returns_403_or_405(self) -> None:
        response = self.client.put(
            f"/api/v1/import-logs/{self.log.pk}/",
            {"source": "updated.json"},
            format="json",
            **pub_headers(),
        )
        assert response.status_code in (403, 405)

    def test_patch_with_internal_key_returns_405(self) -> None:
        response = self.client.patch(
            f"/api/v1/import-logs/{self.log.pk}/",
            {"status": "FAILED"},
            format="json",
            **int_headers(),
        )
        assert response.status_code == 405

    def test_patch_with_public_key_returns_403_or_405(self) -> None:
        response = self.client.patch(
            f"/api/v1/import-logs/{self.log.pk}/",
            {"status": "FAILED"},
            format="json",
            **pub_headers(),
        )
        assert response.status_code in (403, 405)

    def test_delete_with_internal_key_returns_405(self) -> None:
        response = self.client.delete(
            f"/api/v1/import-logs/{self.log.pk}/",
            **int_headers(),
        )
        assert response.status_code == 405

    def test_delete_with_public_key_returns_403_or_405(self) -> None:
        response = self.client.delete(
            f"/api/v1/import-logs/{self.log.pk}/",
            **pub_headers(),
        )
        assert response.status_code in (403, 405)

    def test_delete_without_auth_returns_401_or_403(self) -> None:
        response = self.client.delete(f"/api/v1/import-logs/{self.log.pk}/")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestImportLogViewSetOrdering(TestCase):
    """Results must be ordered from most recent to oldest (by -started_at)."""

    def setUp(self) -> None:
        self.client = APIClient()
        ImportLog.objects.all().delete()

    def test_results_ordered_most_recent_first(self) -> None:
        older = make_import_log(
            source="old.json",
            started_at=timezone.now() - timedelta(hours=2),
        )
        newer = make_import_log(
            source="new.json",
            started_at=timezone.now(),
        )
        response = self.client.get("/api/v1/import-logs/", **pub_headers())
        ids = [item["id"] for item in response.data["results"]]
        assert ids[0] == newer.pk
        assert ids[1] == older.pk

    def test_logs_without_started_at_appear_last(self) -> None:
        with_time = make_import_log(
            source="with_time.json",
            started_at=timezone.now(),
        )
        without_time = make_import_log(source="no_time.json")
        response = self.client.get("/api/v1/import-logs/", **pub_headers())
        ids = [item["id"] for item in response.data["results"]]
        assert ids[0] == with_time.pk
        assert ids[-1] == without_time.pk
