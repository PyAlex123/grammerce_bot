import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.engine import Base
from bot.db import models  # noqa: F401 — register models with Base


# ---------------------------------------------------------------------------
# Async SQLite in-memory DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


# ---------------------------------------------------------------------------
# Fake Telegram object helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def make_message():
    """Factory for fake aiogram Message objects."""
    def _make(
        text: str = "/start",
        user_id: int = 123456,
        username: str = "testuser",
        first_name: str = "Иван",
        language_code: str = "ru",
        chat_id: int | None = None,
    ):
        msg = MagicMock()
        msg.text = text
        msg.answer = AsyncMock()
        msg.forward = AsyncMock()
        # Личный чат: chat.id == from_user.id, если не задано иное.
        msg.chat.id = user_id if chat_id is None else chat_id
        msg.from_user = MagicMock()
        msg.from_user.id = user_id
        msg.from_user.username = username
        msg.from_user.first_name = first_name
        msg.from_user.language_code = language_code
        return msg
    return _make


@pytest.fixture
def make_callback():
    """Factory for fake CallbackQuery objects."""
    def _make(
        data: str = "lang:ru",
        user_id: int = 123456,
        username: str = "testuser",
        first_name: str = "Иван",
    ):
        cb = MagicMock()
        cb.data = data
        cb.answer = AsyncMock()
        # spec=Message so handlers' isinstance(callback.message, Message) passes.
        cb.message = MagicMock(spec=Message)
        cb.message.answer = AsyncMock()
        cb.message.edit_text = AsyncMock()
        cb.from_user = MagicMock()
        cb.from_user.id = user_id
        cb.from_user.username = username
        cb.from_user.first_name = first_name
        return cb
    return _make


@pytest.fixture
def make_command():
    """Factory for fake CommandObject (aiogram)."""
    def _make(args: str | None = None):
        cmd = MagicMock()
        cmd.args = args
        return cmd
    return _make


@pytest.fixture
def make_state():
    """Factory for a fake FSMContext (aiogram)."""
    def _make() -> FSMContext:
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.clear = AsyncMock()
        state.get_state = AsyncMock(return_value=None)
        return state
    return _make
