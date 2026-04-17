from django.contrib import admin

from unfold.admin import ModelAdmin, TabularInline

from apps.submissions.models import Submission, Answer


class AnswerInline(TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "value", "answered_at")


@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):
    list_display = ("id", "client", "template", "tariff", "status", "created_at")
    list_filter = ("status", "tariff", "template__industry")
    search_fields = ("client__name", "client__company")
    readonly_fields = ("id", "template", "created_at")
    inlines = [AnswerInline]
