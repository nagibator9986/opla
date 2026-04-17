"""Serializers for Submission lifecycle API."""
from rest_framework import serializers

from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.payments.models import Tariff
from apps.submissions.models import Submission, Answer


class SubmissionCreateSerializer(serializers.Serializer):
    industry_code = serializers.CharField(max_length=50)
    tariff_code = serializers.CharField(max_length=50)

    def validate_industry_code(self, value):
        try:
            return Industry.objects.get(code=value, is_active=True)
        except Industry.DoesNotExist:
            raise serializers.ValidationError("Отрасль не найдена.")

    def validate_tariff_code(self, value):
        try:
            return Tariff.objects.get(code=value, is_active=True)
        except Tariff.DoesNotExist:
            raise serializers.ValidationError("Тариф не найден.")

    def create(self, validated_data):
        industry = validated_data["industry_code"]
        tariff = validated_data["tariff_code"]
        client = self.context["client"]

        template = QuestionnaireTemplate.objects.filter(
            industry=industry, is_active=True
        ).first()
        if not template:
            raise serializers.ValidationError(
                {"industry_code": "Для этой отрасли нет активной анкеты."}
            )

        return Submission.objects.create(
            client=client,
            template=template,
            tariff=tariff,
        )


class SubmissionDetailSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    industry_name = serializers.CharField(source="template.industry.name", read_only=True)
    total_questions = serializers.SerializerMethodField()
    answered_count = serializers.SerializerMethodField()
    tariff_code = serializers.CharField(source="tariff.code", read_only=True, default=None)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id", "status", "template_name", "industry_name",
            "total_questions", "answered_count",
            "tariff_code", "pdf_url",
            "created_at", "completed_at",
        ]
        read_only_fields = fields

    def get_total_questions(self, obj):
        return obj.template.questions.filter(required=True).count()

    def get_answered_count(self, obj):
        return obj.answers.count()

    def get_pdf_url(self, obj):
        report = getattr(obj, "report", None)
        return report.pdf_url if report and report.pdf_url else None


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "order", "text", "field_type", "options", "block", "required"]
        read_only_fields = fields


class AnswerCreateSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    value = serializers.JSONField()

    def validate(self, data):
        submission = self.context["submission"]
        try:
            question = submission.template.questions.get(id=data["question_id"])
        except Question.DoesNotExist:
            raise serializers.ValidationError(
                {"question_id": "Вопрос не принадлежит этой анкете."}
            )

        # Check duplicate
        if Answer.objects.filter(submission=submission, question=question).exists():
            raise serializers.ValidationError(
                {"question_id": "Ответ на этот вопрос уже сохранён."}
            )

        # Validate value by field_type
        value = data["value"]
        ft = question.field_type

        if ft == "text":
            if not isinstance(value, dict) or "text" not in value:
                raise serializers.ValidationError(
                    {"value": 'Ожидается формат {"text": "..."}'}
                )
        elif ft == "number":
            if not isinstance(value, dict) or "number" not in value:
                raise serializers.ValidationError(
                    {"value": 'Ожидается формат {"number": N}'}
                )
            if not isinstance(value["number"], (int, float)):
                raise serializers.ValidationError(
                    {"value": "number должен быть числом."}
                )
        elif ft == "choice":
            if not isinstance(value, dict) or "choice" not in value:
                raise serializers.ValidationError(
                    {"value": 'Ожидается формат {"choice": "option"}'}
                )
            valid_choices = question.options.get("choices", [])
            if valid_choices and value["choice"] not in valid_choices:
                raise serializers.ValidationError(
                    {"value": f"Выбор должен быть одним из: {valid_choices}"}
                )
        elif ft == "multichoice":
            if not isinstance(value, dict) or "choices" not in value:
                raise serializers.ValidationError(
                    {"value": 'Ожидается формат {"choices": ["a", "b"]}'}
                )
            if not isinstance(value["choices"], list):
                raise serializers.ValidationError(
                    {"value": "choices должен быть списком."}
                )
            valid_choices = question.options.get("choices", [])
            if valid_choices:
                invalid = set(value["choices"]) - set(valid_choices)
                if invalid:
                    raise serializers.ValidationError(
                        {"value": f"Недопустимые варианты: {invalid}"}
                    )

        data["question"] = question
        return data

    def create(self, validated_data):
        return Answer.objects.create(
            submission=self.context["submission"],
            question=validated_data["question"],
            value=validated_data["value"],
        )
