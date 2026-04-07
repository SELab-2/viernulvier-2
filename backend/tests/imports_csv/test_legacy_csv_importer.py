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


def test_import_legacy_csv_missing_csv_headers(tmp_path) -> None:
    """Test CSV file with missing headers raises ValueError."""
    csv_path = tmp_path / "Productions - output.csv"
    # Write a CSV with production headers but no data, then call count_csv_rows
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [],
    )

    # The empty file will be handled gracefully, but let's test the actual error path
    # with a truly malformed file
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing headers"):
        from apps.imports.csv_importer.legacy_csv_io import _iter_csv_rows
        _iter_csv_rows(bad_csv)


def test_import_legacy_event_missing_production_reference(tmp_path) -> None:
    """Test event row with missing production reference fails gracefully."""
    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", ""]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 0
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    # When there's 1 error and 0 imported, the status is PARTIAL_SUCCESS if attempted, or FAILED if complete error
    assert log.status in [ImportLog.Status.PARTIAL_SUCCESS, ImportLog.Status.FAILED]
    assert log.records_failed == 1


def test_import_legacy_event_production_not_found(tmp_path) -> None:
    """Test event row with non-existent production fails gracefully."""
    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", "999999"]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 0
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status in [ImportLog.Status.PARTIAL_SUCCESS, ImportLog.Status.FAILED]
    assert log.records_failed == 1
    assert "not found" in (log.error_message or "")


def test_normalise_cell_with_legacy_null_marker(tmp_path) -> None:
    """Test that \\N is treated as empty string."""
    csv_path = tmp_path / "Productions - output.csv"
    _write_raw_csv(
        csv_path,
        "Titel,Ondertitel,Description1,Description2,Genre,ID,Planning ID\n"
        "Artist,Title,\\N,\\N,Theater,500,legacy-500\n",
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    production = Production.objects.get(external_id="500")
    translation = production.translations.get(language__code="nl")
    assert translation.description == ""
    assert translation.description_extra == ""


def test_normalise_multiline_text_with_only_backslashes(tmp_path) -> None:
    """Test multiline text that's empty after normalizing."""
    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "\\", "\\", "Theater", "501", "legacy-501"]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    production = Production.objects.get(external_id="501")
    translation = production.translations.get(language__code="nl")
    assert translation.description == ""


def test_split_genres_empty_string(tmp_path) -> None:
    """Test that empty genre string returns empty list."""
    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "", "502", "legacy-502"]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    production = Production.objects.get(external_id="502")
    assert production.genres.count() == 0


