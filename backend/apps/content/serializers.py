"""Serializers for ContentBlock API."""
from rest_framework import serializers

from apps.content.models import ContentBlock


class ContentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentBlock
        fields = ["key", "content", "content_type"]
        read_only_fields = fields
