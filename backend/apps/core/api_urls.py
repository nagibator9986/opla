"""Central API v1 URL router.

Maps top-level prefixes to per-app URL modules.
All paths are relative to the /api/v1/ prefix mounted in baqsy/urls.py.
"""
from django.urls import include, path

urlpatterns = [
    path("chat/", include("apps.ai.urls")),
    path("cases/", include("apps.cases.urls")),
    path("content/", include("apps.content.urls")),
    path("industries/", include("apps.industries.urls")),
    path("submissions/", include("apps.submissions.urls")),
    path("payments/", include("apps.payments.urls")),
    path("reports/", include("apps.reports.urls")),
]
