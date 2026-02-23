import pytest
from django.core.exceptions import ValidationError
from django.db import connection

from tests.factories.core import CoreDummy, CoreDummyFactory

pytestmark = pytest.mark.django_db(transaction=True)


def create_core_dummy_table():
    """
    Creates the table for CoreDummy in the test database.

    Because CoreDummy is a test-only model (not part of migrations),
    its schema is created manually for these tests.
    """
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(CoreDummy)


def drop_core_dummy_table():
    with connection.schema_editor() as schema_editor:
        schema_editor.delete_model(CoreDummy)


class TestBaseModel:
    def test_basemodel_is_abstract(self):
        from apps.core.model import BaseModel
        assert BaseModel._meta.abstract is True

    def test_save_runs_full_clean_and_blocks_invalid_data(self):
        create_core_dummy_table()
        try:
            obj = CoreDummyFactory.build(name="this_is_way_too_long")
            with pytest.raises(ValidationError):
                obj.save()
        finally:
            drop_core_dummy_table()

    def test_save_persists_valid_instance(self):
        create_core_dummy_table()
        try:
            obj = CoreDummyFactory.build(name="valid")
            obj.save()
            assert obj.pk is not None
        finally:
            drop_core_dummy_table()