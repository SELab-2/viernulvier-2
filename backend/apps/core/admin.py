"""
Base admin configuration for the core app.

``BaseAdmin`` is the single parent class for every ``ModelAdmin`` in the
project. Centralising shared admin behaviour here means project-wide
changes (e.g. adding a global ``list_per_page``, disabling bulk delete,
or injecting request-scoped context) only need to be made in one place.
"""

from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse


class PersistentSelectionMixin:
    """Persist admin action selections in session across changelist pages and searches."""

    persistent_selection_session_prefix = "admin_persistent_selection"

    def _persistent_selection_session_key(self) -> str:
        return f"{self.persistent_selection_session_prefix}:{self.model._meta.label_lower}"

    def _get_persisted_selected_ids(self, request: any) -> set[str]:
        return set(request.session.get(self._persistent_selection_session_key(), []))

    def _set_persisted_selected_ids(self, request: any, selected_ids: set[str]) -> None:
        request.session[self._persistent_selection_session_key()] = sorted(selected_ids)
        request.session.modified = True

    def _clear_persisted_selected_ids(self, request: any) -> None:
        request.session.pop(self._persistent_selection_session_key(), None)
        request.session.modified = True

    def _update_persisted_selection_from_snapshot(
        self,
        request: any,
        *,
        selected_ids: set[str],
        visible_ids: set[str],
    ) -> set[str]:
        """Update session selection using current page snapshot.

        Visible but unselected rows are removed from the persisted set; selected
        rows are added.
        """
        stored_ids = self._get_persisted_selected_ids(request)
        stored_ids.difference_update(visible_ids - selected_ids)
        stored_ids.update(selected_ids)
        self._set_persisted_selected_ids(request, stored_ids)
        return stored_ids

    def _persist_current_posted_selection(self, request: any) -> None:
        posted_ids = set(request.POST.getlist(ACTION_CHECKBOX_NAME))
        if not posted_ids:
            return

        stored_ids = self._get_persisted_selected_ids(request)
        stored_ids.update(posted_ids)
        self._set_persisted_selected_ids(request, stored_ids)

    def _inject_persisted_selection_into_post(self, request: any) -> set[str]:
        """Merge current POST selection with session selection and write it back to POST."""
        posted_ids = set(request.POST.getlist(ACTION_CHECKBOX_NAME))
        stored_ids = self._get_persisted_selected_ids(request)
        merged_ids = posted_ids | stored_ids

        if not merged_ids:
            return set()

        mutable_state = getattr(request.POST, "_mutable", None)
        if mutable_state is not None:
            request.POST._mutable = True

        request.POST.setlist(ACTION_CHECKBOX_NAME, sorted(merged_ids))

        if mutable_state is not None:
            request.POST._mutable = mutable_state

        self._set_persisted_selected_ids(request, merged_ids)
        return merged_ids

    def changelist_view(self, request: any, extra_context: dict | None = None):
        if request.method == "POST" and request.POST.get("clear_persistent_selection") == "1":
            self._clear_persisted_selected_ids(request)
            return JsonResponse({"ok": True, "count": 0})

        if request.method == "POST" and request.POST.get("persist_selection") == "1":
            selected_ids = set(request.POST.getlist("selected_ids"))
            visible_ids = set(request.POST.getlist("visible_ids"))
            stored_ids = self._update_persisted_selection_from_snapshot(
                request,
                selected_ids=selected_ids,
                visible_ids=visible_ids,
            )
            return JsonResponse({"ok": True, "count": len(stored_ids)})

        if request.method == "POST":
            self._persist_current_posted_selection(request)

        stored_ids = sorted(self._get_persisted_selected_ids(request))
        if extra_context is None:
            extra_context = {}
        extra_context.update(
            {
                "persistent_selected_ids": stored_ids,
                "persistent_selected_count": len(stored_ids),
            }
        )

        return super().changelist_view(request, extra_context=extra_context)

    def response_action(self, request: any, queryset: any):
        """Apply actions on persisted+posted selections, not only current changelist page queryset."""
        merged_ids: set[str] = set()
        is_select_across = False

        if request.method == "POST":
            merged_ids = self._inject_persisted_selection_into_post(request)
            is_select_across = request.POST.get("select_across") == "1"

            if merged_ids and not is_select_across:
                queryset = self.model.objects.filter(pk__in=merged_ids)

        response = super().response_action(request, queryset)

        if isinstance(response, HttpResponseRedirect) and request.method == "POST" and not is_select_across and merged_ids:
            self._clear_persisted_selected_ids(request)

        return response


