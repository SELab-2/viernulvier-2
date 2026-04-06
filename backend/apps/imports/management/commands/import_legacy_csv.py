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
        parser.add_argument(
            "--only",
            type=str,
            default=None,
            help="Only parse the CSV files matching the provided criteria.",
        )

    def handle(self, *_args: tuple, **options: dict) -> None:
        """Run the legacy CSV import command."""
        dry_run = options.get("dry_run", False)
        only = options.get("only")
        if only not in ["productions", "events", None]:
            self.stdout.write(
                self.style.ERROR(
                    "Invalid value for --only. Expected 'productions' or 'events'."
                )
            )
            return
        total = import_bundled_legacy_csv_files(dry_run=dry_run, only=only)
        suffix = " [DRY RUN]" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"Imported {total} legacy CSV records{suffix}"))
