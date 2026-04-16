"""Bot authentication permission class."""
from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import BasePermission


class IsBotAuthenticated(BasePermission):
    """Verify X-Bot-Token header matches BOT_API_SECRET."""

    message = "Доступ разрешён только внутреннему боту."

    def has_permission(self, request, view) -> bool:
        token = request.headers.get("X-Bot-Token", "")
        return bool(token and token == settings.BOT_API_SECRET)
