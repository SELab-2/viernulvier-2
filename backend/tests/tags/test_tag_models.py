"""Tests for Tag and TagTranslation model behaviour."""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.tags.models import TagTranslation
from tests.factories.language import LanguageFactory
from tests.factories.tag import (
    TagFactory,
    TagTranslationFactory,
)

pytestmark = pytest.mark.django_db

# =====================================================
# Tag
# =====================================================


class TestTag:
    def test_tag_creation(self) -> None:
        tag = TagFactory(
            url="http://example.com/tag/rock",
            source="source",
            is_enabled=True,
            type="type",
        )

        assert tag.url == "http://example.com/tag/rock"
        assert tag.source == "source"
        assert tag.is_enabled is True
        assert tag.type == "type"

    def test_wrong_url(self) -> None:
        tag = TagFactory.build(url="not-a-valid-url")
        with pytest.raises(ValidationError):
            tag.full_clean()

    def test_empty_type(self) -> None:
        tag = TagFactory.build(type="")

        tag.full_clean()

    def test_str_representation(self) -> None:
        tag = TagFactory(type="genre")
        TagTranslationFactory(tag=tag, language__code="en", name="Rock")
        assert str(tag) == "Rock"

    def test_delete_cascades_to_translations(self) -> None:
        tag = TagFactory()
        TagTranslationFactory.create_batch(2, tag=tag)

        assert TagTranslation.objects.count() == 2

        tag.delete()

        assert TagTranslation.objects.count() == 0

    def test_clean_wraps_media_validation_errors_for_uploaded_image(self, monkeypatch) -> None:
        def _raise_validation_error(*args, **kwargs):
            raise ValueError("Invalid image file")

        monkeypatch.setattr("apps.tags.models.validate_media_file", _raise_validation_error)
        image = SimpleUploadedFile("tag.png", b"fake-image", content_type="image/png")
        tag = TagFactory.build(image=image)

        with pytest.raises(ValidationError) as exc:
            tag.full_clean()

        assert "image" in exc.value.message_dict

    def test_new_tag_can_be_created_without_translations(self) -> None:
        """New tags are exempt from the translation requirement because
        translations are added after creation."""
        tag = TagFactory()
        assert tag.pk is not None
        assert tag.translations.count() == 0

    def test_existing_tag_cannot_be_saved_without_translations(self) -> None:
        """Once a tag exists, it must retain at least one translation."""
        tag = TagFactory()
        # Tag was created without translations (new-tag exemption)
        assert tag.translations.count() == 0

        with pytest.raises(ValidationError) as exc:
            tag.save()

        assert "translations" in exc.value.message_dict

    def test_existing_tag_with_translations_can_be_saved(self) -> None:
        """A tag that has translations can be saved normally."""
        tag = TagFactory()
        TagTranslationFactory(tag=tag, language__code="en", name="Rock")

        tag.save()  # should not raise

        assert tag.translations.count() == 1


# =====================================================
# TagTranslation
# =====================================================


class TestTagTranslation:
    def test_requires_name(self) -> None:
        translation = TagTranslationFactory.build(name="")
        with pytest.raises(ValidationError):
            translation.full_clean()

    def test_optional_fields_can_be_blank(self) -> None:
        translation = TagTranslationFactory(short_description="", url_title="")
        translation.full_clean()  # should not raise

    def test_str(self) -> None:
        translation = TagTranslationFactory(
            language__code="en",
            name="Rock",
        )
        assert str(translation) == "en - Rock"

    def test_unique_together_tag_language(self) -> None:
        tag = TagFactory()
        language = LanguageFactory()

        TagTranslationFactory(tag=tag, language=language)

        with pytest.raises(ValidationError):
            TagTranslationFactory(tag=tag, language=language)

    def test_language_reverse_relation(self) -> None:
        language = LanguageFactory()
        TagTranslationFactory.create_batch(3, language=language)

        assert language.tag_translations.count() == 3

    def test_tag_reverse_relation(self) -> None:
        tag = TagFactory()
        TagTranslationFactory.create_batch(2, tag=tag)

        assert tag.translations.count() == 2
