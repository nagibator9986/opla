from django.urls import path

from apps.payments.views import (
    CloudPaymentsCheckView,
    CloudPaymentsPayView,
    TariffListView,
)

urlpatterns = [
    path("tariffs/", TariffListView.as_view(), name="tariff-list"),
    path("cloudpayments/check/", CloudPaymentsCheckView.as_view(), name="cp-check"),
    path("cloudpayments/pay/", CloudPaymentsPayView.as_view(), name="cp-pay"),
]
