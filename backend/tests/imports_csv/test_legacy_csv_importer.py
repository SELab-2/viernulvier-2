from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import StringIO

from django.core.management import call_command
import pytest

from apps.events.models import Event
from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from apps.import_log.models import ImportLog
from apps.imports.csv_importer import import_bundled_legacy_csv_files, import_legacy_csv_file
from apps.imports.management.commands import import_legacy_csv as import_legacy_csv_command
from apps.languages.models import Language
from apps.locations.models import Hall
from apps.productions.models import Production, ProductionGenre
from tests.factories.production import ProductionFactory

pytestmark = pytest.mark.django_db(transaction=True)


def _write_csv(path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _write_raw_csv(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_import_legacy_productions_creates_translations_and_genres(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [
            [
                "Rosas",
                "Elena's Aria",
                "\\\n    First line\n\\\nSecond line",
                "Credits, with comma",
                "Party,Feest",
                "199",
                "legacy-3175",
            ],
        ],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_total == 1
    assert log.records_imported == 1
    assert log.records_failed == 0

    production = Production.objects.get(external_id="199")
    translation = production.translations.get(language__code="nl")
    assert translation.title == "Elena's Aria"
    assert translation.artist_name == "Rosas"
    assert "First line" in translation.description
    assert "Second line" in translation.description
    assert translation.description_extra == "Credits, with comma"

    assert production.genres.count() == 2
    assert list(
        ProductionGenre.objects.filter(production=production).order_by("position").values_list("position", flat=True)
    ) == [0, 1]


def test_import_legacy_productions_reuses_duplicate_genres(tmp_path) -> None:
    language, _ = Language.objects.get_or_create(code="nl", defaults={"name": "Dutch", "is_active": True})
    genre_use_as, _ = GenreUseAs.objects.get_or_create(name="genre")
    first_genre = Genre.objects.create(type="theater", use_as=genre_use_as)
    GenreTranslation.objects.create(genre=first_genre, language=language, name="Theater")
    Genre.objects.create(type="theater", use_as=genre_use_as)

    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Rosas", "Elena's Aria", "Body", "Credits", "Theater", "200", "legacy-200"]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    assert Genre.objects.filter(type="theater", use_as=genre_use_as).count() == 2
    production = Production.objects.get(external_id="200")
    assert production.genres.count() == 1
    assert production.genres.first().id == first_genre.id


def test_import_legacy_productions_fails_with_missing_id(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [
            ["Rosas", "Valid", "Body", "Credits", "Theater", "201", "legacy-201"],
            ["Broken", "Missing ID", "Body", "Credits", "Theater", "", ""],
            ["Later", "Should Not Import", "Body", "Credits", "Theater", "202", "legacy-202"],
        ],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 2

    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.PARTIAL_SUCCESS
    assert log.records_total == 3
    assert log.records_imported == 2
    assert log.records_failed == 1
    assert "Missing production ID in legacy CSV row" in (log.error_message or "")
    assert Production.objects.filter(external_id="201").exists()
    assert Production.objects.filter(external_id="202").exists()
    assert not Production.objects.filter(external_id="").exists()


def test_import_legacy_events_creates_events_and_normalizes_end_time(tmp_path) -> None:
    production = ProductionFactory.create(external_id="5831")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
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


def test_import_legacy_events_treats_year_zero_endtime_as_missing(tmp_path) -> None:
    production = ProductionFactory.create(external_id="7001")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2013-05-10 19:00:00", "0000-00-10 21:00:00", "Balzaal", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_failed == 0

    event = Event.objects.get(hall__translations__name="Balzaal")
    assert event.starts_at == datetime(2013, 5, 10, 19, 0, tzinfo=UTC)
    assert event.ends_at is None


def test_import_legacy_events_drops_irrecoverable_end_before_start(tmp_path) -> None:
    production = ProductionFactory.create(external_id="7002")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-06-01 10:00:00", "2010-05-01 18:00:00", "Domzaal", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_failed == 0

    event = Event.objects.get(hall__translations__name="Domzaal")
    assert event.starts_at == datetime(2010, 6, 1, 10, 0, tzinfo=UTC)
    assert event.ends_at is None


def test_import_legacy_csv_file_rejects_unknown_headers(tmp_path) -> None:
    csv_path = tmp_path / "mystery.csv"
    _write_csv(csv_path, ["foo", "bar"], [["1", "2"]])

    with pytest.raises(ValueError, match="Unsupported legacy CSV headers"):
        import_legacy_csv_file(csv_path)


def test_import_legacy_csv_dry_run_has_no_side_effect_writes(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "9001", "legacy-9001"]],
    )

    before_productions = Production.objects.count()
    before_languages = Language.objects.count()
    before_halls = Hall.objects.count()

    imported = import_legacy_csv_file(csv_path, dry_run=True)

    assert imported == 1
    assert Production.objects.count() == before_productions
    assert Language.objects.count() == before_languages
    assert Hall.objects.count() == before_halls

    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.SUCCESS
    assert log.records_total == 1
    assert log.records_imported == 1
    assert log.records_failed == 0


def test_import_legacy_csv_management_command_uses_importer(monkeypatch) -> None:
    call_args = {}

    def _fake_import(*, dry_run: bool, only: str | None = None, progress_callback=None) -> int:
        call_args["dry_run"] = dry_run
        call_args["only"] = only
        call_args["has_progress_callback"] = progress_callback is not None
        return 12

    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", "--dry-run", stdout=output)

    assert call_args == {"dry_run": True, "only": None, "has_progress_callback": True}
    assert "Imported 12 legacy CSV records [DRY RUN]" in output.getvalue()


def test_import_legacy_csv_management_command_supports_only_productions(monkeypatch) -> None:
    call_args = {}

    def _fake_import(*, dry_run: bool, only: str | None = None, progress_callback=None) -> int:
        call_args["dry_run"] = dry_run
        call_args["only"] = only
        call_args["has_progress_callback"] = progress_callback is not None
        return 7

    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", "--only", "productions", stdout=output)

    assert call_args == {"dry_run": False, "only": "productions", "has_progress_callback": True}
    assert "Imported 7 legacy CSV records" in output.getvalue()


def test_import_bundled_legacy_csv_files_reports_cumulative_progress(tmp_path) -> None:
    productions_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    _write_csv(
        productions_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "400", "legacy-400"]],
    )
    _write_csv(
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


def test_import_legacy_csv_management_command_updates_tqdm(monkeypatch) -> None:
    class _FakeBar:
        def __init__(self, total):
            self.total = total
            self.n = 0
            self.updates: list[int] = []
            self.closed = False
            self.refresh_count = 0

        def update(self, value: int) -> None:
            self.n += value
            self.updates.append(value)

        def refresh(self) -> None:
            self.refresh_count += 1

        def close(self) -> None:
            self.closed = True

    created: dict[str, _FakeBar] = {}

    def _fake_tqdm(*, total, unit, desc, leave):
        assert unit == "rows"
        assert desc == "Importing legacy CSV"
        assert leave is False
        bar = _FakeBar(total)
        created["bar"] = bar
        return bar

    def _fake_import(*, dry_run: bool, only: str | None = None, progress_callback=None) -> int:
        assert dry_run is False
        assert only is None
        assert progress_callback is not None
        progress_callback(1, 3)
        progress_callback(3, 3)
        return 3

    monkeypatch.setattr(import_legacy_csv_command, "_tqdm", _fake_tqdm)
    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", stdout=output)

    bar = created["bar"]
    assert bar.updates == [1, 2]
    assert bar.closed is True
    assert "Imported 3 legacy CSV records" in output.getvalue()


def test_import_legacy_csv_management_command_works_without_tqdm(monkeypatch) -> None:
    callback_observed = {"called": False}

    def _fake_import(*, dry_run: bool, only: str | None = None, progress_callback=None) -> int:
        assert dry_run is True
        assert only is None
        assert progress_callback is not None
        callback_observed["called"] = True
        progress_callback(1, 1)
        return 1

    monkeypatch.setattr(import_legacy_csv_command, "_tqdm", None)
    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", "--dry-run", stdout=output)

    assert callback_observed["called"] is True
    assert "Imported 1 legacy CSV records [DRY RUN]" in output.getvalue()


def test_import_bundled_legacy_csv_converts_original_production_file(tmp_path) -> None:
    original_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    _write_raw_csv(
        original_path,
        "Titel,Ondertitel,Description1,Description2,Genre,ID,Planning ID\n"
        'Artist,Title,"Body line one\nBody line two",Credits,Theater,301,legacy-301\n',
    )
    _write_csv(events_path, ["Starttime", "Endtime", "Hall", "Production"], [])

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

    _write_raw_csv(
        original_path,
        "Titel,Ondertitel,Description1,Description2,Genre,ID,Planning ID\nArtist,Title,Body,Credits,Theater,302,legacy-302"
        "\n",
    )
    _write_csv(events_path, ["Starttime", "Endtime", "Hall", "Production"], [])

    imported = import_bundled_legacy_csv_files(base_dir=tmp_path, only="productions", dry_run=True)

    assert imported == 1
    assert not (tmp_path / "Productions - converted.csv").exists()
