from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.blog.models import BlogPost
from apps.blog.serializers import BlogPostDetailSerializer, BlogPostListSerializer


class BlogPostListView(generics.ListAPIView):
    """GET /api/v1/blog/ — публичный список опубликованных записей."""

    permission_classes = [AllowAny]
    serializer_class = BlogPostListSerializer
    pagination_class = None

    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True,
            published_at__lte=timezone.now(),
        ).order_by("order", "-published_at", "-created_at")


class BlogPostDetailView(generics.RetrieveAPIView):
    """GET /api/v1/blog/<slug>/ — публичная детальная запись."""

    permission_classes = [AllowAny]
    serializer_class = BlogPostDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True, published_at__lte=timezone.now()
        )
