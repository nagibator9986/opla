"""Auth endpoints — magic-link login by WhatsApp number."""
from django.urls import path

from apps.accounts.views import LoginLinkRequestView, MagicLinkVerifyView

urlpatterns = [
    path("login-link/", LoginLinkRequestView.as_view(), name="auth-login-link"),
    path("magic/<str:token>/", MagicLinkVerifyView.as_view(), name="auth-magic-verify"),
]
