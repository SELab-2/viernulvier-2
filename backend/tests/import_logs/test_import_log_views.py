"""
Tests for apps/import_log/views.py

Covers:
- ImportLogViewSet inherits from ApiReadOnlyViewSet
- ImportLogViewSet does NOT inherit from ApiModelViewSet
- Queryset model is ImportLog
- Serializer class is ImportLogSerializer
- GET  /api/import-logs/       — public key ✓, internal key ✓
- GET  /api/import-logs/<id>/  — public key ✓, internal key ✓
- All GET requests rejected without auth header
- All GET requests rejected with a wrong key
- POST /api/import-logs/       — 405 Method Not Allowed (both keys)
- PUT  /api/import-logs/<id>/  — 405 Method Not Allowed (both keys)
- PATCH /api/import-logs/<id>/ — 405 Method Not Allowed (both keys)
- DELETE /api/import-logs/<id>/— 405 Method Not Allowed (both keys)
- Response structure / fields on list and detail
- duration field is present in list and detail responses
- Results are ordered by -started_at (most recent first)
- Pagination is present on list response
"""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.views import ApiReadOnlyViewSet, ApiModelViewSet
from apps.import_log.models import ImportLog
from apps.import_log.serializers import ImportLogSerializer
from apps.import_log.views import ImportLogViewSet


PUB_KEY = "pub-import-log-view-test-key"
INT_KEY = "int-import-log-view-test-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pub_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {PUB_KEY}"}


def int_headers():
    return {"HTTP_AUTHORIZATION": f"Api-Key {INT_KEY}"}


def wrong_headers():
    return {"HTTP_AUTHORIZATION": "Api-Key completely-wrong-key"}


def make_import_log(**kwargs):
    defaults = {
        "source": "test_import.json",
        "status": ImportLog.Status.SUCCESS,
        "records_total": 10,
        "records_imported": 10,
        "records_failed": 0,
    }
    defaults.update(kwargs)
    return ImportLog.objects.create(**defaults)


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

    def test_inherits_from_api_read_only_viewset(self):
        self.assertTrue(issubclass(ImportLogViewSet, ApiReadOnlyViewSet))

    def test_does_not_inherit_from_api_model_viewset(self):
        """ImportLogViewSet must be read-only — not a full CRUD viewset."""
        self.assertFalse(issubclass(ImportLogViewSet, ApiModelViewSet))

    def test_queryset_model_is_import_log(self):
        self.assertEqual(ImportLogViewSet.queryset.model, ImportLog)

    def test_serializer_class_is_import_log_serializer(self):
        self.assertEqual(ImportLogViewSet.serializer_class, ImportLogSerializer)


# ---------------------------------------------------------------------------
# GET /api/import-logs/ — list
# ---------------------------------------------------------------------------