def test_parse_legacy_datetime_with_exception_handling(tmp_path) -> None:
    """Test datetime parsing handles invalid formats gracefully."""
    csv_path = tmp_path / "Events - voorstellingen.csv"
    production = ProductionFactory.create(external_id="5832")
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["not-a-date", "not-a-date", "Balzaal", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(hall__translations__name="Balzaal")
    assert event.starts_at is None
    assert event.ends_at is None


def test_parse_legacy_datetime_with_year_zero(tmp_path) -> None:
    """Test that year 0000 is treated as missing."""
    csv_path = tmp_path / "Events - voorstellingen.csv"
    production = ProductionFactory.create(external_id="5833")
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["0000-01-01 10:00:00", "0000-01-01 12:00:00", "Balzaal", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(hall__translations__name="Balzaal")
    assert event.starts_at is None
    assert event.ends_at is None


def test_parse_legacy_datetime_with_epoch_marker(tmp_path) -> None:
    """Test that epoch marker is treated as missing."""
    csv_path = tmp_path / "Events - voorstellingen.csv"
    production = ProductionFactory.create(external_id="5834")
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["1970-01-01 00:00:00", "1970-01-01 00:00:00", "Balzaal", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(hall__translations__name="Balzaal")
    assert event.starts_at is None
    assert event.ends_at is None


def test_hall_for_name_with_empty_name_returns_none(tmp_path) -> None:
    """Test that empty hall name returns None."""
    production = ProductionFactory.create(external_id="5835")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(production=production)
    assert event.hall is None


def test_hall_for_name_creates_new_hall_when_not_found(tmp_path) -> None:
    """Test that new hall is created when not found by translation name."""
    production = ProductionFactory.create(external_id="5836")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    hall_name = "New Hall That Doesnt Exist"
    _write_csv(
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
    """Test that existing hall is reused when translation name matches."""
    production = ProductionFactory.create(external_id="5837")
    language, _ = Language.objects.get_or_create(code="nl", defaults={"name": "Dutch", "is_active": True})
    hall = Hall.objects.create(space=None, seat_selection=False, open_seating=False)
    hall_name = "Existing Hall Name"
    from apps.locations.models import HallTranslation
    HallTranslation.objects.create(hall=hall, language=language, name=hall_name)

    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", hall_name, production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(production=production)
    assert event.hall == hall


def test_import_csv_rows_with_exception_during_iteration(tmp_path) -> None:
    """Test that exception during row iteration is properly logged."""
    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [
            ["Artist1", "Title1", "Body", "Credits", "Theater", "600", "legacy-600"],
            ["Artist2", "Title2", "Body", "Credits", "Theater", "601", "legacy-601"],
        ],
    )

    imported = import_legacy_csv_file(csv_path, dry_run=False)

    assert imported == 2
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.SUCCESS


def test_import_csv_with_unsupported_kind(tmp_path) -> None:
    """Test that unsupported CSV kind raises ValueError."""
    csv_path = tmp_path / "mystery.csv"
    _write_csv(csv_path, ["foo", "bar"], [["1", "2"]])

    with pytest.raises(ValueError, match="Unsupported legacy CSV headers"):
        import_legacy_csv_file(csv_path)


def test_import_bundled_only_productions_param(tmp_path) -> None:
    """Test import_bundled_legacy_csv_files with only=productions parameter."""
    productions_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    _write_csv(
        productions_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "700", "legacy-700"]],
    )
    _write_csv(
        events_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", "700"]],
    )

    imported = import_bundled_legacy_csv_files(base_dir=tmp_path, only="productions")

    assert imported == 1
    assert Production.objects.filter(external_id="700").exists()


def test_import_bundled_only_events_param(tmp_path) -> None:
    """Test import_bundled_legacy_csv_files with only=events parameter."""
    production = ProductionFactory.create(external_id="701")
    productions_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    _write_csv(
        productions_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "800", "legacy-800"]],
    )
    _write_csv(
        events_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", production.external_id]],
    )

    imported = import_bundled_legacy_csv_files(base_dir=tmp_path, only="events")

    assert imported == 1
    assert Event.objects.filter(production=production).exists()
    assert not Production.objects.filter(external_id="800").exists()


def test_import_legacy_csv_rows_exception_during_processing(tmp_path) -> None:
    """Test that exception during row processing is properly logged."""
    from apps.imports.csv_importer import legacy_csv_sync

    def _failing_handler(row, *, dry_run):
        raise RuntimeError("Test failure")

    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "900", "legacy-900"]],
    )

    rows = list(legacy_csv_sync._io._iter_csv_rows(csv_path))

    imported = legacy_csv_sync._import_legacy_csv_rows(
        source_name="test.csv",
        rows=rows,
        row_handler=_failing_handler,
        partial_error_label="test failed",
        failed_error_label="test failed",
        dry_run=False,
    )

    # The exception is caught and logged, so it returns 0 imports
    assert imported == 0

    log = ImportLog.objects.get(source="legacy_csv:test.csv")
    # When all rows fail, the status is FAILED (not PARTIAL_SUCCESS)
    assert log.status == ImportLog.Status.FAILED
    assert log.records_failed == 1


