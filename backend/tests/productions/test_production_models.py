"""Comprehensive tests for production-related models and relationships."""

from django.core.exceptions import ValidationError
import pytest

from apps.productions.models import (
    ProductionGenre,
    ProductionTag,
    ProductionTagTranslation,
    ProductionTranslation,
)
from tests.factories.genre import GenreFactory
from tests.factories.language import LanguageFactory
from tests.factories.media_library import MediaGalleryFactory
from tests.factories.production import (
    ProductionFactory,
    ProductionGenreFactory,
    ProductionTagFactory,
    ProductionTagTranslationFactory,
    ProductionTranslationFactory,
    UitDatabaseThemeFactory,
    UitDatabaseTypeFactory,
)
from tests.factories.tag import TagFactory

pytestmark = pytest.mark.django_db


class TestUitDatabaseTheme:
    """Tests for UitDatabaseTheme model behavior."""

    def test_requires_name(self) -> None:
        """Validate that an empty name is rejected."""
        theme = UitDatabaseThemeFactory.build(name="")

        with pytest.raises(ValidationError):
            theme.full_clean()

    def test_reverse_relation_productions(self) -> None:
        """Verify reverse relation from theme to linked productions."""
        theme = UitDatabaseThemeFactory()
        productions = ProductionFactory.create_batch(3, uit_database_theme=theme)

        assert theme.productions.count() == 3
        assert all(p.uit_database_theme == theme for p in productions)


class TestUitDatabaseType:
    """Tests for UitDatabaseType model behavior."""

    def test_requires_name(self) -> None:
        """Validate that an empty name is rejected."""
        production_type = UitDatabaseTypeFactory.build(name="")

        with pytest.raises(ValidationError):
            production_type.full_clean()

    def test_reverse_relation_productions(self) -> None:
        """Verify reverse relation from type to linked productions."""
        production_type = UitDatabaseTypeFactory()
        productions = ProductionFactory.create_batch(2, uit_database_type=production_type)

        assert production_type.productions.count() == 2
        assert all(p.uit_database_type == production_type for p in productions)


class TestProduction:
    """Tests for Production model behavior and FK relations."""

    def test_production_creation(self) -> None:
        """Create a production and assert required factory relations exist."""
        production = ProductionFactory.create()

        assert production.pk is not None
        assert production.uit_database_theme is not None
        assert production.uit_database_type is not None
        assert production.media_gallery is not None

    def test_allows_nullable_foreign_keys(self) -> None:
        """Ensure nullable foreign keys can all be set to None."""
        production = ProductionFactory.create(
            uit_database_theme=None,
            uit_database_type=None,
            media_gallery=None,
        )

        assert production.uit_database_theme is None
        assert production.uit_database_type is None
        assert production.media_gallery is None

    def test_attendance_mode_must_be_valid_choice(self) -> None:
        """Reject attendance_mode values outside the configured choices."""
        production = ProductionFactory.build(attendance_mode="invalid")

        with pytest.raises(ValidationError):
            production.full_clean()

    def test_performer_type_must_be_valid_choice(self) -> None:
        """Reject performer_type values outside the configured choices."""
        production = ProductionFactory.build(performer_type="invalid")

        with pytest.raises(ValidationError):
            production.full_clean()

    def test_deleting_theme_sets_production_theme_to_null(self) -> None:
        """Deleting a theme should set linked production FK to null."""
        theme = UitDatabaseThemeFactory()
        production = ProductionFactory.create(uit_database_theme=theme)

        theme.delete()
        production.refresh_from_db()

        assert production.uit_database_theme is None

    def test_deleting_type_sets_production_type_to_null(self) -> None:
        """Deleting a type should set linked production FK to null."""
        production_type = UitDatabaseTypeFactory()
        production = ProductionFactory.create(uit_database_type=production_type)

        production_type.delete()
        production.refresh_from_db()

        assert production.uit_database_type is None

    def test_deleting_media_gallery_sets_production_gallery_to_null(self) -> None:
        """Deleting a media gallery should set linked production FK to null."""
        gallery = MediaGalleryFactory()
        production = ProductionFactory.create(media_gallery=gallery)

        gallery.delete()
        production.refresh_from_db()

        assert production.media_gallery is None


