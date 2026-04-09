from django.test import TestCase
import pytest

from apps.blogs.models import BlogTranslation
from apps.blogs.serializers import BlogSerializer
from apps.languages.models import Language
from tests.factories.blog import BlogFactory, BlogTranslationFactory
from tests.factories.language import LanguageFactory
from tests.factories.production import ProductionFactory, ProductionTranslationFactory


class TestBlogSerializer(TestCase):
    def setUp(self) -> None:
        self.lang_en = LanguageFactory(code="en", name="English")
        self.production = ProductionFactory()
        ProductionTranslationFactory(production=self.production, language=self.lang_en, title="Production EN")

    def test_serialization_includes_body_and_nested_productions(self) -> None:
        blog = BlogFactory(slug="blog-1")
        blog.productions.add(self.production)
        BlogTranslationFactory(blog=blog, language=self.lang_en, title="Blog EN", body="Body EN", excerpt="Ex EN")

        data = BlogSerializer(blog).data

        assert "body" in data
        assert "productions" in data
        assert isinstance(data["productions"], list)
        assert len(data["productions"]) == 1
        assert data["productions"][0]["id"] == self.production.id

    def test_create_with_production_ids_and_translations_data(self) -> None:
        payload = {
            "slug": "new-blog",
            "production_ids": [self.production.id],
            "translations_data": [
                {
                    "language_id": self.lang_en.pk,
                    "title": "New title",
                    "body": "New body",
                    "excerpt": "New excerpt",
                }
            ],
        }

        serializer = BlogSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors
        blog = serializer.save()

        assert blog.productions.count() == 1
        assert blog.productions.first().id == self.production.id
        assert blog.translations.count() == 1
        assert blog.translations.first().title == "New title"

    def test_update_replaces_translations_when_translations_data_is_provided(self) -> None:
        blog = BlogFactory(slug="replace-translations")
        BlogTranslationFactory(blog=blog, language=self.lang_en, title="Old", body="Old body", excerpt="Old ex")

        payload = {
            "translations_data": [
                {
                    "language_id": self.lang_en.pk,
                    "title": "Updated",
                    "body": "Updated body",
                    "excerpt": "Updated ex",
                }
            ]
        }

        serializer = BlogSerializer(instance=blog, data=payload, partial=True)

        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        assert BlogTranslation.objects.filter(blog=updated).count() == 1
        assert updated.translations.first().title == "Updated"

    def test_update_keeps_translations_when_translations_data_missing(self) -> None:
        blog = BlogFactory(slug="keep-translations")
        BlogTranslationFactory(blog=blog, language=self.lang_en, title="Keep", body="Keep body", excerpt="Keep ex")

        serializer = BlogSerializer(instance=blog, data={"slug": "keep-translations-updated"}, partial=True)

        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        assert updated.translations.count() == 1
        assert updated.translations.first().title == "Keep"

    def test_create_with_invalid_production_id_is_invalid(self) -> None:
        payload = {
            "slug": "invalid-prod",
            "production_ids": [999999],
            "translations_data": [
                {
                    "language_id": self.lang_en.pk,
                    "title": "Title",
                    "body": "Body",
                }
            ],
        }

        serializer = BlogSerializer(data=payload)

        assert not serializer.is_valid()
        assert "production_ids" in serializer.errors

    def test_create_with_invalid_language_id_is_invalid(self) -> None:
        payload = {
            "slug": "invalid-lang",
            "translations_data": [
                {
                    "language_id": 999999,
                    "title": "Title",
                    "body": "Body",
                }
            ],
        }

        serializer = BlogSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors
        with pytest.raises(Language.DoesNotExist):
            serializer.save()
