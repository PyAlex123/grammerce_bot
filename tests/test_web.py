from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from aiohttp.test_utils import TestClient, TestServer
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.engine import Base
from bot.db import models  # noqa: F401 — register models with Base
from bot.db import crud
from bot.db.models import BotEvent
from bot.web import create_app

# Matches PLATFORM_BOT_SHARED_SECRET set in the root conftest.py
SECRET = "test-secret"
ENDPOINT = "/api/bot/user-registered"
ORDER_ENDPOINT = "/api/bot/new-order"
LOW_ENDPOINT = "/api/bot/low-products"
FUNNEL_ENDPOINT = "/api/bot/funnel-state"


@pytest.fixture
async def factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


@pytest.fixture
async def client(factory):
    bot = AsyncMock()
    cl = TestClient(TestServer(create_app(bot, factory)))
    await cl.start_server()
    yield cl, bot
    await cl.close()


@pytest.mark.asyncio
async def test_valid_registration_notifies_admin_and_user(client, factory):
    cl, bot = client
    async with factory() as session:
        user, _ = await crud.get_or_create_user(session, 70001, "alice")
        await crud.save_utm(session, user, "tgads", "tg", "uzb4ru")
        await session.commit()

    resp = await cl.post(
        ENDPOINT,
        headers={"X-Bot-Secret": SECRET},
        json={"telegram_id": "70001", "first_name": "Алиса"},
    )

    assert resp.status == 200
    # Two messages: admin notice + user "store created"
    assert bot.send_message.await_count == 2
    admin_chat, admin_text = bot.send_message.call_args_list[0].args
    assert admin_chat == -1  # SUPPORT_CHAT_ID from conftest
    assert "Алиса" in admin_text
    assert "tgads" in admin_text
    user_chat, user_text = bot.send_message.call_args_list[1].args
    assert user_chat == 70001
    assert "Магазин создан" in user_text


@pytest.mark.asyncio
async def test_bad_secret_returns_401(client):
    cl, bot = client
    resp = await cl.post(
        ENDPOINT,
        headers={"X-Bot-Secret": "wrong"},
        json={"telegram_id": "70010"},
    )
    assert resp.status == 401
    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_missing_telegram_id_returns_400(client):
    cl, bot = client
    resp = await cl.post(
        ENDPOINT,
        headers={"X-Bot-Secret": SECRET},
        json={"first_name": "Безымянный"},
    )
    assert resp.status == 400
    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_duplicate_registration_does_not_renotify(client):
    cl, bot = client
    payload = {"telegram_id": "70020", "first_name": "Боб"}

    r1 = await cl.post(ENDPOINT, headers={"X-Bot-Secret": SECRET}, json=payload)
    r2 = await cl.post(ENDPOINT, headers={"X-Bot-Secret": SECRET}, json=payload)

    assert r1.status == 200
    assert r2.status == 200
    # First registration → admin + user (2 messages); duplicate → none
    assert bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_logs_register_complete_event(client, factory):
    cl, _ = client
    await cl.post(
        ENDPOINT,
        headers={"X-Bot-Secret": SECRET},
        json={"telegram_id": "70030"},
    )

    async with factory() as session:
        result = await session.execute(
            sa_select(BotEvent).where(BotEvent.event_type == "register_complete")
        )
        events = result.scalars().all()
    assert len(events) == 1
    assert events[0].payload == {"first": True}


@pytest.mark.asyncio
async def test_unknown_utm_falls_back(client):
    cl, bot = client
    resp = await cl.post(
        ENDPOINT,
        headers={"X-Bot-Secret": SECRET},
        json={"telegram_id": "70040", "first_name": "Дина"},
    )
    assert resp.status == 200
    # Admin notice is the first send_message call
    _, text = bot.send_message.call_args_list[0].args
    assert "не указан" in text


