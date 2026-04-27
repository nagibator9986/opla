"""Endpoints for the multi-participant Ashide 2 flow."""
from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.industries.models import Question
from apps.submissions.group_invites import (
    create_group,
    participant_summary,
    send_email_invitation,
)
from apps.submissions.models import (
    Answer,
    AuditGroup,
    AuditParticipant,
    Submission,
)
from apps.submissions.views import _get_client_profile

log = logging.getLogger(__name__)


class ParticipantInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone_wa = serializers.CharField(max_length=30, required=False, allow_blank=True)


class CreateGroupSerializer(serializers.Serializer):
    submission_id = serializers.UUIDField()
    quorum_size = serializers.IntegerField(min_value=3, max_value=7)
    invitation_text = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    participants = ParticipantInputSerializer(many=True)


class CreateGroupView(APIView):
    """POST /api/v1/audit-groups/ — инициатор создаёт группу из 3–7 участников.

    Требует JWT инициатора. Submission должен быть оплачен и принадлежать
    клиенту, у которого тариф = ashide_2.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CreateGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        client = _get_client_profile(request.user)
        if not client:
            return Response({"detail": "Профиль клиента не найден."}, status=403)

        try:
            submission = Submission.objects.select_for_update().get(
                pk=data["submission_id"], client=client,
            )
        except Submission.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=404)

        if submission.status not in (
            Submission.Status.PAID,
            Submission.Status.IN_PROGRESS_FULL,
        ):
            return Response(
                {"detail": "Группу можно создать только после оплаты тарифа."},
                status=400,
            )
        if not submission.tariff or submission.tariff.code != "ashide_2":
            return Response(
                {"detail": "Группа доступна только для пакета Ashıde 2."},
                status=400,
            )

        group = create_group(
            submission=submission,
            quorum_size=data["quorum_size"],
            participants_data=[dict(p) for p in data["participants"]],
            invitation_text=data.get("invitation_text", "") or "",
        )

        # Отправляем email каждому (ошибки гасятся; админ может перепослать)
        for p in group.participants.all():
            send_email_invitation(p)

        return Response(
            {
                "group_id": group.id,
                "quorum_size": group.quorum_size,
                "completed_count": group.completed_count,
                "participants": [participant_summary(p) for p in group.participants.all()],
            },
            status=status.HTTP_201_CREATED,
        )


class GroupStatusView(APIView):
    """GET /api/v1/audit-groups/by-submission/<submission_id>/ — состояние группы."""

    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        client = _get_client_profile(request.user)
        if not client:
            return Response({"detail": "Профиль клиента не найден."}, status=403)
        try:
            submission = Submission.objects.get(pk=submission_id, client=client)
        except Submission.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=404)
        try:
            group = submission.audit_group
        except AuditGroup.DoesNotExist:
            return Response({"detail": "Группа ещё не создана."}, status=404)

        return Response(
            {
                "group_id": group.id,
                "quorum_size": group.quorum_size,
                "completed_count": group.completed_count,
                "is_quorum_complete": group.is_quorum_complete,
                "participants": [
                    participant_summary(p) for p in group.participants.all()
                ],
            }
        )


# ─── Public participant endpoints (no auth — token-based) ───────────────


class ParticipantContextView(APIView):
    """GET /api/v1/invite/<token>/ — участник открывает страницу опроса.

    Возвращает: данные шаблона анкеты + следующий вопрос (учитывает
    предыдущие ответы и условную логику).
    """

    permission_classes = [AllowAny]

    def get(self, request, token):
        participant = _resolve_participant(token)
        if isinstance(participant, Response):
            return participant
        return _participant_state(participant)


class ParticipantAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    value = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    values = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )


class ParticipantAnswerView(APIView):
    """POST /api/v1/invite/<token>/answer/ — сохранить ответ + получить следующий."""

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, token):
        participant = _resolve_participant(token)
        if isinstance(participant, Response):
            return participant

        serializer = ParticipantAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        # Создаём собственный Submission участника, если ещё нет
        if participant.submission_id is None:
            template = participant.group.initiator_submission.template
            sub = Submission.objects.create(
                client=participant.group.initiator_submission.client,
                template=template,
                tariff=participant.group.initiator_submission.tariff,
            )
            try:
                sub.start_onboarding(); sub.save()
                sub.mark_paid(); sub.save()
                sub.start_questionnaire(); sub.save()
            except Exception:
                pass
            participant.submission = sub
            participant.status = AuditParticipant.Status.IN_PROGRESS
            participant.started_at = timezone.now()
            participant.save(update_fields=["submission", "status", "started_at", "updated_at"])

        # Сохраняем ответ через тот же движок, что и в чате
        from apps.ai.questionnaire import next_question, save_answer, try_complete

        try:
            question = participant.submission.template.questions.get(pk=payload["question_id"])
        except Question.DoesNotExist:
            return Response({"detail": "Вопрос не найден."}, status=404)

        raw: Any = payload.get("values") or payload.get("value") or ""
        try:
            save_answer(participant.submission, question, raw)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        # Завершено?
        if try_complete(participant.submission):
            participant.status = AuditParticipant.Status.COMPLETED
            participant.completed_at = timezone.now()
            participant.save(update_fields=["status", "completed_at", "updated_at"])
            return Response({
                "completed": True,
                "thanks": (
                    "Спасибо! Ваши ответы сохранены и анонимно переданы "
                    "эксперту Baqsy для формирования отчёта."
                ),
                "progress": _progress(participant),
            })

        upcoming = next_question(participant.submission)
        if upcoming is None:
            return Response({"completed": True, "progress": _progress(participant)})

        return Response({
            "completed": False,
            "next_question": upcoming.to_payload(),
            "progress": _progress(participant),
        })


# ─── helpers ────────────────────────────────────────────────────────────


def _resolve_participant(token: str):
    try:
        return AuditParticipant.objects.select_related(
            "group", "group__initiator_submission",
            "group__initiator_submission__client",
            "submission", "submission__template",
        ).get(invite_token=token)
    except AuditParticipant.DoesNotExist:
        return Response(
            {"detail": "Ссылка не найдена или истекла. Запросите новую у инициатора."},
            status=404,
        )


def _participant_state(participant: AuditParticipant):
    from apps.ai.questionnaire import next_question, visible_questions_for

    sub = participant.submission
    intro_company = (
        participant.group.initiator_submission.client.company
        if participant.group.initiator_submission.client
        else "компании"
    )

    if sub is None:
        # Ещё не начал отвечать — отдадим первый вопрос исходного шаблона
        template = participant.group.initiator_submission.template
        return Response({
            "participant": {
                "name": participant.name,
                "company": intro_company,
                "status": participant.status,
            },
            "intro": (
                "Здравствуйте! Это анкета группового аудита для "
                f"«{intro_company}». Вы — один из {participant.group.quorum_size} "
                "участников; ваши ответы конфиденциальны и видны только "
                "эксперту, готовящему отчёт."
            ),
            "first_question": _first_question_payload(template),
            "progress": {"done": 0, "total": _total_for_template(template)},
        })

    visible = visible_questions_for(sub)
    answered = sub.answers.count()
    upcoming = next_question(sub)
    return Response({
        "participant": {
            "name": participant.name,
            "company": intro_company,
            "status": participant.status,
        },
        "next_question": upcoming.to_payload() if upcoming else None,
        "completed": upcoming is None,
        "progress": {"done": answered, "total": len(visible)},
    })


def _first_question_payload(template) -> dict:
    from apps.ai.questionnaire import _render

    q = template.questions.order_by("order").first()
    if q is None:
        return {}
    return _render(q, done=0, total=template.questions.count()).to_payload()


def _total_for_template(template) -> int:
    """Грубая оценка длины — без учёта conditional логики."""
    return template.questions.count()


def _progress(participant) -> dict:
    sub = participant.submission
    if sub is None:
        return {"done": 0, "total": 0}
    from apps.ai.questionnaire import visible_questions_for
    visible = visible_questions_for(sub)
    return {"done": sub.answers.count(), "total": len(visible)}
