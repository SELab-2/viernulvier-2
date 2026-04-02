from unittest.mock import patch

from django.core.exceptions import ValidationError
import pytest

from apps.core.models import BaseModel
from tests.factories.core import CoreDummy, CoreDummyFactory

pytestmark = pytest.mark.django_db(transaction=True)


class TestBaseModel:
    def test_basemodel_is_abstract(self) -> None:
        assert BaseModel._meta.abstract is True

    def test_save_calls_full_clean(self) -> None:
        """save() must delegate to full_clean(), regardless of validity."""
        obj = CoreDummyFactory.build(name="ok")
        with patch.object(obj, "full_clean", wraps=obj.full_clean) as mock_clean:
            obj.save()
            mock_clean.assert_called_once()

    def test_save_persists_valid_instance(self) -> None:
        obj = CoreDummyFactory.build(name="valid")
        obj.save()
        assert obj.pk is not None

    def test_save_valid_instance_is_retrievable(self) -> None:
        obj = CoreDummyFactory.build(name="hello")
        obj.save()
        fetched = CoreDummy.objects.get(pk=obj.pk)
        assert fetched.name == "hello"

    def test_save_max_length_boundary_is_accepted(self) -> None:
        """A name of exactly 10 characters (the max_length) must be valid."""
        obj = CoreDummyFactory.build(name="a" * 10)
        obj.save()
        assert obj.pk is not None

    def test_save_blocks_name_too_long(self) -> None:
        """Names longer than max_length=10 must be rejected."""
        obj = CoreDummyFactory.build(name="this_is_way_too_long")
        with pytest.raises(ValidationError):
            obj.save()

    def test_save_blocks_blank_name(self) -> None:
        """blank=False means an empty string must be rejected."""
        obj = CoreDummyFactory.build(name="")
        with pytest.raises(ValidationError):
            obj.save()

    def test_save_blocks_null_name(self) -> None:
        """null=False means None must be rejected."""
        obj = CoreDummyFactory.build(name=None)
        with pytest.raises(ValidationError):
            obj.save()

    def test_save_on_update_also_runs_full_clean(self) -> None:
        """Validation must run not just on insert but also on update."""
        obj = CoreDummyFactory.build(name="valid")
        obj.save()

        obj.name = "this_is_way_too_long"
        with pytest.raises(ValidationError):
            obj.save()

    def test_save_valid_update_persists(self) -> None:
        obj = CoreDummyFactory.build(name="first")
        obj.save()
        obj.name = "second"
        obj.save()
        assert CoreDummy.objects.get(pk=obj.pk).name == "second"

    def test_get_base_translation_returns_none_without_related_manager(self) -> None:
        obj = CoreDummyFactory.build(name="valid")
        assert obj.get_base_translation(related_name="translations") is None
