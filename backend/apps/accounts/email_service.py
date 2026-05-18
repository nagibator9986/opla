"""Resend HTTP API client + 6-digit code generator/validator.

Хранение кода — в `ChatSession.collected_data` (без новой модели/миграции).
Поля: email, email_code, email_code_expires (ISO), email_code_attempts (int),
email_verified (bool).
"""
from __future__ import annotations

import json
import logging
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

from django.conf import settings

log = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def gen_code() -> str:
    """Безопасный 6-значный код."""
    n = secrets.randbelow(1_000_000)
    return f"{n:06d}"


def make_email_state(code: str) -> dict:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.EMAIL_CODE_TTL_MINUTES
    )
    return {
        "email_code": code,
        "email_code_expires": expires.isoformat(),
        "email_code_attempts": 0,
        "email_verified": False,
    }


def verify_code(state: dict, provided: str) -> tuple[bool, str]:
    """Сверяет введённый код. Возвращает (ok, message).

    state — обновляется in-place: attempts++, email_verified=True при успехе.
    """
    expected = (state or {}).get("email_code") or ""
    if not expected:
        return False, "Код не отправлен. Запросите новый."
    # TTL
    exp_iso = (state or {}).get("email_code_expires") or ""
    try:
        exp_dt = datetime.fromisoformat(exp_iso)
    except Exception:
        exp_dt = None
    if exp_dt and datetime.now(timezone.utc) > exp_dt:
        return False, "Код истёк. Запросите новый."
    # Attempts
    attempts = int(state.get("email_code_attempts") or 0)
    if attempts >= settings.EMAIL_CODE_MAX_ATTEMPTS:
        return False, "Слишком много попыток. Запросите новый код."
    state["email_code_attempts"] = attempts + 1
    if (provided or "").strip() != expected:
        left = settings.EMAIL_CODE_MAX_ATTEMPTS - state["email_code_attempts"]
        return False, f"Неверный код. Осталось попыток: {left}."
    state["email_verified"] = True
    return True, "OK"


def _render_email_html(code: str, name: str = "") -> str:
    greet = f"Здравствуйте, {name}!" if name else "Здравствуйте!"
    return f"""
<!doctype html>
<html lang="ru">
<head><meta charset="utf-8"><title>Код подтверждения Baqsy</title></head>
<body style="margin:0;padding:0;background:#f5f5f4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f5f5f4;padding:40px 20px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:520px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(15,23,42,0.06);">
        <tr><td style="padding:32px 32px 24px;background:linear-gradient(135deg,#0f172a,#1e293b);color:#ffffff;">
          <h1 style="margin:0;font-size:20px;font-weight:700;letter-spacing:-0.01em;">Baqsy System</h1>
          <p style="margin:4px 0 0;font-size:13px;color:#cbd5e1;">Платформа бизнес-аудита</p>
        </td></tr>
        <tr><td style="padding:32px;">
          <p style="margin:0 0 16px;font-size:16px;color:#0f172a;">{greet}</p>
          <p style="margin:0 0 24px;font-size:14px;line-height:1.6;color:#334155;">
            Это ваш код подтверждения email для завершения регистрации в Baqsy System.
            Введите его в окне чата на сайте.
          </p>
          <div style="text-align:center;padding:24px 0;background:#f8fafc;border-radius:12px;margin-bottom:24px;">
            <div style="font-family:'SF Mono','Monaco','Menlo',monospace;font-size:32px;font-weight:700;letter-spacing:0.4em;color:#0f172a;padding-left:0.4em;">
              {code}
            </div>
          </div>
          <p style="margin:0 0 8px;font-size:13px;color:#64748b;">
            Код действителен <strong>{settings.EMAIL_CODE_TTL_MINUTES} минут</strong>. Никому его не передавайте.
          </p>
          <p style="margin:0;font-size:13px;color:#64748b;">
            Если вы не запрашивали код — просто проигнорируйте это письмо.
          </p>
        </td></tr>
        <tr><td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #e2e8f0;font-size:12px;color:#94a3b8;text-align:center;">
          © Baqsy System · {settings.PUBLIC_SITE_URL.replace('https://', '').replace('http://', '')}
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
""".strip()


def send_verification_code(to_email: str, code: str, name: str = "") -> tuple[bool, Optional[str]]:
    """Отправка письма через Resend HTTP API.

    Если RESEND_API_KEY не задан — пишет код в логи (console fallback).
    Возвращает (ok, error_message).
    """
    to_email = (to_email or "").strip().lower()
    if not to_email:
        return False, "Email не указан."

    api_key = (settings.RESEND_API_KEY or "").strip()
    if not api_key:
        log.warning(
            "[EMAIL CONSOLE FALLBACK] Verification code for %s: %s (RESEND_API_KEY is empty)",
            to_email, code,
        )
        return True, None

    payload = {
        "from": settings.EMAIL_FROM_ADDR,
        "to": [to_email],
        "subject": "Код подтверждения Baqsy — " + code,
        "html": _render_email_html(code, name=name),
        "text": (
            f"Ваш код подтверждения Baqsy: {code}\n\n"
            f"Код действителен {settings.EMAIL_CODE_TTL_MINUTES} минут. "
            "Никому его не передавайте.\n\nBaqsy System"
        ),
    }
    reply_to = (settings.EMAIL_REPLY_TO or "").strip()
    if reply_to:
        payload["reply_to"] = reply_to

    req = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Resend behind Cloudflare блокирует default Python-urllib UA (1010).
            "User-Agent": "Baqsy-Backend/1.0 (baqsy.tnriazun.com)",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            body = ""
        log.error(
            "Resend rejected email for %s: HTTP %s body=%s",
            to_email, exc.code, body,
        )
        return False, f"Email не доставлен (код {exc.code}). Попробуйте позже."
    except (urllib.error.URLError, OSError) as exc:
        log.error("Resend network error for %s: %s", to_email, exc)
        return False, "Сервис email-уведомлений временно недоступен."

    if status not in (200, 201, 202):
        log.error("Resend unexpected status for %s: %s", to_email, status)
        return False, f"Email не доставлен (код {status}). Попробуйте позже."

    log.info("Verification email sent to %s, code length=%d", to_email, len(code))
    return True, None
