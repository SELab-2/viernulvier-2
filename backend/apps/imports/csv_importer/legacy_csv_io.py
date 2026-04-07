"""CSV file IO and dataset detection for legacy imports."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from apps.imports.scrapers.viernulvier import clean_string

from .legacy_csv_constants import LEGACY_EVENT_HEADERS, LEGACY_PRODUCTION_HEADERS


def _iter_csv_rows(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing headers in {csv_path.name}")
        return list(reader)


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing headers in {csv_path.name}")
        return sum(1 for _ in reader)


def detect_legacy_csv_kind(csv_path: Path | str) -> str:
    """Identify which legacy dataset a CSV file contains."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = {clean_string(header) for header in (reader.fieldnames or []) if header}

    if headers == LEGACY_PRODUCTION_HEADERS:
        return "productions"
    if headers == LEGACY_EVENT_HEADERS:
        return "events"
    raise ValueError(f"Unsupported legacy CSV headers in {path.name}: {sorted(headers)}")
