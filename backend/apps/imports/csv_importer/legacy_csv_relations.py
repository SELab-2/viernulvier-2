"""Model relation helpers for legacy CSV imports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.text import slugify

from apps.genres.models import Genre, GenreTranslation
from apps.languages.models import Language
from apps.locations.models import Hall, HallTranslation
from apps.productions.models import ProductionGenre

from .legacy_csv_constants import LEGACY_LANGUAGE_ACTIVE, LEGACY_LANGUAGE_CODE, LEGACY_LANGUAGE_NAME

if TYPE_CHECKING:
    from apps.productions.models import Production


def _ensure_language() -> Language:
    """Get or create the language used for legacy CSV imports.

    Returns:
        The Language object for the legacy CSV language.
    """
    language, _ = Language.objects.get_or_create(
        code=LEGACY_LANGUAGE_CODE,
        defaults={"name": LEGACY_LANGUAGE_NAME, "is_active": LEGACY_LANGUAGE_ACTIVE},
    )
    return language


def _ensure_genre(label: str, language: Language) -> Genre:
    """Get or create a genre with a translation for the given language.

    Args:
        label: The name or label of the genre.
        language: The Language object to associate with the genre translation.

    Returns:
        The Genre object, either existing or newly created.
    """
    genre_type = slugify(label)[:50] or label.strip().lower().replace(" ", "_")[:50] or "genre"

    translation = (
        GenreTranslation.objects.select_related("genre")
        .filter(language=language, name=label[:50])
        .order_by("genre_id")
        .first()
    )
    if translation:
        return translation.genre

    genre = Genre.objects.filter(type=genre_type).order_by("id").first()
    if genre is None:
        genre = Genre.objects.create(type=genre_type)

    GenreTranslation.objects.update_or_create(genre=genre, language=language, defaults={"name": label[:50]})
    return genre


def _sync_production_genres(production: Production, genre_labels: list[str], language: Language) -> None:
    """Synchronize genres for a production, replacing existing genre associations.

    Args:
        production: The Production object to update.
        genre_labels: List of genre labels to associate with the production.
        language: The Language object for genre translations.
    """
    ProductionGenre.objects.filter(production=production).delete()
    links = []
    for position, label in enumerate(genre_labels):
        genre = _ensure_genre(label, language)
        links.append(ProductionGenre(production=production, genre=genre, position=position))
    if links:
        ProductionGenre.objects.bulk_create(links)


def _hall_for_name(name: str, language: Language) -> Hall | None:
    """Get or create a hall for the given name in the specified language.

    Args:
        name: The name of the hall.
        language: The Language object for the hall translation.

    Returns:
        The Hall object if name is not empty, None otherwise.
    """
    if not name:
        return None

    translation = HallTranslation.objects.select_related("hall").filter(name=name).first()
    if translation:
        return translation.hall

    hall = Hall.objects.create(space=None, seat_selection=False, open_seating=False)
    HallTranslation.objects.create(hall=hall, language=language, name=name)
    return hall
