import factory
from factory.helpers import post_generation
from factory.declarations import LazyFunction, LazyAttribute
from faker import Faker
from django.utils import timezone
from datetime import timedelta

from apps.import_log.models import ImportLog  # pas pad aan indien nodig

faker = Faker()


class ImportLogFactory(factory.django.DjangoModelFactory):
    class Meta(factory.django.DjangoModelFactory.Meta):
        model = ImportLog

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
        lambda o: o.started_at + timedelta(minutes=faker.random_int(min=1, max=60))
        if o.started_at else None
    )

    error_message = None

    @post_generation
    def adjust_counts(obj, create, extracted, **kwargs):
        """
        Zorgt dat imported + failed <= total
        """
        if not create:
            return

        total = obj.records_total
        imported = faker.random_int(min=0, max=total)
        failed = faker.random_int(min=0, max=(total - imported))

        obj.records_imported = imported
        obj.records_failed = failed
        obj.save()

    @post_generation
    def adjust_status_logic(obj, create, extracted, **kwargs):
        """
        Logische status-afhandeling.
        """
        if not create:
            return

        if obj.status == ImportLog.Status.FAILED:
            obj.error_message = faker.sentence()
        elif obj.status in [ImportLog.Status.PENDING, ImportLog.Status.IN_PROGRESS]:
            obj.finished_at = None

        obj.save()