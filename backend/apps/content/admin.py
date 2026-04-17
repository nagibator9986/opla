from django.contrib import admin
from django.db import models

from django_ckeditor_5.widgets import CKEditor5Widget
from unfold.admin import ModelAdmin

from apps.content.models import ContentBlock


@admin.register(ContentBlock)
class ContentBlockAdmin(ModelAdmin):
    list_display = ("key", "title", "content_type", "is_active")
    list_filter = ("content_type", "is_active")
    search_fields = ("key", "title")
    list_editable = ("is_active",)
    formfield_overrides = {
        models.TextField: {
            "widget": CKEditor5Widget(config_name="content_block")
        },
    }
