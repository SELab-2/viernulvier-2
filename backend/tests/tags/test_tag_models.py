import pytest
from django.core.exceptions import ValidationError
from apps.tags.models import TagTranslation

# Use the factories to create test data
from tests.factories.tag import (
    TagFactory,
    TagTranslationFactory,
)
from tests.factories.language import LanguageFactory

pytestmark = pytest.mark.django_db

# =====================================================
# Tag
# =====================================================


class TestTag:
    def test_tag_creation(self):
        tag = TagFactory(
            url="http://example.com/tag/rock",
            source="source",
            source_type="source_type",
            is_external=True,
            is_enabled=True,
            type="type",
        )

        assert tag.url == "http://example.com/tag/rock"
        assert tag.source == "source"
        assert tag.source_type == "source_type"
        assert tag.is_external is True
        assert tag.is_enabled is True
        assert tag.type == "type"

    def test_wrong_url(self):
        tag = TagFactory.build(url="not-a-valid-url")
        with pytest.raises(ValidationError):
            tag.full_clean()

    def test_empty_type(self):
        tag = TagFactory.build(type="")

        tag.full_clean()

    def test_str_representation(self):
        tag = TagFactory(type="genre")
        TagTranslationFactory(tag=tag, language__code="en", name="Rock")
        assert str(tag) == "Rock"

    def test_delete_cascades_to_translations(self):
        tag = TagFactory()
        TagTranslationFactory.create_batch(2, tag=tag)

        assert TagTranslation.objects.count() == 2

        tag.delete()

        assert TagTranslation.objects.count() == 0


# =====================================================
# TagTranslation
# =====================================================


class TestTagTranslation:
    def test_requires_name(self):
        translation = TagTranslationFactory.build(name="")
        with pytest.raises(ValidationError):
            translation.full_clean()

    def test_optional_fields_can_be_blank(self):
        translation = TagTranslationFactory(short_description="", url_title="")
        translation.full_clean()  # should not raise

    def test_str(self):
        translation = TagTranslationFactory(
            language__code="en",
            name="Rock",
        )
        assert str(translation) == "en - Rock"

    def test_unique_together_tag_language(self):
        tag = TagFactory()
        language = LanguageFactory()

        TagTranslationFactory(tag=tag, language=language)

        with pytest.raises(ValidationError):
            TagTranslationFactory(tag=tag, language=language)

    def test_language_reverse_relation(self):
        language = LanguageFactory()
        TagTranslationFactory.create_batch(3, language=language)

        assert language.tag_translations.count() == 3

    def test_tag_reverse_relation(self):
        tag = TagFactory()
        TagTranslationFactory.create_batch(2, tag=tag)

        assert tag.translations.count() == 2
