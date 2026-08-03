import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    BotBroadcast,
    BotDemoView,
    BotEvent,
    BotPushSend,
    BotSupportTicket,
    BotUser,
    SurveyResponse,
    SurveySource,
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


async def get_step_sends(
    session: AsyncSession, user: BotUser, step: int
) -> dict[int, datetime]:
    """Return {send_no: sent_at} for pushes already sent for the given step."""
    result = await session.execute(
        select(BotPushSend.send_no, BotPushSend.sent_at).where(
            BotPushSend.bot_user_id == user.id, BotPushSend.step == step
        )
    )
    return {send_no: sent_at for send_no, sent_at in result.all()}


async def last_push_sent_at(
    session: AsyncSession, user: BotUser
) -> datetime | None:
    """Timestamp of the most recent push to the user across all steps (for the
    per-user daily cap), or None if none sent yet."""
    result = await session.execute(
        select(func.max(BotPushSend.sent_at)).where(
            BotPushSend.bot_user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def select_push_candidates(session: AsyncSession) -> list[BotUser]:
    """Owners eligible for activation pushes (paid plan turns all pushes off)."""
    result = await session.execute(
        select(BotUser).where(BotUser.plan_paid.is_(False))
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Research survey
# ---------------------------------------------------------------------------

async def save_survey_source(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    source: str,
) -> SurveySource:
    """Record a research deep-link click. Idempotent: duplicate (user, source)
    pairs are silently ignored via the unique constraint."""
    row = SurveySource(user_id=telegram_id, username=username, source=source)
    session.add(row)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        result = await session.execute(
            select(SurveySource).where(
                SurveySource.user_id == telegram_id,
                SurveySource.source == source,
            )
        )
        row = result.scalar_one()
    return row


async def save_survey_response(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    payload: dict,
) -> SurveyResponse:
    """Persist a completed survey submission from web_app_data.
    Multiple submissions from the same user are allowed (analytics takes latest)."""
    answers = payload.get("answers", {})
    contact = payload.get("contact", {})
    meta = payload.get("meta", {})

    row = SurveyResponse(
        user_id=telegram_id,
        username=username,
        source=meta.get("start_param"),
        category=answers.get("category"),
        platforms=answers.get("platforms") or None,
        commission=answers.get("commission"),
        contacts=answers.get("contacts"),
        lost_case=answers.get("lost_case"),
        own_channel=answers.get("own_channel"),
        budget=answers.get("budget"),
        pain=answers.get("pain"),
        contact_tg=contact.get("tg"),
        contact_store=contact.get("store"),
        consent=bool(contact.get("consent", False)),
        lang=meta.get("lang"),
        platform=meta.get("platform"),
        raw_payload=payload,
    )
    session.add(row)
    await session.flush()
    return row


# ---------------------------------------------------------------------------
# Broadcast segments (manual admin mailings)
# ---------------------------------------------------------------------------

# Ordered so the segment picker renders in funnel order. Keys are stable and
# used both in callback data and in the BotBroadcast audit rows.
BROADCAST_SEGMENTS: tuple[str, ...] = (
    "all",
    "no_shop",
    "no_product",
    "no_training",
    "trial",
    "paid",
    "referral",
)


def _segment_conditions(segment: str) -> list:
    """WHERE-clauses selecting a broadcast segment on ``BotUser``.

    Each segment is an independent filter over the same funnel state that drives
    the activation pushes (see ``push_scheduler.current_step``). ``referral``
    matches anyone who ever entered via a partner link (``referral_enter`` event).
    """
    if segment == "all":
        return []
    if segment == "no_shop":
        return [BotUser.registered_at.is_(None)]
    if segment == "no_product":
        return [BotUser.registered_at.is_not(None), BotUser.product_count == 0]
    if segment == "no_training":
        return [BotUser.product_count > 0, BotUser.training_completed.is_(False)]
    if segment == "trial":
        return [BotUser.trial_ends_at.is_not(None), BotUser.plan_paid.is_(False)]
    if segment == "paid":
        return [BotUser.plan_paid.is_(True)]
    if segment == "referral":
        return [
            BotUser.id.in_(
                select(BotEvent.bot_user_id).where(
                    BotEvent.event_type == "referral_enter"
                )
            )
        ]
    raise ValueError(f"unknown broadcast segment: {segment!r}")


def _lang_condition(lang: str | None) -> list:
    """Optional language filter. ``None`` means all languages."""
    return [BotUser.language == lang] if lang else []


async def count_segment(
    session: AsyncSession, segment: str, lang: str | None = None
) -> int:
    """How many users match ``segment`` (optionally filtered by language)."""
    stmt = select(func.count()).select_from(BotUser).where(
        *_segment_conditions(segment), *_lang_condition(lang)
    )
    return int((await session.execute(stmt)).scalar_one())


async def segment_counts(session: AsyncSession) -> dict[str, int]:
    """Live recipient count per segment (language-agnostic) for the picker."""
    return {seg: await count_segment(session, seg) for seg in BROADCAST_SEGMENTS}


async def broadcast_recipients(
    session: AsyncSession, segment: str, lang: str | None = None
) -> list[int]:
    """Telegram ids to broadcast to, for ``segment`` + optional language."""
    stmt = (
        select(BotUser.telegram_id)
        .where(*_segment_conditions(segment), *_lang_condition(lang))
        .order_by(BotUser.first_seen_at)
    )
    return list((await session.execute(stmt)).scalars().all())


async def record_broadcast(
    session: AsyncSession,
    *,
    segment: str,
    lang: str | None,
    total: int,
    delivered: int,
    failed: int,
) -> BotBroadcast:
    """Persist an audit row for one completed broadcast run."""
    row = BotBroadcast(
        segment=segment,
        lang=lang,
        total=total,
        delivered=delivered,
        failed=failed,
    )
    session.add(row)
    await session.flush()
    return row
