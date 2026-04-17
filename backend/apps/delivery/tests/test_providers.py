"""Tests for WhatsApp provider abstraction and Wazzup24 implementation."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from apps.delivery.providers.base import WhatsAppProvider
from apps.delivery.providers.wazzup24 import Wazzup24Provider


# ─── WhatsAppProvider ABC ────────────────────────────────────────────────────

def test_abstract_provider_cannot_instantiate():
    """WhatsAppProvider is abstract and cannot be instantiated directly (DLV-03)."""
    with pytest.raises(TypeError):
        WhatsAppProvider()  # type: ignore[abstract]


# ─── Wazzup24Provider ────────────────────────────────────────────────────────

def _make_provider() -> Wazzup24Provider:
    return Wazzup24Provider(api_key="test-api-key", channel_id="test-channel-id")


def _mock_response(message_id: str = "msg-123", status_code: int = 200) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {"messageId": message_id}
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = requests.HTTPError(
            response=mock_resp
        )
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp


def test_wazzup24_send_document_success():
    """Successful send_document returns messageId and sends correct request body (DLV-02)."""
    provider = _make_provider()
    mock_resp = _mock_response(message_id="abc-456")

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = provider.send_document(
            phone="77001234567",
            file_url="https://minio.example.com/file.pdf",
            caption="Ваш отчёт готов",
        )

    assert result == "abc-456"
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json") or call_kwargs[0][1]
    # Extract json from the call
    _, kwargs = mock_post.call_args
    request_json = kwargs["json"]
    assert request_json["channelId"] == "test-channel-id"
    assert request_json["chatId"] == "77001234567"
    assert request_json["chatType"] == "whatsapp"
    assert request_json["contentUri"] == "https://minio.example.com/file.pdf"
    assert request_json["text"] == "Ваш отчёт готов"


def test_wazzup24_normalizes_phone():
    """Phone '+77001234567' is normalized to '77001234567' in request chatId."""
    provider = _make_provider()
    mock_resp = _mock_response()

    with patch("requests.post", return_value=mock_resp) as mock_post:
        provider.send_document(
            phone="+77001234567",
            file_url="https://minio.example.com/file.pdf",
            caption="Test",
        )

    _, kwargs = mock_post.call_args
    assert kwargs["json"]["chatId"] == "77001234567"


def test_wazzup24_raises_on_http_error():
    """send_document raises requests.HTTPError on 5xx responses."""
    provider = _make_provider()
    mock_resp = _mock_response(status_code=500)

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(requests.HTTPError):
            provider.send_document(
                phone="77001234567",
                file_url="https://minio.example.com/file.pdf",
                caption="Test",
            )


def test_wazzup24_auth_header():
    """Authorization: Bearer header is set correctly."""
    provider = _make_provider()
    mock_resp = _mock_response()

    with patch("requests.post", return_value=mock_resp) as mock_post:
        provider.send_document(
            phone="77001234567",
            file_url="https://minio.example.com/file.pdf",
            caption="Test",
        )

    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test-api-key"
