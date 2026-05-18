"""Factory Boy factories for language test data."""

import factory
from faker import Faker

from apps.languages.models import Language

faker = Faker()


class LanguageFactory(factory.django.DjangoModelFactory):
    """Factory for Language model."""

    class Meta:
        model = Language

    # Keep a small deterministic language set; override code=... in tests that need unique values.
    code = factory.Iterator(["nl", "en", "de", "fr"])  # Repeatable codes for testing
    name = factory.LazyAttribute(
        lambda o: {"nl": "Dutch", "en": "English", "de": "German", "fr": "French"}.get(o.code)
    )  # So we get consistent names for the codes
    is_active = True
