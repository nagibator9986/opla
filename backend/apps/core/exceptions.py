"""Custom DRF exception handler for consistent API error responses."""
from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Wraps DRF exception responses in a consistent structure.

    For detail-only errors:  {"error": "code", "detail": "text"}
    For validation errors:   {"field_name": ["Ошибка"]}  (unchanged)
    """
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        # Wrap single "detail" responses (401, 403, 404, 405…)
        if isinstance(data, dict) and "detail" in data and len(data) == 1:
            response.data = {
                "error": _status_to_code(response.status_code),
                "detail": str(data["detail"]),
            }
        # Validation errors with multiple fields remain as-is {"field": ["msg"]}

    return response


def _status_to_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        429: "throttled",
        500: "server_error",
    }.get(status_code, "error")
