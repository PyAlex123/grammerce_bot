"""Партнёрские (реферальные) заходы: ?start=ref_<code>.

В отличие от :mod:`bot.services.platform_auth`, этот модуль **никогда** не
поднимает исключений наружу: трекинг реф-захода — fire-and-forget, любая
ошибка сети или бэкенда не должна мешать онбордингу пользователя.
"""
import logging
from dataclasses import dataclass

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 5.0
_ENDPOINT = "/api/platform/referrals/track"


@dataclass(frozen=True)
class ReferralDiscount:
    """Скидка на «заявку под ключ», которую вернула платформа.

    ``type``: ``percent`` (0..100) либо ``fixed`` (сумма в сумах).
    Применяет скидку сама платформа — бот только показывает приветствие.
    """

    type: str
    value: float
    label: str | None = None


async def track_referral(
    code: str,
    telegram_id: int,
    *,
    username: str | None = None,
    first_name: str | None = None,
) -> ReferralDiscount | None:
    """Сообщить платформе о заходе по реф-коду.

    Возвращает :class:`ReferralDiscount`, если код найден и активен, иначе
    ``None`` (неизвестный код, ошибка сети, таймаут, битый ответ).
    Идемпотентно на стороне бэкенда: повторный вызов тем же telegram_id не
    создаёт новый уникальный заход.
    """
    url = f"{settings.PLATFORM_URL.rstrip('/')}{_ENDPOINT}"
    payload = {
        "code": code,
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
    }
    headers = {
        "X-Bot-Secret": settings.PLATFORM_BOT_SHARED_SECRET,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.warning(
                "referral track failed: HTTP %s %s",
                response.status_code,
                response.text[:200],
            )
            return None
        data = response.json()
    except Exception as exc:  # сеть, таймаут, битый JSON — молча продолжаем
        logger.warning("referral track failed for code %r: %s", code, exc)
        return None

    if not isinstance(data, dict) or data.get("ok") is not True:
        return None

    discount = data.get("discount")
    if not isinstance(discount, dict):
        return None
    raw_value = discount.get("value")
    if raw_value is None:
        return None
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        logger.warning("referral track: bad discount value %r", raw_value)
        return None

    d_type = "percent" if discount.get("type") == "percent" else "fixed"
    return ReferralDiscount(type=d_type, value=value, label=data.get("label"))
