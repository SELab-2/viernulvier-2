from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.blogs.models import Blog, BlogTranslation
from apps.core.admin_widgets import RichTextAdminWidget, enable_rich_text_for_fields


class TestRichTextAdminWidget(TestCase):
    def test_media_contains_modular_js_files(self) -> None:
        js_files = RichTextAdminWidget.Media.js
        assert "admin/js/rich_text_admin_widget_utils.js" in js_files
        assert "admin/js/rich_text_admin_widget_utils_selection.js" in js_files
        assert "admin/js/rich_text_admin_widget_utils_inline.js" in js_files
        assert "admin/js/rich_text_admin_widget_utils_dom.js" in js_files
        assert "admin/js/rich_text_admin_widget_utils_caret.js" in js_files
        assert "admin/js/rich_text_admin_widget_actions.js" in js_files
        assert "admin/js/rich_text_admin_widget_actions_block.js" in js_files
        assert "admin/js/rich_text_admin_widget_actions_list.js" in js_files
        assert "admin/js/rich_text_admin_widget_bootstrap.js" in js_files

    def test_default_attrs_are_applied(self) -> None:
        widget = RichTextAdminWidget()
        assert widget.attrs["data-richtext-editor"] == "1"
        assert "vLargeTextField" in widget.attrs["class"]

    def test_custom_attrs_override_defaults(self) -> None:
        widget = RichTextAdminWidget(attrs={"class": "custom", "data-test": "x"})
        assert widget.attrs["class"] == "custom"
        assert widget.attrs["data-test"] == "x"


class TestEnableRichTextForFields(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def _get_excerpt_field(self):
        return BlogTranslation._meta.get_field("excerpt")

    def _get_title_field(self):
        return BlogTranslation._meta.get_field("title")

    def test_decorator_sets_widget_and_appends_help_text(self) -> None:
        @enable_rich_text_for_fields(
            "excerpt",
            widget_attrs={"data-test": "1"},
            help_text_suffix="HTML allowed",
        )
        class Inline(admin.TabularInline):
            model = BlogTranslation

        inline = Inline(Blog, admin.site)
        formfield = inline.formfield_for_dbfield(self._get_excerpt_field(), self.request)

        assert isinstance(formfield.widget, RichTextAdminWidget)
        assert formfield.widget.attrs["data-test"] == "1"
        assert formfield.help_text.endswith("HTML allowed")

    def test_decorator_does_not_duplicate_existing_suffix(self) -> None:
        existing_help = BlogTranslation._meta.get_field("excerpt").help_text

        @enable_rich_text_for_fields("excerpt", help_text_suffix=existing_help)
        class Inline(admin.TabularInline):
            model = BlogTranslation

        inline = Inline(Blog, admin.site)
        formfield = inline.formfield_for_dbfield(self._get_excerpt_field(), self.request)

        assert formfield.help_text == existing_help

    def test_decorator_sets_suffix_when_help_text_empty(self) -> None:
        @enable_rich_text_for_fields("title", help_text_suffix="HTML allowed")
        class Inline(admin.TabularInline):
            model = BlogTranslation

            def formfield_for_dbfield(self, db_field, request, **kwargs):
                formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
                formfield.help_text = ""
                return formfield

        inline = Inline(Blog, admin.site)
        formfield = inline.formfield_for_dbfield(self._get_title_field(), self.request)

        assert formfield.help_text == "HTML allowed"

    def test_decorator_uses_original_formfield_for_dbfield(self) -> None:
        @enable_rich_text_for_fields("excerpt")
        class Inline(admin.TabularInline):
            model = BlogTranslation

            def formfield_for_dbfield(self, db_field, request, **kwargs):
                self._called = True
                return super().formfield_for_dbfield(db_field, request, **kwargs)

        inline = Inline(Blog, admin.site)
        inline.formfield_for_dbfield(self._get_excerpt_field(), self.request)

        assert inline._called is True

    def test_non_rich_text_field_uses_default_widget(self) -> None:
        @enable_rich_text_for_fields("excerpt")
        class Inline(admin.TabularInline):
            model = BlogTranslation

        inline = Inline(Blog, admin.site)
        formfield = inline.formfield_for_dbfield(self._get_title_field(), self.request)

        assert not isinstance(formfield.widget, RichTextAdminWidget)
