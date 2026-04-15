from unittest.mock import Mock

from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from apps.core.admin import BaseAdmin, TwoStepBulkActionMixin
from apps.productions.models import Production
from tests.factories.production import ProductionFactory


class _DummyTwoStepAdmin(TwoStepBulkActionMixin, BaseAdmin):
    pass


class DummyForm(forms.Form):
    note = forms.CharField(required=False)


class RequiredFieldForm(forms.Form):
    note = forms.CharField(required=True)


class TestTwoStepBulkActionMixin(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.admin = _DummyTwoStepAdmin(Production, admin.site)
        self.production = ProductionFactory()

    def _request_with_messages(self, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data or {})
        SessionMiddleware(lambda _: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        request.user = AnonymousUser()
        return request

    def test_run_two_step_bulk_action_renders_intermediate_form(self) -> None:
        request = self._request_with_messages("get", "/admin/productions/production/")

        response = self.admin._run_two_step_bulk_action(
            request,
            Production.objects.filter(pk=self.production.pk),
            form_class=DummyForm,
            action_name="dummy_action",
            title="Dummy action",
            apply_handler=Mock(return_value="Done"),
            selected_label="Selected productions",
        )

        assert response.status_code == 200
        assert response.template_name == "admin/two_step_action.html"

    def test_run_two_step_bulk_action_apply_calls_handler(self) -> None:
        request = self._request_with_messages(
            "post",
            "/admin/productions/production/",
            data={
                "apply": "1",
                ACTION_CHECKBOX_NAME: [str(self.production.pk)],
            },
        )

        apply_handler = Mock(return_value="Applied")
        response = self.admin._run_two_step_bulk_action(
            request,
            Production.objects.none(),
            form_class=DummyForm,
            action_name="dummy_action",
            title="Dummy action",
            apply_handler=apply_handler,
        )

        assert response is None
        apply_handler.assert_called_once()
        selected_qs = apply_handler.call_args[0][0]
        assert list(selected_qs.values_list("id", flat=True)) == [self.production.id]

    def test_run_two_step_bulk_action_apply_with_no_selection_returns_none(self) -> None:
        request = self._request_with_messages(
            "post",
            "/admin/productions/production/",
            data={
                "apply": "1",
            },
        )

        response = self.admin._run_two_step_bulk_action(
            request,
            Production.objects.none(),
            form_class=DummyForm,
            action_name="dummy_action",
            title="Dummy action",
            apply_handler=Mock(return_value="Applied"),
        )

        assert response is None

    def test_run_two_step_bulk_action_apply_with_invalid_form_renders_form_page(self) -> None:
        request = self._request_with_messages(
            "post",
            "/admin/productions/production/",
            data={
                "apply": "1",
                ACTION_CHECKBOX_NAME: [str(self.production.pk)],
            },
        )

        response = self.admin._run_two_step_bulk_action(
            request,
            Production.objects.none(),
            form_class=RequiredFieldForm,
            action_name="dummy_action",
            title="Dummy action",
            apply_handler=Mock(return_value="Applied"),
        )

        assert response.status_code == 200
        assert response.template_name == "admin/two_step_action.html"

    def test_run_two_step_bulk_action_initial_step_with_empty_queryset_returns_none(
        self,
    ) -> None:
        request = self._request_with_messages("get", "/admin/productions/production/")

        response = self.admin._run_two_step_bulk_action(
            request,
            Production.objects.none(),
            form_class=DummyForm,
            action_name="dummy_action",
            title="Dummy action",
            apply_handler=Mock(return_value="Applied"),
        )

        assert response is None
