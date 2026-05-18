from django.urls import path

from apps.ai.views import (
    AIConfigView,
    ChatAuthTokenView,
    ChatCollectView,
    ChatMessageView,
    ChatStartView,
    RequestEmailCodeView,
    StartQuestionnaireView,
    VerifyEmailCodeView,
)

urlpatterns = [
    path("config/", AIConfigView.as_view(), name="chat-config"),
    path("start/", ChatStartView.as_view(), name="chat-start"),
    path("message/", ChatMessageView.as_view(), name="chat-message"),
    path("collect/", ChatCollectView.as_view(), name="chat-collect"),
    path("auth-token/", ChatAuthTokenView.as_view(), name="chat-auth-token"),
    path("request-email-code/", RequestEmailCodeView.as_view(), name="chat-request-email-code"),
    path("verify-email-code/", VerifyEmailCodeView.as_view(), name="chat-verify-email-code"),
    path("start-questionnaire/", StartQuestionnaireView.as_view(), name="chat-start-questionnaire"),
]
