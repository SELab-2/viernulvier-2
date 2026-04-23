"""
Tests for apps/import_log/filters.py
"""

from django.test import TestCase
from django.utils import timezone

from apps.import_log.filters import ImportLogFilter
from apps.import_log.models import ImportLog
from tests.factories.import_log import ImportLogFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dt(days_offset=0):
    """Timezone-aware datetime offset from *now* by days_offset days."""
    return timezone.now() + timezone.timedelta(days=days_offset)


def _make_finished(started_days, finished_days, **kwargs):
    """
    Create a SUCCESS ImportLog with explicit started_at / finished_at.

    finished_days must be >= started_days (DB constraint).
    Uses status=SUCCESS so adjust_status_logic does NOT clear finished_at.
    """
    assert finished_days >= started_days, "finished_at must be >= started_at"
    return ImportLogFactory(
        status=ImportLog.Status.SUCCESS,
        started_at=_dt(started_days),
        finished_at=_dt(finished_days),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestImportLogFilter(TestCase):
    def setUp(self) -> None:
        ImportLog.objects.all().delete()

    def _qs(self, params):
        return ImportLogFilter(params, queryset=ImportLog.objects.all()).qs

    # -------------------------------------------------------------------------
    # status
    # -------------------------------------------------------------------------

    def test_filter_by_status_success(self) -> None:
        ImportLogFactory(status=ImportLog.Status.SUCCESS)
        ImportLogFactory(status=ImportLog.Status.FAILED)

        result = self._qs({"status": "SUCCESS"})

        assert result.count() == 1
        assert result.first().status == ImportLog.Status.SUCCESS

    def test_filter_by_status_failed(self) -> None:
        ImportLogFactory(status=ImportLog.Status.FAILED)
        ImportLogFactory(status=ImportLog.Status.SUCCESS)
        ImportLogFactory(status=ImportLog.Status.PENDING)

        result = self._qs({"status": "FAILED"})

        assert result.count() == 1
        assert result.first().status == ImportLog.Status.FAILED

    def test_filter_by_status_pending(self) -> None:
        ImportLogFactory(status=ImportLog.Status.PENDING)
        ImportLogFactory(status=ImportLog.Status.SUCCESS)

        result = self._qs({"status": "PENDING"})

        assert result.count() == 1
        assert result.first().status == ImportLog.Status.PENDING

    def test_filter_by_status_in_progress(self) -> None:
        ImportLogFactory(status=ImportLog.Status.IN_PROGRESS)
        ImportLogFactory(status=ImportLog.Status.SUCCESS)

        result = self._qs({"status": "IN_PROGRESS"})

        assert result.count() == 1
        assert result.first().status == ImportLog.Status.IN_PROGRESS

    def test_filter_by_status_partial_success(self) -> None:
        ImportLogFactory(status=ImportLog.Status.PARTIAL_SUCCESS)
        ImportLogFactory(status=ImportLog.Status.SUCCESS)

        result = self._qs({"status": "PARTIAL_SUCCESS"})

        assert result.count() == 1
        assert result.first().status == ImportLog.Status.PARTIAL_SUCCESS

    def test_invalid_status_returns_unfiltered(self) -> None:
        """ChoiceFilter silently ignores invalid choices and returns the full queryset."""
        ImportLogFactory(status=ImportLog.Status.SUCCESS)
        ImportLogFactory(status=ImportLog.Status.FAILED)

        assert self._qs({"status": "UNKNOWN"}).count() == 2

    def test_status_filter_excludes_other_statuses(self) -> None:
        ImportLogFactory(status=ImportLog.Status.SUCCESS)
        ImportLogFactory(status=ImportLog.Status.FAILED)
        ImportLogFactory(status=ImportLog.Status.PENDING)

        result = self._qs({"status": "SUCCESS"})

        statuses = list(result.values_list("status", flat=True))
        assert ImportLog.Status.FAILED not in statuses
        assert ImportLog.Status.PENDING not in statuses

    # -------------------------------------------------------------------------
    # source
    # -------------------------------------------------------------------------

    def test_source_icontains_match(self) -> None:
        ImportLogFactory(source="viernulvier-api")
        ImportLogFactory(source="local-csv")

        assert self._qs({"source": "viernulvier"}).count() == 1
        assert self._qs({"source": "csv"}).count() == 1

    def test_source_case_insensitive(self) -> None:
        ImportLogFactory(source="Viernulvier")

        assert self._qs({"source": "viernulvier"}).count() == 1
        assert self._qs({"source": "VIERNULVIER"}).count() == 1

    def test_source_partial_match_returns_multiple(self) -> None:
        ImportLogFactory(source="import_2024_01.json")
        ImportLogFactory(source="import_2024_02.json")
        ImportLogFactory(source="export_2024_01.json")

        assert self._qs({"source": "import"}).count() == 2

    def test_source_no_match_returns_empty(self) -> None:
        ImportLogFactory(source="import_a.json")

        assert self._qs({"source": "nonexistent"}).count() == 0

    def test_source_full_exact_string_matches_one(self) -> None:
        ImportLogFactory(source="exact-match.json")
        ImportLogFactory(source="other.json")

        result = self._qs({"source": "exact-match.json"})

        assert result.count() == 1
        assert result.first().source == "exact-match.json"

    # -------------------------------------------------------------------------
    # started_at range
    # -------------------------------------------------------------------------

    def test_started_at_after_returns_later_record(self) -> None:
        ImportLogFactory(started_at=_dt(-5))
        ImportLogFactory(started_at=_dt(5))

        assert self._qs({"started_at_after": _dt(0).isoformat()}).count() == 1

    def test_started_at_before_returns_earlier_record(self) -> None:
        ImportLogFactory(started_at=_dt(-5))
        ImportLogFactory(started_at=_dt(5))

        assert self._qs({"started_at_before": _dt(0).isoformat()}).count() == 1

    def test_started_at_range_returns_only_records_within_window(self) -> None:
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

    def test_started_at_after_boundary_is_inclusive(self) -> None:
        boundary = _dt(0)
        ImportLogFactory(started_at=boundary)
        ImportLogFactory(started_at=_dt(-1))

        assert self._qs({"started_at_after": boundary.isoformat()}).count() == 1

    def test_started_at_before_boundary_is_inclusive(self) -> None:
        boundary = _dt(0)
        ImportLogFactory(started_at=boundary)
        ImportLogFactory(started_at=_dt(1))

        assert self._qs({"started_at_before": boundary.isoformat()}).count() == 1

    def test_started_at_null_excluded_from_range_filter(self) -> None:
        ImportLogFactory(started_at=None)
        ImportLogFactory(started_at=_dt(-1))

        result = self._qs({"started_at_after": _dt(-5).isoformat()})

        assert result.count() == 1
        assert result.first().started_at is not None

    # -------------------------------------------------------------------------
    # finished_at range
    #
    # Rules:
    # - Use _make_finished(started_days, finished_days) - always status=SUCCESS
    #   so adjust_status_logic never clears finished_at.
    # - finished_days must be >= started_days (DB constraint).
    # -------------------------------------------------------------------------

    def test_finished_at_after_returns_later_record(self) -> None:
        _make_finished(-5, -2)  # finished 2 days ago  → outside window
        _make_finished(-3, 2)  # finishes in 2 days   → inside window

        assert self._qs({"finished_at_after": _dt(0).isoformat()}).count() == 1

    def test_finished_at_before_returns_earlier_record(self) -> None:
        _make_finished(-5, -2)  # finished 2 days ago  → inside window
        _make_finished(-3, 2)  # finishes in 2 days   → outside window

        assert self._qs({"finished_at_before": _dt(0).isoformat()}).count() == 1

    def test_finished_at_range_returns_only_records_within_window(self) -> None:
        _make_finished(-12, -10)  # too old
        _make_finished(-5, -3)  # inside window: finished 3 days ago
        _make_finished(3, 5)  # in the future

        result = self._qs(
            {
                "finished_at_after": _dt(-5).isoformat(),
                "finished_at_before": _dt(0).isoformat(),
            }
        )

        assert result.count() == 1

    def test_finished_at_null_excluded_from_range_filter(self) -> None:
        # PENDING records always have finished_at=None (set by factory hook)
        ImportLogFactory(status=ImportLog.Status.PENDING, started_at=_dt(-1))
        _make_finished(-1, 1)  # finished_at = tomorrow → inside window

        result = self._qs({"finished_at_after": _dt(0).isoformat()})

        assert result.count() == 1
        assert result.first().finished_at is not None

    # -------------------------------------------------------------------------
    # has_error
    #
    # Factory behaviour:
    # - status=FAILED  → adjust_status_logic sets a random non-empty error_message
    # - other statuses → error_message stays None (factory default)
    # - Pass error_message= explicitly to override for non-FAILED statuses.
    # -------------------------------------------------------------------------

    def test_has_error_true_matches_non_empty_message(self) -> None:
        # FAILED → factory gives a non-empty error_message automatically
        ImportLogFactory(status=ImportLog.Status.FAILED)
        # SUCCESS with explicit empty message → no error
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="")

        assert self._qs({"has_error": "true"}).count() == 1

    def test_has_error_true_excludes_null_message(self) -> None:
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message=None)
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="Some error")

        assert self._qs({"has_error": "true"}).count() == 1

    def test_has_error_true_excludes_empty_string(self) -> None:
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="")
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="Real error")

        result = self._qs({"has_error": "true"})

        assert result.count() == 1
        assert result.first().error_message == "Real error"

    def test_has_error_true_matches_multiple_non_empty_messages(self) -> None:
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="Error A")
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="Error B")
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message=None)

        assert self._qs({"has_error": "true"}).count() == 2

    def test_has_error_false_matches_empty_string(self) -> None:
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="Something broke")
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="")

        assert self._qs({"has_error": "false"}).count() == 1

    def test_has_error_false_matches_null(self) -> None:
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="Something broke")
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message=None)

        assert self._qs({"has_error": "false"}).count() == 1

    def test_has_error_false_matches_both_null_and_empty_string(self) -> None:
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message=None)
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="")
        ImportLogFactory(status=ImportLog.Status.SUCCESS, error_message="An error occurred")

        assert self._qs({"has_error": "false"}).count() == 2

    # -------------------------------------------------------------------------
    # combined filters
    # -------------------------------------------------------------------------

    def test_status_and_source_combined(self) -> None:
        ImportLogFactory(status=ImportLog.Status.FAILED, source="viernulvier")
        ImportLogFactory(status=ImportLog.Status.SUCCESS, source="viernulvier")
        ImportLogFactory(status=ImportLog.Status.FAILED, source="local")

        assert self._qs({"status": "FAILED", "source": "viernulvier"}).count() == 1

    def test_status_and_has_error_combined(self) -> None:
        # FAILED + explicit error → should match
        ImportLogFactory(status=ImportLog.Status.FAILED, source="target")
        # SUCCESS + explicit empty error → no match (no error)
        ImportLogFactory(status=ImportLog.Status.SUCCESS, source="target", error_message="")
        # SUCCESS + error → no match (wrong status)
        ImportLogFactory(status=ImportLog.Status.SUCCESS, source="target", error_message="Oops")

        result = self._qs({"status": "FAILED", "has_error": "true"})

        assert result.count() == 1
        assert result.first().status == ImportLog.Status.FAILED

    def test_source_and_started_at_after_combined(self) -> None:
        ImportLogFactory(source="viernulvier", started_at=_dt(-5))
        ImportLogFactory(source="viernulvier", started_at=_dt(1))
        ImportLogFactory(source="local", started_at=_dt(1))

        result = self._qs({"source": "viernulvier", "started_at_after": _dt(0).isoformat()})

        assert result.count() == 1
        assert result.first().source == "viernulvier"

    def test_all_filters_combined_returns_single_match(self) -> None:
        # Should match: FAILED + viernulvier + recent + has error (factory sets error for FAILED)
        ImportLogFactory(
            status=ImportLog.Status.FAILED,
            source="viernulvier",
            started_at=_dt(-1),
        )
        # Outside date window
        ImportLogFactory(
            status=ImportLog.Status.FAILED,
            source="viernulvier",
            started_at=_dt(-10),
        )
        # Wrong status, no error
        ImportLogFactory(
            status=ImportLog.Status.SUCCESS,
            source="viernulvier",
            started_at=_dt(-1),
            error_message=None,
        )

        result = self._qs(
            {
                "status": "FAILED",
                "source": "viernulvier",
                "started_at_after": _dt(-5).isoformat(),
                "has_error": "true",
            }
        )

        assert result.count() == 1

    # -------------------------------------------------------------------------
    # no params / empty table
    # -------------------------------------------------------------------------

    def test_no_params_returns_all(self) -> None:
        ImportLogFactory.create_batch(4)

        assert self._qs({}).count() == 4

    def test_filter_on_empty_table_returns_empty(self) -> None:
        assert self._qs({"status": "FAILED"}).count() == 0
