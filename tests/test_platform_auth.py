"""Unit tests for platform_auth.issue_auth_link_by — verifies the HTTP payload
sent to the platform, including the lang field added for Fix 3."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.platform_auth import PlatformAuthError, issue_auth_link_by


def _mock_response(consume_url: str, status_code: int = 200):
    """Return a mock httpx.Response that yields the given consume_url."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"consume_url": consume_url})
    return resp


@pytest.mark.asyncio
async def test_issue_auth_link_by_includes_lang():
    """lang kwarg must appear in the JSON payload sent to the platform."""
    fake_url = "https://platform.test/consume/abc"
    captured: list[dict] = []

    async def fake_post(url, *, json=None, headers=None):
        captured.append(json or {})
        return _mock_response(fake_url)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = fake_post

    with patch("bot.services.platform_auth.httpx.AsyncClient", return_value=mock_client):
        result = await issue_auth_link_by(
            12345,
            first_name="Ali",
            username="ali_uz",
            lang="uz",
        )

    assert result == fake_url
    assert len(captured) == 1
    payload = captured[0]
    assert payload["telegram_id"] == "12345"
    assert payload["lang"] == "uz"
    assert payload["username"] == "ali_uz"


@pytest.mark.asyncio
async def test_issue_auth_link_by_lang_none_by_default():
    """When lang is omitted the payload still contains the key (value None)."""
    fake_url = "https://platform.test/consume/xyz"
    captured: list[dict] = []

    async def fake_post(url, *, json=None, headers=None):
        captured.append(json or {})
        return _mock_response(fake_url)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = fake_post

    with patch("bot.services.platform_auth.httpx.AsyncClient", return_value=mock_client):
        result = await issue_auth_link_by(99)

    assert result == fake_url
    assert "lang" in captured[0]
    assert captured[0]["lang"] is None


@pytest.mark.asyncio
async def test_issue_auth_link_by_raises_on_missing_consume_url():
    """PlatformAuthError raised when response has no consume_url."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"error": "oops"})

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=resp)

    with patch("bot.services.platform_auth.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(PlatformAuthError, match="missing consume_url"):
            await issue_auth_link_by(1)
