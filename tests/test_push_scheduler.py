from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db import crud
from bot.db import models  # noqa: F401 — register models with Base
from bot.db.engine import Base
from bot.db.models import BotPushSend, BotUser
from bot.services import push_scheduler as ps

# A fixed "now" in the Tashkent daytime window: 10:00 UTC == 15:00 Tashkent.
DAY = datetime(2026, 6, 10, 10, 0, 0)
# A fixed "now" at night: 02:00 UTC == 07:00 Tashkent.
NIGHT = datetime(2026, 6, 10, 2, 0, 0)


def _user(**overrides) -> BotUser:
    """Build an in-memory BotUser with explicit funnel state for logic tests."""
    defaults = dict(
        telegram_id=1,
        language="ru",
        first_seen_at=DAY,
        registered_at=None,
        product_count=0,
        first_product_at=None,
        training_completed=False,
        trial_ends_at=None,
        plan_paid=False,
    )
    defaults.update(overrides)
    return BotUser(**defaults)


# ---------------------------------------------------------------------------
# within_quiet_hours
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "utc, allowed",
    [
        (datetime(2026, 6, 10, 3, 59), False),  # 08:59 Tashkent
        (datetime(2026, 6, 10, 4, 0), True),    # 09:00 Tashkent
        (datetime(2026, 6, 10, 15, 59), True),  # 20:59 Tashkent
        (datetime(2026, 6, 10, 16, 0), False),  # 21:00 Tashkent
    ],
)
def test_within_quiet_hours_boundaries(utc, allowed):
    assert ps.within_quiet_hours(utc) is allowed


# ---------------------------------------------------------------------------
# current_step priority
# ---------------------------------------------------------------------------

def test_current_step_no_store():
    assert ps.current_step(_user(registered_at=None)) == 1


def test_current_step_store_no_product():
    assert ps.current_step(_user(registered_at=DAY, product_count=0)) == 2


def test_current_step_product_no_training():
    assert ps.current_step(
        _user(registered_at=DAY, product_count=3, training_completed=False)
    ) == 3


def test_current_step_trained_trial_set():
    assert ps.current_step(
        _user(registered_at=DAY, product_count=3, training_completed=True, trial_ends_at=DAY)
    ) == 4


def test_current_step_all_done_no_trial_is_none():
    assert ps.current_step(
        _user(registered_at=DAY, product_count=3, training_completed=True, trial_ends_at=None)
    ) is None


def test_current_step_paid_is_none():
    assert ps.current_step(_user(registered_at=None, plan_paid=True)) is None


# ---------------------------------------------------------------------------
# due_send thresholds (steps 1–3)
# ---------------------------------------------------------------------------

def test_due_send1_not_yet():
    u = _user(first_seen_at=DAY - timedelta(hours=23))
    assert ps.due_send(u, 1, set(), DAY) is None


def test_due_send1_after_24h():
    u = _user(first_seen_at=DAY - timedelta(hours=25))
    assert ps.due_send(u, 1, set(), DAY) == 1


def test_due_send2_requires_send1():
    u = _user(first_seen_at=DAY - timedelta(days=4))
    # send1 not recorded yet → still offer send1, not send2
    assert ps.due_send(u, 1, set(), DAY) == 1


def test_due_send2_after_3d():
    u = _user(first_seen_at=DAY - timedelta(days=4))
    assert ps.due_send(u, 1, {1}, DAY) == 2


def test_due_send2_not_yet():
    u = _user(first_seen_at=DAY - timedelta(days=2))
    assert ps.due_send(u, 1, {1}, DAY) is None


def test_due_send_capped_at_two():
    u = _user(first_seen_at=DAY - timedelta(days=10))
    assert ps.due_send(u, 1, {1, 2}, DAY) is None


# ---------------------------------------------------------------------------
# due_send trial windows (step 4)
# ---------------------------------------------------------------------------

def test_trial_send1_window():
    # ~1.5 days left → inside the send-1 window [end-2d, end-1d).
    u = _user(trial_ends_at=DAY + timedelta(days=1, hours=12))
    assert ps.due_send(u, 4, set(), DAY) == 1


