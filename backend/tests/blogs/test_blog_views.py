from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tests.factories.blog import BlogFactory, BlogTranslationFactory
from tests.factories.language import LanguageFactory
from tests.factories.production import ProductionFactory, ProductionTranslationFactory

PUB_KEY = "pub-blog-test-key"
INT_KEY = "int-blog-test-key"


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def wrong_headers():
    return {"HTTP_X_API_KEY": "wrong-blog-key"}


def results_list(response):
    return response.data.get("results", response.data)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestBlogViewSet(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.language = LanguageFactory(code="en", name="English")
        self.production = ProductionFactory()
        ProductionTranslationFactory(production=self.production, language=self.language, title="Prod EN")

        self.blog = BlogFactory(slug="blog-view")
        self.blog.productions.add(self.production)
        BlogTranslationFactory(
            blog=self.blog,
            language=self.language,
            title="Blog EN",
            body="Body EN",
            excerpt="Excerpt EN",
        )

    def test_list_public_returns_200_and_body_is_present(self) -> None:
        response = self.client.get("/api/v1/blogs/", **pub_headers())

        assert response.status_code == 200
        item = results_list(response)[0]
        assert "body" in item

    def test_list_includes_nested_production_objects(self) -> None:
        response = self.client.get("/api/v1/blogs/", **pub_headers())

        assert response.status_code == 200
        item = results_list(response)[0]
        assert "productions" in item
        assert isinstance(item["productions"], list)
        assert item["productions"][0]["id"] == self.production.id

    def test_retrieve_public_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/blogs/{self.blog.id}/", **pub_headers())

        assert response.status_code == 200
        assert response.data["id"] == self.blog.id

    def test_retrieve_internal_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/blogs/{self.blog.id}/", **int_headers())

        assert response.status_code == 200

    def test_retrieve_wrong_key_returns_401(self) -> None:
        response = self.client.get(f"/api/v1/blogs/{self.blog.id}/", **wrong_headers())

        assert response.status_code == 401

    def test_create_internal_returns_201(self) -> None:
        payload = {
            "slug": "created-via-view",
            "production_ids": [self.production.id],
            "translations_data": [
                {
                    "language_id": self.language.pk,
                    "title": "Created title",
                    "body": "Created body",
                    "excerpt": "Created excerpt",
                }
            ],
        }

        response = self.client.post("/api/v1/blogs/", payload, format="json", **int_headers())

        assert response.status_code == 201

    def test_create_missing_slug_returns_422(self) -> None:
        payload = {
            "translations_data": [
                {
                    "language_id": self.language.pk,
                    "title": "Created title",
                    "body": "Created body",
                }
            ],
        }

        response = self.client.post("/api/v1/blogs/", payload, format="json", **int_headers())

        assert response.status_code == 422

    def test_create_public_denied(self) -> None:
        payload = {
            "slug": "created-public",
            "translations_data": [
                {
                    "language_id": self.language.pk,
                    "title": "Created title",
                    "body": "Created body",
                }
            ],
        }

        response = self.client.post("/api/v1/blogs/", payload, format="json", **pub_headers())

        assert response.status_code == 403

    def test_filter_by_production(self) -> None:
        other_blog = BlogFactory(slug="other-blog")
        BlogTranslationFactory(blog=other_blog, language=self.language)

        response = self.client.get("/api/v1/blogs/", {"production": self.production.id}, **pub_headers())

        assert response.status_code == 200
        items = results_list(response)
        assert len(items) == 1
        assert items[0]["id"] == self.blog.id

    def test_filter_by_slug(self) -> None:
        BlogFactory(slug="different-slug")

        response = self.client.get("/api/v1/blogs/", {"slug": "blog-view"}, **pub_headers())

        assert response.status_code == 200
        items = results_list(response)
        assert len(items) == 1
        assert items[0]["slug"] == "blog-view"

    def test_filter_by_published_false(self) -> None:
        draft = BlogFactory(slug="draft-blog", published_at=None)
        BlogTranslationFactory(blog=draft, language=self.language)

        response = self.client.get("/api/v1/blogs/", {"published": "false"}, **pub_headers())

        assert response.status_code == 200
        items = results_list(response)
        assert any(item["id"] == draft.id for item in items)

    def test_search_on_translated_title(self) -> None:
        response = self.client.get("/api/v1/blogs/", {"search": "Blog EN"}, **pub_headers())

        assert response.status_code == 200
        items = results_list(response)
        assert len(items) == 1
        assert items[0]["id"] == self.blog.id

    def test_search_on_translated_excerpt(self) -> None:
        response = self.client.get("/api/v1/blogs/", {"search": "Excerpt EN"}, **pub_headers())

        assert response.status_code == 200
        items = results_list(response)
        assert len(items) == 1
        assert items[0]["id"] == self.blog.id

    def test_ordering_by_slug(self) -> None:
        second_blog = BlogFactory(slug="aaa-blog")
        BlogTranslationFactory(blog=second_blog, language=self.language)

        response = self.client.get("/api/v1/blogs/", {"ordering": "slug"}, **pub_headers())

        assert response.status_code == 200
        items = results_list(response)
        assert items[0]["slug"] == "aaa-blog"

    def test_patch_internal_updates_slug(self) -> None:
        response = self.client.patch(
            f"/api/v1/blogs/{self.blog.id}/",
            {"slug": "blog-view-updated"},
            format="json",
            **int_headers(),
        )

        assert response.status_code == 200

    def test_patch_public_denied(self) -> None:
        response = self.client.patch(
            f"/api/v1/blogs/{self.blog.id}/",
            {"slug": "blog-view-updated"},
            format="json",
            **pub_headers(),
        )

        assert response.status_code == 403

    def test_delete_internal_returns_204(self) -> None:
        response = self.client.delete(f"/api/v1/blogs/{self.blog.id}/", **int_headers())

        assert response.status_code == 204

    def test_delete_public_denied(self) -> None:
        response = self.client.delete(f"/api/v1/blogs/{self.blog.id}/", **pub_headers())

        assert response.status_code == 403

    def test_missing_auth_returns_401(self) -> None:
        response = self.client.get("/api/v1/blogs/")

        assert response.status_code == 401

    def test_wrong_key_returns_401(self) -> None:
        response = self.client.get("/api/v1/blogs/", **wrong_headers())

        assert response.status_code == 401
