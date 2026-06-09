# Telegram Auth — интеграция бота с платформой Grammerce

> ⚠️ Ветка `Redesign`: главная кнопка теперь **WebApp (Mini App)** с авто-логином
> по `initData`, когда задан `PLATFORM_WEBAPP_URL`. Описанный ниже `consume_url`-флоу
> остаётся **fallback** при пустом `PLATFORM_WEBAPP_URL`. См. `mdS/redesign_integration.md`.

## Статус

✅ **Реализовано** на ветке `tgauth` (Вариант Б — одноразовый токен).
Сайт Grammerce открывает `t.me/GrammerceBot?start=register`, бот
запрашивает у платформы `consume_url` и отдаёт пользователю inline-
кнопку «Открыть платформу». Платформа по токену создаёт/логинит
пользователя по `telegram_id`.

---

## Как это работает (финальная схема)

```
Пользователь нажимает «🏪 Создать магазин» в боте
  ИЛИ открывает t.me/GrammerceBot?start=register
        ↓
Бот делает POST {PLATFORM_URL}/api/auth/telegram/issue
  заголовок X-Bot-Secret: <PLATFORM_BOT_SHARED_SECRET>
  тело: { telegram_id, first_name, last_name, username, photo_url: null }
        ↓
Платформа:
  - создаёт одноразовый токен (UUID, TTL 5 минут)
  - возвращает { token, consume_url, expires_at }
        ↓
Бот шлёт пользователю сообщение + inline-кнопку
  «✅ Открыть платформу» с url = consume_url
        ↓
Пользователь кликает → браузер идёт на consume_url
        ↓
Платформа валидирует токен, помечает как использованный,
  создаёт/находит User по telegram_id, выдаёт сессию
        ↓
Редирект в личный кабинет (залогинен)
```

Повторный клик по `consume_url` (или клик после истечения TTL) →
редирект на `/login?error=auth_expired`.

---

## API-контракт

**Endpoint:** `POST {PLATFORM_URL}/api/auth/telegram/issue`

**Headers:**

| Header | Описание |
|---|---|
| `X-Bot-Secret` | Общий секрет, должен совпадать с `BOT_SHARED_SECRET` на платформе |
| `Content-Type` | `application/json` |

**Body** (обязательно только `telegram_id`, остальное опционально):
```json
{
  "telegram_id": "123456789",
  "first_name":  "Александр",
  "last_name":   "Иванов",
  "username":    "alex",
  "photo_url":   null
}
```

**Ответ 200:**
```json
{
  "token": "a1b2c3d4-...",
  "consume_url": "https://grammerce.io/api/auth/telegram/consume?token=a1b2c3d4-...",
  "expires_at": "2026-04-20T12:34:56+00:00"
}
```

**Ошибки:**
- `401` — неверный/отсутствует `X-Bot-Secret`
- `501` — секрет не настроен на платформе
- Сетевые таймауты / 5xx — логируются, пользователю показывается
  сообщение об ошибке

TTL токена — 5 минут. Токен одноразовый.

---

## Что есть в боте (реализация)

| Файл | Что делает |
|---|---|
| [bot/services/platform_auth.py](bot/services/platform_auth.py) | `issue_auth_link(tg_user)` — POST на платформу, возвращает `consume_url`. Поднимает `PlatformAuthError` при любой ошибке |
| [bot/handlers/register.py](bot/handlers/register.py) | `send_auth_link()` helper + handler reply-кнопки «🏪 Создать магазин» |
| [bot/handlers/start.py](bot/handlers/start.py) | Обработка payload `register` в `/start` (deeplink с сайта) |
| [bot/locales/ru.py](bot/locales/ru.py) · [uz.py](bot/locales/uz.py) | Тексты `register_link_text` / `register_link_btn` / `register_error` |
| [bot/config.py](bot/config.py) · [.env.example](.env.example) | `PLATFORM_URL` + `PLATFORM_BOT_SHARED_SECRET` |
| [tests/test_register.py](tests/test_register.py) | Моки `issue_auth_link`: успех, `PlatformAuthError`, deeplink, локаль |

Ни таблица `bot_auth_tokens`, ни Alembic-миграции в боте не нужны —
токены управляются платформой.

---

## События в BotEvent

- `register_click` — `{"consume_url": "..."}` — ссылка успешно выдана
- `register_error` — `{"reason": "..."}` — платформа вернула ошибку /
  таймаут / сеть упала

---

## Конфигурация

`.env` бота:
```
PLATFORM_URL=https://grammerce.io
PLATFORM_BOT_SHARED_SECRET=<тот же секрет, что и BOT_SHARED_SECRET на платформе>
```

Значение `PLATFORM_BOT_SHARED_SECRET` согласуется один раз с админом
платформы и **должно в точности совпадать** с `BOT_SHARED_SECRET` в
её конфиге. Если не совпадёт — бот поймает 401 и пользователь увидит
«⚠️ Не удалось создать ссылку…».

---

## История решения (оставлено как контекст)

### Вариант А — URL-параметры (отклонено)
Передача `tg_user_id` в открытом URL — любой может подделать ссылку и
войти под чужим аккаунтом. Так работал прошлый код
(`https://admin.grammerce.io/sign-up?tg_user_id=...`).

### Вариант Б — Одноразовый токен ✅ (выбрано)
Платформа выдаёт токен в ответ на аутентифицированный через
`X-Bot-Secret` запрос. Токен нельзя подделать, TTL 5 минут,
одноразовый.

### Вариант В — Telegram Login Widget (отклонено)
Работает только на веб-странице, не подходит для дипссылки из бота.

---

## Verification (E2E)

1. В `.env` бота выставить `PLATFORM_URL` и `PLATFORM_BOT_SHARED_SECRET`
   (совпадающий с платформой). Запустить `python -m bot.main`.
2. Нажать «🏪 Создать магазин» в чате → получить сообщение «Нажмите
   кнопку ниже…» с одной inline-кнопкой. В `BotEvent` — `register_click`.
3. Клик по кнопке → браузер → платформа логинит пользователя и
   редиректит в кабинет.
4. Открыть `t.me/<bot>?start=register` → бот присылает ту же кнопку
   без выбора языка.
5. Повторный клик по `consume_url` (или через 5+ минут) → редирект на
   `/login?error=auth_expired`.
6. Сломать секрет в `.env` → нажать «Создать магазин» → юзер видит
   ошибку, в логах 401, в `BotEvent` — `register_error`.
7. `pytest` — все тесты (включая `tests/test_register.py`) зелёные.
