"""
Tests for apps/import_log/filters.py and apps/import_log/views.py.
"""

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.import_log.filters import ImportLogFilter
from apps.import_log.models import ImportLog
from tests.factories.import_log import ImportLogFactory

pytestmark = pytest.mark.django_db


def _dt(days_offset=0):
    return timezone.now() + timezone.timedelta(days=days_offset)


# =====================================================
# ImportLogFilter
# =====================================================


class TestImportLogFilter:
    def _qs(self, params):
        return ImportLogFilter(params, queryset=ImportLog.objects.all()).qs

    # --- status ---

    def test_filter_by_status_exact(self):
        ImportLogFactory(status=ImportLog.Status.SUCCESS)
        ImportLogFactory(status=ImportLog.Status.FAILED)

        result = self._qs({"status": "SUCCESS"})

        assert result.count() == 1
        assert result.first().status == ImportLog.Status.SUCCESS

    def test_invalid_status_returns_empty(self):
        ImportLogFactory(status=ImportLog.Status.SUCCESS)

        assert self._qs({"status": "UNKNOWN"}).count() == 0

    # --- source ---

    def test_source_icontains(self):
        ImportLogFactory(source="viernulvier-api")
        ImportLogFactory(source="local-csv")

        assert self._qs({"source": "viernulvier"}).count() == 1
        assert self._qs({"source": "csv"}).count() == 1

    def test_source_case_insensitive(self):
        ImportLogFactory(source="Viernulvier")

        assert self._qs({"source": "viernulvier"}).count() == 1

    # --- started_at range ---

    def test_started_at_after(self):
        ImportLogFactory(started_at=_dt(-5))
        ImportLogFactory(started_at=_dt(5))

        assert self._qs({"started_at_after": _dt(0).isoformat()}).count() == 1

    def test_started_at_before(self):
        ImportLogFactory(started_at=_dt(-5))
        ImportLogFactory(started_at=_dt(5))

        assert self._qs({"started_at_before": _dt(0).isoformat()}).count() == 1

    def test_started_at_range(self):
        ImportLogFactory(started_at=_dt(-10))
        ImportLogFactory(started_at=_dt(-3))
        ImportLogFactory(started_at=_dt(5))

        result = self._qs(
            {
                "started_at_after": _dt(-5).isoformat(),
                "started_at_before": _dt(0).isoformat(),
            }
        )

        assert result.count() == 1

    # --- finished_at range ---

    def test_finished_at_after(self):
        ImportLogFactory(finished_at=_dt(-1))
        ImportLogFactory(finished_at=_dt(1))

        assert self._qs({"finished_at_after": _dt(0).isoformat()}).count() == 1

    def test_finished_at_before(self):
        ImportLogFactory(finished_at=_dt(-1))
        ImportLogFactory(finished_at=_dt(1))

        assert self._qs({"finished_at_before": _dt(0).isoformat()}).count() == 1

    # --- has_error ---

    def test_has_error_true_matches_non_empty_message(self):
        ImportLogFactory(error_message="Something broke")
        ImportLogFactory(error_message="")

        assert self._qs({"has_error": "true"}).count() == 1

    def test_has_error_true_excludes_null(self):
        ImportLogFactory(error_message=None)
        ImportLogFactory(error_message="Some error")

        assert self._qs({"has_error": "true"}).count() == 1

    def test_has_error_false_catches_empty_string(self):
        ImportLogFactory(error_message="Something broke")
        ImportLogFactory(error_message="")

        assert self._qs({"has_error": "false"}).count() == 1

    def test_has_error_false_catches_null(self):
        ImportLogFactory(error_message="Something broke")
        ImportLogFactory(error_message=None)

        assert self._qs({"has_error": "false"}).count() == 1

    # --- combined ---

    def test_status_and_source_combined(self):
        ImportLogFactory(status=ImportLog.Status.FAILED, source="viernulvier")
        ImportLogFactory(status=ImportLog.Status.SUCCESS, source="viernulvier")
        ImportLogFactory(status=ImportLog.Status.FAILED, source="local")

        assert self._qs({"status": "FAILED", "source": "viernulvier"}).count() == 1

    def test_no_params_returns_all(self):
        ImportLogFactory.create_batch(4)

        assert self._qs({}).count() == 4


