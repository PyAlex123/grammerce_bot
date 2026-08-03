from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from bot.config import settings
from bot.db import crud
from bot.db.models import BotEvent, BotUser
from bot.handlers import admin
from bot.services import broadcast as bc

ADMIN_ID = settings.SUPPORT_CHAT_ID  # == -1 in the test env


# ---------------------------------------------------------------------------
# Segment queries
# ---------------------------------------------------------------------------

async def _seed(session) -> dict[str, BotUser]:
    """One user per funnel state, plus one referral entrant."""
    now = datetime(2026, 7, 1)
    users = {
        # no_shop (never registered), ru
        "no_shop": BotUser(telegram_id=101, language="ru", registered_at=None),
        # registered, no product, uz
        "no_product": BotUser(
            telegram_id=102, language="uz", registered_at=now, product_count=0
        ),
        # has product, training not done, ru
        "no_training": BotUser(
            telegram_id=103, language="ru", registered_at=now,
            product_count=2, training_completed=False,
        ),
        # on trial (not paid), ru
        "trial": BotUser(
            telegram_id=104, language="ru", registered_at=now,
            product_count=2, training_completed=True, trial_ends_at=now, plan_paid=False,
        ),
        # paid, uz (registered — a real paying owner has a shop)
        "paid": BotUser(
            telegram_id=105, language="uz", registered_at=now,
            product_count=3, training_completed=True, plan_paid=True,
        ),
        # referral entrant (also never registered), ru
        "referral": BotUser(telegram_id=106, language="ru", registered_at=None),
    }
    for u in users.values():
        session.add(u)
    await session.flush()
    session.add(
        BotEvent(bot_user_id=users["referral"].id, event_type="referral_enter")
    )
    await session.flush()
    return users


@pytest.mark.parametrize(
    "segment, expected",
    [
        ("all", {101, 102, 103, 104, 105, 106}),
        ("no_shop", {101, 106}),
        ("no_product", {102}),
        ("no_training", {103}),
        ("trial", {104}),
        ("paid", {105}),
        ("referral", {106}),
    ],
)
async def test_broadcast_recipients_per_segment(db_session, segment, expected):
    await _seed(db_session)
    recipients = await crud.broadcast_recipients(db_session, segment)
    assert set(recipients) == expected


async def test_language_filter(db_session):
    await _seed(db_session)
    assert set(await crud.broadcast_recipients(db_session, "all", "ru")) == {101, 103, 104, 106}
    assert set(await crud.broadcast_recipients(db_session, "all", "uz")) == {102, 105}


async def test_segment_counts(db_session):
    await _seed(db_session)
    counts = await crud.segment_counts(db_session)
    assert counts["all"] == 6
    assert counts["no_shop"] == 2
    assert counts["referral"] == 1


async def test_blocked_users_are_excluded_from_audience(db_session):
    """Заблокировавшие бота недостижимы — ни в списке получателей, ни в счётчике."""
    await _seed(db_session)
    await crud.mark_blocked(db_session, 101)

    assert set(await crud.broadcast_recipients(db_session, "all")) == {
        102, 103, 104, 105, 106
    }
    assert set(await crud.broadcast_recipients(db_session, "no_shop")) == {106}
    assert (await crud.segment_counts(db_session))["all"] == 5


async def test_mark_blocked_is_idempotent(db_session):
    await _seed(db_session)
    await crud.mark_blocked(db_session, 101)
    first = (await crud.get_user_by_telegram_id(db_session, 101)).blocked_at
    await crud.mark_blocked(db_session, 101)
    assert (await crud.get_user_by_telegram_id(db_session, 101)).blocked_at == first


async def test_mark_blocked_ignores_unknown_user(db_session):
    await crud.mark_blocked(db_session, 999999)  # не должно падать


async def test_record_broadcast(db_session):
    row = await crud.record_broadcast(
        db_session, segment="no_shop", lang=None, total=10, delivered=8, failed=2
    )
    assert row.id is not None
    assert (row.delivered, row.failed, row.total) == (8, 2, 10)


# ---------------------------------------------------------------------------
# run_broadcast delivery loop
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Skip the throttle/backoff sleeps so the loop tests run instantly."""
    monkeypatch.setattr(bc.asyncio, "sleep", AsyncMock())


async def test_run_broadcast_all_delivered():
    bot = MagicMock()
    bot.copy_message = AsyncMock()
    delivered, failed, blocked = await bc.run_broadcast(
        bot, [1, 2, 3], from_chat_id=99, message_id=5
    )
    assert (delivered, failed, blocked) == (3, 0, [])
    assert bot.copy_message.await_count == 3


async def test_run_broadcast_forbidden_counts_as_failed_and_is_reported():
    bot = MagicMock()

    async def _copy(chat_id, **kwargs):
        if chat_id == 2:
            raise TelegramForbiddenError(method=MagicMock(), message="blocked")

    bot.copy_message = AsyncMock(side_effect=_copy)
    delivered, failed, blocked = await bc.run_broadcast(
        bot, [1, 2, 3], from_chat_id=99, message_id=5
    )
    # Заблокировавший возвращается вызывающему, чтобы тот пометил его в БД.
    assert (delivered, failed, blocked) == (2, 1, [2])


async def test_run_broadcast_reports_forbidden_on_flood_retry():
    """403 может прийти и на повторе после flood wait — его тоже надо вернуть."""
    bot = MagicMock()
    bot.copy_message = AsyncMock(side_effect=[
        TelegramRetryAfter(method=MagicMock(), message="flood", retry_after=0),
        TelegramForbiddenError(method=MagicMock(), message="blocked"),
    ])
    delivered, failed, blocked = await bc.run_broadcast(
        bot, [7], from_chat_id=99, message_id=5
    )
    assert (delivered, failed, blocked) == (0, 1, [7])


async def test_run_broadcast_retry_after_then_success():
    bot = MagicMock()
    bot.copy_message = AsyncMock(side_effect=[
        TelegramRetryAfter(method=MagicMock(), message="flood", retry_after=0),
        None,  # retry succeeds
    ])
    delivered, failed, blocked = await bc.run_broadcast(
        bot, [1], from_chat_id=99, message_id=5
    )
    assert (delivered, failed, blocked) == (1, 0, [])
    assert bot.copy_message.await_count == 2


# ---------------------------------------------------------------------------
# Admin gating
# ---------------------------------------------------------------------------

def _msg(chat_id: int):
    msg = MagicMock()
    msg.chat.id = chat_id
    msg.from_user = MagicMock()
    msg.answer = AsyncMock()
    return msg


async def test_broadcast_ignored_for_non_admin(db_session):
    msg = _msg(chat_id=999999)  # not the admin chat
    state = MagicMock()
    state.clear = AsyncMock()
    await admin.cmd_broadcast(msg, state, db_session)
    msg.answer.assert_not_called()


async def test_broadcast_prompts_admin(db_session):
    msg = _msg(chat_id=ADMIN_ID)
    state = MagicMock()
    state.clear = AsyncMock()
    await admin.cmd_broadcast(msg, state, db_session)
    msg.answer.assert_awaited_once()