class BaseAdmin(PersistentSelectionMixin, admin.ModelAdmin):
    """
    Project-wide base class for all ``ModelAdmin`` registrations.

    Every app-level admin class should inherit from ``BaseAdmin`` instead
    of ``admin.ModelAdmin`` directly. This ensures any future cross-cutting
    concerns (auditing, permission overrides, queryset scoping, etc.) can
    be introduced here without touching individual app admins.

    Current behaviour
    -----------------
    Delegates entirely to Django's default ``ModelAdmin``. Subclasses
    override ``get_queryset`` to add ``select_related`` / ``prefetch_related``
    optimisations specific to their model.

    List per page and result count settings are set here to apply globally, but can
    be overridden on a per-admin basis if needed.
    """

    # Default pagination and performance settings for all admin changelists.
    list_per_page = 50
    show_full_result_count = False
    change_list_template = "admin/persistent_change_list.html"

    def get_queryset(self, request: any) -> any:
        """
        Return the base queryset for this admin.

        Subclasses should call ``super().get_queryset(request)`` and chain
        ``select_related`` / ``prefetch_related`` calls on the result to
        prevent N+1 queries on list and detail pages.
        """
        return super().get_queryset(request)


class TwoStepBulkActionMixin:
    """
    Reusable two-step admin action flow for bulk updates.

    The first step is the normal changelist selection. The second step renders
    an intermediate form where additional input can be provided before applying
    the action to the selected objects.
    """

    two_step_action_template = "admin/two_step_action.html"
    two_step_empty_selection_message = "No items selected."

    def _action_changelist_url(self) -> str:
        """Return changelist URL for the current admin model."""
        return reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")

    def _render_two_step_action_page(
        self,
        request: any,
        *,
        selected_qs: any,
        form: any,
        action_name: str,
        title: str,
        changelist_url: str,
        selected_label: str = "Selected items",
    ) -> TemplateResponse:
        """Render the intermediate action page containing the extra form."""
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "queryset": selected_qs,
            "form": form,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
            "action_name": action_name,
            "title": title,
            "changelist_url": changelist_url,
            "selected_label": selected_label,
        }
        return TemplateResponse(request, self.two_step_action_template, context)

    def _run_two_step_bulk_action(
        self,
        request: any,
        queryset: any,
        *,
        form_class: any,
        action_name: str,
        title: str,
        apply_handler: any,
        selected_label: str = "Selected items",
    ) -> any:
        """Execute a two-step action with optional intermediate form data."""
        changelist_url = self._action_changelist_url()

        if "apply" in request.POST:
            form = form_class(request.POST)
            selected_ids = request.POST.getlist(ACTION_CHECKBOX_NAME)
            selected_qs = self.model.objects.filter(pk__in=selected_ids)

            if not selected_ids:
                self.message_user(
                    request,
                    self.two_step_empty_selection_message,
                    level=messages.ERROR,
                )
                return None

            if form.is_valid():
                success_message = apply_handler(selected_qs, form.cleaned_data)
                self.message_user(request, success_message, level=messages.SUCCESS)
                return None

            return self._render_two_step_action_page(
                request,
                selected_qs=selected_qs,
                form=form,
                action_name=action_name,
                title=title,
                changelist_url=changelist_url,
                selected_label=selected_label,
            )

        selected_qs = queryset
        if not selected_qs.exists():
            self.message_user(
                request,
                self.two_step_empty_selection_message,
                level=messages.ERROR,
            )
            return None

        return self._render_two_step_action_page(
            request,
            selected_qs=selected_qs,
            form=form_class(),
            action_name=action_name,
            title=title,
            changelist_url=changelist_url,
            selected_label=selected_label,
        )
