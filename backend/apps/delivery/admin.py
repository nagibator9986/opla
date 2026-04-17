from django.contrib import admin

from unfold.admin import ModelAdmin

from apps.delivery.models import DeliveryLog


@admin.register(DeliveryLog)
class DeliveryLogAdmin(ModelAdmin):
    list_display = ("report", "channel", "status", "external_id", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("report__submission__client__name",)
    readonly_fields = ("report", "channel", "created_at")
