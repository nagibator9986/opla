import logging

import requests

from .base import WhatsAppProvider

log = logging.getLogger(__name__)


class Wazzup24Provider(WhatsAppProvider):
    BASE_URL = "https://api.wazzup24.com/v3/message"

    def __init__(self, api_key: str, channel_id: str):
        self.api_key = api_key
        self.channel_id = channel_id

    def send_document(self, phone: str, file_url: str, caption: str) -> str:
        # Нормализовать телефон: убрать "+" если есть
        normalized_phone = phone.lstrip("+")

        resp = requests.post(
            self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "channelId": self.channel_id,
                "chatId": normalized_phone,
                "chatType": "whatsapp",
                "text": caption,
                "contentUri": file_url,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        message_id = str(data.get("messageId", ""))
        log.info("Wazzup24: sent to %s, messageId=%s", normalized_phone, message_id)
        return message_id

    def send_text(self, phone: str, text: str) -> str:
        """Send a plain text message (no attachment) — для magic-link и нотификаций."""
        normalized_phone = phone.lstrip("+")
        resp = requests.post(
            self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "channelId": self.channel_id,
                "chatId": normalized_phone,
                "chatType": "whatsapp",
                "text": text,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        message_id = str(data.get("messageId", ""))
        log.info("Wazzup24: text to %s, messageId=%s", normalized_phone, message_id)
        return message_id
