from rest_framework import serializers

from apps.ai.models import AIAssistantConfig, ChatMessage, ChatSession


class AIConfigPublicSerializer(serializers.ModelSerializer):
    """What the frontend needs to render the chat UI — no admin-only fields."""

    class Meta:
        model = AIAssistantConfig
        fields = ("name", "greeting", "quick_replies")


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "role", "content", "created_at")


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ("id", "status", "collected_data", "messages", "created_at")


class ChatStartSerializer(serializers.Serializer):
    # Optional — existing client may pass their session id to continue chat
    session_id = serializers.UUIDField(required=False)


class ChatMessageInputSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    content = serializers.CharField(max_length=4000)


class ChatCollectDataSerializer(serializers.Serializer):
    """Frontend pushes structured onboarding data as the user fills the
    Stage I (company passport) + Stage II (role) registration questionnaire.
    """

    session_id = serializers.UUIDField()
    # Personal
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone_wa = serializers.CharField(max_length=20, required=False, allow_blank=True)
    # Stage I — company passport
    company = serializers.CharField(max_length=255, required=False, allow_blank=True)
    company_website = serializers.CharField(max_length=500, required=False, allow_blank=True)
    industry_field = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=255, required=False, allow_blank=True)
    employees_count = serializers.CharField(max_length=50, required=False, allow_blank=True)
    company_age = serializers.CharField(max_length=100, required=False, allow_blank=True)
    parent_company = serializers.CharField(max_length=255, required=False, allow_blank=True)
    # Stage II — role
    role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    # Legacy / optional
    industry_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    goals = serializers.CharField(max_length=1000, required=False, allow_blank=True)
