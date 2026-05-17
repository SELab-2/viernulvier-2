"""Factory Boy factories for import log test data."""

from datetime import timedelta

from django.utils import timezone
import factory
from factory.declarations import LazyAttribute, LazyFunction
from factory.helpers import post_generation
from faker import Faker

from apps.import_log.models import ImportLog

faker = Faker()


class ImportLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ImportLog
        skip_postgeneration_save = True

    source = LazyFunction(lambda: faker.file_name(extension="csv"))

    status = LazyFunction(
        lambda: faker.random_element(
            elements=[
                ImportLog.Status.PENDING,
                ImportLog.Status.IN_PROGRESS,
                ImportLog.Status.PARTIAL_SUCCESS,
                ImportLog.Status.SUCCESS,
                ImportLog.Status.FAILED,
            ]
        )
    )

    records_total = LazyFunction(lambda: faker.random_int(min=1, max=500))
    records_imported = 0
    records_failed = 0

    started_at = LazyFunction(timezone.now)
    finished_at = LazyAttribute(
        lambda o: o.started_at + timedelta(minutes=faker.random_int(min=1, max=60)) if o.started_at else None
    )

    error_message = None

    @post_generation
    def adjust_counts(self, create, _) -> None:
        """Keep imported + failed counts within the total record count."""
        if not create:
            return

        total = self.records_total
        imported = faker.random_int(min=0, max=total)
        failed = faker.random_int(min=0, max=(total - imported))

        self.records_imported = imported
        self.records_failed = failed
        self.save()

    @post_generation
    def adjust_status_logic(self, create, _, **__) -> None:
        """Adjust timestamps and error messages so they match the selected status."""
        if not create:
            return

        if self.status == ImportLog.Status.FAILED:
            self.error_message = faker.sentence()
        elif self.status in [ImportLog.Status.PENDING, ImportLog.Status.IN_PROGRESS]:
            self.finished_at = None

        self.save()
