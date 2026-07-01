# Grammerce Bot — Research Survey Integration

> Спецификация для интеграции CustDev-опроса в существующий Telegram-бот Grammerce.
> Цель: получить параллельный поток для исследования рынка через deep-link, не нарушая основной коммерческий поток.

---

## Контекст

Существующий бот Grammerce имеет главное меню с тремя пунктами:
- Создать магазин
- Смотреть демо
- Поддержка

Нужно добавить **отдельный исследовательский поток**, активируемый специальным deep-link. Этот поток **не отображается** в главном меню и **не виден** обычному пользователю.

---

## 1. Deep-Link Handling

### Формат
```
t.me/<bot_username>?start=research_<source>
```

### Поддерживаемые источники
- `research_uzsellerclub` — для Uz Seller Club (текущий приоритет)
- `research_marketplace` — для @MarketplaceUzum (план B)
- `research_bestats` — для BESTATS Community (план C)
- `research_other` — для всех прочих каналов

### Логика обработки `/start`

```python
async def handle_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    start_param = extract_start_param(message)  # например "research_uzsellerclub"

    if start_param and start_param.startswith("research_"):
        # ИССЛЕДОВАТЕЛЬСКИЙ ПОТОК
        await save_survey_source(user_id, username, start_param)
        await send_research_welcome(message)
        # НЕ показываем главное меню
    else:
        # ОБЫЧНЫЙ ПОТОК (как было)
        await show_main_menu(message)
```

### Welcome-сообщение для research-потока

Текст:
```
Здравствуйте.

Это короткий опрос для исследования рынка селлеров маркетплейсов Узбекистана.

8 вопросов · ~2 минуты · конфиденциально

Опрос проводится совместно с Uz Seller Club. Результаты будут опубликованы в канале клуба обезличенно. Контакты собираем только если вы их явно укажете в финале.

Нажмите кнопку ниже, чтобы начать.
```

Кнопка под сообщением:
- **Текст:** `🔍 Начать опрос`
- **Тип:** WebApp button
- **URL:** `https://grammerce.io/research/survey` (или используемый домен)

**Главное меню НЕ показываем** в этом сообщении. Никаких кнопок «Создать магазин» / «Демо» / «Поддержка».

---

## 2. WebApp Survey Integration

### URL опросника
```
https://grammerce.io/research/survey
```

### Передача параметров
Telegram WebApp автоматически передаёт через `tg.initDataUnsafe`:
- `user.id` → TG user ID
- `user.username` → TG username (если есть)
- `user.first_name` / `last_name`
- `start_param` → значение из deep-link (`research_uzsellerclub`)

Опросник уже умеет читать эти данные. Никаких query-параметров через URL передавать не нужно.

### Обработка `web_app_data`

Когда пользователь завершает опрос, WebApp вызывает `tg.sendData(JSON)`. Бот должен:

```python
async def handle_web_app_data(message: Message):
    try:
        payload = json.loads(message.web_app_data.data)
    except json.JSONDecodeError:
        await message.answer("Не удалось обработать ответы. Попробуйте ещё раз.")
        return

    # Валидация структуры
    if payload.get("type") != "survey_submission":
        return

    # Сохраняем в БД
    await save_survey_response(
        user_id=message.from_user.id,
        username=message.from_user.username,
        payload=payload
    )

    # Отправляем подтверждение БЕЗ CTA-кнопок
    await send_confirmation(message)
```

### Структура payload (что приходит от WebApp)

```json
{
  "type": "survey_submission",
  "timestamp": "2026-05-14T10:23:15.123Z",
  "answers": {
    "category": "Одежда и обувь",
    "platforms": ["Uzum", "Свой Instagram-магазин"],
    "commission": "20–30%",
    "contacts": "Не вижу никого",
    "lost_case": "Клиент написал негативный отзыв, я не смог объяснить...",
    "own_channel": "Был, забросил",
    "budget": "300 000 – 700 000 сум/мес",
    "pain": "Возвраты съедают маржу, не могу удержать клиента..."
  },
  "contact": {
    "tg": "@username",
    "store": "MyShop",
    "consent": true
  },
  "meta": {
    "tg_user": {
      "id": 123456789,
      "username": "username",
      "first_name": "Alex"
    },
    "start_param": "research_uzsellerclub",
    "lang": "ru-RU",
    "platform": "android"
  }
}
```

