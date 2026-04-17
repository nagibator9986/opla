from django.contrib import admin

from unfold.admin import ModelAdmin

from apps.content.models import ContentBlock


@admin.register(ContentBlock)
class ContentBlockAdmin(ModelAdmin):
    list_display = ("key", "title", "content_type", "is_active")
    list_filter = ("content_type", "is_active")
    search_fields = ("key", "title")
    list_editable = ("is_active",)
