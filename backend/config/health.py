from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse


def health(_):
    try:
        connection = connections["default"]
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError:
        return JsonResponse(
            {"status": "error", "detail": "database unavailable"}, status=503
        )

    return JsonResponse({"status": "ok"})
