from django.contrib import admin
from django.utils.html import format_html

from unfold.admin import ModelAdmin

from apps.core.models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """Singleton-настройки платформы.

    В админке всегда показывается один существующий экземпляр или ссылка
    на создание первого. Удалять и добавлять второй — нельзя.
    """

    list_display = ("status_badge", "payments_enabled", "free_mode_banner", "updated_at")
    fields = ("payments_enabled", "free_mode_banner")
    save_on_top = True

    @admin.display(description="Статус")
    def status_badge(self, obj):
        if obj.payments_enabled:
            return format_html(
                '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
                'background:#dcfce7;color:#065f46;font-size:11px;font-weight:700;">'
                'ОПЛАТА ВКЛЮЧЕНА</span>'
            )
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'background:#fef3c7;color:#92400e;font-size:11px;font-weight:700;">'
            'СВОБОДНЫЙ РЕЖИМ</span>'
        )

    def has_add_permission(self, request):
        # Singleton — добавлять можно только если ещё ничего нет.
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
