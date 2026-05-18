from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import QuickLoginView

urlpatterns = [
    path("quick-login/", QuickLoginView.as_view(), name="auth-quick-login"),
    # JWT refresh — фронт дёргает /auth/token/refresh/ для продления access-токена.
    # Без этого юзер выкидывается из ЛК через 4 часа и регистрируется заново.
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