### Confirmation-сообщение (после опроса)

```
Спасибо за участие.

Опрос конфиденциальный — для аналитики используется агрегированная статистика.

Если оставили контакт и согласились на связь — напишем по итогам отбора пилотных проектов в течение 2 недель.

Отчёт «Профиль селлера Узбекистана 2026» опубликуем в @uzsellerclub.
```

**КРИТИЧНО:** никаких inline-кнопок «Узнать про Grammerce» / «Демо» / «Связаться». Только текст.

Если пользователь хочет дальше — он сам напишет `/start` (без параметра) или `/menu`. Это его инициатива, не наша автоподтяжка.

---

## 3. Главное меню — что важно

### Когда показываем главное меню
- `/start` без параметра
- `/menu` (если такая команда есть)
- Любая команда из главного меню (`/create_store`, `/demo`, `/support`)

### Когда НЕ показываем главное меню
- При первом запуске с `start=research_*`
- После завершения опроса (web_app_data)

### Что если пользователь после опроса напишет `/start`?
- Показываем обычное главное меню. Это **его выбор** — он сам захотел дальше.
- Не блокируем, не подталкиваем, не упоминаем что он только что прошёл опрос.

---

## 4. Database Schema

Минимальный набор таблиц (можно адаптировать под уже существующую БД):

### `survey_sources`
Аналитика по источникам.

```sql
CREATE TABLE survey_sources (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    source VARCHAR(64) NOT NULL,  -- research_uzsellerclub
    entered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, source)  -- один user может прийти из одного источника один раз
);

CREATE INDEX idx_survey_sources_source ON survey_sources(source);
```

### `survey_responses`
Финальные ответы.

```sql
CREATE TABLE survey_responses (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    source VARCHAR(64),

    -- Answers (8 questions)
    category VARCHAR(64),
    platforms TEXT[],  -- multi-select
    commission VARCHAR(32),
    contacts VARCHAR(64),
    lost_case TEXT,
    own_channel VARCHAR(64),
    budget VARCHAR(64),
    pain TEXT,

    -- Contact
    contact_tg VARCHAR(255),
    contact_store VARCHAR(255),
    consent BOOLEAN DEFAULT FALSE,

    -- Meta
    lang VARCHAR(16),
    platform VARCHAR(32),

    -- Raw payload for analytics flexibility
    raw_payload JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_responses_source ON survey_responses(source);
CREATE INDEX idx_responses_consent ON survey_responses(consent) WHERE consent = TRUE;
CREATE INDEX idx_responses_created ON survey_responses(created_at);
```

---

## 5. Funnel Analytics

Метрики которые нужно отслеживать:

| Метрика | Откуда брать | Зачем |
|---|---|---|
| Кликов по deep-link | INSERT в `survey_sources` | Conversion от поста Романа |
| Начали опрос | Event "webapp_opened" (опционально) | UX-анализ |
| Завершили опрос | INSERT в `survey_responses` | Главная метрика |
| Оставили контакт | `contact_tg IS NOT NULL` | Полу-самоквалификация |
| Consent=true | `consent = TRUE` | Воронка пилота |

### Простой dashboard-запрос

```sql
SELECT
    source,
    COUNT(*) FILTER (WHERE TRUE) AS clicks,
    COUNT(DISTINCT sr.user_id) AS completed,
    COUNT(DISTINCT sr.user_id) FILTER (WHERE sr.contact_tg IS NOT NULL) AS with_contact,
    COUNT(DISTINCT sr.user_id) FILTER (WHERE sr.consent = TRUE) AS with_consent
FROM survey_sources ss
LEFT JOIN survey_responses sr ON sr.user_id = ss.user_id AND sr.source = ss.source
GROUP BY source;
```

