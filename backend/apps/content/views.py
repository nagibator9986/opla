"""Views for ContentBlock API."""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.models import ContentBlock


class ContentBlockListView(APIView):
    """GET /api/v1/content/ — flat dict of active content blocks."""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = ContentBlock.objects.filter(is_active=True)
        data = {block.key: block.content for block in qs}
        return Response(data)
