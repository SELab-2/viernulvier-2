from unittest.mock import MagicMock, patch

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


def test_base_language_code_with_region(settings):
    settings.LANGUAGE_CODE = "nl-BE"
    assert BaseModel.base_language_code() == "nl"


def test_base_language_code_without_region(settings):
    settings.LANGUAGE_CODE = "fr"
    assert BaseModel.base_language_code() == "fr"


def test_get_base_translation_prefers_base_language():
    obj = CoreDummyFactory.build(name="valid")

    base_translation = MagicMock()
    base_translation.language.code = "nl"

    fallback_translation = MagicMock()
    fallback_translation.language.code = "en"

    qs = MagicMock()
    qs.filter.return_value.first.return_value = base_translation
    qs.first.return_value = fallback_translation

    manager = MagicMock()
    manager.all.return_value = qs
    obj.translations = manager

    with patch.object(CoreDummy, "base_language_code", return_value="nl"):
        result = obj.get_base_translation("translations")

    assert result == base_translation


def test_get_base_translation_fallback_first():
    obj = CoreDummyFactory.build(name="valid")

    fallback_translation = MagicMock()
    fallback_translation.language.code = "fr"

    qs = MagicMock()
    qs.filter.return_value.first.return_value = None
    qs.first.return_value = fallback_translation

    manager = MagicMock()
    manager.all.return_value = qs
    obj.translations = manager

    with patch.object(CoreDummy, "base_language_code", return_value="nl"):
        result = obj.get_base_translation("translations")

    assert result == fallback_translation


def test_get_base_display_name_returns_value():
    obj = CoreDummyFactory.build(name="valid")

    translation = MagicMock()
    translation.name = "Hello"

    with patch.object(obj, "get_base_translation", return_value=translation):
        result = obj.get_base_display_name(
            related_name="translations",
            name_field="name",
        )

    assert result == "Hello"


def test_get_base_display_name_fallback_when_no_translation():
    obj = CoreDummyFactory.build(name="valid")

    with patch.object(obj, "get_base_translation", return_value=None):
        result = obj.get_base_display_name(fallback="DEFAULT")

    assert result == "DEFAULT"


def test_get_base_display_name_fallback_when_value_empty():
    obj = CoreDummyFactory.build(name="valid")

    translation = MagicMock()
    translation.name = ""

    with patch.object(obj, "get_base_translation", return_value=translation):
        result = obj.get_base_display_name(
            name_field="name",
            fallback="DEFAULT",
        )

    assert result == "DEFAULT"
