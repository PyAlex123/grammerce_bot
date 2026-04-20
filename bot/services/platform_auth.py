import logging

import httpx
from aiogram.types import User

from bot.config import settings

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 5.0
_ENDPOINT = "/api/auth/telegram/issue"


class PlatformAuthError(Exception):
    """Raised when the platform fails to issue a Telegram auth link."""


async def issue_auth_link(tg_user: User) -> str:
    """Request a one-shot auth link from the platform for the given Telegram user.

    Returns the consume_url that the user must open in the browser.
    Raises PlatformAuthError on any network / HTTP / timeout failure.
    """
    url = f"{settings.PLATFORM_URL.rstrip('/')}{_ENDPOINT}"
    payload = {
        "telegram_id": str(tg_user.id),
        "first_name": tg_user.first_name,
        "last_name": tg_user.last_name,
        "username": tg_user.username,
        "photo_url": None,
    }
    headers = {
        "X-Bot-Secret": settings.PLATFORM_BOT_SHARED_SECRET,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "platform auth issue failed: HTTP %s %s",
            exc.response.status_code,
            exc.response.text[:200],
        )
        raise PlatformAuthError(
            f"platform returned HTTP {exc.response.status_code}"
        ) from exc
    except httpx.TimeoutException as exc:
        logger.error("platform auth issue timed out after %ss", _REQUEST_TIMEOUT)
        raise PlatformAuthError("platform request timed out") from exc
    except httpx.RequestError as exc:
        logger.error("platform auth issue network error: %s", exc)
        raise PlatformAuthError("platform is unreachable") from exc

    consume_url = data.get("consume_url")
    if not consume_url:
        logger.error("platform auth issue: no consume_url in response: %r", data)
        raise PlatformAuthError("platform response missing consume_url")
    return consume_url
