import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def make_message():
    """Factory for fake aiogram Message objects."""
    def _make(text: str = "/start", user_id: int = 123456, username: str = "testuser"):
        message = MagicMock()
        message.text = text
        message.answer = AsyncMock()
        message.forward = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = user_id
        message.from_user.username = username
        message.from_user.language_code = "ru"
        return message
    return _make
