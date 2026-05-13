"""Core API views — singleton platform settings."""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import SiteSettings


class SiteSettingsView(APIView):
    """GET /api/v1/site/ — публичные настройки платформы.

    Возвращает только те поля, которые фронт должен знать. Никаких
    секретных ключей здесь не отдаём.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        s = SiteSettings.get_solo()
        return Response(
            {
                "payments_enabled": s.payments_enabled,
                "free_mode_banner": s.free_mode_banner,
            }
        )
