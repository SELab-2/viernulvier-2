import factory
from faker import Faker
from apps.pricing.models import Price, PriceTranslation, PriceRank, PriceRankTranslation
from tests.factories.language import LanguageFactory

faker = Faker()


class PriceFactory(factory.django.DjangoModelFactory):
    """Factory for Price model."""
    class Meta:
        model = Price

    type = factory.Sequence(lambda n: f"price_type_{n}")
    visibility = factory.Iterator(["public", "hidden", "members"])
    membership = factory.Iterator(["", "member", "vip"])
    minimum = None
    maximum = None
    step = None
    sort_order = factory.Sequence(lambda n: n)
    cineville_box = False


class PriceTranslationFactory(factory.django.DjangoModelFactory):
    """Factory for PriceTranslation model."""
    class Meta:
        model = PriceTranslation

    price = factory.SubFactory(PriceFactory)
    language = factory.SubFactory(LanguageFactory)
    description = factory.LazyAttribute(lambda _: faker.sentence(nb_words=6))


class PriceRankFactory(factory.django.DjangoModelFactory):
    """Factory for PriceRank model."""
    class Meta:
        model = PriceRank

    position = factory.Faker('random_int', min=0, max=10)
    sold_out_buffer = factory.Faker('random_int', min=0, max=10)


class PriceRankTranslationFactory(factory.django.DjangoModelFactory):
    """Factory for PriceRankTranslation model."""
    class Meta:
        model = PriceRankTranslation

    price_rank = factory.SubFactory(PriceRankFactory)
    language = factory.SubFactory(LanguageFactory)
    description = factory.LazyAttribute(lambda _: faker.sentence(nb_words=6))