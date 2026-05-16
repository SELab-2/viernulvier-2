"""Tests for the UitDatabaseTheme-to-Genre data migration."""

import importlib
from types import SimpleNamespace

migration = importlib.import_module("apps.productions.migrations.0002_merge_uitdatabank_theme_into_genre")


class QuerySetStub:
    """Minimal queryset-like object for migration unit tests."""

    def __init__(self, items):
        self.items = list(items)

    def iterator(self):
        return iter(self.items)

    def first(self):
        return self.items[0] if self.items else None

    def order_by(self, *_args):
        return self

    def values_list(self, *_args, **_kwargs):
        return self

    def only(self, *_args):
        return self

    def exists(self):
        return bool(self.items)


class RecordingGenre(SimpleNamespace):
    """Small mutable object that records save(update_fields=...)."""

    def save(self, update_fields=None):
        self.saved_update_fields = update_fields


class GenreUseAsManager:
    def __init__(self):
        self.obj = SimpleNamespace(pk=501, name="genre")

    def get_or_create(self, **kwargs):
        self.last_kwargs = kwargs
        return self.obj, True


class LanguageManager:
    def __init__(self, languages):
        self.languages = languages

    def filter(self, **kwargs):
        code = kwargs.get("code")
        return QuerySetStub([language for language in self.languages if language.code == code])

    def first(self):
        return self.languages[0] if self.languages else None


class ThemeManager:
    def __init__(self, themes):
        self.themes = themes

    def all(self):
        return QuerySetStub(self.themes)


class GenreManager:
    def __init__(self, existing_by_external_id=None):
        self.existing_by_external_id = existing_by_external_id or {}
        self.created = []
        self.next_pk = 1000

    def get_or_create(self, external_id, defaults):
        if external_id in self.existing_by_external_id:
            return self.existing_by_external_id[external_id], False

        genre = RecordingGenre(pk=self.next_pk, external_id=external_id, **defaults)
        self.next_pk += 1
        self.created.append(genre)
        self.existing_by_external_id[external_id] = genre
        return genre, True


class GenreTranslationManager:
    def __init__(self):
        self.calls = []

    def get_or_create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(pk=len(self.calls)), True


class ProductionManager:
    def __init__(self, productions):
        self.productions = productions

    def exclude(self, **kwargs):
        assert kwargs == {"uit_database_theme_id__isnull": True}
        return QuerySetStub([p for p in self.productions if p.uit_database_theme_id is not None])


class ProductionGenreManager:
    def __init__(self, *, existing_links=None, positions_by_production=None):
        self.existing_links = set(existing_links or [])
        self.positions_by_production = positions_by_production or {}
        self.created = []
        self._last_filter = {}

    def filter(self, **kwargs):
        self._last_filter = kwargs
        if "genre_id" in kwargs:
            exists = (kwargs["production_id"], kwargs["genre_id"]) in self.existing_links
            return QuerySetStub([SimpleNamespace()] if exists else [])

        positions = sorted(self.positions_by_production.get(kwargs["production_id"], []), reverse=True)
        return QuerySetStub(positions)

    def create(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace(**kwargs)


class FakeApps:
    def __init__(self, mapping):
        self.mapping = mapping

    def get_model(self, app_label, model_name):
        return self.mapping[(app_label, model_name)]


def _model(manager):
    return SimpleNamespace(objects=manager)


def test_forwards_merge_creates_genres_translations_and_production_links() -> None:
    language = SimpleNamespace(pk=10, code="nl")
    theme_without_external_id = SimpleNamespace(pk=1, external_id="", name="Theme A")
    theme_with_existing_genre = SimpleNamespace(pk=2, external_id="/api/v1/themes/2", name="Theme B")

    existing_genre = RecordingGenre(
        pk=202,
        external_id="/api/v1/themes/2",
        type="uitdatabank_theme",
        use_as_id=None,
        vendor_id="",
    )
    genre_manager = GenreManager(existing_by_external_id={"/api/v1/themes/2": existing_genre})
    translation_manager = GenreTranslationManager()
    production_genre_manager = ProductionGenreManager(
        existing_links={(22, 202)},
        positions_by_production={11: [1, 2]},
    )

    production_with_new_link = SimpleNamespace(pk=11, uit_database_theme_id=1)
    production_with_existing_link = SimpleNamespace(pk=22, uit_database_theme_id=2)
    production_with_unknown_theme = SimpleNamespace(pk=33, uit_database_theme_id=999)

    apps = FakeApps(
        {
            ("productions", "Production"): _model(
                ProductionManager(
                    [
                        production_with_new_link,
                        production_with_existing_link,
                        production_with_unknown_theme,
                    ]
                )
            ),
            ("productions", "ProductionGenre"): _model(production_genre_manager),
            ("productions", "UitDatabaseTheme"): _model(
                ThemeManager([theme_without_external_id, theme_with_existing_genre])
            ),
            ("genres", "Genre"): _model(genre_manager),
            ("genres", "GenreUseAs"): _model(GenreUseAsManager()),
            ("genres", "GenreTranslation"): _model(translation_manager),
            ("languages", "Language"): _model(LanguageManager([language])),
        }
    )

    migration._forwards_merge_theme_into_genres(apps, None)

    assert genre_manager.created[0].external_id == "/legacy/uitdatabank/themes/1"
    assert genre_manager.created[0].type == "uitdatabank_theme"
    assert genre_manager.created[0].use_as_id == 501
    assert genre_manager.created[0].vendor_id == "Theme A"

    assert existing_genre.vendor_id == "Theme B"
    assert existing_genre.saved_update_fields == ["vendor_id"]

    assert translation_manager.calls == [
        {
            "genre_id": genre_manager.created[0].pk,
            "language_id": language.pk,
            "defaults": {"name": "Theme A"},
        },
        {
            "genre_id": existing_genre.pk,
            "language_id": language.pk,
            "defaults": {"name": "Theme B"},
        },
    ]
    assert production_genre_manager.created == [
        {
            "production_id": production_with_new_link.pk,
            "genre_id": genre_manager.created[0].pk,
            "position": 3,
        }
    ]


def test_forwards_merge_returns_early_when_there_are_no_themes() -> None:
    production_genre_manager = ProductionGenreManager()
    apps = FakeApps(
        {
            ("productions", "Production"): _model(ProductionManager([SimpleNamespace(pk=1, uit_database_theme_id=1)])),
            ("productions", "ProductionGenre"): _model(production_genre_manager),
            ("productions", "UitDatabaseTheme"): _model(ThemeManager([])),
            ("genres", "Genre"): _model(GenreManager()),
            ("genres", "GenreUseAs"): _model(GenreUseAsManager()),
            ("genres", "GenreTranslation"): _model(GenreTranslationManager()),
            ("languages", "Language"): _model(LanguageManager([])),
        }
    )

    migration._forwards_merge_theme_into_genres(apps, None)

    assert production_genre_manager.created == []


def test_backwards_noop_returns_none() -> None:
    assert migration._backwards_noop(None, None) is None
