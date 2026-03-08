"""
Tests for apps/import_log/serializers.py

Covers:
- ImportLogSerializer field presence and completeness
- No extra fields are exposed
- All fields are read-only
- Correct serialization of each Status choice
- Correct serialization of integer counter fields
- Null fields (started_at, finished_at, error_message) serialize as None
- Populated timestamps serialize correctly
- error_message serializes correctly when set
- Partial success state (some records failed) serializes correctly
- duration field returns None when started_at or finished_at is missing
- duration field returns HH:MM:SS string when both timestamps are set
- duration strips microseconds from the result
- duration is correct for sub-minute, minute-range and hour-range deltas
- create() raises ValidationError
- update() raises ValidationError
"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.import_log.models import ImportLog
from apps.import_log.serializers import ImportLogSerializer
from tests.factories.import_log import ImportLogFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_import_log(**kwargs):
    defaults = {
        "source": "test_import.json",
        "status": ImportLog.Status.PENDING,
        "records_total": 0,
        "records_imported": 0,
        "records_failed": 0,
        "started_at": None,
        "finished_at": None,
        "error_message": None,
    }
    defaults.update(kwargs)
    log = ImportLogFactory.build(**defaults)
    log.save()
    return log


def make_finished_log(duration_seconds=0, **kwargs):
    """
    Helper that creates a log with both timestamps set,
    separated by the given number of seconds.
    """
    start = timezone.now()
    finish = start + timedelta(seconds=duration_seconds)
    return make_import_log(
        status=ImportLog.Status.SUCCESS,
        started_at=start,
        finished_at=finish,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Field presence
# ---------------------------------------------------------------------------


class TestImportLogSerializerFields(TestCase):
    """Verify all expected fields are present and no extras are exposed."""

    def setUp(self):
        self.log = make_import_log()
        self.data = ImportLogSerializer(self.log).data

    def test_expected_fields_are_present(self):
        expected = {
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
        }
        for field in expected:
            with self.subTest(field=field):
                self.assertIn(field, self.data)

    def test_no_extra_fields_are_exposed(self):
        expected = {
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
        }
        self.assertEqual(set(self.data.keys()), expected)


# ---------------------------------------------------------------------------
# Read-only fields
# ---------------------------------------------------------------------------


class TestImportLogSerializerReadOnly(TestCase):
    """All declared fields must be read-only — the serializer is for monitoring only."""

    def setUp(self):
        self.meta_read_only = set(
            getattr(ImportLogSerializer.Meta, "read_only_fields", [])
        )

    def test_source_is_read_only(self):
        self.assertIn("source", self.meta_read_only)

    def test_status_is_read_only(self):
        self.assertIn("status", self.meta_read_only)

    def test_records_total_is_read_only(self):
        self.assertIn("records_total", self.meta_read_only)

    def test_records_imported_is_read_only(self):
        self.assertIn("records_imported", self.meta_read_only)

    def test_records_failed_is_read_only(self):
        self.assertIn("records_failed", self.meta_read_only)

    def test_started_at_is_read_only(self):
        self.assertIn("started_at", self.meta_read_only)

    def test_finished_at_is_read_only(self):
        self.assertIn("finished_at", self.meta_read_only)

    def test_error_message_is_read_only(self):
        self.assertIn("error_message", self.meta_read_only)

    def test_duration_is_read_only(self):
        self.assertIn("duration", self.meta_read_only)


# ---------------------------------------------------------------------------
# Scalar field values
# ---------------------------------------------------------------------------


class TestImportLogSerializerScalarFields(TestCase):
    """Verify scalar fields are serialized with the correct values."""

    def test_source_value_is_correct(self):
        log = make_import_log(source="events_2024.csv")
        self.assertEqual(ImportLogSerializer(log).data["source"], "events_2024.csv")

    def test_records_total_value_is_correct(self):
        log = make_import_log(records_total=500)
        self.assertEqual(ImportLogSerializer(log).data["records_total"], 500)

    def test_records_imported_value_is_correct(self):
        log = make_import_log(records_imported=480)
        self.assertEqual(ImportLogSerializer(log).data["records_imported"], 480)

    def test_records_failed_value_is_correct(self):
        log = make_import_log(records_failed=20)
        self.assertEqual(ImportLogSerializer(log).data["records_failed"], 20)


# ---------------------------------------------------------------------------
# Status choices
# ---------------------------------------------------------------------------


class TestImportLogSerializerStatusChoices(TestCase):
    """Each Status choice must serialize to its string value."""

    def _serialize_status(self, status):
        return ImportLogSerializer(make_import_log(status=status)).data["status"]

    def test_status_pending(self):
        self.assertEqual(self._serialize_status(ImportLog.Status.PENDING), "PENDING")

    def test_status_in_progress(self):
        self.assertEqual(
            self._serialize_status(ImportLog.Status.IN_PROGRESS), "IN_PROGRESS"
        )

    def test_status_partial_success(self):
        self.assertEqual(
            self._serialize_status(ImportLog.Status.PARTIAL_SUCCESS), "PARTIAL_SUCCESS"
        )

    def test_status_success(self):
        self.assertEqual(self._serialize_status(ImportLog.Status.SUCCESS), "SUCCESS")

    def test_status_failed(self):
        self.assertEqual(self._serialize_status(ImportLog.Status.FAILED), "FAILED")


# ---------------------------------------------------------------------------
# Nullable fields
# ---------------------------------------------------------------------------


class TestImportLogSerializerNullableFields(TestCase):
    """Nullable fields must serialize as None when not set."""

    def setUp(self):
        self.data = ImportLogSerializer(make_import_log()).data

    def test_started_at_is_none_when_not_set(self):
        self.assertIsNone(self.data["started_at"])

    def test_finished_at_is_none_when_not_set(self):
        self.assertIsNone(self.data["finished_at"])

    def test_error_message_is_none_when_not_set(self):
        self.assertIsNone(self.data["error_message"])


class TestImportLogSerializerPopulatedNullableFields(TestCase):
    """Nullable fields must serialize their value when populated."""

    def test_started_at_serializes_when_set(self):
        log = make_import_log(started_at=timezone.now())
        self.assertIsNotNone(ImportLogSerializer(log).data["started_at"])

    def test_finished_at_serializes_when_set(self):
        start = timezone.now()
        log = make_import_log(
            started_at=start,
            finished_at=start + timedelta(minutes=1),
            status=ImportLog.Status.SUCCESS,
        )
        self.assertIsNotNone(ImportLogSerializer(log).data["finished_at"])

    def test_error_message_serializes_when_set(self):
        log = make_import_log(
            status=ImportLog.Status.FAILED,
            error_message="Connection timed out after 30s.",
        )
        self.assertEqual(
            ImportLogSerializer(log).data["error_message"],
            "Connection timed out after 30s.",
        )


# ---------------------------------------------------------------------------
# duration field
# ---------------------------------------------------------------------------


class TestImportLogSerializerDurationNone(TestCase):
    """duration must be None whenever one or both timestamps are missing."""

    def test_duration_is_none_when_both_timestamps_missing(self):
        log = make_import_log()
        self.assertIsNone(ImportLogSerializer(log).data["duration"])

    def test_duration_is_none_when_only_started_at_is_set(self):
        log = make_import_log(started_at=timezone.now())
        self.assertIsNone(ImportLogSerializer(log).data["duration"])

    def test_duration_is_none_when_only_finished_at_is_set(self):
        # finished_at without started_at — edge case
        log = make_import_log(finished_at=timezone.now())
        self.assertIsNone(ImportLogSerializer(log).data["duration"])


class TestImportLogSerializerDurationFormat(TestCase):
    """duration must be a HH:MM:SS string with no microseconds."""

    def test_duration_returns_string(self):
        log = make_finished_log(duration_seconds=90)
        self.assertIsInstance(ImportLogSerializer(log).data["duration"], str)

    def test_duration_has_no_microseconds(self):
        log = make_finished_log(duration_seconds=90)
        duration = ImportLogSerializer(log).data["duration"]
        self.assertNotIn(".", duration)

    def test_duration_matches_hhmmss_pattern(self):
        log = make_finished_log(duration_seconds=3661)
        duration = ImportLogSerializer(log).data["duration"]
        self.assertRegex(duration, r"^\d+:\d{2}:\d{2}$")


class TestImportLogSerializerDurationValues(TestCase):
    """duration must reflect the actual elapsed time between the two timestamps."""

    def test_duration_for_45_seconds(self):
        log = make_finished_log(duration_seconds=45)
        self.assertEqual(ImportLogSerializer(log).data["duration"], "0:00:45")

    def test_duration_for_90_seconds(self):
        log = make_finished_log(duration_seconds=90)
        self.assertEqual(ImportLogSerializer(log).data["duration"], "0:01:30")

    def test_duration_for_1_hour(self):
        log = make_finished_log(duration_seconds=3600)
        self.assertEqual(ImportLogSerializer(log).data["duration"], "1:00:00")

    def test_duration_for_1_hour_1_minute_1_second(self):
        log = make_finished_log(duration_seconds=3661)
        self.assertEqual(ImportLogSerializer(log).data["duration"], "1:01:01")

    def test_duration_for_zero_seconds(self):
        log = make_finished_log(duration_seconds=0)
        self.assertEqual(ImportLogSerializer(log).data["duration"], "0:00:00")

    def test_duration_strips_microseconds(self):
        """Ensure fractional seconds from real datetime objects are stripped."""
        start = timezone.now()
        # Add a sub-second offset to guarantee microseconds are present
        finish = start + timedelta(seconds=5, microseconds=123456)
        log = make_import_log(
            status=ImportLog.Status.SUCCESS,
            started_at=start,
            finished_at=finish,
        )
        duration = ImportLogSerializer(log).data["duration"]
        self.assertNotIn(".", duration)
        self.assertEqual(duration, "0:00:05")


# ---------------------------------------------------------------------------
# create() and update() overrides
# ---------------------------------------------------------------------------


class TestImportLogSerializerWriteProtection(TestCase):
    """create() and update() must raise ValidationError to protect log integrity."""

    def setUp(self):
        self.log = make_import_log()
        self.serializer = ImportLogSerializer(self.log)

    def test_create_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.serializer.create({})

    def test_create_error_message_mentions_api(self):
        try:
            self.serializer.create({})
        except ValidationError as exc:
            self.assertIn("API", str(exc.detail))

    def test_update_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.serializer.update(self.log, {})

    def test_update_error_message_mentions_api(self):
        try:
            self.serializer.update(self.log, {})
        except ValidationError as exc:
            self.assertIn("API", str(exc.detail))


# ---------------------------------------------------------------------------
# Realistic states
# ---------------------------------------------------------------------------


class TestImportLogSerializerRealisticStates(TestCase):
    """Verify the serializer handles common real-world import states correctly."""

    def test_successful_import_serializes_correctly(self):
        start = timezone.now()
        log = make_import_log(
            source="productions_2024.json",
            status=ImportLog.Status.SUCCESS,
            records_total=100,
            records_imported=100,
            records_failed=0,
            started_at=start,
            finished_at=start + timedelta(minutes=2),
        )
        data = ImportLogSerializer(log).data
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["records_total"], 100)
        self.assertEqual(data["records_imported"], 100)
        self.assertEqual(data["records_failed"], 0)
        self.assertIsNone(data["error_message"])
        self.assertEqual(data["duration"], "0:02:00")

    def test_partial_success_serializes_correctly(self):
        log = make_import_log(
            status=ImportLog.Status.PARTIAL_SUCCESS,
            records_total=100,
            records_imported=80,
            records_failed=20,
        )
        data = ImportLogSerializer(log).data
        self.assertEqual(data["status"], "PARTIAL_SUCCESS")
        self.assertEqual(data["records_imported"], 80)
        self.assertEqual(data["records_failed"], 20)
        self.assertIsNone(data["duration"])

    def test_failed_import_with_error_message_serializes_correctly(self):
        log = make_import_log(
            status=ImportLog.Status.FAILED,
            records_total=50,
            records_imported=0,
            records_failed=50,
            error_message="Unexpected EOF while parsing JSON.",
        )
        data = ImportLogSerializer(log).data
        self.assertEqual(data["status"], "FAILED")
        self.assertEqual(data["error_message"], "Unexpected EOF while parsing JSON.")
        self.assertIsNone(data["duration"])

    def test_pending_import_has_zero_counters_and_no_duration(self):
        log = make_import_log(status=ImportLog.Status.PENDING)
        data = ImportLogSerializer(log).data
        self.assertEqual(data["records_total"], 0)
        self.assertEqual(data["records_imported"], 0)
        self.assertEqual(data["records_failed"], 0)
        self.assertIsNone(data["duration"])

    def test_in_progress_import_has_no_duration_yet(self):
        log = make_import_log(
            status=ImportLog.Status.IN_PROGRESS,
            started_at=timezone.now(),
        )
        data = ImportLogSerializer(log).data
        self.assertIsNone(data["duration"])
