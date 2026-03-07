from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from apps.productions.admin import ProductionAdmin
from apps.productions.models import Production, ProductionGenre
from tests.factories.genre import GenreFactory
from tests.factories.production import ProductionFactory
from tests.factories.tag import TagFactory


class TestProductionAdminActions(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = ProductionAdmin(Production, admin.site)
        self.production_1 = ProductionFactory()
        self.production_2 = ProductionFactory()

    def _request_with_messages(self, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data or {})
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        request.user = AnonymousUser()
        return request

    def test_add_tag_action_apply_adds_selected_tag_to_all_selected_productions(self):
        tag = TagFactory(type="festival")
        self.production_1.tags.add(tag)

        request = self._request_with_messages(
            "post",
            "/admin/productions/production/",
            data={
                "apply": "1",
                "action": "add_tag_to_selected_productions",
                "tag": str(tag.pk),
                ACTION_CHECKBOX_NAME: [str(self.production_1.pk), str(self.production_2.pk)],
            },
        )

        response = self.admin.add_tag_to_selected_productions(request, Production.objects.none())

        self.assertIsNone(response)
        self.assertEqual(
            Production.tags.through.objects.filter(tag_id=tag.pk).count(),
            2,
        )

    def test_add_genre_action_apply_skips_existing_links_and_sets_next_position(self):
        target_genre = GenreFactory(type="target")
        other_genre = GenreFactory(type="other")

        ProductionGenre.objects.create(
            production=self.production_1,
            genre=target_genre,
            position=2,
        )
        ProductionGenre.objects.create(
            production=self.production_2,
            genre=other_genre,
            position=4,
        )

        request = self._request_with_messages(
            "post",
            "/admin/productions/production/",
            data={
                "apply": "1",
                "action": "add_genre_to_selected_productions",
                "genre": str(target_genre.pk),
                ACTION_CHECKBOX_NAME: [str(self.production_1.pk), str(self.production_2.pk)],
            },
        )

        response = self.admin.add_genre_to_selected_productions(request, Production.objects.none())

        self.assertIsNone(response)
        self.assertEqual(
            ProductionGenre.objects.filter(production=self.production_1, genre=target_genre).count(),
            1,
        )

        created_link = ProductionGenre.objects.get(production=self.production_2, genre=target_genre)
        self.assertEqual(created_link.position, 5)

    def test_add_tag_action_initial_step_returns_two_step_page(self):
        request = self._request_with_messages("get", "/admin/productions/production/")
        queryset = Production.objects.filter(pk=self.production_1.pk)

        response = self.admin.add_tag_to_selected_productions(request, queryset)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "admin/two_step_action.html")
