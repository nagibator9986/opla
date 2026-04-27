"""Multi-participant audit invitations.

Used by:
* AI chat (бот спрашивает у инициатора кол-во участников + контакты)
* Admin (для повторной отправки писем)

Channel strategy:
* Email — SMTP через Django (требует EMAIL_HOST настроек)
* WhatsApp — генерируем ссылку wa.me с pre-filled текстом. Инициатор
  сам перешлёт (или мы дадим список ссылок при создании группы).
"""
from __future__ import annotations

import logging
import uuid
from urllib.parse import quote_plus

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.submissions.models import AuditGroup, AuditParticipant, Submission

log = logging.getLogger(__name__)


DEFAULT_INVITATION_TEXT = (
    "Добрый день! Вы включены в группу экспертной оценки состояния компании "
    "{{company}} по Коду Вечного Иля. Цель — выявить системные риски и "
    "точки потери эффективности. Ваши ответы конфиденциальны и будут "
    "использованы ИИ для формирования консолидированного отчёта.\n\n"
    "Пройти опрос: {{link}}"
)


def _build_invite_url(token: str) -> str:
    base = getattr(settings, "SITE_URL", "").rstrip("/") or "https://baqsy.tnriazun.com"
    return f"{base}/invite/{token}"


def _wa_me_link(phone: str, text: str) -> str | None:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if not digits:
        return None
    return f"https://wa.me/{digits}?text={quote_plus(text)}"


def _render_invitation(template: str, *, company: str, link: str) -> str:
    out = template or DEFAULT_INVITATION_TEXT
    out = out.replace("{{company}}", company or "вашей компании")
    out = out.replace("{{link}}", link)
    return out


@transaction.atomic
def create_group(
    *,
    submission: Submission,
    quorum_size: int,
    participants_data: list[dict],
    invitation_text: str = "",
) -> AuditGroup:
    """Создать группу аудита и заготовить участников.

    `participants_data` — список dict-ов: {name, email, phone_wa}. Длина
    должна совпадать с quorum_size. Уникальные invite_tokens создаются здесь
    же. Инициатор НЕ входит в эту коллекцию — у него своя анкета.
    """
    if not 3 <= quorum_size <= 7:
        raise ValueError("quorum_size должно быть от 3 до 7.")
    if len(participants_data) != quorum_size:
        raise ValueError(
            f"Передано {len(participants_data)} участников, а quorum_size={quorum_size}."
        )

    group, _ = AuditGroup.objects.get_or_create(
        initiator_submission=submission,
        defaults={"quorum_size": quorum_size, "invitation_text": invitation_text},
    )
    # Удаляем предыдущих, если сценарий «пересоздать группу»
    group.participants.all().delete()
    group.quorum_size = quorum_size
    group.invitation_text = invitation_text
    group.save(update_fields=["quorum_size", "invitation_text", "updated_at"])

    for data in participants_data:
        token = uuid.uuid4().hex
        AuditParticipant.objects.create(
            group=group,
            name=(data.get("name") or "").strip(),
            email=(data.get("email") or "").strip().lower(),
            phone_wa=(data.get("phone_wa") or "").strip(),
            invite_token=token,
        )
    return group


def send_email_invitation(participant: AuditParticipant) -> bool:
    """Отправить SMTP-приглашение участнику. Возвращает True при успехе.

    Гасит ошибки в лог — приглашение можно перепослать руками или через
    wa.me-кнопку, поэтому фейл одного канала не должен валить флоу.
    """
    if not participant.email:
        return False
    company = (
        participant.group.initiator_submission.client.company
        if participant.group.initiator_submission.client
        else "вашей компании"
    )
    link = _build_invite_url(participant.invite_token)
    text = _render_invitation(
        participant.group.invitation_text or DEFAULT_INVITATION_TEXT,
        company=company,
        link=link,
    )
    subject = f"Аудит «Digital Baqsylyq» · {company}"
    try:
        send_mail(
            subject=subject,
            message=text,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@baqsy.kz"),
            recipient_list=[participant.email],
            fail_silently=False,
        )
        participant.last_email_sent_at = timezone.now()
        participant.save(update_fields=["last_email_sent_at", "updated_at"])
        log.info("invitation: emailed participant=%s", participant.id)
        return True
    except Exception as exc:
        log.warning("invitation: email failed for participant=%s: %s", participant.id, exc)
        return False


def participant_summary(participant: AuditParticipant) -> dict:
    """Что нужно фронту/админке для строки участника."""
    company = (
        participant.group.initiator_submission.client.company
        if participant.group.initiator_submission.client
        else "вашей компании"
    )
    invite_url = _build_invite_url(participant.invite_token)
    text = _render_invitation(
        participant.group.invitation_text or DEFAULT_INVITATION_TEXT,
        company=company,
        link=invite_url,
    )
    return {
        "id": participant.id,
        "name": participant.name,
        "email": participant.email,
        "phone_wa": participant.phone_wa,
        "status": participant.status,
        "invite_url": invite_url,
        "wa_me_url": _wa_me_link(participant.phone_wa, text),
        "invited_at": participant.invited_at,
        "completed_at": participant.completed_at,
    }
