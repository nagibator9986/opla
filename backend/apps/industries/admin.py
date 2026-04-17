from django.contrib import admin

from unfold.admin import ModelAdmin, TabularInline

from apps.industries.models import Industry, QuestionnaireTemplate, Question


class QuestionInline(TabularInline):
    model = Question
    extra = 0
    ordering = ["order"]


@admin.register(Industry)
class IndustryAdmin(ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    prepopulated_fields = {"code": ("name",)}


@admin.register(QuestionnaireTemplate)
class QuestionnaireTemplateAdmin(ModelAdmin):
    list_display = ("name", "industry", "version", "is_active", "published_at")
    list_filter = ("industry", "is_active")
    inlines = [QuestionInline]
    readonly_fields = ("version",)
