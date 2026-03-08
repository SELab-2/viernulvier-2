from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.productions.admin import ProductionAdmin
from apps.productions.admin_filters import ArtistNameFilter, GenreFilter, TagFilter
from apps.productions.models import Production
from tests.factories.genre import GenreFactory, GenreTranslationFactory
from tests.factories.language import LanguageFactory
from tests.factories.production import ProductionFactory, ProductionTranslationFactory
from tests.factories.tag import TagFactory, TagTranslationFactory


class TestProductionAdminFilters(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = ProductionAdmin(Production, admin.site)
        self.language = LanguageFactory(code="nl", name="Dutch")

        self.production_1 = ProductionFactory()
        self.production_2 = ProductionFactory()
        self.production_3 = ProductionFactory()

        self.tag_theater = TagFactory(type="theater")
        self.tag_family = TagFactory(type="family")
        self.tag_music = TagFactory(type="music")
        TagTranslationFactory(tag=self.tag_theater, language=self.language, name="Theater")
        TagTranslationFactory(tag=self.tag_family, language=self.language, name="Familie")

        self.genre_dance = GenreFactory(type="dance")
        self.genre_jazz = GenreFactory(type="jazz")
        self.genre_rock = GenreFactory(type="rock")
        GenreTranslationFactory(genre=self.genre_dance, language=self.language, name="Dans")
        GenreTranslationFactory(genre=self.genre_jazz, language=self.language, name="Jazz")

        self.production_1.tags.add(self.tag_theater, self.tag_family)
        self.production_2.tags.add(self.tag_theater)
        self.production_3.tags.add(self.tag_music)

        self.production_1.genres.add(self.genre_dance, through_defaults={"position": 1})
        self.production_1.genres.add(self.genre_jazz, through_defaults={"position": 2})
        self.production_2.genres.add(self.genre_dance, through_defaults={"position": 1})
        self.production_3.genres.add(self.genre_rock, through_defaults={"position": 1})

        ProductionTranslationFactory(production=self.production_1, language=self.language, artist_name="John Doe")
        ProductionTranslationFactory(production=self.production_2, language=LanguageFactory(code="en", name="English"), artist_name="Jane Doe")
        ProductionTranslationFactory(production=self.production_3, language=LanguageFactory(code="fr", name="French"), artist_name="John Doe")

    def _build_filter(self, filter_class, query_string):
        request = self.factory.get(f"/admin/productions/production/?{query_string}")
        params = request.GET.copy()
        return filter_class(request, params, Production, self.admin)

    def test_tag_filter_uses_and_semantics_for_multiple_selected_tags(self):
        filter_instance = self._build_filter(
            TagFilter,
            f"tag={self.tag_theater.pk}&tag={self.tag_family.pk}",
        )
        queryset = filter_instance.queryset(filter_instance.request, Production.objects.order_by("id"))
        self.assertEqual(list(queryset.values_list("id", flat=True)), [self.production_1.id])

    def test_genre_filter_uses_and_semantics_for_multiple_selected_genres(self):
        filter_instance = self._build_filter(
            GenreFilter,
            f"genre={self.genre_dance.pk}&genre={self.genre_jazz.pk}",
        )
        queryset = filter_instance.queryset(filter_instance.request, Production.objects.order_by("id"))
        self.assertEqual(list(queryset.values_list("id", flat=True)), [self.production_1.id])

    def test_artist_name_filter_uses_or_semantics(self):
        filter_instance = self._build_filter(
            ArtistNameFilter,
            "artist_name=John+Doe&artist_name=Jane+Doe",
        )
        queryset = filter_instance.queryset(filter_instance.request, Production.objects.order_by("id"))
        self.assertEqual(
            set(queryset.values_list("id", flat=True)),
            {self.production_1.id, self.production_2.id, self.production_3.id},
        )

    def test_tag_filter_search_includes_selected_value_outside_search_result(self):
        filter_instance = self._build_filter(
            TagFilter,
            f"tag={self.tag_music.pk}&tag_q=thea",
        )
        option_values = {value for value, _ in filter_instance.lookups(filter_instance.request, self.admin)}
        self.assertIn(str(self.tag_theater.pk), option_values)
        self.assertIn(str(self.tag_music.pk), option_values)

    def test_tag_filter_search_without_selected_values_filters_by_search_only(self):
        filter_instance = self._build_filter(TagFilter, "tag_q=thea")
        option_values = [value for value, _ in filter_instance.lookups(filter_instance.request, self.admin)]
        self.assertEqual(option_values, [str(self.tag_theater.pk)])

    def test_genre_filter_search_matches_translation_names(self):
        filter_instance = self._build_filter(GenreFilter, "genre_q=dans")
        option_values = {value for value, _ in filter_instance.lookups(filter_instance.request, self.admin)}
        self.assertIn(str(self.genre_dance.pk), option_values)

    def test_genre_filter_search_includes_selected_value_outside_search_result(self):
        filter_instance = self._build_filter(
            GenreFilter,
            f"genre={self.genre_rock.pk}&genre_q=dans",
        )
        option_values = {value for value, _ in filter_instance.lookups(filter_instance.request, self.admin)}
        self.assertIn(str(self.genre_dance.pk), option_values)
        self.assertIn(str(self.genre_rock.pk), option_values)

    def test_artist_name_filter_search_limits_options(self):
        filter_instance = self._build_filter(ArtistNameFilter, "artist_name_q=jane")
        option_values = [value for value, _ in filter_instance.lookups(filter_instance.request, self.admin)]
        self.assertEqual(option_values, ["Jane Doe"])

    def test_artist_name_filter_keeps_selected_values_not_in_search_results(self):
        filter_instance = self._build_filter(
            ArtistNameFilter,
            "artist_name=Zed+Artist&artist_name_q=jane",
        )
        option_values = [value for value, _ in filter_instance.lookups(filter_instance.request, self.admin)]
        self.assertEqual(option_values, ["Jane Doe", "Zed Artist"])

    def test_tag_filter_uses_non_empty_label_when_type_is_blank(self):
        tag_without_type = TagFactory(type="")
        TagTranslationFactory(tag=tag_without_type, language=self.language, name="Zonder type")

        filter_instance = self._build_filter(TagFilter, "")
        lookup_map = dict(filter_instance.lookups(filter_instance.request, self.admin))

        self.assertEqual(lookup_map[str(tag_without_type.pk)], "Zonder type")
