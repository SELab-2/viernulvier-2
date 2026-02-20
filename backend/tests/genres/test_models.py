"""
Test file for Genre related models
"""
import pytest
from django.core.exceptions import ValidationError

from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from apps.languages.models import Language


@pytest.mark.django_db
def test_genre_use_as_requires_name() -> None:
    """Ensure GenreUseAs validation rejects an empty name."""
    with pytest.raises(ValidationError):
        GenreUseAs(name="").save()


@pytest.mark.django_db
def test_genre_requires_use_as() -> None:
    """Ensure a Genre cannot be saved without a GenreUseAs relation."""
    with pytest.raises(ValidationError):
        Genre(type="Rock", use_as=None).save()


@pytest.mark.django_db
def test_genre_translation_str() -> None:
    """Verify GenreTranslation.__str__ returns '<language code> - <name>'."""
    language = Language.objects.create(code="en", name="English", is_active=True)
    use_as = GenreUseAs.objects.create(name="tag")
    genre = Genre.objects.create(type="Rock", use_as=use_as)

    translation = GenreTranslation.objects.create(
        name="Rock",
        language=language,
        genre=genre,
    )

    assert str(translation) == "en - Rock"


@pytest.mark.django_db
def test_deleting_genre_use_as_cascades_to_genre() -> None:
    """Verify deleting GenreUseAs cascades and removes related Genre records."""
    use_as = GenreUseAs.objects.create(name="tag")
    Genre.objects.create(type="Rock", use_as=use_as)

    use_as.delete()

    assert Genre.objects.count() == 0


@pytest.mark.django_db
def test_deleting_language_cascades_to_genre_translation() -> None:
    """Verify deleting Language cascades and removes related GenreTranslation records."""
    language = Language.objects.create(code="nl", name="Dutch", is_active=True)
    use_as = GenreUseAs.objects.create(name="genre")
    genre = Genre.objects.create(type="Theater", use_as=use_as)
    GenreTranslation.objects.create(name="Theater", language=language, genre=genre)

    language.delete()

    assert GenreTranslation.objects.count() == 0


@pytest.mark.django_db
def test_genre_str() -> None:
    """Ensure Genre.__str__ includes is correct."""
    use_as = GenreUseAs.objects.create(name="tag")
    genre = Genre.objects.create(type="Festival", use_as=use_as)
    english = Language.objects.create(code="en", name="English", is_active=True)
    dutch = Language.objects.create(code="nl", name="Dutch", is_active=True)

    GenreTranslation.objects.create(name="Festival", language=english, genre=genre)
    GenreTranslation.objects.create(name="Festival NL", language=dutch, genre=genre)

    result = str(genre)

    assert "Festival - [en - Festival] - [nl - Festival NL]" in result

@pytest.mark.django_db
def test_genre_has_multiple_translations() -> None:
    """Ensure a Genre can have multiple related GenreTranslation entries."""
    language_en = Language.objects.create(code="en", name="English", is_active=True)
    language_nl = Language.objects.create(code="nl", name="Dutch", is_active=True)

    use_as = GenreUseAs.objects.create(name="genre")
    genre = Genre.objects.create(type="Theater", use_as=use_as)

    GenreTranslation.objects.create(name="Theater", language=language_en, genre=genre)
    GenreTranslation.objects.create(name="Theater NL", language=language_nl, genre=genre)

    translations = genre.genre_translations.all()

    assert translations.count() == 2

@pytest.mark.django_db
def test_language_has_related_genre_translations() -> None:
    """Ensure Language exposes related GenreTranslation records via related_name."""
    language = Language.objects.create(code="fr", name="French", is_active=True)
    use_as = GenreUseAs.objects.create(name="tag")
    genre = Genre.objects.create(type="Dance", use_as=use_as)

    GenreTranslation.objects.create(name="Danse", language=language, genre=genre)

    assert language.genre_translations.count() == 1

@pytest.mark.django_db
def test_genre_use_as_has_related_genres() -> None:
    """Ensure GenreUseAs exposes related Genre records via related_name."""
    use_as = GenreUseAs.objects.create(name="tag")
    Genre.objects.create(type="Rock", use_as=use_as)
    Genre.objects.create(type="Jazz", use_as=use_as)

    assert use_as.genres.count() == 2


@pytest.mark.django_db
def test_deleting_genre_cascades_to_translations() -> None:
    """Verify deleting Genre cascades and removes its GenreTranslation records."""
    language = Language.objects.create(code="en", name="English", is_active=True)
    use_as = GenreUseAs.objects.create(name="genre")
    genre = Genre.objects.create(type="Opera", use_as=use_as)

    GenreTranslation.objects.create(name="Opera", language=language, genre=genre)

    genre.delete()

    assert GenreTranslation.objects.count() == 0
