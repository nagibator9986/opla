from rest_framework import serializers

from apps.cases.models import Case


class CaseListSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "slug",
            "title",
            "subtitle",
            "company_name",
            "industry",
            "logo_url",
            "metric",
            "metric_label",
            "short_text",
            "accent",
            "order",
        )

    def get_logo_url(self, obj: Case) -> str | None:
        if obj.logo:
            request = self.context.get("request")
            if request is not None:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class CaseDetailSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "slug",
            "title",
            "subtitle",
            "company_name",
            "industry",
            "logo_url",
            "cover_url",
            "metric",
            "metric_label",
            "short_text",
            "body",
            "accent",
            "published_at",
        )

    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get("request")
            if request is not None:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    def get_cover_url(self, obj):
        if obj.cover_image:
            request = self.context.get("request")
            if request is not None:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
