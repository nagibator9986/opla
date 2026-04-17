"""Submission API URL patterns for /api/v1/submissions/."""
from django.urls import path

from apps.submissions.views import (
    SubmissionCreateView,
    SubmissionDetailView,
    MySubmissionView,
    NextQuestionView,
    AnswerCreateView,
    SubmissionCompleteView,
)

urlpatterns = [
    path("", SubmissionCreateView.as_view(), name="submission-create"),
    path("my/", MySubmissionView.as_view(), name="submission-my"),
    path("<uuid:pk>/", SubmissionDetailView.as_view(), name="submission-detail"),
    path("<uuid:pk>/next-question/", NextQuestionView.as_view(), name="submission-next-question"),
    path("<uuid:pk>/answers/", AnswerCreateView.as_view(), name="submission-answer"),
    path("<uuid:pk>/complete/", SubmissionCompleteView.as_view(), name="submission-complete"),
]
