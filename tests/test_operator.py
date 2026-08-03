"""Релей оператора: пересылает текст админа пользователю, но не команды.

Роутер оператора подключён раньше start.router, поэтому без фильтра он съедал
бы `/start` из админского чата — и админ не видел бы кнопок входа на платформу.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.config import settings
from bot.handlers import operator
from bot.handlers.operator import (
    RELAY_FILTER,
    is_relayable,
    operator_relay_to_user,
)
from bot.locales.ru import texts as RU


@pytest.fixture(autouse=True)
def _reset_session():
    """Модуль хранит активную сессию в глобальной переменной — чистим её."""
    operator._current_user_id = None
    operator._active_user_ids.clear()
    yield
    operator._current_user_id = None
    operator._active_user_ids.clear()


def _msg(chat_id: int, text: str | None):
    return SimpleNamespace(chat=SimpleNamespace(id=chat_id), text=text)


# ---------------------------------------------------------------------------
# is_relayable
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", ["привет", "цена 100 000", "скидка 30% — до 5/10"])
def test_is_relayable_plain_text(text):
    assert is_relayable(text) is True


def test_is_relayable_rejects_any_leading_slash():
    """Осознанный компромисс: отличить команду от текста с '/' в начале нельзя,
    поэтому не пересылается ничего, начинающегося со слэша."""
    assert is_relayable("/ не команда") is False


@pytest.mark.parametrize("text", ["/start", "/chatid", "/broadcast", "/start ref_ABC"])
def test_is_relayable_rejects_commands(text):
    assert is_relayable(text) is False


@pytest.mark.parametrize("text", ["", None])
def test_is_relayable_rejects_empty(text):
    assert is_relayable(text) is False


# ---------------------------------------------------------------------------
# Фильтр хендлера целиком
# ---------------------------------------------------------------------------

def test_filter_passes_admin_text():
    assert RELAY_FILTER.resolve(_msg(settings.SUPPORT_CHAT_ID, "привет"))


def test_filter_skips_admin_command():
    """Главное: /start админа проходит дальше, в start.router."""
    assert not RELAY_FILTER.resolve(_msg(settings.SUPPORT_CHAT_ID, "/start"))


def test_filter_skips_non_admin_chat():
    assert not RELAY_FILTER.resolve(_msg(settings.SUPPORT_CHAT_ID + 1, "привет"))


def test_filter_skips_message_without_text():
    assert not RELAY_FILTER.resolve(_msg(settings.SUPPORT_CHAT_ID, None))


# ---------------------------------------------------------------------------
# Сам релей не сломан
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_relay_forwards_to_active_user():
    operator._current_user_id = 777
    message = MagicMock()
    message.text = "чем помочь?"
    message.answer = AsyncMock()
    bot = AsyncMock()

    await operator_relay_to_user(message, bot)

    bot.send_message.assert_awaited_once_with(777, RU["operator_relay_prefix"] + "чем помочь?")
    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_relay_without_active_chat_warns_admin():
    message = MagicMock()
    message.text = "кому это?"
    message.answer = AsyncMock()
    bot = AsyncMock()

    await operator_relay_to_user(message, bot)

    bot.send_message.assert_not_called()
    message.answer.assert_awaited_once_with(RU["operator_no_active_chat"])
