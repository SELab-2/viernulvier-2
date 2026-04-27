"""Reusable custom admin widgets and decorators."""

from collections.abc import Callable
from typing import Any

from django import forms


class RichTextAdminWidget(forms.Textarea):
    """Simple WYSIWYG textarea widget for HTML-capable admin fields."""

    class Media:
        js = (
            "admin/js/rich_text_admin_widget_utils.js",
            "admin/js/rich_text_admin_widget_actions.js",
            "admin/js/rich_text_admin_widget_bootstrap.js",
        )

    def __init__(self, attrs: dict[str, Any] | None = None) -> None:
        base_attrs = {
            "data-richtext-editor": "1",
            "class": "vLargeTextField richtext-admin-input",
        }
        if attrs:
            base_attrs.update(attrs)
        super().__init__(attrs=base_attrs)


def enable_rich_text_for_fields(
    *field_names: str,
    widget_attrs: dict[str, Any] | None = None,
    help_text_suffix: str = "",
) -> Callable[[type], type]:
    """Class decorator that enables the rich text widget for selected fields.

    Example:
        @enable_rich_text_for_fields("body", "excerpt")
        class BlogTranslationInline(admin.TabularInline):
            ...
    """
    configured_fields = frozenset(field_names)
    configured_widget_attrs = dict(widget_attrs or {})

    def decorator(admin_class: type) -> type:
        original_formfield_for_dbfield = admin_class.__dict__.get("formfield_for_dbfield")

        def formfield_for_dbfield(self: Any, db_field: Any, request: Any, **kwargs: Any) -> Any:
            if db_field.name in self.rich_text_fields:
                kwargs.setdefault(
                    "widget",
                    RichTextAdminWidget(attrs=self.rich_text_widget_attrs),
                )

            if original_formfield_for_dbfield is not None:
                formfield = original_formfield_for_dbfield(self, db_field, request, **kwargs)
            else:
                formfield = super(admin_class, self).formfield_for_dbfield(db_field, request, **kwargs)

            if formfield is not None and db_field.name in self.rich_text_fields:
                existing_help_text = formfield.help_text or ""
                if self.rich_text_help_text_suffix and self.rich_text_help_text_suffix not in existing_help_text:
                    if existing_help_text:
                        formfield.help_text = f"{existing_help_text} {self.rich_text_help_text_suffix}"
                    else:
                        formfield.help_text = self.rich_text_help_text_suffix

            return formfield

        admin_class.rich_text_fields = configured_fields
        admin_class.rich_text_widget_attrs = configured_widget_attrs
        admin_class.rich_text_help_text_suffix = help_text_suffix
        admin_class.formfield_for_dbfield = formfield_for_dbfield
        return admin_class

    return decorator
