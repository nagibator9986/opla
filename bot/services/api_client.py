import asyncio
import logging

import httpx

from bot.config import API_BASE_URL, BOT_API_SECRET

log = logging.getLogger(__name__)


class APIError(Exception):
    """Raised when the Django API cannot satisfy a bot request.

    The message is safe to show to end users — handlers should catch this and
    reply with a friendly text instead of letting the bot crash.
    """


_client: httpx.AsyncClient | None = None
_DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
_TRANSPORT_RETRIES = 2  # handled at transport level, not per-request


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=_DEFAULT_TIMEOUT,
            headers={"X-Bot-Token": BOT_API_SECRET},
            transport=httpx.AsyncHTTPTransport(retries=_TRANSPORT_RETRIES),
        )
    return _client


async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


async def _request(method: str, url: str, *, client: httpx.AsyncClient | None = None, **kwargs) -> httpx.Response:
    """Single request with bounded app-level retries for transient errors.

    We retry on network errors and 5xx responses up to 3 attempts with a short
    exponential back-off. On the final failure we raise APIError which handlers
    translate into a user-facing message.
    """
    last_exc: Exception | None = None
    c = client or get_client()
    for attempt in range(3):
        try:
            resp = await c.request(method, url, **kwargs)
            if resp.status_code >= 500:
                log.warning(
                    "API %s %s -> %s (attempt %d/3): %s",
                    method, url, resp.status_code, attempt + 1, resp.text[:200],
                )
                last_exc = APIError(f"Сервис временно недоступен (HTTP {resp.status_code})")
                await asyncio.sleep(0.5 * (2**attempt))
                continue
            return resp
        except httpx.TimeoutException as e:
            log.warning("API %s %s timeout (attempt %d/3): %s", method, url, attempt + 1, e)
            last_exc = APIError("Превышено время ожидания. Попробуйте ещё раз.")
            await asyncio.sleep(0.5 * (2**attempt))
        except httpx.HTTPError as e:
            log.warning("API %s %s network error (attempt %d/3): %s", method, url, attempt + 1, e)
            last_exc = APIError("Ошибка соединения с сервисом.")
            await asyncio.sleep(0.5 * (2**attempt))
    assert last_exc is not None
    raise last_exc


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.status_code < 400:
        return
    log.warning("API %s %s -> %s: %s", resp.request.method, resp.url, resp.status_code, resp.text[:200])
    if resp.status_code in (401, 403):
        raise APIError("Сессия истекла, отправьте /start.")
    if resp.status_code == 404:
        raise APIError("Данные не найдены.")
    if 400 <= resp.status_code < 500:
        raise APIError("Некорректный запрос. Проверьте данные.")
    raise APIError("Сервис временно недоступен.")


# Bot-authenticated endpoints (X-Bot-Token)

async def onboard(telegram_id, name, company, industry_code="", phone_wa="", city=""):
    r = await _request("POST", "/bot/onboarding/", json={
        "telegram_id": telegram_id, "name": name, "company": company,
        "industry_code": industry_code, "phone_wa": phone_wa, "city": city,
    })
    _raise_for_status(r)
    return r.json()


async def create_deeplink(telegram_id):
    r = await _request("POST", "/bot/deeplink/", json={"telegram_id": telegram_id})
    _raise_for_status(r)
    return r.json()


async def get_industries():
    r = await _request("GET", "/industries/")
    _raise_for_status(r)
    return r.json()["results"]


async def get_jwt(telegram_id):
    r = await _request("POST", "/bot/jwt/", json={"telegram_id": telegram_id})
    _raise_for_status(r)
    return r.json()


async def get_active_submission(telegram_id):
    r = await _request("GET", "/bot/active-submission/", params={"telegram_id": telegram_id})
    if r.status_code == 404:
        return None
    _raise_for_status(r)
    return r.json()


# JWT-authenticated endpoints (for submission operations)

def _jwt_client(jwt_token: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=API_BASE_URL,
        timeout=_DEFAULT_TIMEOUT,
        headers={"Authorization": f"Bearer {jwt_token}"},
        transport=httpx.AsyncHTTPTransport(retries=_TRANSPORT_RETRIES),
    )


async def get_next_question(submission_id, jwt_token):
    async with _jwt_client(jwt_token) as c:
        r = await _request("GET", f"/submissions/{submission_id}/next-question/", client=c)
        if r.status_code == 204:
            return None
        _raise_for_status(r)
        return r.json()


async def save_answer(submission_id, question_id, value, jwt_token):
    async with _jwt_client(jwt_token) as c:
        r = await _request(
            "POST",
            f"/submissions/{submission_id}/answers/",
            json={"question_id": question_id, "value": value},
            client=c,
        )
        _raise_for_status(r)
        return r.json()


async def complete_submission(submission_id, jwt_token):
    async with _jwt_client(jwt_token) as c:
        r = await _request("POST", f"/submissions/{submission_id}/complete/", client=c)
        _raise_for_status(r)
        return r.json()


async def get_submission_status(submission_id, jwt_token):
    async with _jwt_client(jwt_token) as c:
        r = await _request("GET", f"/submissions/{submission_id}/", client=c)
        _raise_for_status(r)
        return r.json()
