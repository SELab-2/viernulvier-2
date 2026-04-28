"""
Tests for PersistentSelectionMixin — covering lines 56-62, 71, 101.
"""

import json
from unittest.mock import patch

from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.contrib.sessions.backends.cache import SessionStore
from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from apps.core.admin import BaseAdmin


def _make_admin():
    return BaseAdmin(User, admin.site)


def _make_session():
    """Return a session instance that supports .modified (mirrors real Django sessions)."""
    s = SessionStore()
    s.create()
    return s


class TestPersistentSelectionMixin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = _make_admin()

    def _get_get_request(self):
        request = self.factory.get("/")
        request.session = _make_session()
        return request

    def _get_post_request(self, posted_ids=None):
        data = {ACTION_CHECKBOX_NAME: posted_ids or []}

        request = self.factory.post("/", data=data)
        request.session = _make_session()
        return request

    def test_update_adds_selected_ids_to_empty_session(self):
        """Selected IDs that were not in the session are stored."""
        request = self._get_get_request()
        result = self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids={"1", "2"},
            visible_ids={"1", "2", "3"},
        )
        assert "1" in result
        assert "2" in result

    def test_update_removes_visible_but_unselected_ids(self):
        """IDs that are visible but not selected are removed from the session."""
        request = self._get_get_request()
        self.admin._set_persisted_selected_ids(request, {"1", "2", "3"})

        result = self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids={"1"},
            visible_ids={"1", "2"},
        )
        assert "1" in result
        assert "2" not in result
        assert "3" in result

    def test_update_preserves_non_visible_stored_ids(self):
        """IDs stored from a previous page (not visible now) are kept untouched."""
        request = self._get_get_request()
        self.admin._set_persisted_selected_ids(request, {"99", "100"})

        result = self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids=set(),
            visible_ids={"1", "2"},
        )
        assert "99" in result
        assert "100" in result

    def test_update_returns_merged_set(self):
        """Return value reflects the full post-update stored set."""
        request = self._get_get_request()
        self.admin._set_persisted_selected_ids(request, {"5"})

        result = self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids={"7"},
            visible_ids={"7"},
        )
        assert result == {"5", "7"}

    def test_update_persists_session_after_update(self):
        """After the call the session contains the updated selection."""
        request = self._get_get_request()
        self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids={"42"},
            visible_ids={"42"},
        )
        stored = self.admin._get_persisted_selected_ids(request)
        assert "42" in stored

    def test_persist_current_posted_selection_adds_posted_ids_to_session(self):
        """POSTed selection is merged into the persisted session state."""
        request = self._get_post_request(["1", "2"])

        self.admin._persist_current_posted_selection(request)

        assert self.admin._get_persisted_selected_ids(request) == {"1", "2"}

    def test_persist_current_posted_selection_returns_early_when_empty(self):
        """Empty POST data must short-circuit before touching the session."""
        request = self._get_post_request()
        self.admin._set_persisted_selected_ids(request, {"10"})

        with patch.object(self.admin, "_set_persisted_selected_ids") as mock_set:
            self.admin._persist_current_posted_selection(request)

        mock_set.assert_not_called()
        assert self.admin._get_persisted_selected_ids(request) == {"10"}

    def test_inject_persisted_selection_into_post_returns_empty_set_when_no_selection_exists(self):
        """An empty POST and empty session short-circuit without changes."""
        request = self._get_post_request()

        result = self.admin._inject_persisted_selection_into_post(request)

        assert result == set()
        assert self.admin._get_persisted_selected_ids(request) == set()

    def test_changelist_view_post_request_persists_selection_before_delegating(self):
        """POST requests trigger persistence before the parent changelist view runs."""
        request = self._get_post_request(["1", "2"])

        with patch.object(admin.ModelAdmin, "changelist_view", return_value=JsonResponse({"ok": True})) as super_view:
            response = self.admin.changelist_view(request)

        super_view.assert_called_once()
        assert self.admin._get_persisted_selected_ids(request) == {"1", "2"}
        assert json.loads(response.content) == {"ok": True}
