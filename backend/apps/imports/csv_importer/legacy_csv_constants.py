"""Constants for importing legacy Viernulvier CSV exports."""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LEGACY_PRODUCTION_ORIGINAL_CSV = PACKAGE_ROOT / "Productions - output.csv"
LEGACY_PRODUCTION_CSV = PACKAGE_ROOT / "Productions - converted.csv"
LEGACY_EVENT_CSV = PACKAGE_ROOT / "Events - voorstellingen.csv"
LEGACY_LANGUAGE_CODE = "nl"
LEGACY_LANGUAGE_NAME = "Dutch"
LEGACY_LANGUAGE_ACTIVE = True
LEGACY_PRODUCTION_FIELDNAMES = [
    "Titel",
    "Ondertitel",
    "Description1",
    "Description2",
    "Genre",
    "ID",
    "Planning ID",
]
LEGACY_PRODUCTION_HEADERS = set(LEGACY_PRODUCTION_FIELDNAMES)
LEGACY_EVENT_HEADERS = {"Starttime", "Endtime", "Hall", "Production"}
