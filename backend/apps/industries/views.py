"""Views for the industries app."""
from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.industries.models import Industry
from apps.industries.serializers import IndustrySerializer


class IndustryListView(generics.ListAPIView):
    """GET /api/v1/industries/ — list active industries.

    Public endpoint (AllowAny). Paginated at PAGE_SIZE=20 via global settings.
    Returns only industries where is_active=True, ordered alphabetically by name.
    """

    serializer_class = IndustrySerializer
    permission_classes = [AllowAny]
    queryset = Industry.objects.filter(is_active=True).order_by("name")
