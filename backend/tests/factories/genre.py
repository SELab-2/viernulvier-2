import factory
from faker import Faker

from apps.genres.models import Genre, GenreTranslation
from tests.factories.language import LanguageFactory

faker = Faker()


class GenreFactory(factory.django.DjangoModelFactory):
    """Factory for Genre model."""

    class Meta:
        model = Genre

    type = factory.Sequence(lambda n: f"Genre_{n}")  # Unique type for each instance


class GenreTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GenreTranslation

    name = factory.LazyAttribute(lambda _: faker.word())  # Random name for the translation
    language = factory.SubFactory(LanguageFactory)
    genre = factory.SubFactory(GenreFactory)
