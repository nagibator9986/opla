"""Central API v1 URL router."""
from django.urls import include, path

from apps.submissions.group_views import (
    CreateGroupView,
    GroupStatusView,
    ParticipantAnswerView,
    ParticipantContextView,
)

urlpatterns = [
    path("chat/", include("apps.ai.urls")),
    path("cases/", include("apps.cases.urls")),
    path("blog/", include("apps.blog.urls")),
    path("content/", include("apps.content.urls")),
    path("industries/", include("apps.industries.urls")),
    path("submissions/", include("apps.submissions.urls")),
    path("payments/", include("apps.payments.urls")),
    path("reports/", include("apps.reports.urls")),

    # Multi-participant audit (Ashide 2)
    path("audit-groups/", CreateGroupView.as_view(), name="audit-group-create"),
    path(
        "audit-groups/by-submission/<uuid:submission_id>/",
        GroupStatusView.as_view(),
        name="audit-group-status",
    ),
    path("invite/<str:token>/", ParticipantContextView.as_view(), name="invite-context"),
    path("invite/<str:token>/answer/", ParticipantAnswerView.as_view(), name="invite-answer"),
]
