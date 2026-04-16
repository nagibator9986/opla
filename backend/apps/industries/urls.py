"""URL patterns for the industries app.

Mounted at /api/v1/industries/ via apps.core.api_urls.
"""
from django.urls import path

from apps.industries.views import IndustryListView

urlpatterns = [
    path("", IndustryListView.as_view(), name="industry-list"),
]
