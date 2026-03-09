"""
Base admin configuration for the core app.

``BaseAdmin`` is the single parent class for every ``ModelAdmin`` in the
project. Centralising shared admin behaviour here means project-wide
changes (e.g. adding a global ``list_per_page``, disabling bulk delete,
or injecting request-scoped context) only need to be made in one place.
"""

from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.template.response import TemplateResponse
from django.urls import reverse


class BaseAdmin(admin.ModelAdmin):
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
    """

    # Default pagination and performance settings for all admin changelists.
    list_per_page = 50
    show_full_result_count = False

    def get_queryset(self, request):
        """
        Return the base queryset for this admin.

        Subclasses should call ``super().get_queryset(request)`` and chain
        ``select_related`` / ``prefetch_related`` calls on the result to
        prevent N+1 queries on list and detail pages.
        """
        return super().get_queryset(request)


class TwoStepBulkActionMixin:
    """Reusable two-step admin action flow for bulk updates.

    The first step is the normal changelist selection. The second step renders
    an intermediate form where additional input can be provided before applying
    the action to the selected objects.
    """

    two_step_action_template = "admin/two_step_action.html"
    two_step_empty_selection_message = "No items selected."

    def _action_changelist_url(self):
        """Return changelist URL for the current admin model."""
        return reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist"
        )

    def _render_two_step_action_page(
        self,
        request,
        *,
        selected_qs,
        form,
        action_name,
        title,
        changelist_url,
        selected_label,
    ):
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
        request,
        queryset,
        *,
        form_class,
        action_name,
        title,
        apply_handler,
        selected_label="Selected items",
    ):
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