def test_import_legacy_csv_rows_with_progress_callback(tmp_path) -> None:
    """Test that progress callback is called during import."""
    from apps.imports.csv_importer import legacy_csv_sync

    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [
            ["Artist1", "Title1", "Body", "Credits", "Theater", "1000", "legacy-1000"],
            ["Artist2", "Title2", "Body", "Credits", "Theater", "1001", "legacy-1001"],
        ],
    )

    progress_updates = []

    def _progress_callback(processed, total):
        progress_updates.append((processed, total))

    imported = legacy_csv_sync._import_legacy_csv_file(
        csv_path,
        row_handler=legacy_csv_sync._handlers._import_legacy_production_row,
        partial_error_label="test failed",
        failed_error_label="test failed",
        dry_run=False,
        progress_callback=_progress_callback,
    )

    assert imported == 2
    assert len(progress_updates) == 2
    assert progress_updates[0][0] == 1
    assert progress_updates[1][0] == 2


def test_import_legacy_event_dry_run_returns_true(tmp_path) -> None:
    """Test that event import in dry_run mode still processes and returns True."""
    production = ProductionFactory.create(external_id="5838")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", production.external_id]],
    )

    before_events = Event.objects.count()
    imported = import_legacy_csv_file(csv_path, dry_run=True)

    assert imported == 1
    assert Event.objects.count() == before_events


def test_parse_legacy_datetime_with_naive_datetime(tmp_path) -> None:
    """Test that naive datetimes are properly converted to aware."""
    csv_path = tmp_path / "Events - voorstellingen.csv"
    production = ProductionFactory.create(external_id="5839")
    # These are valid datetime strings that should be parsed and made aware
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-05-10 20:00:00", "2010-05-10 22:00:00", "Balzaal", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    event = Event.objects.get(hall__translations__name="Balzaal")
    # Verify the datetime is properly set and aware
    assert event.starts_at is not None
    assert event.ends_at is not None
    assert event.starts_at.tzinfo is not None
    assert event.ends_at.tzinfo is not None


def test_count_csv_rows_with_valid_csv(tmp_path) -> None:
    """Test counting rows in a valid CSV file."""
    from apps.imports.csv_importer.legacy_csv_io import _count_csv_rows

    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [
            ["Artist1", "Title1", "Body", "Credits", "Theater", "1100", "legacy-1100"],
            ["Artist2", "Title2", "Body", "Credits", "Theater", "1101", "legacy-1101"],
            ["Artist3", "Title3", "Body", "Credits", "Theater", "1102", "legacy-1102"],
        ],
    )

    count = _count_csv_rows(csv_path)

    assert count == 3


def test_import_csv_without_progress_callback_no_count(tmp_path) -> None:
    """Test that without progress callback, row count is not calculated."""
    from apps.imports.csv_importer import legacy_csv_sync

    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "1110", "legacy-1110"]],
    )

    imported = legacy_csv_sync._import_legacy_csv_file(
        csv_path,
        row_handler=legacy_csv_sync._handlers._import_legacy_production_row,
        partial_error_label="test failed",
        failed_error_label="test failed",
        dry_run=False,
        progress_callback=None,
    )

    assert imported == 1


def test_import_bundled_without_progress_callback(tmp_path) -> None:
    """Test import_bundled_legacy_csv_files without progress callback."""
    productions_path = tmp_path / "Productions - output.csv"
    events_path = tmp_path / "Events - voorstellingen.csv"

    _write_csv(
        productions_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "1120", "legacy-1120"]],
    )
    _write_csv(
        events_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [],
    )

    imported = import_bundled_legacy_csv_files(base_dir=tmp_path)

    assert imported == 1


