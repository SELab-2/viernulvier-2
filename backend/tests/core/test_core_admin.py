"""
Tests for apps/core/admin.py

Covers:
- BaseAdmin class inheritance and configuration
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from apps.core.admin import BaseAdmin


class TestBaseAdmin(TestCase):
    """Tests for BaseAdmin."""

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_inherits_from_model_admin(self) -> None:
        assert issubclass(BaseAdmin, ModelAdmin)

    def test_is_registered_as_admin_class(self) -> None:
        """BaseAdmin should be a proper ModelAdmin subclass, usable in admin."""
        assert issubclass(BaseAdmin, admin.ModelAdmin)

    def test_can_be_instantiated_with_model_and_site(self) -> None:
        """BaseAdmin can be instantiated without error."""
        instance = BaseAdmin(User, admin.site)
        assert isinstance(instance, BaseAdmin)

    def test_has_no_extra_list_display_by_default(self) -> None:
        """BaseAdmin should not add any list_display columns by default."""
        instance = BaseAdmin(User, admin.site)
        # The default ModelAdmin list_display is ('__str__',)
        assert instance.list_display == ("__str__",)

    def test_has_no_list_filter_by_default(self) -> None:
        instance = BaseAdmin(User, admin.site)
        assert list(instance.list_filter) == []

    def test_has_no_search_fields_by_default(self) -> None:
        instance = BaseAdmin(User, admin.site)
        assert list(instance.search_fields) == []

    def test_subclassing_works(self) -> None:
        """Other admin classes should be able to extend BaseAdmin."""

        class MyAdmin(BaseAdmin):
            list_display = ("id",)

        assert issubclass(MyAdmin, BaseAdmin)
        assert MyAdmin.list_display == ("id",)

    def test_list_per_page_default(self) -> None:
        """BaseAdmin should have a default list_per_page value."""
        instance = BaseAdmin(User, admin.site)
        assert instance.list_per_page == 50

    def test_list_per_page_can_be_overridden(self) -> None:
        """Subclasses should be able to override list_per_page."""

        class MyAdmin(BaseAdmin):
            list_per_page = 100

        instance = MyAdmin(User, admin.site)
        assert instance.list_per_page == 100

    def test_show_full_result_count_default(self) -> None:
        """BaseAdmin should have show_full_result_count set to False by default."""
        instance = BaseAdmin(User, admin.site)
        assert not instance.show_full_result_count

    def test_show_full_result_count_can_be_overridden(self) -> None:
        """Subclasses should be able to override show_full_result_count."""

        class MyAdmin(BaseAdmin):
            show_full_result_count = True

        instance = MyAdmin(User, admin.site)
        assert instance.show_full_result_count

    def test_get_queryset_returns_model_queryset(self) -> None:
        User.objects.create_user(username="u1", password="secret")
        instance = BaseAdmin(User, admin.site)
        request = self.factory.get("/admin/auth/user/")

        queryset = instance.get_queryset(request)

        assert queryset.model == User
        assert queryset.filter(username="u1").exists()
