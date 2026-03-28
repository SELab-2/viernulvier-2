import factory
from factory.declarations import LazyFunction, SubFactory
from faker import Faker

from apps.productions.models import (
    Production,
    ProductionGenre,
    ProductionTag,
    ProductionTagTranslation,
    ProductionTranslation,
    UitDatabaseTheme,
    UitDatabaseType,
)
from tests.factories.genre import GenreFactory
from tests.factories.language import LanguageFactory
from tests.factories.media_library import MediaGalleryFactory
from tests.factories.tag import TagFactory

faker = Faker()


class UitDatabaseThemeFactory(factory.django.DjangoModelFactory):
    """Factory for UitDatabaseTheme model."""

    class Meta:
        model = UitDatabaseTheme

    name = LazyFunction(lambda: faker.word())


class UitDatabaseTypeFactory(factory.django.DjangoModelFactory):
    """Factory for UitDatabaseType model."""

    class Meta:
        model = UitDatabaseType

    name = LazyFunction(lambda: faker.word())


class ProductionFactory(factory.django.DjangoModelFactory):
    """Factory for Production model."""

    class Meta:
        model = Production

    uit_database_theme = SubFactory(UitDatabaseThemeFactory)
    uit_database_type = SubFactory(UitDatabaseTypeFactory)
    media_gallery = SubFactory(MediaGalleryFactory)
    attendance_mode = LazyFunction(lambda: faker.random_element([choice[0] for choice in Production.AttendanceMode.choices]))
    performer_type = LazyFunction(lambda: faker.random_element([choice[0] for choice in Production.PerformerType.choices]))


class ProductionTranslationFactory(factory.django.DjangoModelFactory):
    """Factory for ProductionTranslation model."""

    class Meta:
        model = ProductionTranslation

    production = SubFactory(ProductionFactory)
    language = SubFactory(LanguageFactory)
    supertitle = LazyFunction(lambda: faker.sentence(nb_words=3))
    title = LazyFunction(lambda: faker.sentence(nb_words=4))
    artist_name = LazyFunction(lambda: faker.name())
    tagline = LazyFunction(lambda: faker.sentence(nb_words=6))
    teaser = LazyFunction(lambda: faker.text(max_nb_chars=120))
    description = LazyFunction(lambda: faker.text(max_nb_chars=240))
    description_short = LazyFunction(lambda: faker.text(max_nb_chars=80))
    description_extra = LazyFunction(lambda: faker.text(max_nb_chars=160))
    description_2 = LazyFunction(lambda: faker.text(max_nb_chars=160))
    video_1 = LazyFunction(lambda: faker.url())
    video_2 = LazyFunction(lambda: faker.url())
    meta_title = LazyFunction(lambda: faker.sentence(nb_words=5))
    meta_description = LazyFunction(lambda: faker.text(max_nb_chars=150))


class ProductionTagFactory(factory.django.DjangoModelFactory):
    """Factory for ProductionTag model."""

    class Meta:
        model = ProductionTag

    production = SubFactory(ProductionFactory)
    tag = SubFactory(TagFactory)


class ProductionTagTranslationFactory(factory.django.DjangoModelFactory):
    """Factory for ProductionTagTranslation model."""

    class Meta:
        model = ProductionTagTranslation

    production_tag = SubFactory(ProductionTagFactory)
    language = SubFactory(LanguageFactory)
    description = LazyFunction(lambda: faker.text(max_nb_chars=1000))


class ProductionGenreFactory(factory.django.DjangoModelFactory):
    """Factory for ProductionGenre model."""

    class Meta:
        model = ProductionGenre

    production = SubFactory(ProductionFactory)
    genre = SubFactory(GenreFactory)
    position = LazyFunction(lambda: faker.random_int(min=0, max=50))
