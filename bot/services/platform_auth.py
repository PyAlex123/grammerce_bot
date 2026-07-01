import logging
from dataclasses import dataclass

import httpx
from aiogram.types import User

from bot.config import settings

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 5.0
_ENDPOINT = "/api/auth/telegram/issue"


class PlatformAuthError(Exception):
    """Raised when the platform fails to issue a Telegram auth link."""


@dataclass(frozen=True)
class AuthLink:
    """Result of ``POST /api/auth/telegram/issue``.

    ``consume_url`` is the one-shot browser login link. ``has_shop`` drives the
    CTA label (create shop vs open platform); ``needs_setup`` mirrors the
    platform's onboarding flag (True when the user has no shop yet).
    """

    consume_url: str
    has_shop: bool
    needs_setup: bool


async def issue_auth(tg_user: User, lang: str | None = None) -> AuthLink:
    """Request an :class:`AuthLink` for a live aiogram Telegram user."""
    return await issue_auth_by(
        tg_user.id,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        username=tg_user.username,
        lang=lang,
    )


async def issue_auth_link(tg_user: User, lang: str | None = None) -> str:
    """Request a one-shot auth link for a live aiogram Telegram user.

    Thin wrapper around :func:`issue_auth_link_by` (kept for existing callers
    that have a full ``aiogram.types.User``)."""
    return await issue_auth_link_by(
        tg_user.id,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        username=tg_user.username,
        lang=lang,
    )


async def issue_auth_link_by(
    telegram_id: int,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
    lang: str | None = None,
) -> str:
    """Request a one-shot auth link from the platform by raw fields.

    Returns the consume_url only. Kept for callers that just need the link
    (register CTA, activation pushes). Use :func:`issue_auth_by` when the
    ``has_shop`` flag is needed too. Raises PlatformAuthError on any failure.
    """
    return (
        await issue_auth_by(
            telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            lang=lang,
        )
    ).consume_url


async def issue_auth_by(
    telegram_id: int,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
    lang: str | None = None,
) -> AuthLink:
    """Request an :class:`AuthLink` from the platform by raw fields.

    The ``consume_url`` logs the user in by telegram_id when opened in a browser.
    ``lang`` (ru/uz) is forwarded so the platform can open in the language chosen
    in the bot. Raises PlatformAuthError on any failure.
    """
    url = f"{settings.PLATFORM_URL.rstrip('/')}{_ENDPOINT}"
    payload = {
        "telegram_id": str(telegram_id),
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "photo_url": None,
        "lang": lang,
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
    return AuthLink(
        consume_url=consume_url,
        has_shop=bool(data.get("has_shop", False)),
        needs_setup=bool(data.get("needs_setup", True)),
    )