---

## 6. Privacy & Safety

### Что хранить
- Все ответы опроса (включая user_id даже без consent — для агрегата)
- Контакт только если respondent его явно ввёл
- Consent-флаг явный

### Что НЕ делать
- НЕ писать в личку пользователям с `consent = false`
- НЕ использовать user_id для outreach без явного согласия
- НЕ передавать данные третьим сторонам (даже партнёру Uz Seller Club — только агрегированные результаты в отчёте)

### Privacy notice в welcome-сообщении
Уже включено: "конфиденциально", "контакты только если явно укажете".

---

## 7. Testing Checklist

Перед запуском боевой ссылки на 1268 подписчиков:

- [ ] Deep-link `t.me/<bot>?start=research_uzsellerclub` открывает welcome-сообщение
- [ ] Welcome-сообщение содержит **только** кнопку «Начать опрос», без других пунктов меню
- [ ] Кнопка открывает WebApp с правильным URL
- [ ] WebApp получает `tg.initDataUnsafe.start_param === "research_uzsellerclub"`
- [ ] Все 8 вопросов рендерятся корректно
- [ ] Контактный экран показывается после Q8
- [ ] Checkbox consent работает (можно поставить и снять)
- [ ] `tg.sendData(payload)` отправляет корректный JSON
- [ ] Бот получает `web_app_data` и парсит payload
- [ ] Запись попадает в `survey_responses` со всеми полями
- [ ] `source` корректно сохраняется
- [ ] `consent` сохраняется как boolean
- [ ] Confirmation-сообщение приходит **без кнопок** (только текст)
- [ ] WebApp автоматически закрывается через 4 сек
- [ ] После закрытия — пользователь видит **только** confirmation, без главного меню
- [ ] `/start` без параметра показывает обычное главное меню
- [ ] `/start research_uzsellerclub` дважды — не создаёт дубли в `survey_sources` (UNIQUE constraint)

---

## 8. Implementation Priority

Порядок реализации (если время ограничено до конференции 19 мая):

### MVP (минимум для запуска опроса)
1. Deep-link parsing для `research_*`
2. Welcome-сообщение + WebApp button (без главного меню)
3. Хостинг опросника на `grammerce.io/research/survey`
4. `web_app_data` handler — приём JSON
5. Сохранение в БД (даже простая таблица или Google Sheets для MVP)
6. Confirmation-сообщение без CTA

### Phase 2 (после конференции, для отчёта)
7. Полная схема БД с `survey_sources` + `survey_responses`
8. Dashboard-запросы для воронки
9. Сегментация Hot/Warm/Cold через SQL
10. Аналитика по источникам

### Phase 3 (после первых пилотов)
11. Автоматическое уведомление команды о новых consent=true
12. Outreach-шаблоны для Hot-сегмента

---

## 9. Edge Cases

| Кейс | Что делать |
|---|---|
| Пользователь закрыл WebApp до завершения опроса | Ничего не сохраняем. Если откроет ссылку снова — опрос с начала |
| Пользователь прошёл опрос дважды | Сохраняем обе записи. В аналитике берём последнюю по `created_at` |
| WebApp не открывается (старый клиент TG) | Welcome-сообщение содержит fallback ссылку на `grammerce.io/research/survey` |
| `start_param` отсутствует | Обычное главное меню (поведение как было) |
| `web_app_data` приходит с битым JSON | Логируем ошибку, отвечаем пользователю «Не удалось обработать. Попробуйте ещё раз» |
| Пользователь в research-потоке нажал `/menu` | Показываем главное меню — это его выбор |

---

## 10. Что говорить если Роман попросит "посмотреть как работает"

Перед публичным запуском можно дать ему ссылку:
```
t.me/<bot_username>?start=research_uzsellerclub
```

Он пройдёт сам — увидит UX, формулировки вопросов, финальный экран. Это его валидация методологии.

Опросник в продакшене всё равно сохранит его ответ (помечен по user_id) — можно исключить из финальной аналитики или пометить как `test_response = true` в payload.
