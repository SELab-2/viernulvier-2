"""Shared helpers for legacy CSV importer tests."""

from __future__ import annotations

import csv
from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    """Write CSV rows with a header to a UTF-8 encoded test file."""
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def write_raw_csv(path: Path, content: str) -> None:
    """Write raw CSV text to a UTF-8 encoded test file."""
    path.write_text(content, encoding="utf-8")
