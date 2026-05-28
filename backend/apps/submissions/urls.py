"""Submission API URL patterns for /api/v1/submissions/."""
from django.urls import path

from apps.reports.views import DownloadReportPdfView
from apps.submissions.views import (
    AnswerCreateView,
    MySubmissionView,
    NextQuestionView,
    StartFreeSubmissionView,
    SubmissionCompleteView,
    SubmissionCreateView,
    SubmissionDetailView,
)

urlpatterns = [
    path("", SubmissionCreateView.as_view(), name="submission-create"),
    path("start-free/", StartFreeSubmissionView.as_view(), name="submission-start-free"),
    path("my/", MySubmissionView.as_view(), name="submission-my"),
    path("<uuid:pk>/", SubmissionDetailView.as_view(), name="submission-detail"),
    path("<uuid:pk>/next-question/", NextQuestionView.as_view(), name="submission-next-question"),
    path("<uuid:pk>/answers/", AnswerCreateView.as_view(), name="submission-answer"),
    path("<uuid:pk>/complete/", SubmissionCompleteView.as_view(), name="submission-complete"),
    # Публичная отдача PDF (стримит из MinIO, MinIO не торчит наружу через nginx)
    path("<uuid:submission_id>/pdf/", DownloadReportPdfView.as_view(), name="submission-pdf"),
]
