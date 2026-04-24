"""Import the legacy Viernulvier CSV exports bundled with the backend."""

from argparse import ArgumentParser
from typing import Any

from django.core.cache import cache
from django.core.management.base import BaseCommand

from apps.imports.csv_importer.legacy_csv_sync import import_bundled_legacy_csv_files

try:
    from tqdm import tqdm as _tqdm
except Exception:  # pragma: no cover - optional dependency in runtime environments
    _tqdm = None


class Command(BaseCommand):
    """Import the legacy production and event CSV exports."""

    help = "Import the legacy Viernulvier CSV exports bundled with the backend"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Define command options."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Parse the CSV files and validate the rows without saving anything.",
        )
        parser.add_argument(
            "--only",
            type=str,
            choices=["productions", "events"],
            default=None,
            help="Import only one legacy CSV dataset.",
        )

    def handle(self, *_args: tuple, **options: dict) -> None:
        """Run the legacy CSV import command."""
        dry_run_value = options.get("dry_run", False)
        dry_run = dry_run_value if isinstance(dry_run_value, bool) else False  # type: ignore[reportGeneralTypeIssues]

        only_value = options.get("only")
        only = only_value if isinstance(only_value, str) else None  # type: ignore[reportGeneralTypeIssues]

        progress_bar: Any = None

        def _on_progress(processed: int, total_rows: int | None) -> None:
            nonlocal progress_bar
            if _tqdm is None:
                return
            if progress_bar is None:
                progress_bar = _tqdm(total=total_rows, unit="rows", desc="Importing legacy CSV", leave=False)
            bar = progress_bar
            if total_rows is not None and bar.total != total_rows:
                bar.total = total_rows
                bar.refresh()

            delta = processed - bar.n
            if delta > 0:
                bar.update(delta)

        try:
            total = import_bundled_legacy_csv_files(  # type: ignore[reportGeneralTypeIssues]
                dry_run=dry_run,
                only=only,
                progress_callback=_on_progress,
            )
        finally:
            if progress_bar is not None:
                progress_bar.close()

        suffix = " [DRY RUN]" if dry_run else ""
        if not dry_run:
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Cleared API cache"))

        self.stdout.write(self.style.SUCCESS(f"Imported {total} legacy CSV records{suffix}"))
