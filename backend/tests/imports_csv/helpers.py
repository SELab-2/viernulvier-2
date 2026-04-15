from __future__ import annotations

import csv
from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def write_raw_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