# ---------------------------------------------------------------------------
# new-order endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_order_notifies_user(client, factory):
    cl, bot = client
    async with factory() as session:
        await crud.get_or_create_user(session, 80001, "buyer")
        await session.commit()

    resp = await cl.post(
        ORDER_ENDPOINT,
        headers={"X-Bot-Secret": SECRET},
        json={
            "telegram_id": "80001",
            "order_number": 42,
            "customer_name": "Вася",
            "phone": "+998901112233",
            "amount": "100 000",
        },
    )

    assert resp.status == 200
    bot.send_message.assert_awaited_once()
    chat_id, text = bot.send_message.call_args.args
    assert chat_id == 80001
    assert "42" in text
    assert "Вася" in text


@pytest.mark.asyncio
async def test_new_order_bad_secret_returns_401(client):
    cl, bot = client
    resp = await cl.post(
        ORDER_ENDPOINT, headers={"X-Bot-Secret": "wrong"}, json={"telegram_id": "80002"}
    )
    assert resp.status == 401
    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_new_order_missing_telegram_id_returns_400(client):
    cl, bot = client
    resp = await cl.post(
        ORDER_ENDPOINT, headers={"X-Bot-Secret": SECRET}, json={"order_number": 1}
    )
    assert resp.status == 400
    bot.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# low-products (re-engagement) endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_low_products_notifies_user(client, factory):
    cl, bot = client
    async with factory() as session:
        await crud.get_or_create_user(session, 80010, "merchant")
        await session.commit()

    resp = await cl.post(
        LOW_ENDPOINT,
        headers={"X-Bot-Secret": SECRET},
        json={"telegram_id": "80010", "product_count": 2},
    )

    assert resp.status == 200
    bot.send_message.assert_awaited_once()
    chat_id, text = bot.send_message.call_args.args
    assert chat_id == 80010
    assert "2" in text


@pytest.mark.asyncio
async def test_low_products_bad_secret_returns_401(client):
    cl, bot = client
    resp = await cl.post(
        LOW_ENDPOINT, headers={"X-Bot-Secret": "wrong"}, json={"telegram_id": "80011"}
    )
    assert resp.status == 401
    bot.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# funnel-state endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_funnel_state_upserts_fields(client, factory):
    cl, _ = client
    resp = await cl.post(
        FUNNEL_ENDPOINT,
        headers={"X-Bot-Secret": SECRET},
        json={
            "telegram_id": "90001",
            "product_count": 5,
            "training_completed": True,
            "trial_ends_at": "2026-06-20T00:00:00Z",
            "plan_paid": False,
            "store_created_at": "2026-06-01T10:00:00Z",
        },
    )

    assert resp.status == 200
    async with factory() as session:
        user = await crud.get_user_by_telegram_id(session, 90001)
    assert user.product_count == 5
    assert user.training_completed is True
    assert user.plan_paid is False
    assert user.trial_ends_at == datetime(2026, 6, 20, 0, 0, 0)
    assert user.registered_at == datetime(2026, 6, 1, 10, 0, 0)
    # product_count 0 -> >0 transition stamps first_product_at
    assert user.first_product_at is not None


@pytest.mark.asyncio
async def test_funnel_state_partial_update_keeps_other_fields(client, factory):
    cl, _ = client
    async with factory() as session:
        user, _ = await crud.get_or_create_user(session, 90002, "merchant")
        await crud.update_funnel_state(session, user, product_count=3, plan_paid=False)
        await session.commit()

    # Only flip training_completed; product_count must survive.
    resp = await cl.post(
        FUNNEL_ENDPOINT,
        headers={"X-Bot-Secret": SECRET},
        json={"telegram_id": "90002", "training_completed": True},
    )

    assert resp.status == 200
    async with factory() as session:
        user = await crud.get_user_by_telegram_id(session, 90002)
    assert user.product_count == 3
    assert user.training_completed is True


@pytest.mark.asyncio
async def test_funnel_state_bad_secret_returns_401(client):
    cl, bot = client
    resp = await cl.post(
        FUNNEL_ENDPOINT, headers={"X-Bot-Secret": "wrong"}, json={"telegram_id": "90003"}
    )
    assert resp.status == 401


@pytest.mark.asyncio
async def test_funnel_state_missing_telegram_id_returns_400(client):
    cl, _ = client
    resp = await cl.post(
        FUNNEL_ENDPOINT, headers={"X-Bot-Secret": SECRET}, json={"product_count": 1}
    )
    assert resp.status == 400
