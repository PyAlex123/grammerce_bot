# Grammerce Bot — редизайн: интеграция и ручные шаги

Документ к ветке `Redesign`. Что сделано в коде, что нужно настроить на стороне
платформы и в BotFather, чтобы редизайн заработал полностью.

---

## 1. WebApp (Mini App) авторизация

Главная кнопка «Создать магазин» и кнопки уведомлений становятся **WebApp-кнопками**
(авто-логин по Telegram `initData`), когда в `.env` задан `PLATFORM_WEBAPP_URL`.
Если пусто — бот откатывается на рабочий `consume_url`-флоу (одна кнопка-ссылка).

```
# .env бота
PLATFORM_WEBAPP_URL=https://grammerce.io/app   # URL страницы Mini App
```

**Требование к платформе:** страница по `PLATFORM_WEBAPP_URL` должна:
1. Прочитать `Telegram.WebApp.initData` (Telegram WebApp SDK).
2. Провалидировать подпись `initData` секретом из bot token (HMAC-SHA256).
3. Создать/найти `User` по `telegram_id` и выдать сессию (залогинить без пароля).

Меню-кнопка слева от поля ввода ставится ботом автоматически при старте
(`set_chat_menu_button` → WebApp «Кабинет»), если `PLATFORM_WEBAPP_URL` задан.

---

## 2. Контракт вебхуков (платформа → бот)

Все эндпоинты: `POST`, заголовок `X-Bot-Secret: <PLATFORM_BOT_SHARED_SECRET>`,
тело JSON с обязательным `telegram_id`. Ответ `200 {"ok": true}`; `401` — неверный
секрет; `400` — нет/битый `telegram_id`.

### 2.1. `POST /api/bot/user-registered` (уже вызывается платформой)
```json
{ "telegram_id": "123", "username": "alex", "first_name": "Александр", "last_name": "Иванов" }
```
Бот: уведомляет админа (как раньше) **и** шлёт пользователю «🎉 Магазин создан!»
с кнопкой «Открыть кабинет». Повторный вызов для того же `telegram_id` — тихо
игнорируется (без повторных сообщений).

### 2.2. `POST /api/bot/new-order` (нужно подключить на платформе)
```json
{ "telegram_id": "123", "order_number": 42, "customer_name": "Вася", "phone": "+998901112233", "amount": "100 000 сум" }
```
Бот шлёт пользователю «🛒 Новый заказ №42…» + кнопка «Открыть заказ».

### 2.3. `POST /api/bot/low-products` (ре-энгейджмент, нужно подключить)
```json
{ "telegram_id": "123", "product_count": 2 }
```
Бот шлёт «В вашем магазине 2 товара…» + кнопка «Добавить товары».
Платформа сама решает, *когда* звать (например, cron через 2–3 дня при < N товаров).

> Эндпоинты 2.2 и 2.3 уже реализованы и покрыты тестами, но «спят», пока платформа
> их не вызывает. Тексты — `bot/locales/{ru,uz}.py` (`notify_*`).

---

## 3. BotFather — ручной чек-лист (без кода)

Через [@BotFather](https://t.me/BotFather):
- **Герой-картинка**: `/setuserpic` (видна до `/start`).
- **Короткое описание** (`/setdescription` — до `/start`):
  - RU: `Магазин в Telegram за 2 минуты. 0% комиссии.`
  - UZ: `2 daqiqada Telegram'da do'kon. 0% komissiya.`
- **«О боте»** (`/setabouttext`):
  - RU: `Grammerce — ваш магазин в Telegram за 2 минуты. Витрина, оплата Click/Payme/Uzum, заказы и клиенты в одном месте. 0% комиссии с продаж. Нажмите «Запустить».`
  - UZ: `Grammerce — 2 daqiqada Telegram'dagi do'koningiz. Vitrina, Click/Payme/Uzum to'lovi, buyurtma va mijozlar bir joyda. Savdodan 0% komissiya. «Boshlash» tugmasini bosing.`
- **Menu-кнопка / Mini App**: задать домен Mini App (`/setdomain` или раздел Bot Settings → Menu Button). Бот также ставит menu-кнопку программно при наличии `PLATFORM_WEBAPP_URL`.

---

## 4. Не реализовано намеренно

**Соцдоказательство (§5 спеки — «пара витрин „сделано на Grammerce“»)** — не добавлено:
нет реальных витрин/ссылок, чтобы не выдумывать контент. Когда будут настоящие
ссылки на магазины-клиенты, их можно добавить в приветствие или раздел «Демо».
