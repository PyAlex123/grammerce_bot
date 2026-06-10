"""Activation-push scheduler.

Runs in-process once an hour. For every owner who has not paid yet, it works
out the single funnel step they are stuck on (by priority), checks whether a
reminder is due, respects Tashkent quiet hours, dedups via ``bot_push_sends``,
and sends the right localized message + CTA button.

Spec: mdS/grammerce_push_notifications.md
"""
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.db import crud
from bot.db.models import BotUser
from bot.keyboards.menu import push_keyboard
from bot.locales import t

logger = logging.getLogger(__name__)

# Tashkent is UTC+5 year-round (no DST). Quiet-hours window is 09:00–21:00
# local time => 04:00 ≤ UTC < 16:00.
_TASHKENT_OFFSET = timedelta(hours=5)
_QUIET_START_HOUR = 9
_QUIET_END_HOUR = 21

# Activation pushes (steps 1–3): send 1 at +24h, send 2 at +3 days since stuck.
_SEND1_AFTER = timedelta(hours=24)
_SEND2_AFTER = timedelta(days=3)
# Trial push (step 4) is anchored on trial_ends_at: 2 days / 1 day before.
_TRIAL_SEND1_BEFORE = timedelta(days=2)
_TRIAL_SEND2_BEFORE = timedelta(days=1)

# step -> CTA button label key
_STEP_CTA = {
    1: "push_btn_create",
    2: "push_btn_add_product",
    3: "push_btn_training",
    4: "push_btn_tariff",
}
# Steps whose 2nd send carries the channel button.
_CHANNEL_STEPS = {1, 2, 3}


def within_quiet_hours(now_utc: datetime) -> bool:
    """True when sending is allowed (09:00–21:00 Tashkent)."""
    local_hour = (now_utc + _TASHKENT_OFFSET).hour
    return _QUIET_START_HOUR <= local_hour < _QUIET_END_HOUR


def current_step(user: BotUser) -> int | None:
    """The single active funnel step by priority, or None.

    Priority (spec §2): create store → add product → finish training → trial.
    A paid plan turns every push off.
    """
    if user.plan_paid:
        return None
    if user.registered_at is None:
        return 1
    if user.product_count == 0:
        return 2
    if not user.training_completed:
        return 3
    if user.trial_ends_at is not None:
        return 4
    return None


def stuck_since(user: BotUser, step: int) -> datetime | None:
    """Timestamp from which the +24h / +3d offsets are measured (steps 1–3)."""
    if step == 1:
        return user.first_seen_at
    if step == 2:
        return user.registered_at
    if step == 3:
        return user.first_product_at
    return None  # step 4 is anchored on trial_ends_at instead


def due_send(
    user: BotUser, step: int, sent: set[int], now_utc: datetime
) -> int | None:
    """Which send (1 or 2) is due now for ``step``, or None.

    Caps at 2 sends per step. Steps 1–3 use relative offsets and require send 1
    before send 2. Step 4 (trial) uses fixed windows before ``trial_ends_at``.
    """
    if step == 4:
        end = user.trial_ends_at
        if end is None or now_utc >= end:
            return None
        if 1 not in sent and end - _TRIAL_SEND1_BEFORE <= now_utc < end - _TRIAL_SEND2_BEFORE:
            return 1
        if 2 not in sent and now_utc >= end - _TRIAL_SEND2_BEFORE:
            return 2
        return None

    since = stuck_since(user, step)
    if since is None:
        return None
    if 1 not in sent and now_utc >= since + _SEND1_AFTER:
        return 1
    if 1 in sent and 2 not in sent and now_utc >= since + _SEND2_AFTER:
        return 2
    return None


async def _send_push(bot: Bot, user: BotUser, step: int, send_no: int) -> bool:
    """Render and send one push. Returns True on success (so the caller records
    it). Failures are logged and left unrecorded → retried next tick."""
    lang = user.language or "ru"
    text = t(lang, f"push{step}_s{send_no}")
    with_channel = send_no == 2 and step in _CHANNEL_STEPS
    markup = push_keyboard(lang, _STEP_CTA[step], with_channel=with_channel)
    try:
        # Text-only for now. Image support (send_photo with the spec's briefs)
        # is a future, config-driven enhancement — it would slot in here.
        await bot.send_message(user.telegram_id, text, reply_markup=markup)
        return True
    except Exception:
        logger.error(
            "push: failed to send step=%s send=%s to tg_id=%s",
            step,
            send_no,
            user.telegram_id,
            exc_info=True,
        )
        return False


async def run_once(
    bot: Bot, session_factory: async_sessionmaker, now_utc: datetime | None = None
) -> int:
    """One scheduler pass. Returns the number of pushes sent.

    Gated entirely on quiet hours: a send that becomes due at night is simply
    picked up by the first allowed (daytime) tick — that is the spec's
    "accumulate at night, send in the morning" behaviour.
    """
    now_utc = now_utc or datetime.utcnow()
    if not within_quiet_hours(now_utc):
        logger.info("push: quiet hours (%s UTC) — skipping tick", now_utc.strftime("%H:%M"))
        return 0

    sent_count = 0
    async with session_factory() as session:
        candidates = await crud.select_push_candidates(session)
        for user in candidates:
            step = current_step(user)
            if step is None:
                continue
            already = await crud.get_sent_steps(session, user, step)
            send_no = due_send(user, step, already, now_utc)
            if send_no is None:
                continue
            if not await _send_push(bot, user, step, send_no):
                continue
            await crud.record_push_sent(session, user, step, send_no)
            await crud.log_event(
                session, user, "push_sent", {"step": step, "send_no": send_no}
            )
            await session.commit()
            sent_count += 1

    if sent_count:
        logger.info("push: sent %s reminder(s)", sent_count)
    return sent_count


def _seconds_until_next_hour(now: datetime | None = None) -> float:
    now = now or datetime.utcnow()
    nxt = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return max(1.0, (nxt - now).total_seconds())


async def scheduler_loop(bot: Bot, session_factory: async_sessionmaker) -> None:
    """Run ``run_once`` aligned to the top of every hour, forever."""
    logger.info("Push scheduler started")
    while True:
        try:
            await run_once(bot, session_factory)
        except Exception:
            logger.error("push scheduler tick failed", exc_info=True)
        await asyncio.sleep(_seconds_until_next_hour())
