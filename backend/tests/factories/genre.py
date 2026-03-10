import factory
from faker import Faker

from apps.genres.models import Genre, GenreTranslation, GenreUseAs
from tests.factories.language import LanguageFactory

faker = Faker()


class GenreUseAsFactory(factory.django.DjangoModelFactory):
    """Factory for GenreUseAs model."""

    class Meta:
        model = GenreUseAs

    name = factory.Sequence(lambda n: f"type_{n}")


class GenreFactory(factory.django.DjangoModelFactory):
    """Factory for Genre model."""

    class Meta:
        model = Genre

    type = factory.Sequence(lambda n: f"Genre_{n}")  # Unique type for each instance
    use_as = factory.SubFactory(GenreUseAsFactory)


class GenreTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GenreTranslation

    name = factory.LazyAttribute(lambda _: faker.word())  # Random name for the translation
    language = factory.SubFactory(LanguageFactory)
    genre = factory.SubFactory(GenreFactory)
