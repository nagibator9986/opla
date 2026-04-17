from django.urls import path
from apps.dashboard.views import dashboard_stats_partial

urlpatterns = [
    path("stats/", dashboard_stats_partial, name="admin_dashboard_stats"),
]
