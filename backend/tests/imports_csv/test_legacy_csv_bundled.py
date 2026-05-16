"""Tests for importing bundled legacy CSV files."""

from __future__ import annotations

import pytest

from apps.events.models import Event
from apps.import_log.models import ImportLog
from apps.imports.csv_importer.legacy_csv_sync import import_bundled_legacy_csv_files
from apps.productions.models import Production
from tests.factories.production import ProductionFactory
from tests.imports_csv.helpers import write_csv, write_raw_csv

pytestmark = pytest.mark.django_db(transaction=True)


def test_import_bundled_legacy_csv_files_reports_cumulative_progress(tmp_path) -> None:
    productions_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    write_csv(
        productions_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "400", "legacy-400"]],
    )
    write_csv(
        events_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", "400"]],
    )

    progress_updates: list[tuple[int, int | None]] = []

    imported = import_bundled_legacy_csv_files(
        base_dir=tmp_path,
        progress_callback=lambda processed, total: progress_updates.append((processed, total)),
    )

    assert imported == 2
    assert progress_updates == [(1, 2), (2, 2)]


def test_import_bundled_legacy_csv_converts_original_production_file(tmp_path) -> None:
    original_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    write_raw_csv(
        original_path,
        "Titel,Ondertitel,Description1,Description2,Genre,ID,Planning ID\n"
        'Artist,Title,"Body line one\nBody line two",Credits,Theater,301,legacy-301\n',
    )
    write_csv(events_path, ["Starttime", "Endtime", "Hall", "Production"], [])

    imported = import_bundled_legacy_csv_files(base_dir=tmp_path, only="productions")

    assert imported == 1
    assert not (tmp_path / "Productions - converted.csv").exists()

    log = ImportLog.objects.get(source="legacy_csv:Productions - output.csv")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_total == 1
    assert log.records_imported == 1
    assert log.records_failed == 0

    production = Production.objects.get(external_id="301")
    translation = production.translations.get(language__code="nl")
    assert "Body line one" in translation.description
    assert "Body line two" in translation.description


def test_import_bundled_legacy_csv_converts_original_before_detecting_kind(tmp_path) -> None:
    original_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    write_raw_csv(
        original_path,
        "Titel,Ondertitel,Description1,Description2,Genre,ID,Planning ID\nArtist,Title,Body,Credits,Theater,302,legacy-302\n",
    )
    write_csv(events_path, ["Starttime", "Endtime", "Hall", "Production"], [])

    imported = import_bundled_legacy_csv_files(base_dir=tmp_path, only="productions", dry_run=True)

    assert imported == 1
    assert not (tmp_path / "Productions - converted.csv").exists()


@pytest.mark.parametrize(
    "only",
    ["productions", "events"],
)
def test_import_bundled_only_param(tmp_path, only: str) -> None:

    production = ProductionFactory.create(external_id="701")
    productions_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    write_csv(
        productions_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "800", "legacy-800"]],
    )
    write_csv(
        events_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", production.external_id]],
    )

    imported = import_bundled_legacy_csv_files(base_dir=tmp_path, only=only)

    assert imported == 1
    if only == "productions":
        assert Production.objects.filter(external_id="800").exists()
    else:
        assert Event.objects.filter(production=production).exists()
        assert not Production.objects.filter(external_id="800").exists()


def test_import_bundled_without_progress_callback(tmp_path) -> None:
    productions_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    write_csv(
        productions_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "1120", "legacy-1120"]],
    )
    write_csv(events_path, ["Starttime", "Endtime", "Hall", "Production"], [])

    imported = import_bundled_legacy_csv_files(base_dir=tmp_path)

    assert imported == 1
