"""Unit tests for platform_auth.issue_auth_link_by — verifies the HTTP payload
sent to the platform, including the lang field added for Fix 3."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.platform_auth import (
    PlatformAuthError,
    issue_auth_by,
    issue_auth_link_by,
)


def _mock_response(consume_url: str, status_code: int = 200, **extra):
    """Return a mock httpx.Response that yields the given consume_url.

    Extra top-level JSON fields (e.g. has_shop, needs_setup) can be passed via
    **extra to exercise AuthLink parsing."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"consume_url": consume_url, **extra})
    return resp


def _mock_client(response):
    """Async-context httpx client whose .post returns the given response."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.post = AsyncMock(return_value=response)
    return client


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


@pytest.mark.asyncio
async def test_issue_auth_by_parses_has_shop_and_needs_setup():
    """AuthLink carries has_shop / needs_setup from the platform response."""
    resp = _mock_response("https://p.test/c/1", has_shop=True, needs_setup=False)
    with patch(
        "bot.services.platform_auth.httpx.AsyncClient",
        return_value=_mock_client(resp),
    ):
        auth = await issue_auth_by(42, lang="ru")

    assert auth.consume_url == "https://p.test/c/1"
    assert auth.has_shop is True
    assert auth.needs_setup is False


@pytest.mark.asyncio
async def test_issue_auth_by_defaults_when_flags_absent():
    """Older platforms may omit the flags: has_shop→False, needs_setup→True."""
    resp = _mock_response("https://p.test/c/2")  # no has_shop / needs_setup
    with patch(
        "bot.services.platform_auth.httpx.AsyncClient",
        return_value=_mock_client(resp),
    ):
        auth = await issue_auth_by(7)

    assert auth.consume_url == "https://p.test/c/2"
    assert auth.has_shop is False
    assert auth.needs_setup is True
