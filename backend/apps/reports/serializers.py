"""Serializers for the reports app."""
from __future__ import annotations

from rest_framework import serializers

from apps.reports.models import AuditReport


class AuditReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditReport
        fields = ["id", "submission", "status", "pdf_url", "approved_at", "created_at"]
        read_only_fields = ["id", "submission", "status", "pdf_url", "approved_at", "created_at"]
