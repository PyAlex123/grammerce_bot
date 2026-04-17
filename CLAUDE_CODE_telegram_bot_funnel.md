# Telegram-бот Grammerce — лидогенерация + демо-магазины

## Решения
- Библиотека: aiogram 3.x, long polling на старте, отдельный Docker-service
- FSM: MemoryStorage на старте, миграция на Redis после 100+ активных лидов
- Локализация: словари `locales/ru.py` и `locales/uz.py` (Python dict, без i18n-библиотек)
- Языки: UZ и RU на старте (EN позже), выбор при первом /start, сохранение в `bot_users.language`
- Демо-магазины: WebApp-кнопки на живые шаблоны по 6 нишам (кофейня, одежда, цветы, доставка еды, косметика, электроника)
- Регистрация: deep link на `admin.grammerce.io/sign-up` с UTM + `tg_user_id` для атрибуции
- Поддержка: FAQ инлайн-кнопки (цена, Setup Fee, сроки) → кнопка «Живой оператор» → FSM сбора вопроса → форвард в закрытый чат операторов
- UTM-атрибуция: парсинг `start`-payload Telegram deep link (рекламные ссылки вида `t.me/bot?start=utm_tgads_uzb4ru`)
- Аналитика: единая таблица `bot_events` для всей воронки
- Связь с кабинетом сайта: по `tg_user_id` в URL регистрации → сохранение в `users.telegram_id` при создании аккаунта
- Никакого хардкода текстов — всё через `locales/`

## Миграция БД (новые таблицы)
- `bot_users`: id, telegram_id UNIQUE, username, language CHAR(2), utm_source, utm_medium, utm_campaign, registered_user_id FK NULLABLE, first_seen_at, last_active_at
- `bot_demo_views`: id, bot_user_id FK, niche VARCHAR(32), viewed_at
- `bot_support_tickets`: id, bot_user_id FK, message TEXT, status VARCHAR(16), operator_id NULLABLE, created_at, resolved_at
- `bot_events`: id, bot_user_id FK, event_type VARCHAR(32), payload JSONB, created_at
- В `users` сайта: добавить `telegram_id` BIGINT NULLABLE UNIQUE (для связи аккаунтов)

## Этапы
0. Аудит проекта: найти точки интеграции (модель User сайта, API регистрации, docker-compose, .env) → `AUDIT_BOT.md` ⛔ СТОП
1. Базовая структура: aiogram 3.x, новый Docker-service, `.env` с BOT_TOKEN, хэндлер /start с «Hello» для проверки ⛔ СТОП
2. Миграция БД: 4 новые таблицы + поле `telegram_id` в `users` ⛔ СТОП
3. Выбор языка при /start: инлайн-кнопки UZ/RU, сохранение в `bot_users`, словари `locales/` ⛔ СТОП
4. Парсинг UTM из start-payload: сохранение в `bot_users` при первом /start (формат `utm_источник_кампания`) ⛔ СТОП
5. Главное меню: приветствие + 3 кнопки (Создать магазин, Смотреть демо, Поддержка) с переводом по языку пользователя ⛔ СТОП
6. Демо-поток: меню выбора ниши (6 кнопок) → WebApp-кнопка на демо-магазин + лог в `bot_demo_views` ⛔ СТОП
7. Регистрация: кнопка с deep link на `admin.grammerce.io/sign-up?utm_*&tg_user_id=...` + событие `register_click` ⛔ СТОП
8. Поддержка: 3–5 FAQ-кнопок с готовыми ответами + «Живой оператор» → FSM сбора вопроса → форвард в чат операторов, тикет в `bot_support_tickets` ⛔ СТОП
9. Событийный middleware: пишет все действия в `bot_events` (language_select, menu_view, demo_view, register_click, support_faq, support_ticket) ⛔ СТОП
10. Связь с кабинетом: при регистрации через сайт с `tg_user_id` — проставить `users.telegram_id` и `bot_users.registered_user_id` ⛔ СТОП
11. Сквозное тестирование + edge cases (повторный /start, смена языка, пустой UTM, сетевые сбои, дубликаты telegram_id) ⛔ СТОП

## Правила работы по этапам
- Каждый этап: автотест (pytest) → рекомендации по ручному тестированию в чате → ⛔ СТОП → исправления по фидбэку → коммит и пуш → переход к следующему
- Формат коммита: `feat(bot): описание этапа`
- Перед началом: `git checkout -b telegram-bot-funnel`
- Ручное тестирование: тестовый бот через @BotFather, реальные клики в Telegram
- Логи: INFO для событий воронки, ERROR для сбоев, без PII в логах
- Перед этапом 8 завести закрытый Telegram-чат операторов и добавить его ID в `.env` как `SUPPORT_CHAT_ID`
