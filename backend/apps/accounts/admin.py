from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html

from unfold.admin import ModelAdmin

from apps.accounts.models import BaseUser, ClientProfile, MagicLink


@admin.register(BaseUser)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )


@admin.register(ClientProfile)
class ClientProfileAdmin(ModelAdmin):
    list_display = ("name", "company", "telegram_id", "city", "industry")
    search_fields = ("name", "company", "telegram_id")
    list_filter = ("industry", "city")


@admin.register(MagicLink)
class MagicLinkAdmin(ModelAdmin):
    """Magic-ссылки для входа клиентов через WhatsApp.

    Admin-кнопка «Скопировать» рядом с токеном — для ручной отправки если
    Wazzup24 канал не настроен.
    """

    list_display = ("created_at", "client", "delivered_via", "is_used", "is_expired", "magic_url")
    list_filter = ("delivered_via",)
    search_fields = ("client__name", "client__company", "client__phone_wa", "token")
    readonly_fields = ("token", "client", "expires_at", "used_at", "requested_ip", "delivered_via", "created_at", "updated_at", "magic_url")
    ordering = ("-created_at",)

    @admin.display(boolean=True, description="Использована")
    def is_used(self, obj):
        return obj.is_used

    @admin.display(boolean=True, description="Просрочена")
    def is_expired(self, obj):
        return obj.is_expired

    @admin.display(description="Ссылка для копирования")
    def magic_url(self, obj):
        from django.conf import settings
        base = getattr(settings, "PUBLIC_SITE_URL", "https://baqsy.tnriazun.com").rstrip("/")
        url = f"{base}/auth/magic/{obj.token}"
        return format_html(
            '<a href="{}" target="_blank" style="font-family:ui-monospace,monospace;'
            'font-size:11px;color:#1d4ed8;word-break:break-all;">{}</a>',
            url, url,
        )

    def has_add_permission(self, request):
        # Создаются только через POST /auth/login-link/ — вручную не добавлять
        return False
