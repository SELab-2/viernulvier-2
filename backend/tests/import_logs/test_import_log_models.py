from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.import_log.models import ImportLog
from tests.factories.import_log import ImportLogFactory

pytestmark = pytest.mark.django_db

# =====================================================
# ImportLog
# =====================================================

class TestImportLog:
    def test_requires_source(self):
        log = ImportLogFactory.build(source="")
        with pytest.raises(ValidationError):
            log.full_clean()

    def test_str_representation(self):
        log = ImportLogFactory(source="file.csv", status=ImportLog.Status.SUCCESS)
        assert str(log) == "file.csv - SUCCESS"

    def test_status_is_valid_choice(self):
        log = ImportLogFactory(status=ImportLog.Status.FAILED)
        assert log.status in ImportLog.Status.values

    def test_records_consistency_from_factory(self):
        log = ImportLogFactory()
        assert log.records_imported + log.records_failed <= log.records_total

    def test_finished_after_started_constraint_valid(self):
        started = timezone.now()
        finished = started + timedelta(minutes=10)

        log = ImportLogFactory(
            started_at=started,
            finished_at=finished,
            status=ImportLog.Status.SUCCESS
        )

        assert log.finished_at > log.started_at

    def test_finished_before_started_raises_validation_error(self):
        started = timezone.now()
        finished = started - timedelta(minutes=10)

        with pytest.raises(ValidationError):
            with transaction.atomic():
                ImportLogFactory(
                    started_at=started,
                    finished_at=finished
                )

    def test_null_timestamps_allowed(self):
        log = ImportLogFactory(
            started_at=None,
            finished_at=None
        )

        assert log.started_at is None
        assert log.finished_at is None

    def test_pending_or_in_progress_has_no_finished_at(self):
        log = ImportLogFactory(status=ImportLog.Status.PENDING)
        assert log.finished_at is None

        log = ImportLogFactory(status=ImportLog.Status.IN_PROGRESS)
        assert log.finished_at is None

    def test_failed_status_sets_error_message(self):
        log = ImportLogFactory(status=ImportLog.Status.FAILED)
        assert log.error_message is not None

    def test_success_status_can_have_finished_at(self):
        log = ImportLogFactory(status=ImportLog.Status.SUCCESS)
        assert log.finished_at is not None