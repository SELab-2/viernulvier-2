"""
Tests for PersistentSelectionMixin — covering lines 56-62, 71, 101.
"""
import json

from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.contrib.sessions.backends.cache import SessionStore
from django.test import RequestFactory, TestCase

from apps.core.admin import BaseAdmin
from unittest.mock import patch


def _make_admin():
    return BaseAdmin(User, admin.site)


def _make_session():
    """Return a session instance that supports .modified (mirrors real Django sessions)."""
    s = SessionStore()
    s.create()
    return s


class TestUpdatePersistedSelectionFromSnapshot(TestCase):
    """Covers lines 56-62: _update_persisted_selection_from_snapshot."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = _make_admin()

    def _get_request(self):
        request = self.factory.get("/")
        request.session = _make_session()
        return request

    def test_adds_selected_ids_to_empty_session(self):
        """Selected IDs that were not in the session are stored."""
        request = self._get_request()
        result = self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids={"1", "2"},
            visible_ids={"1", "2", "3"},
        )
        assert "1" in result
        assert "2" in result

    def test_removes_visible_but_unselected_ids(self):
        """IDs that are visible but not selected are removed from the session."""
        request = self._get_request()
        self.admin._set_persisted_selected_ids(request, {"1", "2", "3"})

        result = self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids={"1"},
            visible_ids={"1", "2"},
        )
        assert "1" in result
        assert "2" not in result
        # 3 was not visible on this page, so it must survive
        assert "3" in result

    def test_preserves_non_visible_stored_ids(self):
        """IDs stored from a previous page (not visible now) are kept untouched."""
        request = self._get_request()
        self.admin._set_persisted_selected_ids(request, {"99", "100"})

        result = self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids=set(),
            visible_ids={"1", "2"},
        )
        assert "99" in result
        assert "100" in result

    def test_returns_merged_set(self):
        """Return value reflects the full post-update stored set."""
        request = self._get_request()
        self.admin._set_persisted_selected_ids(request, {"5"})

        result = self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids={"7"},
            visible_ids={"7"},
        )
        assert result == {"5", "7"}

    def test_session_is_persisted_after_update(self):
        """After the call the session contains the updated selection."""
        request = self._get_request()
        self.admin._update_persisted_selection_from_snapshot(
            request,
            selected_ids={"42"},
            visible_ids={"42"},
        )
        stored = self.admin._get_persisted_selected_ids(request)
        assert "42" in stored


class TestPersistCurrentPostedSelection(TestCase):
    """Covers line 71: early return when posted_ids is empty."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = _make_admin()

    def _post_request(self, ids):
        data = {ACTION_CHECKBOX_NAME: ids} if ids else {}
        request = self.factory.post("/", data)
        request.session = _make_session()
        return request

    def test_no_posted_ids_does_not_modify_session(self):
        """When POST contains no checkbox IDs the session must remain unchanged."""
        request = self._post_request([])
        self.admin._set_persisted_selected_ids(request, {"10"})

        self.admin._persist_current_posted_selection(request)

        stored = self.admin._get_persisted_selected_ids(request)
        assert stored == {"10"}

    def test_empty_post_does_not_add_empty_string_to_session(self):
        """An empty POST must not corrupt the session with empty/falsy IDs."""
        request = self._post_request([])

        self.admin._persist_current_posted_selection(request)

        stored = self.admin._get_persisted_selected_ids(request)
        assert stored == set()

    def test_non_empty_posted_ids_are_stored(self):
        """Control case: when IDs are posted they are added to the session."""
        request = self._post_request(["3", "4"])

        self.admin._persist_current_posted_selection(request)

        stored = self.admin._get_persisted_selected_ids(request)
        assert {"3", "4"}.issubset(stored)


class TestChangelistViewClearPersistentSelection(TestCase):
    """Covers line 101: clear_persistent_selection POST branch."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = _make_admin()

    def _clear_request(self):
        request = self.factory.post("/", {"clear_persistent_selection": "1"})
        request.session = _make_session()
        return request

    def test_clear_returns_json_ok(self):
        """POSTing clear_persistent_selection=1 returns JSON {ok: true, count: 0}."""
        request = self._clear_request()
        self.admin._set_persisted_selected_ids(request, {"1", "2", "3"})

        response = self.admin.changelist_view(request)

        assert response.status_code == 200
        body = json.loads(response.content)
        assert body == {"ok": True, "count": 0}

    def test_clear_removes_ids_from_session(self):
        """After clearing, the session must contain no persisted IDs."""
        request = self._clear_request()
        self.admin._set_persisted_selected_ids(request, {"7", "8"})

        self.admin.changelist_view(request)

        stored = self.admin._get_persisted_selected_ids(request)
        assert stored == set()

    def test_clear_with_no_prior_selection_still_returns_ok(self):
        """Clearing when nothing is stored must not raise and must return ok."""
        request = self._clear_request()

        response = self.admin.changelist_view(request)

        body = json.loads(response.content)
        assert body["ok"] is True
        assert body["count"] == 0



class TestLine71EarlyReturn(TestCase):
    """Directly verifies line 71 is reached: the return inside _persist_current_posted_selection."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = _make_admin()

    def test_early_return_fires_when_no_checkbox_ids_posted(self):
        """
        When POST has no ACTION_CHECKBOX_NAME key, posted_ids is empty set,
        the method must return immediately without ever calling _set_persisted_selected_ids.
        Patching _set_persisted_selected_ids lets us assert it was never called,
        which is only possible if the early return on line 71 executed.
        """
        request = self.factory.post("/", {})
        request.session = _make_session()

        with patch.object(self.admin, "_set_persisted_selected_ids") as mock_set:
            self.admin._persist_current_posted_selection(request)
            mock_set.assert_not_called()


class TestLine101ClearJsonResponse(TestCase):
    """Directly verifies line 101 is reached: the JsonResponse inside the clear branch."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = _make_admin()

    def test_clear_branch_short_circuits_before_super(self):
        """
        When clear_persistent_selection=1 is posted, changelist_view must return
        the JsonResponse on line 101 WITHOUT ever calling super().changelist_view.
        Patching the super call confirms the early return executed.
        """
        request = self.factory.post("/", {"clear_persistent_selection": "1"})
        request.session = _make_session()

        with patch.object(admin.ModelAdmin, "changelist_view") as mock_super:
            response = self.admin.changelist_view(request)
            mock_super.assert_not_called()

        assert response.status_code == 200
        body = json.loads(response.content)
        assert body == {"ok": True, "count": 0}
