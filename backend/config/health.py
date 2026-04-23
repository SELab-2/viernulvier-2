"""Health check endpoint for the viernulvier_archive project.

Exposed at ``/health/`` by ``config.urls``. Used by load balancers,
container orchestrators (Kubernetes liveness/readiness probes), and
uptime monitors to verify the application is running and the database
is reachable.

Response codes
--------------
200  Application is healthy and the database is reachable.
503  Database is unreachable. The response body contains a detail message.
"""

from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpRequest, JsonResponse


def health(_request: HttpRequest) -> JsonResponse:
    """Return 200 if the application and database are healthy, 503 otherwise.

    The database check executes a minimal ``SELECT 1`` query against the
    default connection. Any ``OperationalError`` (e.g. the database is
    down, credentials are wrong, the connection pool is exhausted) is
    caught and results in a 503 response so that the caller knows not to
    route traffic here.
    """
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
    except OperationalError:
        return JsonResponse(
            {"status": "error", "detail": "database unavailable"},
            status=503,
        )

    return JsonResponse({"status": "ok"})
