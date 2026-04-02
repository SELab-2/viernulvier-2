from django.db.models import Q

from apps.core.admin_filters import SearchableMultiSelectFilter
from apps.genres.models import Genre
from apps.tags.models import Tag

from .models import ProductionTranslation


class TagFilter(SearchableMultiSelectFilter):
    """Searchable multi-select filter for Production tags.

    Behavior
    --------
    - Options are loaded from ``Tag``.
    - Option search matches both ``Tag.type`` and translated names.
    - Queryset filtering uses AND semantics: selecting multiple tags returns
      productions that contain *all* selected tags.
    """

    title = "Tags"
    parameter_name = "tag"
    search_param = "tag_q"

    def get_option_queryset(self) -> list[tuple[str, str]]:
        """Return tag options as ``(id, label)`` tuples for the filter UI."""
        tags = Tag.objects.prefetch_related("translations")
        if self.search_value:
            search_q = Q(type__icontains=self.search_value) | Q(translations__name__icontains=self.search_value)
            tags = tags.filter(search_q | Q(id__in=self.selected_values)) if self.selected_values else tags.filter(search_q)
        tags = tags.distinct().order_by("type", "id")
        return [(str(tag.pk), tag.type.strip() or str(tag)) for tag in tags]

    def filter_queryset(self, queryset: Q) -> Q:
        """Apply selected tags to queryset using cumulative AND filters."""
        filtered = queryset
        for tag_id in self.selected_values:
            filtered = filtered.filter(tags__id=tag_id)
        return filtered.distinct()


class GenreFilter(SearchableMultiSelectFilter):
    """Searchable multi-select filter for Production genres.

    Behavior mirrors :class:`TagFilter`:
    - Search in ``Genre.type`` and translation names.
    - Multiple selected genres are combined with AND semantics.
      so return productions that have *all* selected genres.
    """

    title = "Genres"
    parameter_name = "genre"
    search_param = "genre_q"

    @staticmethod
    def _genre_label(genre: Genre) -> str:
        """Return the label exactly as the model exposes it via ``__str__``."""
        return str(genre)

    @staticmethod
    def _genre_search_text(genre: Genre) -> str:
        """Return only the human-readable part used for searching."""
        return genre.get_base_display_name(related_name="translations", fallback="") or ""

    def get_option_queryset(self) -> list[tuple[str, str]]:
        """Return genre options as ``(id, label)`` tuples."""
        genres = list(Genre.objects.prefetch_related("translations").order_by("type", "id"))
        if self.search_value:
            search_term = self.search_value.lower()
            selected_ids = set(self.selected_values)
            genres = [
                genre
                for genre in genres
                if search_term in self._genre_search_text(genre).lower() or str(genre.pk) in selected_ids
            ]

        return [(str(genre.pk), self._genre_label(genre)) for genre in genres]

    def filter_queryset(self, queryset: Q) -> Q:
        """Apply selected genres with cumulative AND semantics."""
        filtered = queryset
        for genre_id in self.selected_values:
            filtered = filtered.filter(genres__id=genre_id)
        return filtered.distinct()


class ArtistNameFilter(SearchableMultiSelectFilter):
    """Searchable multi-select filter for translation artist names.

    Data source
    -----------
    Options come from ``ProductionTranslation.artist_name`` (non-empty values).

    Filtering semantics
    -------------------
    Uses OR semantics via ``__in``: selecting multiple artist names returns
    productions with any translation matching one of those names.
    """

    title = "Artist name"
    parameter_name = "artist_name"
    search_param = "artist_name_q"

    def get_option_queryset(self) -> list[tuple[str, str]]:
        """Return artist-name options as ``(value, label)`` tuples."""
        names = (
            ProductionTranslation.objects.exclude(artist_name="")
            .values_list("artist_name", flat=True)
            .distinct()
            .order_by("artist_name")
        )

        if self.search_value:
            names = names.filter(artist_name__icontains=self.search_value)

        name_values = list(names)
        if self.selected_values:
            name_values = sorted(set(name_values) | set(self.selected_values), key=str.lower)

        return [(name, name) for name in name_values]

    def filter_queryset(self, queryset: Q) -> Q:
        """Filter productions by selected artist names (OR semantics)."""
        return queryset.filter(translations__artist_name__in=self.selected_values).distinct()
