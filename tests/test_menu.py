"""Unit tests for the welcome keyboard (BOT_AUTH_SPEC A–C):

- the primary CTA is a WebApp button on the persistent Mini App (PLATFORM_WEBAPP_URL),
  NOT the one-shot consume_url — so re-opening never hits `auth_expired`;
- its label follows has_shop (create shop vs open platform);
- the one-shot consume_url is exposed only via the separate "open on computer"
  url-button.
"""
import pytest

from bot.keyboards import menu
from bot.locales import t

WEBAPP_URL = "https://grammerce.io/login"
CONSUME_URL = "https://grammerce.io/api/auth/telegram/consume?token=abc"


@pytest.fixture(autouse=True)
def _webapp_url(monkeypatch):
    """Configure a persistent Mini App URL so the CTA becomes a WebApp button."""
    monkeypatch.setattr(menu.settings, "PLATFORM_WEBAPP_URL", WEBAPP_URL)


def _cta(markup):
    """Row-0, col-0 button — the primary CTA."""
    return markup.inline_keyboard[0][0]


def test_cta_label_create_shop_when_no_shop():
    markup = menu.welcome_keyboard("ru", has_shop=False, consume_url=CONSUME_URL)
    assert _cta(markup).text == t("ru", "btn_create_shop")


def test_cta_label_open_platform_when_has_shop():
    markup = menu.welcome_keyboard("ru", has_shop=True, consume_url=CONSUME_URL)
    assert _cta(markup).text == t("ru", "btn_open_platform")


def test_cta_opens_persistent_webapp_not_consume_url():
    markup = menu.welcome_keyboard("ru", has_shop=False, consume_url=CONSUME_URL)
    cta = _cta(markup)
    assert cta.web_app is not None
    assert cta.web_app.url == WEBAPP_URL
    assert cta.web_app.url != CONSUME_URL


def test_desktop_button_carries_consume_url_as_plain_link():
    markup = menu.welcome_keyboard("ru", has_shop=False, consume_url=CONSUME_URL)
    desktop = markup.inline_keyboard[1][0]
    assert desktop.text == t("ru", "btn_open_desktop")
    assert desktop.url == CONSUME_URL
    assert desktop.web_app is None  # a browser link, not a WebApp


def test_no_desktop_button_without_consume_url():
    markup = menu.welcome_keyboard("ru", has_shop=False, consume_url=None)
    # Second row is Demo/Support, not the desktop button.
    texts = [b.text for row in markup.inline_keyboard for b in row]
    assert t("ru", "btn_open_desktop") not in texts


def test_uz_labels():
    markup = menu.welcome_keyboard("uz", has_shop=True, consume_url=CONSUME_URL)
    assert _cta(markup).text == t("uz", "btn_open_platform")
    assert markup.inline_keyboard[1][0].text == t("uz", "btn_open_desktop")
