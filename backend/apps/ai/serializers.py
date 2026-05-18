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


import re

ALLOWED_ROLES = {
    "Владелец / Совладелец",
    "Топ-менеджер",
    "Менеджер среднего / нижнего звена",
}


def _validate_meaningful_text(value: str, *, field_label: str, min_len: int = 2) -> str:
    """Базовая защита от мусорного ввода.

    Отбивает:
      • строки короче min_len символов
      • строки только из спецсимволов / повторений одной буквы (вроде "ааа", "...")
      • строки только из цифр когда ожидается текст
    """
    if not value:
        return value
    v = value.strip()
    if len(v) < min_len:
        raise serializers.ValidationError(
            f"{field_label}: укажите не менее {min_len} символов."
        )
    # Не разрешаем строки только из одной повторяющейся буквы (аааа, бббббб)
    if len(set(v.lower().replace(" ", ""))) <= 1:
        raise serializers.ValidationError(
            f"{field_label}: похоже на случайный набор символов. Введите корректно."
        )
    # Должна быть хотя бы одна буква (русская или латинская)
    if not re.search(r"[A-Za-zА-Яа-яЁёҚқҢңӨөҮүҰұІіҺһҒғӘә]", v):
        raise serializers.ValidationError(
            f"{field_label}: должно содержать буквы."
        )
    return v


class ChatCollectDataSerializer(serializers.Serializer):
    """Frontend pushes structured onboarding data as the user fills the
    Stage I (company passport) + Stage II (role) registration questionnaire.

    Server-side валидация защищает от случайного и мусорного ввода —
    «абвгде», «....», повторений одной буквы и т.д.
    """

    session_id = serializers.UUIDField()
    # Personal
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone_wa = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
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

    # Validators per field
    def validate_name(self, value):
        if not value:
            return value
        v = value.strip()
        if len(v) < 4:
            raise serializers.ValidationError(
                "Имя: укажите имя и фамилию полностью (минимум 4 символа)."
            )
        # Только буквы, пробелы, дефисы, точки, апострофы
        if not re.match(r"^[A-Za-zА-Яа-яЁёҚқҢңӨөҮүҰұІіҺһҒғӘә][A-Za-zА-Яа-яЁёҚқҢңӨөҮүҰұІіҺһҒғӘә\s\-\.']+$", v):
            raise serializers.ValidationError(
                "Имя: только буквы, пробелы, дефисы (без цифр и символов)."
            )
        # Должно быть минимум 2 слова (имя + фамилия), каждое ≥ 2 букв
        words = [w for w in re.split(r"[\s\-]+", v) if w]
        if len(words) < 2:
            raise serializers.ValidationError(
                "Имя: укажите имя И фамилию (через пробел)."
            )
        if any(len(w) < 2 for w in words):
            raise serializers.ValidationError(
                "Имя: слишком короткие слова. Каждое слово — минимум 2 буквы."
            )
        # Защита от 'аааа бббб' — каждое слово должно иметь разные буквы
        if any(len(set(w.lower())) <= 1 for w in words):
            raise serializers.ValidationError(
                "Имя: похоже на случайный набор символов. Введите настоящее имя."
            )
        return v

    def validate_company(self, value):
        if not value:
            return value
        return _validate_meaningful_text(value, field_label="Компания", min_len=2)

    def validate_industry_field(self, value):
        if not value:
            return value
        return _validate_meaningful_text(value, field_label="Сфера деятельности", min_len=2)

    def validate_city(self, value):
        if not value:
            return value
        return _validate_meaningful_text(value, field_label="Локация", min_len=2)

    def validate_company_age(self, value):
        if not value:
            return value
        v = value.strip()
        # Короткие ответы как «1», «5», «12», «новая» — все валидны.
        # Минимум 1 символ. Запрещаем только пустоту и одни спецсимволы.
        if len(v) < 1:
            raise serializers.ValidationError("Срок существования: введите ответ.")
        if not re.search(r"[\w]", v, re.UNICODE):
            raise serializers.ValidationError(
                "Срок существования: введите осмысленный ответ."
            )
        return v

    def validate_parent_company(self, value):
        if not value:
            return value
        return _validate_meaningful_text(value, field_label="Головная компания", min_len=2)

    def validate_employees_count(self, value):
        if not value:
            return value
        v = value.strip()
        # Короткие числовые ответы как «5», «25», «200» валидны.
        # Должна быть хотя бы одна цифра.
        if not re.search(r"\d", v):
            raise serializers.ValidationError(
                "Количество сотрудников: укажите число (например, 5, 25, 200)."
            )
        return v

    def validate_role(self, value):
        if not value:
            return value
        v = value.strip()
        if v not in ALLOWED_ROLES:
            raise serializers.ValidationError(
                "Уровень ответственности: выберите один из предложенных вариантов."
            )
        return v
