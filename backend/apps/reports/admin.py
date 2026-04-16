from django.contrib import admin
from apps.reports.models import AuditReport


@admin.register(AuditReport)
class AuditReportAdmin(admin.ModelAdmin):
    list_display = ("submission", "status", "approved_at", "created_at")
    list_filter = ("status",)
    search_fields = ("submission__client__name", "submission__client__company")
    readonly_fields = ("submission", "created_at", "updated_at")