class TestProductionTranslation:
    """Tests for ProductionTranslation model behavior and constraints."""

    def test_translation_creation(self) -> None:
        """Create a translation and verify base relations are present."""
        translation = ProductionTranslationFactory.create()

        assert translation.pk is not None
        assert translation.production is not None
        assert translation.language is not None

    def test_unique_together_production_language(self) -> None:
        """Disallow duplicate translation language for the same production."""
        production = ProductionFactory.create()
        language = LanguageFactory.create()

        ProductionTranslationFactory.create(production=production, language=language)

        with pytest.raises(ValidationError):
            ProductionTranslationFactory.create(production=production, language=language)

    def test_same_language_allowed_for_different_productions(self) -> None:
        """Allow one language to be reused across different productions."""
        language = LanguageFactory.create()

        first = ProductionTranslationFactory.create(language=language)
        second = ProductionTranslationFactory.create(language=language)

        assert first.production_id != second.production_id

    def test_reverse_relation_from_production(self) -> None:
        """Expose translations through the production reverse relation."""
        production = ProductionFactory.create()
        translations = ProductionTranslationFactory.create_batch(2, production=production)

        assert production.translations.count() == 2
        assert all(t.production == production for t in translations)

    def test_cascade_delete_production_deletes_translations(self) -> None:
        """Deleting production should cascade to production translations."""
        production = ProductionFactory.create()
        ProductionTranslationFactory.create_batch(2, production=production)

        production.delete()

        assert ProductionTranslation.objects.count() == 0


class TestProductionTag:
    """Tests for ProductionTag through model and production-tag relations."""

    def test_production_tag_creation(self) -> None:
        """Create a through record linking one production and one tag."""
        production_tag = ProductionTagFactory.create()

        assert production_tag.pk is not None
        assert production_tag.production is not None
        assert production_tag.tag is not None

    def test_unique_together_production_tag(self) -> None:
        """Disallow duplicate production-tag through entries."""
        production = ProductionFactory.create()
        tag = TagFactory.create()

        ProductionTagFactory.create(production=production, tag=tag)

        with pytest.raises(ValidationError):
            ProductionTagFactory.create(production=production, tag=tag)

    def test_reverse_relations(self) -> None:
        """Check default reverse accessors for through model relations."""
        production = ProductionFactory.create()
        tag = TagFactory.create()
        ProductionTagFactory.create(production=production, tag=tag)

        assert production.tags.count() == 1
        assert production.tags.first() == tag

        assert tag.productions.count() == 1
        assert tag.productions.first() == production

    def test_cascade_delete_production_deletes_production_tags(self) -> None:
        """Deleting production should cascade to ProductionTag rows."""
        production = ProductionFactory.create()
        ProductionTagFactory.create_batch(2, production=production)

        production.delete()

        assert ProductionTag.objects.count() == 0

    def test_cascade_delete_tag_deletes_production_tags(self) -> None:
        """Deleting tag should cascade to ProductionTag rows."""
        tag = TagFactory.create()
        ProductionTagFactory.create(tag=tag)

        tag.delete()

        assert ProductionTag.objects.count() == 0


class TestProductionTagTranslationCreation:
    def test_can_create_translation(self) -> None:
        translation = ProductionTagTranslationFactory.create()
        assert translation.pk is not None

    def test_has_production_tag_relation(self) -> None:
        translation = ProductionTagTranslationFactory.create()
        assert translation.production_tag is not None

    def test_has_language_relation(self) -> None:
        translation = ProductionTagTranslationFactory.create()
        assert translation.language is not None

    def test_description_defaults_to_blank(self) -> None:
        translation = ProductionTagTranslationFactory.create(description="")
        assert translation.description == ""

    def test_description_can_be_set(self) -> None:
        translation = ProductionTagTranslationFactory.create(description="Some context note.")
        assert translation.description == "Some context note."


class TestProductionTagTranslationUniqueConstraint:
    def test_duplicate_production_tag_language_raises(self) -> None:
        production_tag = ProductionTagFactory.create()
        language = LanguageFactory.create()
        ProductionTagTranslationFactory.create(production_tag=production_tag, language=language)

        with pytest.raises(ValidationError):
            ProductionTagTranslationFactory.create(production_tag=production_tag, language=language)

    def test_same_language_different_production_tags_is_allowed(self) -> None:
        language = LanguageFactory.create()
        pt1 = ProductionTagFactory.create()
        pt2 = ProductionTagFactory.create()

        t1 = ProductionTagTranslationFactory.create(production_tag=pt1, language=language)
        t2 = ProductionTagTranslationFactory.create(production_tag=pt2, language=language)

        assert t1.pk != t2.pk

    def test_same_production_tag_different_languages_is_allowed(self) -> None:
        production_tag = ProductionTagFactory.create()
        lang_nl = LanguageFactory.create(code="nl")
        lang_en = LanguageFactory.create(code="en")

        t1 = ProductionTagTranslationFactory.create(production_tag=production_tag, language=lang_nl)
        t2 = ProductionTagTranslationFactory.create(production_tag=production_tag, language=lang_en)

        assert t1.pk != t2.pk


