from __future__ import annotations

import pytest

from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from apps.import_log.models import ImportLog
from apps.imports.csv_importer import import_legacy_csv_file
from apps.languages.models import Language
from apps.locations.models import Hall
from apps.productions.models import Production, ProductionGenre
from tests.imports_csv.helpers import write_csv, write_raw_csv

pytestmark = pytest.mark.django_db(transaction=True)


def test_import_legacy_productions_creates_translations_and_genres(tmp_path) -> None:

    csv_path = tmp_path / "Productions - output.csv"
    write_csv(
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
    write_csv(
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
    write_csv(
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


def test_import_legacy_csv_dry_run_has_no_side_effect_writes(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    write_csv(
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


@pytest.mark.parametrize(
    ("description1", "description2"),
    [
        ("\\N", "\\N"),
        ("\\", "\\"),
    ],
)
def test_import_legacy_production_normalises_empty_text_fields(
    tmp_path,
    description1: str,
    description2: str,
) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    write_raw_csv(
        csv_path,
        "Titel,Ondertitel,Description1,Description2,Genre,ID,Planning ID\n"
        f"Artist,Title,{description1},{description2},Theater,500,legacy-500\n",
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    production = Production.objects.get(external_id="500")
    translation = production.translations.get(language__code="nl")
    assert translation.description == ""
    assert translation.description_extra == ""


def test_split_genres_empty_string(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", "", "502", "legacy-502"]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    production = Production.objects.get(external_id="502")
    assert production.genres.count() == 0


def test_genre_creation_with_long_label(tmp_path) -> None:
    csv_path = tmp_path / "Productions - output.csv"
    long_genre = "A" * 100
    write_csv(
        csv_path,
        ["Titel", "Ondertitel", "Description1", "Description2", "Genre", "ID", "Planning ID"],
        [["Artist", "Title", "Body", "Credits", long_genre, "1130", "legacy-1130"]],
    )

    imported = import_legacy_csv_file(csv_path)

    assert imported == 1
    production = Production.objects.get(external_id="1130")
    assert production.genres.count() == 1
    genre_translation = production.genres.first().translations.first()
    assert len(genre_translation.name) <= 50
