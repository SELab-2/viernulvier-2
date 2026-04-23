from django.utils import timezone
import factory
from factory.declarations import LazyFunction, Sequence, SubFactory
from faker import Faker

from apps.blogs.models import Blog, BlogTranslation
from tests.factories.language import LanguageFactory

faker = Faker()


class BlogFactory(factory.django.DjangoModelFactory):
    """Factory for Blog model."""

    class Meta:
        model = Blog

    slug = Sequence(lambda n: f"blog-post-{n}")
    published_at = LazyFunction(timezone.now)


class BlogTranslationFactory(factory.django.DjangoModelFactory):
    """Factory for BlogTranslation model."""

    class Meta:
        model = BlogTranslation

    blog = SubFactory(BlogFactory)
    language = SubFactory(LanguageFactory)
    title = LazyFunction(lambda: faker.sentence(nb_words=5))
    body = LazyFunction(lambda: faker.text(max_nb_chars=300))
    excerpt = LazyFunction(lambda: faker.sentence(nb_words=12))
