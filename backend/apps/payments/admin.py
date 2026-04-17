from django.contrib import admin

from unfold.admin import ModelAdmin

from apps.payments.models import Tariff, Payment


@admin.register(Tariff)
class TariffAdmin(ModelAdmin):
    list_display = ("title", "code", "price_kzt", "is_active")
    list_editable = ("price_kzt", "is_active")


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("transaction_id", "submission", "tariff", "amount", "status", "created_at")
    list_filter = ("status", "tariff")
    readonly_fields = ("transaction_id", "raw_webhook")
