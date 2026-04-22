from django.urls import path

from apps.cases.views import CaseDetailView, CaseListView

urlpatterns = [
    path("", CaseListView.as_view(), name="case-list"),
    path("<slug:slug>/", CaseDetailView.as_view(), name="case-detail"),
]
