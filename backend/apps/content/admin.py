from django.contrib import admin
from apps.content.models import ContentBlock


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "content_type", "is_active")
    list_filter = ("content_type", "is_active")
    search_fields = ("key", "title")
    list_editable = ("is_active",)
