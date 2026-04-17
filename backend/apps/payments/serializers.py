from rest_framework import serializers

from apps.payments.models import Tariff


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ["id", "code", "title", "price_kzt", "description"]
