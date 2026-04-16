"""Serializers for accounts app (onboarding, deep-link, client profile)."""
from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import ClientProfile


class OnboardingSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    company = serializers.CharField(max_length=255)
    industry_code = serializers.CharField(max_length=50, required=False)
    phone_wa = serializers.CharField(max_length=20, required=False, default="")
    city = serializers.CharField(max_length=100, required=False, default="")


class DeeplinkCreateSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()


class DeeplinkExchangeSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ["id", "telegram_id", "name", "company", "phone_wa", "city", "industry"]
        read_only_fields = ["id", "telegram_id"]
