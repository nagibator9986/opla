"""URL routing for the reports app."""
from django.urls import path

from apps.reports.views import ApproveReportView

app_name = "reports"

urlpatterns = [
    path("<int:report_id>/approve/", ApproveReportView.as_view(), name="approve"),
]