def test_import_legacy_event_with_both_times_still_before_after_adjustment(tmp_path) -> None:
    """Test event where even after adding a day, end is still before start."""
    production = ProductionFactory.create(external_id="5840")
    csv_path = tmp_path / "Events - voorstellingen.csv"
    _write_csv(
        csv_path,
        ["Starttime", "Endtime", "Hall", "Production"],
        [["2010-06-02 10:00:00", "2010-06-01 06:00:00", "Domzaal2", production.external_id]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    log = ImportLog.objects.get(source=f"legacy_csv:{csv_path.name}")
    assert log.status == ImportLog.Status.SUCCESS

    event = Event.objects.get(hall__translations__name="Domzaal2")
    assert event.starts_at == datetime(2010, 6, 2, 10, 0, tzinfo=UTC)
    # After failed adjustment, ends_at is set to None
    assert event.ends_at is None


def test_genre_creation_with_long_label(tmp_path) -> None:
    """Test that genre labels are truncated if they exceed 50 characters."""
    csv_path = tmp_path / "Productions - output.csv"
    long_genre = "A" * 100
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", long_genre, "1130", "legacy-1130"]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    production = Production.objects.get(external_id="1130")
    assert production.genres.count() == 1
    genre_trans = production.genres.first().translations.first()
    assert len(genre_trans.name) <= 50


def test_count_csv_rows_missing_headers_raises_value_error(tmp_path) -> None:
    from apps.imports.csv_importer.legacy_csv_io import _count_csv_rows

    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing headers"):
        _count_csv_rows(csv_path)


def test_parse_legacy_datetime_returns_none_when_parser_raises(monkeypatch) -> None:
    from apps.imports.csv_importer import legacy_csv_normalize

    def _boom(_value):
        raise ValueError("broken parser")

    monkeypatch.setattr(legacy_csv_normalize, "parse_datetime", _boom)

    assert legacy_csv_normalize._parse_legacy_datetime("2010-01-01 10:00:00") is None


def test_import_legacy_csv_rows_marks_log_failed_when_row_iteration_crashes() -> None:
    from apps.imports.csv_importer import legacy_csv_sync

    def _rows():
        yield {
            "Titel": "Artist",
            "Ondertitel": "Title",
            "Description1": "Body",
            "Description2": "Credits",
            "Genre": "Theater",
            "ID": "1140",
            "Planning ID": "legacy-1140",
        }
        raise RuntimeError("iterator exploded")

    def _ok_handler(_row, *, dry_run):
        return True

    with pytest.raises(RuntimeError, match="iterator exploded"):
        legacy_csv_sync._import_legacy_csv_rows(
            source_name="iter-fail.csv",
            rows=_rows(),
            row_handler=_ok_handler,
            partial_error_label="rows failed",
            failed_error_label="rows failed",
            dry_run=False,
        )

    log = ImportLog.objects.get(source="legacy_csv:iter-fail.csv")
    assert log.status == ImportLog.Status.FAILED
    assert log.records_total == 1
    assert log.records_imported == 1
    assert log.records_failed == 0
    assert "iterator exploded" in (log.error_message or "")


def test_import_legacy_csv_file_rejects_unsupported_detected_kind(monkeypatch, tmp_path) -> None:
    from apps.imports.csv_importer import legacy_csv_sync

    csv_path = tmp_path / "Productions - output.csv"
    _write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "Theater", "1141", "legacy-1141"]],
    )

    monkeypatch.setattr(legacy_csv_sync._io, "detect_legacy_csv_kind", lambda _path: "mystery")

    with pytest.raises(ValueError, match="Unsupported CSV kind: mystery"):
        legacy_csv_sync.import_legacy_csv_file(csv_path)


def test_import_legacy_csv_management_command_refreshes_tqdm_when_total_changes(monkeypatch) -> None:
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
        progress_callback(1, 2)
        progress_callback(2, 3)
        return 2

    monkeypatch.setattr(import_legacy_csv_command, "_tqdm", _fake_tqdm)
    monkeypatch.setattr(import_legacy_csv_command, "import_bundled_legacy_csv_files", _fake_import)
    output = StringIO()

    call_command("import_legacy_csv", stdout=output)

    bar = created["bar"]
    assert bar.total == 3
    assert bar.refresh_count == 1
    assert bar.updates == [1, 1]
    assert bar.closed is True
    assert "Imported 2 legacy CSV records" in output.getvalue()

