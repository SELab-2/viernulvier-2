from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.events.models import Event
from apps.import_log.models import ImportLog
from apps.imports.csv_importer.legacy_csv_sync import import_legacy_csv_file
from apps.languages.models import Language
from apps.locations.models import Hall, HallTranslation
from tests.factories.production import ProductionFactory
from tests.imports_csv.helpers import write_csv

pytestmark = pytest.mark.django_db(transaction=True)


def test_import_legacy_events_creates_events_and_normalizes_end_time(tmp_path) -> None:
    production = ProductionFactory.create(external_id="5831")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [
            ["2006-07-01 23:00:00", "2006-07-01 06:00:00", "ICC, Van Rysselberghedreef 2", production.external_id],
            ["2006-07-01 22:00:00", "0000-00-00 00:00:00", "Balzaal", production.external_id],
        ],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 2
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_total == 2
    assert log.records_imported == 2
    assert log.records_failed == 0

    overnight_event = Event.objects.get(hall__translations__name="ICC, Van Rysselberghedreef 2")
    assert overnight_event.production == production
    assert overnight_event.starts_at == datetime(2006, 7, 1, 23, 0, tzinfo=UTC)
    assert overnight_event.ends_at == datetime(2006, 7, 2, 6, 0, tzinfo=UTC)

    open_ended_event = Event.objects.get(hall__translations__name="Balzaal")
    assert open_ended_event.ends_at is None


@pytest.mark.parametrize(
    ("external_id", "endtime", "hall_name", "expected_starts_at"),
    [
        ("7001", "0000-00-10 21:00:00", "Balzaal", datetime(2013, 5, 10, 19, 0, tzinfo=UTC)),
        ("7002", "2010-05-01 18:00:00", "Domzaal", datetime(2010, 6, 1, 10, 0, tzinfo=UTC)),
        ("5840", "2010-06-01 06:00:00", "Domzaal2", datetime(2010, 6, 2, 10, 0, tzinfo=UTC)),
    ],
)
def test_import_legacy_events_clears_invalid_end_times(
    tmp_path,
    external_id: str,
    endtime: str,
    hall_name: str,
    expected_starts_at: datetime,
) -> None:
    production = ProductionFactory.create(external_id=external_id)
    csv_path = tmp_path / "Events - voorstellingen.csv"
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [[expected_starts_at.strftime("%Y-%m-%d %H:%M:%S"), endtime, hall_name, production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_failed == 0

    event = Event.objects.get(hall__translations__name=hall_name)
    assert event.starts_at == expected_starts_at
    assert event.ends_at is None


@pytest.mark.parametrize(
    ("production_ref", "error_match"),
    [
        ("", None),
        ("999999", "not found"),
    ],
)
def test_import_legacy_events_with_invalid_production_reference(
    tmp_path,
    production_ref: str,
    error_match: str | None,
) -> None:
    csv_path = tmp_path / "Events - voorstellingen.csv"
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", production_ref]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 0
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status in [ImportLog.Status.PARTIAL_SUCCESS, ImportLog.Status.FAILED]
    assert log.records_failed == 1
    if error_match:
        assert error_match in (log.error_message or "")


@pytest.mark.parametrize(
    "timestamp",
    [
        "not-a-date",
        "0000-01-01 10:00:00",
        "1970-01-01 00:00:00",
    ],
)
def test_import_legacy_events_handles_missing_or_invalid_datetimes(tmp_path, timestamp: str) -> None:
    csv_path = tmp_path / "Events - voorstellingen.csv"
    production = ProductionFactory.create(external_id="5832")
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [[timestamp, timestamp, "Balzaal", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(hall__translations__name="Balzaal")
    assert event.starts_at is None
    assert event.ends_at is None


def test_hall_for_name_with_empty_name_returns_none(tmp_path) -> None:
    production = ProductionFactory.create(external_id="5835")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(production=production)
    assert event.hall is None


def test_hall_for_name_creates_new_hall_when_not_found(tmp_path) -> None:
    production = ProductionFactory.create(external_id="5836")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    hall_name = "New Hall That Doesnt Exist"
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", hall_name, production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(production=production)
    assert event.hall is not None
    assert event.hall.translations.filter(name=hall_name).exists()


def test_hall_for_name_reuses_existing_translation(tmp_path) -> None:

    production = ProductionFactory.create(external_id="5837")
    language, _ = Language.objects.get_or_create(code="nl", defaults={"name": "Dutch", "is_active": True})
    hall = Hall.objects.create(space=None, seat_selection=False, open_seating=False)
    hall_name = "Existing Hall Name"
    HallTranslation.objects.create(hall=hall, language=language, name=hall_name)

    csv_path = tmp_path / "Events - voorstellingen.csv"
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", hall_name, production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(production=production)
    assert event.hall == hall


def test_import_legacy_event_dry_run_returns_true(tmp_path) -> None:
    production = ProductionFactory.create(external_id="5838")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", production.external_id]],
    )

    before_events = Event.objects.count()
    imported = import_legacy_csv_file(csv_path, dry_run=True)

    assert imported == 1
    assert Event.objects.count() == before_events


def test_parse_legacy_datetime_with_naive_datetime(tmp_path) -> None:
    csv_path = tmp_path / "Events - voorstellingen.csv"
    production = ProductionFactory.create(external_id="5839")
    write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(hall__translations__name="Balzaal")
    assert event.starts_at is not None
    assert event.ends_at is not None
    assert event.starts_at.tzinfo is not None
    assert event.ends_at.tzinfo is not None
