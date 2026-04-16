"""URL patterns for bot-facing endpoints in accounts app."""
from django.urls import path

from apps.accounts.views import (
    ActiveSubmissionView,
    BotJWTView,
    DeeplinkCreateView,
    DeeplinkExchangeView,
    OnboardingView,
)

urlpatterns = [
    path("onboarding/", OnboardingView.as_view(), name="bot-onboarding"),
    path("deeplink/", DeeplinkCreateView.as_view(), name="bot-deeplink-create"),
    path("deeplink/exchange/", DeeplinkExchangeView.as_view(), name="bot-deeplink-exchange"),
    path("jwt/", BotJWTView.as_view(), name="bot-jwt"),
    path("active-submission/", ActiveSubmissionView.as_view(), name="bot-active-submission"),
]