# =====================================================
# ImportLogViewSet - read-only
# =====================================================


class TestImportLogViewSet:
    list_url = reverse("importlog-list")

    def detail_url(self, pk):
        return reverse("importlog-detail", kwargs={"pk": pk})

    def test_anon_is_rejected(self, anon_client):
        assert anon_client.get(self.list_url).status_code in (401, 403)

    def test_public_can_list(self, public_client):
        ImportLogFactory.create_batch(3)

        response = public_client.get(self.list_url)

        assert response.status_code == 200
        assert len(response.data["results"]) == 3

    def test_internal_can_list(self, internal_client):
        ImportLogFactory.create_batch(2)

        assert internal_client.get(self.list_url).status_code == 200

    def test_public_can_retrieve(self, public_client):
        log = ImportLogFactory()

        assert public_client.get(self.detail_url(log.pk)).status_code == 200

    # write operations always return 405 (not 403) because the routes are not registered

    def test_post_returns_405_for_public(self, public_client):
        assert public_client.post(self.list_url, {}).status_code == 405

    def test_post_returns_405_for_internal(self, internal_client):
        assert internal_client.post(self.list_url, {}).status_code == 405

    def test_put_returns_405_for_internal(self, internal_client):
        assert internal_client.put(self.detail_url(ImportLogFactory().pk), {}).status_code == 405

    def test_delete_returns_405_for_internal(self, internal_client):
        assert internal_client.delete(self.detail_url(ImportLogFactory().pk)).status_code == 405

    # --- filtering ---

    def test_filter_by_status(self, public_client):
        ImportLogFactory(status=ImportLog.Status.FAILED)
        ImportLogFactory(status=ImportLog.Status.SUCCESS)

        assert len(public_client.get(self.list_url, {"status": "FAILED"}).data["results"]) == 1

    def test_filter_by_source(self, public_client):
        ImportLogFactory(source="viernulvier")
        ImportLogFactory(source="local-csv")

        assert len(public_client.get(self.list_url, {"source": "viernulvier"}).data["results"]) == 1

    def test_filter_has_error(self, public_client):
        ImportLogFactory(error_message="broken")
        ImportLogFactory(error_message="")

        assert len(public_client.get(self.list_url, {"has_error": "true"}).data["results"]) == 1

    def test_filter_started_at_after(self, public_client):
        ImportLogFactory(started_at=_dt(-5))
        ImportLogFactory(started_at=_dt(5))

        assert len(public_client.get(self.list_url, {"started_at_after": _dt(0).isoformat()}).data["results"]) == 1

    # --- ordering ---

    def test_default_ordering_most_recent_first(self, public_client):
        ImportLogFactory(started_at=_dt(-5))
        ImportLogFactory(started_at=_dt(-1))

        response = public_client.get(self.list_url)
        dates = [r["started_at"] for r in response.data["results"]]

        assert dates == sorted(dates, reverse=True)

    def test_ordering_by_source(self, public_client):
        ImportLogFactory(source="zzz")
        ImportLogFactory(source="aaa")

        response = public_client.get(self.list_url, {"ordering": "source"})
        sources = [r["source"] for r in response.data["results"]]

        assert sources == sorted(sources)

    # --- search ---

    def test_search_by_source(self, public_client):
        ImportLogFactory(source="viernulvier-api")
        ImportLogFactory(source="local-csv")

        assert len(public_client.get(self.list_url, {"search": "viernulvier"}).data["results"]) == 1

    def test_search_by_status(self, public_client):
        ImportLogFactory(status=ImportLog.Status.FAILED)
        ImportLogFactory(status=ImportLog.Status.SUCCESS)

        assert len(public_client.get(self.list_url, {"search": "FAILED"}).data["results"]) == 1
