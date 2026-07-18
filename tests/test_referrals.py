"""Unit tests for platform_referrals.track_referral.

Ключевое требование: fire-and-forget — никакая ошибка бэкенда или сети не
должна вылетать наружу, только ``None``.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.services.platform_referrals import ReferralDiscount, track_referral


def _mock_response(payload, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = "server error"
    if isinstance(payload, Exception):
        resp.json = MagicMock(side_effect=payload)
    else:
        resp.json = MagicMock(return_value=payload)
    return resp


def _mock_client(response=None, *, post_side_effect=None):
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    if post_side_effect is not None:
        client.post = AsyncMock(side_effect=post_side_effect)
    else:
        client.post = AsyncMock(return_value=response)
    return client


def _patch(client):
    return patch(
        "bot.services.platform_referrals.httpx.AsyncClient", return_value=client
    )


@pytest.mark.asyncio
async def test_track_referral_fixed_discount_and_request_shape():
    """ok:true + fixed → ReferralDiscount; проверяем URL, секрет и тело."""
    client = _mock_client(
        _mock_response(
            {"ok": True, "label": "Партнёр X",
             "discount": {"type": "fixed", "value": 500000}}
        )
    )
    with _patch(client):
        result = await track_referral(
            "ABC", 123456789, username="ivan", first_name="Иван"
        )

    assert result == ReferralDiscount(type="fixed", value=500000.0, label="Партнёр X")

    url = client.post.call_args[0][0]
    assert url == "http://platform.test/api/platform/referrals/track"
    headers = client.post.call_args.kwargs["headers"]
    assert headers["X-Bot-Secret"] == "test-secret"
    body = client.post.call_args.kwargs["json"]
    assert body == {
        "code": "ABC",
        "telegram_id": 123456789,
        "username": "ivan",
        "first_name": "Иван",
    }


@pytest.mark.asyncio
async def test_track_referral_percent_discount():
    client = _mock_client(
        _mock_response({"ok": True, "discount": {"type": "percent", "value": 30}})
    )
    with _patch(client):
        result = await track_referral("P", 1)

    assert result is not None
    assert result.type == "percent"
    assert result.value == 30.0


@pytest.mark.asyncio
async def test_track_referral_unknown_code_returns_none():
    with _patch(_mock_client(_mock_response({"ok": False}))):
        assert await track_referral("NOPE", 1) is None


@pytest.mark.asyncio
async def test_track_referral_http_500_returns_none():
    with _patch(_mock_client(_mock_response({}, status_code=500))):
        assert await track_referral("X", 1) is None


@pytest.mark.asyncio
async def test_track_referral_timeout_returns_none():
    client = _mock_client(post_side_effect=httpx.TimeoutException("timed out"))
    with _patch(client):
        assert await track_referral("X", 1) is None


@pytest.mark.asyncio
async def test_track_referral_network_error_returns_none():
    client = _mock_client(post_side_effect=httpx.RequestError("unreachable"))
    with _patch(client):
        assert await track_referral("X", 1) is None


@pytest.mark.asyncio
async def test_track_referral_malformed_json_returns_none():
    with _patch(_mock_client(_mock_response(ValueError("not json")))):
        assert await track_referral("X", 1) is None


@pytest.mark.asyncio
async def test_track_referral_discount_without_value_returns_none():
    with _patch(_mock_client(_mock_response({"ok": True, "discount": {"type": "fixed"}}))):
        assert await track_referral("X", 1) is None


@pytest.mark.asyncio
async def test_track_referral_ok_without_discount_returns_none():
    with _patch(_mock_client(_mock_response({"ok": True}))):
        assert await track_referral("X", 1) is None


@pytest.mark.asyncio
async def test_track_referral_unknown_discount_type_falls_back_to_fixed():
    client = _mock_client(
        _mock_response({"ok": True, "discount": {"type": "weird", "value": 1000}})
    )
    with _patch(client):
        result = await track_referral("X", 1)

    assert result is not None
    assert result.type == "fixed"
