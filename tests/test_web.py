import pytest
from unittest.mock import AsyncMock

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
async def test_valid_registration_notifies_admin(client, factory):
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
    bot.send_message.assert_awaited_once()
    chat_id, text = bot.send_message.call_args.args
    assert chat_id == -1  # SUPPORT_CHAT_ID from conftest
    assert "Алиса" in text
    assert "tgads" in text


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
    assert bot.send_message.await_count == 1


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
    _, text = bot.send_message.call_args.args
    assert "не указан" in text
