import httpx
import logging
from bot.config import API_BASE_URL, BOT_API_SECRET

log = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=30.0,
            headers={"X-Bot-Token": BOT_API_SECRET},
        )
    return _client

async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None

# Bot-authenticated endpoints (X-Bot-Token)

async def onboard(telegram_id, name, company, industry_code="", phone_wa="", city=""):
    r = await get_client().post("/bot/onboarding/", json={
        "telegram_id": telegram_id, "name": name, "company": company,
        "industry_code": industry_code, "phone_wa": phone_wa, "city": city,
    })
    r.raise_for_status()
    return r.json()

async def create_deeplink(telegram_id):
    r = await get_client().post("/bot/deeplink/", json={"telegram_id": telegram_id})
    r.raise_for_status()
    return r.json()

async def get_industries():
    r = await get_client().get("/industries/")
    r.raise_for_status()
    return r.json()["results"]

async def get_jwt(telegram_id):
    r = await get_client().post("/bot/jwt/", json={"telegram_id": telegram_id})
    r.raise_for_status()
    return r.json()

async def get_active_submission(telegram_id):
    r = await get_client().get("/bot/active-submission/", params={"telegram_id": telegram_id})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

# JWT-authenticated endpoints (for submission operations)

async def _jwt_client(jwt_token):
    return httpx.AsyncClient(
        base_url=API_BASE_URL,
        timeout=30.0,
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

async def get_next_question(submission_id, jwt_token):
    async with await _jwt_client(jwt_token) as c:
        r = await c.get(f"/submissions/{submission_id}/next-question/")
        if r.status_code == 204:
            return None
        r.raise_for_status()
        return r.json()

async def save_answer(submission_id, question_id, value, jwt_token):
    async with await _jwt_client(jwt_token) as c:
        r = await c.post(f"/submissions/{submission_id}/answers/", json={
            "question_id": question_id, "value": value,
        })
        r.raise_for_status()
        return r.json()

async def complete_submission(submission_id, jwt_token):
    async with await _jwt_client(jwt_token) as c:
        r = await c.post(f"/submissions/{submission_id}/complete/")
        r.raise_for_status()
        return r.json()

async def get_submission_status(submission_id, jwt_token):
    async with await _jwt_client(jwt_token) as c:
        r = await c.get(f"/submissions/{submission_id}/")
        r.raise_for_status()
        return r.json()
