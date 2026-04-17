from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin, TabularInline

from apps.industries.models import Industry, Question, QuestionnaireTemplate


class QuestionInline(SortableInlineAdminMixin, TabularInline):
    model = Question
    extra = 1
    fields = ("order", "text", "field_type", "options", "required", "block")
    # SortableInlineAdminMixin uses `order` field for sorting (already exists on Question model)


@admin.register(Industry)
class IndustryAdmin(ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    prepopulated_fields = {"code": ("name",)}


@admin.register(QuestionnaireTemplate)
class QuestionnaireTemplateAdmin(ModelAdmin):
    list_display = ("name", "industry", "version", "is_active", "published_at")
    list_filter = ("industry", "is_active")
    inlines = [QuestionInline]
    readonly_fields = ("version", "published_at")

    def save_model(self, request, obj, form, change):
        if change and obj.is_active:
            # Editing active template -> create new version with cloned questions
            new_version = QuestionnaireTemplate.create_new_version(obj)
            messages.success(
                request,
                _(f"Создана новая версия шаблона: v{new_version.version}"),
            )
            # Do NOT call super().save_model() -- create_new_version handles everything
        else:
            super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        # Inactive (archived) templates are read-only
        if obj and not obj.is_active:
            return False
        return super().has_change_permission(request, obj)