def test_trial_send2_window():
    u = _user(trial_ends_at=DAY + timedelta(hours=23))  # <1 day left
    assert ps.due_send(u, 4, set(), DAY) == 2


def test_trial_no_send_too_early():
    u = _user(trial_ends_at=DAY + timedelta(days=5))
    assert ps.due_send(u, 4, set(), DAY) is None


def test_trial_no_send_after_end():
    u = _user(trial_ends_at=DAY - timedelta(hours=1))
    assert ps.due_send(u, 4, set(), DAY) is None


# ---------------------------------------------------------------------------
# run_once integration
# ---------------------------------------------------------------------------

@pytest.fixture
async def factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


async def _count_sends(factory) -> int:
    async with factory() as session:
        result = await session.execute(select(func.count()).select_from(BotPushSend))
        return result.scalar_one()


@pytest.mark.asyncio
async def test_run_once_sends_step1_send1(factory):
    async with factory() as session:
        user, _ = await crud.get_or_create_user(session, 1001, "stuck")
        user.first_seen_at = DAY - timedelta(hours=25)
        await session.commit()

    bot = AsyncMock()
    sent = await ps.run_once(bot, factory, now_utc=DAY)

    assert sent == 1
    bot.send_message.assert_awaited_once()
    chat_id, text = bot.send_message.call_args.args
    assert chat_id == 1001
    assert "магазин" in text.lower()
    assert await _count_sends(factory) == 1


@pytest.mark.asyncio
async def test_run_once_dedups_same_tick(factory):
    async with factory() as session:
        user, _ = await crud.get_or_create_user(session, 1002, "stuck")
        user.first_seen_at = DAY - timedelta(hours=25)
        await session.commit()

    bot = AsyncMock()
    await ps.run_once(bot, factory, now_utc=DAY)
    sent2 = await ps.run_once(bot, factory, now_utc=DAY)

    assert sent2 == 0
    bot.send_message.assert_awaited_once()  # only the first tick sent
    assert await _count_sends(factory) == 1


@pytest.mark.asyncio
async def test_run_once_sends_send2_after_3_days(factory):
    async with factory() as session:
        user, _ = await crud.get_or_create_user(session, 1003, "stuck")
        user.first_seen_at = DAY - timedelta(days=4)
        await crud.record_push_sent(session, user, step=1, send_no=1)
        await session.commit()

    bot = AsyncMock()
    sent = await ps.run_once(bot, factory, now_utc=DAY)

    assert sent == 1
    _, text = bot.send_message.call_args.args
    assert "канал" in text.lower()  # send 2 of push 1 mentions the channel
    assert await _count_sends(factory) == 2


@pytest.mark.asyncio
async def test_run_once_silent_after_two_sends(factory):
    async with factory() as session:
        user, _ = await crud.get_or_create_user(session, 1004, "stuck")
        user.first_seen_at = DAY - timedelta(days=10)
        await crud.record_push_sent(session, user, step=1, send_no=1)
        await crud.record_push_sent(session, user, step=1, send_no=2)
        await session.commit()

    bot = AsyncMock()
    sent = await ps.run_once(bot, factory, now_utc=DAY)

    assert sent == 0
    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_run_once_quiet_hours_skips(factory):
    async with factory() as session:
        user, _ = await crud.get_or_create_user(session, 1005, "stuck")
        user.first_seen_at = NIGHT - timedelta(hours=25)
        await session.commit()

    bot = AsyncMock()
    sent = await ps.run_once(bot, factory, now_utc=NIGHT)

    assert sent == 0
    bot.send_message.assert_not_called()
    assert await _count_sends(factory) == 0


@pytest.mark.asyncio
async def test_run_once_skips_paid(factory):
    async with factory() as session:
        user, _ = await crud.get_or_create_user(session, 1006, "paid")
        user.first_seen_at = DAY - timedelta(hours=25)
        user.plan_paid = True
        await session.commit()

    bot = AsyncMock()
    sent = await ps.run_once(bot, factory, now_utc=DAY)

    assert sent == 0
    bot.send_message.assert_not_called()