class TestProductionTagTranslationCascade:
    def test_deleting_production_tag_cascades_to_translations(self) -> None:
        production_tag = ProductionTagFactory.create()
        ProductionTagTranslationFactory.create_batch(2, production_tag=production_tag)

        production_tag_id = production_tag.id

        production_tag.delete()

        assert not ProductionTagTranslation.objects.filter(production_tag_id=production_tag_id).exists()

    def test_deleting_language_cascades_to_translations(self) -> None:
        language = LanguageFactory.create()
        ProductionTagTranslationFactory.create_batch(2, language=language)

        language_pk = language.pk

        language.delete()

        assert not ProductionTagTranslation.objects.filter(language_id=language_pk).exists()


class TestProductionTagTranslationReverseRelation:
    def test_translations_accessible_from_production_tag(self) -> None:
        production_tag = ProductionTagFactory.create()
        lang_nl = LanguageFactory.create(code="nl")
        lang_en = LanguageFactory.create(code="en")
        ProductionTagTranslationFactory.create(production_tag=production_tag, language=lang_nl)
        ProductionTagTranslationFactory.create(production_tag=production_tag, language=lang_en)

        assert production_tag.translations.count() == 2


class TestProductionTagTranslationStr:
    def test_str_contains_production_tag_id(self) -> None:
        translation = ProductionTagTranslationFactory.create()
        assert str(translation.production_tag_id) in str(translation)

    def test_str_contains_language_code(self) -> None:
        language = LanguageFactory.create(code="fr")
        translation = ProductionTagTranslationFactory.create(language=language)
        assert "fr" in str(translation)


class TestProductionTagTranslationOrdering:
    def test_default_ordering_is_by_language_code(self) -> None:
        production_tag = ProductionTagFactory.create()
        lang_nl = LanguageFactory.create(code="nl")
        lang_en = LanguageFactory.create(code="en")
        lang_de = LanguageFactory.create(code="de")
        ProductionTagTranslationFactory.create(production_tag=production_tag, language=lang_nl)
        ProductionTagTranslationFactory.create(production_tag=production_tag, language=lang_en)
        ProductionTagTranslationFactory.create(production_tag=production_tag, language=lang_de)

        codes = list(production_tag.translations.values_list("language__code", flat=True))
        assert codes == sorted(codes)


class TestProductionGenre:
    """Tests for ProductionGenre through model and production-genre relations."""

    def test_production_genre_creation(self) -> None:
        """Create a through record linking one production and one genre."""
        production_genre = ProductionGenreFactory.create()

        assert production_genre.pk is not None
        assert production_genre.production is not None
        assert production_genre.genre is not None

    def test_production_genre_string_representation(self) -> None:
        """Verify the string representation of a ProductionGenre instance."""
        production = ProductionFactory.create()
        genre = GenreFactory.create()
        production_genre = ProductionGenreFactory.create(production=production, genre=genre)

        expected_str = f"{genre.type}"
        assert str(production_genre) == expected_str

    def test_position_must_be_positive_or_zero(self) -> None:
        """Reject negative position values for genre ordering."""
        production_genre = ProductionGenreFactory.build(position=-1)

        with pytest.raises(ValidationError):
            production_genre.full_clean()

    def test_unique_together_production_genre(self) -> None:
        """Disallow duplicate production-genre through entries."""
        production = ProductionFactory.create()
        genre = GenreFactory.create()

        ProductionGenreFactory.create(production=production, genre=genre)

        with pytest.raises(ValidationError):
            ProductionGenreFactory.create(production=production, genre=genre)

    def test_reverse_relations(self) -> None:
        """Check default reverse accessors for through model relations."""
        production = ProductionFactory.create()
        genre = GenreFactory.create()
        ProductionGenreFactory.create(production=production, genre=genre)

        assert production.genres.count() == 1
        assert production.genres.first() == genre

        assert genre.productions.count() == 1
        assert genre.productions.first() == production

    def test_cascade_delete_production_deletes_production_genres(self) -> None:
        """Deleting production should cascade to ProductionGenre rows."""
        production = ProductionFactory.create()
        ProductionGenreFactory.create_batch(2, production=production)

        production.delete()

        assert ProductionGenre.objects.count() == 0

    def test_cascade_delete_genre_deletes_production_genres(self) -> None:
        """Deleting genre should cascade to ProductionGenre rows."""
        genre = GenreFactory.create()
        ProductionGenreFactory.create(genre=genre)

        genre.delete()

        assert ProductionGenre.objects.count() == 0
