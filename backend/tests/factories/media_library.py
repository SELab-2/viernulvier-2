import factory
from faker import Faker
from apps.media_library.models import (
    MediaGallery,
    MediaItem,
    MediaItemTranslation,
    MediaItemCrop,
)
from tests.factories.language import LanguageFactory

faker = Faker()


class MediaGalleryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MediaGallery

    name = factory.Sequence(lambda n: f"Gallery_{n}")


class MediaItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MediaItem

    gallery = factory.SubFactory(MediaGalleryFactory)
    type = MediaItem.MediaItemType.IMAGE
    format = "jpg"
    original_filename = factory.LazyAttribute(lambda _: faker.file_name())
    position = factory.Sequence(lambda n: n)


class MediaItemTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MediaItemTranslation

    media_item = factory.SubFactory(MediaItemFactory)
    language = factory.SubFactory(LanguageFactory)
    title = factory.LazyAttribute(lambda _: faker.word())
    description = factory.LazyAttribute(lambda _: faker.sentence())
    credits = factory.LazyAttribute(lambda _: faker.name())
    link = factory.LazyAttribute(lambda _: faker.url())


class MediaItemCropFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MediaItemCrop

    media_item = factory.SubFactory(MediaItemFactory)
    name = factory.Sequence(lambda n: f"crop_{n}")
    url = factory.LazyAttribute(lambda _: faker.url())
