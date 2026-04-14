from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.blogs.models import BlogTranslation
from tests.factories.blog import BlogFactory, BlogTranslationFactory
from tests.factories.language import LanguageFactory
from tests.factories.production import ProductionFactory

pytestmark = pytest.mark.django_db


class TestBlog:
    def test_requires_slug(self) -> None:
        blog = BlogFactory.build(slug="")

        with pytest.raises(ValidationError):
            blog.full_clean()

    def test_str_uses_translation_if_available(self) -> None:
        blog = BlogFactory(slug="my-slug")
        BlogTranslationFactory(blog=blog, language__code="nl", title="My Blog Title")

        assert str(blog) == "My Blog Title"

    def test_str_falls_back_to_slug_without_translation(self) -> None:
        blog = BlogFactory(slug="fallback-slug")

        assert str(blog) == "fallback-slug"

    def test_delete_cascades_to_translations(self) -> None:
        blog = BlogFactory()
        BlogTranslationFactory.create_batch(2, blog=blog)

        blog.delete()

        assert BlogTranslation.objects.count() == 0

    def test_reverse_relation_from_production(self) -> None:
        production = ProductionFactory()
        blog = BlogFactory()
        blog.productions.add(production)

        assert production.blogs.count() == 1

    def test_cover_image_rejects_non_image_upload(self) -> None:
        blog = BlogFactory.build(
            cover_image=SimpleUploadedFile(
                "brochure.pdf",
                b"%PDF-1.7",
                content_type="application/pdf",
            )
        )

        with pytest.raises(ValidationError):
            blog.full_clean()


class TestBlogTranslation:
    def test_str_representation(self) -> None:
        translation = BlogTranslationFactory(language__code="en", title="A title")

        assert str(translation) == "en - A title"

    def test_language_reverse_relation(self) -> None:
        language = LanguageFactory(code="nl")
        BlogTranslationFactory.create_batch(2, language=language)

        assert language.blog_translations.count() == 2
