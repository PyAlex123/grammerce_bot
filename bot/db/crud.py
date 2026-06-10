import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    BotDemoView,
    BotEvent,
    BotPushSend,
    BotSupportTicket,
    BotUser,
)

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


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> BotUser | None:
    """Read-only lookup by telegram_id. Returns None if not found."""
    result = await session.execute(
        select(BotUser).where(BotUser.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def mark_registered(session: AsyncSession, user: BotUser) -> bool:
    """Mark the user as registered on the platform.

    Returns True if this is the first time (caller should notify the admin),
    False if the user was already marked (duplicate — stay silent).
    """
    if user.registered_at is not None:
        return False
    user.registered_at = datetime.utcnow()
    await session.flush()
    return True


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


# ---------------------------------------------------------------------------
# Activation-funnel state + push bookkeeping
# ---------------------------------------------------------------------------

async def update_funnel_state(
    session: AsyncSession,
    user: BotUser,
    *,
    product_count: int | None = None,
    training_completed: bool | None = None,
    trial_ends_at: datetime | None = None,
    plan_paid: bool | None = None,
    store_created_at: datetime | None = None,
) -> None:
    """Upsert platform-fed funnel state onto the user.

    Only fields explicitly provided (not None) are written, so partial updates
    are safe. Records ``first_product_at`` the first time product_count goes
    from 0 to >0. ``store_created_at`` backfills ``registered_at`` only when it
    is still empty (never overwrites an existing registration time).
    """
    if product_count is not None:
        if product_count > 0 and user.product_count == 0 and user.first_product_at is None:
            user.first_product_at = datetime.utcnow()
        user.product_count = product_count
    if training_completed is not None:
        user.training_completed = training_completed
    if trial_ends_at is not None:
        user.trial_ends_at = trial_ends_at
    if plan_paid is not None:
        user.plan_paid = plan_paid
    if store_created_at is not None and user.registered_at is None:
        user.registered_at = store_created_at
    await session.flush()


async def record_push_sent(
    session: AsyncSession, user: BotUser, step: int, send_no: int
) -> bool:
    """Record that push (step, send_no) was sent to the user.

    Returns True if a new row was written, False if it already existed
    (idempotent — guards against double-sends on concurrent ticks).
    """
    send = BotPushSend(
        bot_user_id=user.id, step=step, send_no=send_no, sent_at=datetime.utcnow()
    )
    session.add(send)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return False
    return True


async def get_sent_steps(
    session: AsyncSession, user: BotUser, step: int
) -> set[int]:
    """Return the set of send_no values already sent for the given step."""
    result = await session.execute(
        select(BotPushSend.send_no).where(
            BotPushSend.bot_user_id == user.id, BotPushSend.step == step
        )
    )
    return set(result.scalars().all())


async def select_push_candidates(session: AsyncSession) -> list[BotUser]:
    """Owners eligible for activation pushes (paid plan turns all pushes off)."""
    result = await session.execute(
        select(BotUser).where(BotUser.plan_paid.is_(False))
    )
    return list(result.scalars().all())
