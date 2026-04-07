"""
Tests for Viernulvier query parameter handling.
"""

from __future__ import annotations

from apps.imports.scrapers import viernulvier


def test_fetch_accepts_query_params(monkeypatch) -> None:
    """Params dict is forwarded to the first HTTP request."""
    from unittest.mock import Mock

    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    captured = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = {"member": []}
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["params"] = params
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    viernulvier.fetch_viernulvier(endpoint="/events", params={"created_at[after]": "2024-01-01T00:00:00Z"})

    assert captured["params"] == {"created_at[after]": "2024-01-01T00:00:00Z"}


def test_fetch_params_applied_to_initial_request_only(monkeypatch) -> None:
    """Query params are passed on page 1 only; sequential 'next' pages have no params."""
    from unittest.mock import Mock

    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")

    request_count = [0]
    captured_params_list = []

    def fake_build_session():
        session = Mock()

        def fake_get(url, params=None, headers=None, timeout=None):
            request_count[0] += 1
            captured_params_list.append(params)
            mock_response = Mock(status_code=200, ok=True)
            mock_response.headers = Mock()
            mock_response.headers.get.return_value = None

            if request_count[0] == 1:
                mock_response.json.return_value = {
                    "@context": "https://example.com/context.jsonld",
                    "member": [{"@id": "https://example.com/1", "title": "A"}],
                    "view": {"next": "https://example.com/api/v1/events?page=2"},
                }
            else:
                mock_response.json.return_value = {
                    "@context": "https://example.com/context.jsonld",
                    "member": [{"@id": "https://example.com/2", "title": "B"}],
                }
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    result = viernulvier.fetch_viernulvier(endpoint="/events", params={"created_at[after]": "2024-01-01T00:00:00Z"})

    assert len(result) == 2
    assert captured_params_list[0] == {"created_at[after]": "2024-01-01T00:00:00Z"}
    assert captured_params_list[1] is None


def test_fetch_with_multiple_query_params(monkeypatch) -> None:
    """Multiple query parameters are all forwarded correctly."""
    from unittest.mock import Mock

    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    captured = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = {"member": []}
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["params"] = params
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    params = {
        "created_at[after]": "2024-01-01T00:00:00Z",
        "updated_at[before]": "2024-12-31T23:59:59Z",
    }
    viernulvier.fetch_viernulvier(endpoint="/events", params=params)

    assert captured["params"] == params


def test_fetch_without_params_sends_none(monkeypatch) -> None:
    """Calling fetch without params passes None to the HTTP layer."""
    from unittest.mock import Mock

    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    captured = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = {"member": []}
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["params"] = params
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    viernulvier.fetch_viernulvier(endpoint="/events")

    assert captured["params"] is None


def test_fetch_preserves_timestamp_format(monkeypatch) -> None:
    """ISO 8601 timestamp strings in params are not modified."""
    from unittest.mock import Mock

    monkeypatch.setenv("VIERNULVIER_API_KEY", "test-key")
    captured = {}

    def fake_build_session():
        session = Mock()
        mock_response = Mock(status_code=200, ok=True)
        mock_response.json.return_value = {"member": []}
        mock_response.headers = Mock()
        mock_response.headers.get.return_value = None

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["params"] = params
            return mock_response

        session.get.side_effect = fake_get
        return session

    monkeypatch.setattr(viernulvier, "_build_session", fake_build_session)

    iso_timestamp = "2024-12-25T10:30:45Z"
    viernulvier.fetch_viernulvier(endpoint="/events", params={"created_at[after]": iso_timestamp})

    assert captured["params"]["created_at[after]"] == iso_timestamp
