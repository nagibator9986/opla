from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.cases.models import Case
from apps.cases.serializers import CaseDetailSerializer, CaseListSerializer


class CaseListView(generics.ListAPIView):
    """GET /api/v1/cases/ — public list of active cases."""

    serializer_class = CaseListSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Case.objects.filter(is_active=True).order_by("order", "-published_at", "-created_at")


class CaseDetailView(generics.RetrieveAPIView):
    """GET /api/v1/cases/<slug>/ — public case study page."""

    serializer_class = CaseDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Case.objects.filter(is_active=True)
