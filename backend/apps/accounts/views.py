"""Accounts views — intentionally empty.

The legacy Telegram-bot endpoints (onboarding, deeplink, JWT issuance) were
removed when the product switched to an AI-chat-driven onboarding. The new
equivalents live in ``apps.ai.views``:

* ``POST /api/v1/chat/start/``     — create a chat session
* ``POST /api/v1/chat/message/``   — talk to the assistant
* ``POST /api/v1/chat/collect/``   — push gathered profile data
* ``POST /api/v1/chat/auth-token/`` — exchange a qualified session for a JWT pair
"""
