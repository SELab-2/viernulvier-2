# tests/test_health_view.py

import json
from unittest.mock import MagicMock, patch

from django.db.utils import OperationalError
from django.test import RequestFactory, TestCase

from config.health import health


class HealthViewTests(TestCase):
    """
    Tests for the health endpoint.
    """

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_health_ok(self) -> None:
        """
        Health endpoint should return 200 when the database is reachable.
        """
        request = self.factory.get("/health")
        response = health(request)

        assert response.status_code == 200
        assert json.loads(response.content) == {"status": "ok"}

    @patch("config.health.connections")
    def test_health_database_unavailable(self, mock_connections) -> None:
        """
        Health endpoint should return 503 when the database raises OperationalError.
        """
        mock_connection = MagicMock()
        mock_connections.__getitem__.return_value = mock_connection

        mock_connection.cursor.side_effect = OperationalError("Database down")

        request = self.factory.get("/health")
        response = health(request)

        assert response.status_code == 503
        assert json.loads(response.content) == {"status": "error", "detail": "database unavailable"}

    @patch("config.health.connections")
    def test_health_executes_query(self, mock_connections) -> None:
        """
        Verify that the SQL query is executed when the database connection works.
        """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connections.__getitem__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        request = self.factory.get("/health")
        response = health(request)

        mock_cursor.execute.assert_called_once_with("SELECT 1")

        assert response.status_code == 200
        assert json.loads(response.content) == {"status": "ok"}
