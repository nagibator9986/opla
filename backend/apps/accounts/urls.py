from django.urls import path

from apps.accounts.views import QuickLoginView

urlpatterns = [
    path("quick-login/", QuickLoginView.as_view(), name="auth-quick-login"),
]
