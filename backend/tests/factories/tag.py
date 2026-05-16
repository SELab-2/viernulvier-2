"""Factory Boy factories for tag test data."""

import factory
from factory.declarations import LazyAttribute, LazyFunction, SubFactory
from faker import Faker

from apps.tags.models import Tag, TagTranslation
from tests.factories.language import LanguageFactory

faker = Faker()

# ==============================
# TAG
# ==============================


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    url = LazyFunction(faker.url)
    source = LazyFunction(faker.word)
    is_enabled = LazyFunction(lambda: faker.boolean(chance_of_getting_true=90))
    type = LazyFunction(faker.word)


# ==============================
# TAG TRANSLATION
# ==============================


class TagTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TagTranslation

    tag = SubFactory(TagFactory)
    language = SubFactory(LanguageFactory)

    name = LazyAttribute(lambda o: f"{faker.word().capitalize()} ({o.language.code})")

    excerpt = LazyFunction(faker.sentence)

    short_description = LazyFunction(faker.sentence)

    url_title = LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))
