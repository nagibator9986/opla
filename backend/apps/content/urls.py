"""Content API URL patterns for /api/v1/content/."""
from django.urls import path

from apps.content.views import ContentBlockListView

urlpatterns = [
    path("", ContentBlockListView.as_view(), name="content-list"),
]
