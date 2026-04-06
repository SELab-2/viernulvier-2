"""Import the legacy Viernulvier CSV exports bundled with the backend."""

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from apps.imports.csv_importer import import_bundled_legacy_csv_files


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

    def handle(self, *_args: tuple, **options: Any) -> None:
        """Run the legacy CSV import command."""
        dry_run_value = options.get("dry_run", False)
        dry_run = dry_run_value if isinstance(dry_run_value, bool) else False  # type: ignore[reportGeneralTypeIssues]

        only_value = options.get("only")
        only = only_value if isinstance(only_value, str) else None  # type: ignore[reportGeneralTypeIssues]
        total = import_bundled_legacy_csv_files(dry_run=dry_run, only=only)  # type: ignore[reportGeneralTypeIssues]
        suffix = " [DRY RUN]" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"Imported {total} legacy CSV records{suffix}"))
