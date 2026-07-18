# Реферальные ссылки на боте платформы — спека для агента бота

> Для команды/агента, который ведёт **платформенный бот @Grammerce_bot** (отдельный проект).
> Backend уже готов на стороне платформы. Здесь — что нужно сделать в боте.

## Что делаем

Партнёрская/маркетинговая ссылка вида:

```
https://t.me/Grammerce_bot?start=ref_<code>
```

Когда пользователь открывает такую ссылку и жмёт **Start**, бот должен:
1. Распознать payload `ref_<code>`.
2. Сообщить платформе, что человек зашёл по этому реф-коду (для статистики).
3. Показать приветствие со скидкой (её отдаёт бэкенд в ответе).
4. Продолжить обычный сценарий регистрации (кнопка «Создать магазин» через `?start=register`).

Пришедший по реф-ссылке автоматически получит **скидку на «заявку под ключ» (setup fee)** —
её применяет платформа при оформлении, боту ничего дополнительно делать не нужно.

## Как Telegram передаёт payload

Payload — это всё, что идёт после `/start `:

```python
# aiogram
start_arg = message.text.split(maxsplit=1)[1] if message.text and " " in message.text else ""
```

Реферальная ветка — по префиксу `ref_` (по аналогии с уже существующей веткой `register`):

```python
if start_arg.startswith("ref_"):
    code = start_arg[4:]          # срезаем "ref_"
    await handle_referral(message, code)
    # дальше — обычный онбординг/приветствие
```

## Вызов бэкенда платформы

`POST {PLATFORM_BACKEND_URL}/api/platform/referrals/track`

Заголовок аутентификации — тот же секрет, что уже используется ботом для
`/api/auth/telegram/issue`:

```
X-Bot-Secret: <PLATFORM_BOT_SHARED_SECRET>
Content-Type: application/json
```

Тело:

```json
{
  "code": "<code>",
  "telegram_id": 123456789,
  "username": "ivan",
  "first_name": "Иван"
}
```

Пример (aiogram + httpx), fire-and-forget:

```python
import httpx

async def handle_referral(message, code: str):
    backend = PLATFORM_BACKEND_URL.rstrip("/")
    secret = PLATFORM_BOT_SHARED_SECRET
    if not backend or not secret:
        return  # молча, не блокируем пользователя
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{backend}/api/platform/referrals/track",
                headers={"X-Bot-Secret": secret, "Content-Type": "application/json"},
                json={
                    "code": code,
                    "telegram_id": message.from_user.id,
                    "username": message.from_user.username,
                    "first_name": message.from_user.first_name,
                },
            )
        data = resp.json() if resp.status_code == 200 else {}
    except Exception:
        return  # сеть/таймаут — не мешаем онбордингу

    if data.get("ok"):
        d = data.get("discount") or {}
        if d.get("type") == "percent":
            promo = f"скидка {d.get('value')}% на подключение под ключ"
        else:
            promo = f"скидка {int(d.get('value') or 0):,} сум на подключение под ключ".replace(",", " ")
        await message.answer(
            f"🎁 Вы пришли по партнёрской ссылке — вас ждёт {promo}.\n"
            f"Нажмите «Создать магазин», чтобы начать."
        )
```

## Ответ бэкенда

- Успех (код найден и активен):
  ```json
  { "ok": true, "label": "Партнёр X", "discount": { "type": "fixed", "value": 500000 } }
  ```
  `type`: `fixed` (сумма в сумах) | `percent` (0..100).
- Неизвестный/выключенный код:
  ```json
  { "ok": false }
  ```
  → бот просто продолжает обычный сценарий, без сообщения о скидке.

## Важные детали

- **Идемпотентность.** Повторный `/start ref_<code>` тем же пользователем НЕ создаёт новый заход —
  бэкенд считает уникальных людей по паре (ссылка, telegram_id). Бот может звать `track` при
  каждом старте, это безопасно.
- **Скидку применяет платформа.** Бот только фиксирует заход и (опционально) показывает
  приветствие. Само списание скидки происходит, когда этот же telegram_id зарегистрирует магазин
  и оформит «заявку под ключ».
- **Fire-and-forget.** Ошибка/таймаут `track` не должны мешать пользователю — глотаем и продолжаем.
- **Дальше — регистрация.** После реф-ветки веди пользователя в существующий флоу
  `?start=register` (кнопка «Создать магазин» через `/api/auth/telegram/issue`).

## Переменные окружения (у бота)
- `PLATFORM_BACKEND_URL` — базовый URL платформы (напр. `https://grammerce.io`).
- `PLATFORM_BOT_SHARED_SECRET` — общий секрет (тот же, что для `/api/auth/telegram/issue`).

## Образцы в коде платформы (для сверки)
- Ветка `register` deep-link: `bot/handlers/registration.py:302-347` (POST на платформу с `X-Bot-Secret`).
- Спека support-deeplink: `md_s/grammerce_bot_support_deeplink.md`.
- Эндпоинт трекинга: `routers/referrals.py` → `POST /api/platform/referrals/track`.
