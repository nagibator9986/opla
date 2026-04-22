"""Serializers for accounts app.

Legacy bot-era serializers (OnboardingSerializer, DeeplinkCreateSerializer,
DeeplinkExchangeSerializer) were removed — their endpoints moved to
``apps.ai.views`` and use their own serializers in ``apps.ai.serializers``.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import ClientProfile


class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ["id", "name", "company", "phone_wa", "city", "industry"]
        read_only_fields = ["id"]
