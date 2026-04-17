from bot.locales.ru import texts as _ru
from bot.locales.uz import texts as _uz

_LOCALES: dict[str, dict[str, str]] = {"ru": _ru, "uz": _uz}


def t(lang: str | None, key: str) -> str:
    """Return localised string. Falls back to Russian if key or lang missing."""
    locale = _LOCALES.get(lang or "ru", _ru)
    return locale.get(key) or _ru.get(key, key)
