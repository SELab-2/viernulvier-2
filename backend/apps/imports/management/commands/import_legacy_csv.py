"""Import the legacy Viernulvier CSV exports bundled with the backend."""

from argparse import ArgumentParser

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

    def handle(self, *_args: tuple, **options: dict) -> None:
        """Run the legacy CSV import command."""
        dry_run = options.get("dry_run", False)
        total = import_bundled_legacy_csv_files(dry_run=dry_run)
        suffix = " [DRY RUN]" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"Imported {total} legacy CSV records{suffix}"))
