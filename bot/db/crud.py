import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import BotDemoView, BotEvent, BotSupportTicket, BotUser

logger = logging.getLogger(__name__)


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
) -> tuple[BotUser, bool]:
    """Returns (user, created). Safe against duplicate telegram_id."""
    result = await session.execute(
        select(BotUser).where(BotUser.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = BotUser(
            telegram_id=telegram_id,
            username=username,
            first_seen_at=datetime.utcnow(),
            last_active_at=datetime.utcnow(),
        )
        session.add(user)
        await session.flush()
        return user, True

    user.last_active_at = datetime.utcnow()
    if username and user.username != username:
        user.username = username
    await session.flush()
    return user, False


async def set_language(session: AsyncSession, user: BotUser, language: str) -> None:
    user.language = language
    await session.flush()


async def save_utm(
    session: AsyncSession,
    user: BotUser,
    utm_source: str | None,
    utm_medium: str | None,
    utm_campaign: str | None,
) -> None:
    """Saves UTM only on first /start (never overwrites)."""
    if user.utm_source is not None:
        return
    user.utm_source = utm_source
    user.utm_medium = utm_medium
    user.utm_campaign = utm_campaign
    await session.flush()


async def log_demo_view(
    session: AsyncSession, user: BotUser, niche: str
) -> BotDemoView:
    view = BotDemoView(
        bot_user_id=user.id, niche=niche, viewed_at=datetime.utcnow()
    )
    session.add(view)
    await session.flush()
    return view


async def create_ticket(
    session: AsyncSession, user: BotUser, message: str
) -> BotSupportTicket:
    ticket = BotSupportTicket(
        bot_user_id=user.id,
        message=message,
        status="open",
        created_at=datetime.utcnow(),
    )
    session.add(ticket)
    await session.flush()
    return ticket


async def log_event(
    session: AsyncSession,
    user: BotUser,
    event_type: str,
    payload: dict | None = None,
) -> BotEvent:
    event = BotEvent(
        bot_user_id=user.id,
        event_type=event_type,
        payload=payload,
        created_at=datetime.utcnow(),
    )
    session.add(event)
    await session.flush()
    return event
