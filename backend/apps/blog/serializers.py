from rest_framework import serializers

from apps.blog.models import BlogPost


class BlogPostListSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = BlogPost
        fields = (
            "slug",
            "title",
            "excerpt",
            "category",
            "category_label",
            "cover_url",
            "reading_time_min",
            "published_at",
        )

    def get_cover_url(self, obj):
        if not obj.cover_image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.cover_image.url)
        return obj.cover_image.url


class BlogPostDetailSerializer(BlogPostListSerializer):
    class Meta(BlogPostListSerializer.Meta):
        fields = BlogPostListSerializer.Meta.fields + ("body",)