@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestImportLogViewSetList(TestCase):

    def setUp(self):
        self.client = APIClient()
        ImportLog.objects.all().delete()
        self.log_a = make_import_log(source="import_a.json")
        self.log_b = make_import_log(source="import_b.json")

    def test_list_with_public_key_returns_200(self):
        response = self.client.get("/api/import-logs/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_with_internal_key_returns_200(self):
        response = self.client.get("/api/import-logs/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_list_without_auth_returns_401_or_403(self):
        response = self.client.get("/api/import-logs/")
        self.assertIn(response.status_code, (401, 403))

    def test_list_with_wrong_key_returns_401_or_403(self):
        response = self.client.get("/api/import-logs/", **wrong_headers())
        self.assertIn(response.status_code, (401, 403))

    def test_list_returns_all_logs(self):
        response = self.client.get("/api/import-logs/", **pub_headers())
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_response_has_pagination(self):
        response = self.client.get("/api/import-logs/", **pub_headers())
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)

    def test_list_response_contains_expected_fields(self):
        response = self.client.get("/api/import-logs/", **pub_headers())
        item = response.data["results"][0]
        for field in (
            "id", "source", "status", "records_total",
            "records_imported", "records_failed",
            "started_at", "finished_at", "duration", "error_message",
        ):
            with self.subTest(field=field):
                self.assertIn(field, item)

    def test_list_duration_is_none_when_timestamps_missing(self):
        response = self.client.get("/api/import-logs/", **pub_headers())
        item = next(
            r for r in response.data["results"] if r["source"] == "import_a.json"
        )
        self.assertIsNone(item["duration"])

    def test_list_duration_is_string_when_timestamps_set(self):
        ImportLog.objects.all().delete()
        make_finished_log(source="timed.json", duration_seconds=90)
        response = self.client.get("/api/import-logs/", **pub_headers())
        self.assertIsInstance(response.data["results"][0]["duration"], str)


# ---------------------------------------------------------------------------
# GET /api/import-logs/<id>/ — detail
# ---------------------------------------------------------------------------

@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestImportLogViewSetDetail(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.log = make_import_log(
            source="detail_test.json",
            status=ImportLog.Status.FAILED,
            records_total=50,
            records_imported=30,
            records_failed=20,
            error_message="Parse error on line 42.",
        )

    def test_detail_with_public_key_returns_200(self):
        response = self.client.get(f"/api/import-logs/{self.log.pk}/", **pub_headers())
        self.assertEqual(response.status_code, 200)

    def test_detail_with_internal_key_returns_200(self):
        response = self.client.get(f"/api/import-logs/{self.log.pk}/", **int_headers())
        self.assertEqual(response.status_code, 200)

    def test_detail_without_auth_returns_401_or_403(self):
        response = self.client.get(f"/api/import-logs/{self.log.pk}/")
        self.assertIn(response.status_code, (401, 403))

    def test_detail_with_wrong_key_returns_401_or_403(self):
        response = self.client.get(
            f"/api/import-logs/{self.log.pk}/", **wrong_headers()
        )
        self.assertIn(response.status_code, (401, 403))

    def test_detail_returns_correct_source(self):
        response = self.client.get(f"/api/import-logs/{self.log.pk}/", **pub_headers())
        self.assertEqual(response.data["source"], "detail_test.json")

    def test_detail_returns_correct_status(self):
        response = self.client.get(f"/api/import-logs/{self.log.pk}/", **pub_headers())
        self.assertEqual(response.data["status"], "FAILED")

    def test_detail_returns_correct_counters(self):
        response = self.client.get(f"/api/import-logs/{self.log.pk}/", **pub_headers())
        self.assertEqual(response.data["records_total"], 50)
        self.assertEqual(response.data["records_imported"], 30)
        self.assertEqual(response.data["records_failed"], 20)

    def test_detail_returns_error_message(self):
        response = self.client.get(f"/api/import-logs/{self.log.pk}/", **pub_headers())
        self.assertEqual(response.data["error_message"], "Parse error on line 42.")

    def test_detail_duration_is_none_when_timestamps_missing(self):
        response = self.client.get(f"/api/import-logs/{self.log.pk}/", **pub_headers())
        self.assertIsNone(response.data["duration"])

    def test_detail_duration_is_correct_when_timestamps_set(self):
        start = timezone.now()
        log = make_import_log(
            source="timed_detail.json",
            status=ImportLog.Status.SUCCESS,
            started_at=start,
            finished_at=start + timedelta(seconds=3661),
        )
        response = self.client.get(f"/api/import-logs/{log.pk}/", **pub_headers())
        self.assertEqual(response.data["duration"], "1:01:01")

    def test_detail_unknown_id_returns_404(self):
        response = self.client.get("/api/import-logs/999999/", **pub_headers())
        self.assertEqual(response.status_code, 404)


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

    def setUp(self):
        self.client = APIClient()
        self.log = make_import_log()

    def test_post_with_internal_key_returns_405(self):
        response = self.client.post(
            "/api/import-logs/",
            {"source": "manual.json", "status": "PENDING"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 405)

    def test_post_with_public_key_returns_403_or_405(self):
        response = self.client.post(
            "/api/import-logs/",
            {"source": "manual.json"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (403, 405))

    def test_post_without_auth_returns_401_or_403(self):
        response = self.client.post(
            "/api/import-logs/",
            {"source": "manual.json"},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_put_with_internal_key_returns_405(self):
        response = self.client.put(
            f"/api/import-logs/{self.log.pk}/",
            {"source": "updated.json", "status": "SUCCESS"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 405)

    def test_put_with_public_key_returns_403_or_405(self):
        response = self.client.put(
            f"/api/import-logs/{self.log.pk}/",
            {"source": "updated.json"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (403, 405))

    def test_patch_with_internal_key_returns_405(self):
        response = self.client.patch(
            f"/api/import-logs/{self.log.pk}/",
            {"status": "FAILED"},
            format="json",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 405)

    def test_patch_with_public_key_returns_403_or_405(self):
        response = self.client.patch(
            f"/api/import-logs/{self.log.pk}/",
            {"status": "FAILED"},
            format="json",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (403, 405))

    def test_delete_with_internal_key_returns_405(self):
        response = self.client.delete(
            f"/api/import-logs/{self.log.pk}/",
            **int_headers(),
        )
        self.assertEqual(response.status_code, 405)

    def test_delete_with_public_key_returns_403_or_405(self):
        response = self.client.delete(
            f"/api/import-logs/{self.log.pk}/",
            **pub_headers(),
        )
        self.assertIn(response.status_code, (403, 405))

    def test_delete_without_auth_returns_401_or_403(self):
        response = self.client.delete(f"/api/import-logs/{self.log.pk}/")
        self.assertIn(response.status_code, (401, 403))


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestImportLogViewSetOrdering(TestCase):
    """Results must be ordered from most recent to oldest (by -started_at)."""

    def setUp(self):
        self.client = APIClient()
        ImportLog.objects.all().delete()

    def test_results_ordered_most_recent_first(self):
        older = make_import_log(
            source="old.json",
            started_at=timezone.now() - timedelta(hours=2),
        )
        newer = make_import_log(
            source="new.json",
            started_at=timezone.now(),
        )
        response = self.client.get("/api/import-logs/", **pub_headers())
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids[0], newer.pk)
        self.assertEqual(ids[1], older.pk)

    def test_logs_without_started_at_appear_last(self):
        with_time = make_import_log(
            source="with_time.json",
            started_at=timezone.now(),
        )
        without_time = make_import_log(source="no_time.json")
        response = self.client.get("/api/import-logs/", **pub_headers())
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids[0], with_time.pk)
        self.assertEqual(ids[-1], without_time.pk)