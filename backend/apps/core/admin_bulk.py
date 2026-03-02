import json

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse


class BulkOperationAdminMixin:
    bulk_service_class = None
    bulk_template = "admin/bulk_operation.html"

    def get_bulk_service(self):
        if self.bulk_service_class is None:
            raise ValueError("bulk_service_class must be set")
        return self.bulk_service_class()

    def get_urls(self):
        return [
            path(
                "bulk/",
                self.admin_site.admin_view(self.bulk_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_bulk",
            ),
            *super().get_urls(),
        ]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["bulk_url"] = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_bulk"
        )
        return super().changelist_view(request, extra_context=extra_context)

    def bulk_view(self, request):
        service = self.get_bulk_service()
        # pick first action as default on GET so fields show immediately
        default_action = service.actions[0].slug if service.actions else None
        action_slug = request.POST.get("action") if request.method == "POST" else default_action
        action_form, cond_forms = service.build_forms(
            data=request.POST if request.method == "POST" else None,
            action_slug=action_slug,
        )

        spec_payload = {}
        for slug, spec in service._field_map.items():
            field = spec.form_field_factory("value")
            html1 = field.widget.render(name="__name__", value=None, attrs={"id": "__id__"})
            html2 = field.widget.render(name="__name2__", value=None, attrs={"id": "__id2__"})
            spec_payload[slug] = {
                "operators": [
                    {"code": op.code, "label": op.label, "value_kind": op.value_kind}
                    for op in spec.operators
                ],
                "value_html": html1,
                "value2_html": html2,
            }

        # Serialize action-specific fields so the UI can swap them client-side
        action_fields_payload = {}
        for action in service.actions:
            fields_html = ""
            add_links = {}
            for name, field in action.form_fields.items():
                rendered = field.widget.render(name=name, value=None, attrs={"id": f"id_{name}"})
                fields_html += f"<p><label for='id_{name}'>{field.label}</label> {rendered}</p>"

                model_cls = getattr(getattr(field, "queryset", None), "model", None)
                if model_cls and model_cls in self.admin_site._registry:
                    add_url = reverse(f"admin:{model_cls._meta.app_label}_{model_cls._meta.model_name}_add")
                    add_links[name] = add_url

            action_fields_payload[action.slug] = {
                "html": fields_html,
                "add_links": add_links,
            }

        all_valid = action_form.is_valid()
        for form in cond_forms:
            all_valid = all_valid and form.is_valid()

        if request.method == "POST" and all_valid:
            result = service.execute(
                action_form.cleaned_data["action"],
                cond_forms,
                action_form,
                request.user,
            )
            messages.success(
                request,
                f"{result.processed} objects processed (matched {result.matched}). {result.detail}",
            )
            return redirect(
                reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")
            )

        return render(
            request,
            self.bulk_template,
            {
                "title": f"Bulk operations voor {self.model._meta.verbose_name_plural}",
                "action_form": action_form,
                "cond_forms": cond_forms,
                "opts": self.model._meta,
                "media": self.media + action_form.media,
                "field_specs_json": json.dumps(spec_payload),
                "action_fields_json": json.dumps(action_fields_payload),
                "current_action": action_slug,
            },
        )


class BulkInlineAdminMixin(admin.TabularInline):
    """Placeholder to keep import symmetry if needed later."""
    pass
