"""
Tests for shared helper fixtures in tests/scrapers/conftest.py.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from apps.imports.scrapers import viernulvier


@pytest.mark.django_db(transaction=True)
def test_shared_helper_fixtures_are_callable(
    monkeypatch,
    mock_build_session_helper,
    mock_session_helper,
    temp_viernulvier_model,
    fake_trans_model_fixture,
    m2m_setup_fixture,
) -> None:
    """Exercise the wrapper fixtures so their return lines are covered."""

    # mock_build_session_helper -> _mock_build_session
    mock_build_session_helper([(200, [])])
    assert viernulvier._build_session is not None

    # mock_session_helper -> _mock_session
    def responses(_url, _n):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = []
        return response

    call_count = mock_session_helper(responses)
    assert call_count == [0]
    session = viernulvier._build_session()
    assert session.get("https://example.com").json() == []

    # temp_viernulvier_model -> context manager factory
    with temp_viernulvier_model() as M:
        obj = M.objects.create(id="x")
        assert obj.id == "x"

    # fake_trans_model_fixture -> fake translation model factory
    calls = []
    FT = fake_trans_model_fixture(calls)
    FT.objects.update_or_create(language_id="nl", defaults={"title": "Hallo"})
    assert calls[0]["language_id"] == "nl"

    # m2m_setup_fixture -> fake M2M model factory
    related, through, rows = m2m_setup_fixture()
    _ = related(pk=1)
    through(parent_id=1, related_id=2)
    assert rows
    assert rows[0]["parent_id"] == 1







