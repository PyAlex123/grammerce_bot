# Grammerce — пуш-уведомления для владельца бизнеса (RU + UZ)

Активационные напоминания, которые бот-воронка шлёт **владельцу бизнеса**, если он застрял на каком-то шаге онбординга. Цель — мягко подтолкнуть «сделать следующий шаг», на том языке, который он выбрал в боте.

**Эти пуши НЕ включают:**
- события «магазин создан / клиент оплатил / прошёл обучение» → уходят **тебе (@PyAleX)**;
- уведомления о заказах → уходят **менеджеру магазина** (отдельный человек).

---

## Глобальные правила

1. **Один активный пуш на человека** — по его текущему застрявшему шагу. Сделал шаг → этот пуш выключается, при необходимости включается следующий. Никогда не шлём два разных напоминания сразу.
2. **Порядок шагов (приоритет):** создать магазин → загрузить первый товар → пройти обучение → продлить триал.
3. **Язык** = тот, что выбран в боте (`lang = ru | uz`). Берём соответствующий вариант текста.
4. **Тихие часы:** отправка только **09:00–21:00 по Ташкенту**. Что выпало на ночь — копим и шлём утром.
5. **Не давим:** максимум 2 отправки на шаг. Если после второй человек не реагирует — замолкаем по этому шагу.
6. **Отписка:** в настройках бота — тумблер «не присылать напоминания» (триал-напоминания оставляем как сервисные).
7. **Картинка** — опциональна, усиливает первый пуш. Текст в картинку **не запекаем** (кириллица/узбекский рисуются плохо) — слова несёт само сообщение, картинка только атмосферная.

---

## Сводка

| # | Когда (застрял на шаге) | Отправка 1 | Отправка 2 | Канал в тексте | Картинка |
|---|---|---|---|---|---|
| 1 | Зашёл, не создал магазин | +24 ч | +3 дня | во 2-й | да |
| 2 | Создал, не загрузил товар | +24 ч | +3 дня | во 2-й | да |
| 3 | Загрузил товар, не прошёл обучение | +24 ч | +2–3 дня | во 2-й | да |
| 4 | Триал заканчивается | за 2 дня | за 1 день | — | да (по желанию) |

Кнопки в квадратных скобках `[...]` — это WebApp-кнопка или ссылка под сообщением. `[ссылка на канал]` подставить, когда выберешь `@username` канала.

---

## Пуш 1 — Зашёл в бот, но не создал магазин

**Триггер:** был `/start`, но нет события `store_created`.
**Отправка 1:** +24 ч после первого входа. **Отправка 2:** +3 дня, если магазина всё ещё нет.

### Отправка 1

**RU**
🛍 Ваш магазин в Telegram — в паре кликов

Вы заглянули, но пока не создали магазин. Витрину, корзину и оплату мы соберём за вас — нужно только начать.

`[Создать магазин]`

**UZ**
🛍 Telegram'dagi do'koningiz — bir necha bosishda

Siz kirdingiz, lekin hali do'kon yaratmadingiz. Vitrina, savat va to'lovni biz yig'amiz — faqat boshlash kerak.

`[Do'kon yaratish]`

### Отправка 2

**RU**
💡 Не до конца понятно, как это работает?

Создать магазин — правда пара минут, без сайтов и кода. А если хотите сперва посмотреть, как другие продают в Telegram, — загляните в наш канал, там разборы и примеры.

`[Создать магазин]` · `[Канал: ссылка на канал]`

**UZ**
💡 Qanday ishlashini tushunmadingizmi?

Do'kon yaratish — haqiqatan bir necha daqiqa, saytsiz va kodsiz. Avval boshqalar Telegram'da qanday sotishini ko'rmoqchi bo'lsangiz — kanalimizga kiring, u yerda tahlil va misollar bor.

`[Do'kon yaratish]` · `[Kanal: havola]`

**Картинка (бриф):** glowing storefront / shop window forming inside a Telegram chat bubble. Dark background `#0F1115`, teal accent glow, flat light-3D, minimalist, generous empty space, **no text**.

---

## Пуш 2 — Создал магазин, но не загрузил первый товар

**Триггер:** есть `store_created`, но `product_count == 0`.
**Отправка 1:** +24 ч после создания магазина. **Отправка 2:** +3 дня, если товаров всё ещё нет.

### Отправка 1

**RU**
📦 Магазин готов, но полки пустые

Добавьте первый товар — фото, название, цена. Как только он появится, витрину уже можно показывать клиентам.

`[Добавить товар]`

**UZ**
📦 Do'kon tayyor, lekin javonlar bo'sh

Birinchi mahsulotni qo'shing — rasm, nomi, narxi. U paydo bo'lishi bilan vitrinani mijozlarga ko'rsatish mumkin.

`[Mahsulot qo'shish]`

### Отправка 2

**RU**
🛒 Один товар — и магазин оживёт

Не обязательно грузить всё сразу: начните с одного-двух, остальное добавите позже. Нужна помощь с фото и описанием? В канале есть короткий разбор, как оформить карточку, чтобы покупали.

`[Добавить товар]` · `[Канал: ссылка на канал]`

**UZ**
🛒 Bitta mahsulot — va do'kon jonlanadi

Hammasini birato'la yuklash shart emas: bittadan boshlang, qolganini keyin qo'shasiz. Rasm va tavsif bilan yordam kerakmi? Kanalda mahsulot kartasini sotiladigan qilib bezash bo'yicha qisqa tahlil bor.

`[Mahsulot qo'shish]` · `[Kanal: havola]`

**Картинка (бриф):** a single empty product card with a glowing teal "+" placeholder on an otherwise empty shelf. Dark `#0F1115`, teal accent, flat light-3D, minimalist, **no text**.

---

## Пуш 3 — Загрузил товар, но не прошёл обучение

**Триггер:** `product_count > 0`, но `training_completed == false`.
**Отправка 1:** +24 ч. **Отправка 2:** +2–3 дня, если обучение всё ещё не пройдено.

### Отправка 1

**RU**
🎓 Остался один шаг

Товары на месте — теперь короткое обучение, и вы сможете принимать и вести заказы сами. Быстро и по сути.

`[Пройти обучение]`

**UZ**
🎓 Bitta qadam qoldi

Mahsulotlar joyida — endi qisqa o'qish, va buyurtmalarni o'zingiz qabul qilib yurita olasiz. Tez va aniq.

`[O'qishni o'tish]`

### Отправка 2

**RU**
✅ Запуститесь уже сегодня

До приёма первых заказов — буквально одно короткое обучение. Застряли? Напишите @PyAleX, поможем пройти за пару минут, или загляните в канал — там показываем, как всё устроено.

`[Пройти обучение]` · `[Канал: ссылка на канал]`

**UZ**
✅ Bugun ishga tushing

Birinchi buyurtmalargacha — atigi bitta qisqa o'qish. Qotib qoldingizmi? @PyAleX'ga yozing, bir necha daqiqada o'tishga yordam beramiz, yoki kanalga kiring — u yerda hammasi qanday ishlashini ko'rsatamiz.

`[O'qishni o'tish]` · `[Kanal: havola]`

**Картинка (бриф):** a minimalist 3-step path of dots, last dot highlighted teal (one step left), or a clean graduation-cap icon glowing teal. Dark `#0F1115`, flat light-3D, minimalist, **no text**.

---

## Пуш 4 — Триал заканчивается

**Триггер:** `trial_ends_at`. **Отправка 1:** за 2 дня до конца. **Отправка 2:** за 1 день до конца.
(Сервисные — приходят даже при отключённых «напоминаниях».)

### Отправка 1 (за 2 дня)

**RU**
⏳ Осталось 2 дня бесплатного периода

Ваш магазин уже работает — чтобы он не остановился, выберите тариф. Start — 390 000 · Business — 650 000 · Premium — 910 000 сум/мес. Комиссия с продаж по-прежнему 0%.

`[Выбрать тариф]` · Вопросы: @PyAleX

**UZ**
⏳ Bepul davrdan 2 kun qoldi

Do'koningiz allaqachon ishlayapti — to'xtab qolmasligi uchun tarif tanlang. Start — 390 000 · Business — 650 000 · Premium — 910 000 so'm/oy. Savdodan komissiya hamon 0%.

`[Tarif tanlash]` · Savollar: @PyAleX

### Отправка 2 (за 1 день)

**RU**
⚠️ Завтра заканчивается пробный период

Чтобы магазин и база клиентов остались с вами без перерыва — продлите сегодня. Это займёт минуту.

`[Выбрать тариф]` · Вопросы: @PyAleX

**UZ**
⚠️ Ertaga sinov davri tugaydi

Do'kon va mijozlar bazasi sizda uzilishsiz qolishi uchun — bugun uzaytiring. Bu bir daqiqa oladi.

`[Tarif tanlash]` · Savollar: @PyAleX

**Картинка (бриф, по желанию):** a minimalist hourglass or thin countdown ring in teal on dark `#0F1115`. Calm, not alarming, flat light-3D, **no text**.

---

## Что нужно от платформы (для кода)

Чтобы бот знал, кому и когда слать, платформа (через вебхук) и/или БД должны давать на каждого владельца:

- `lang` — `ru` / `uz` (выбранный в боте);
- `started_at` — первый `/start`;
- `store_created_at` — есть/нет магазин;
- `product_count` — число товаров;
- `training_completed` — true/false;
- `trial_ends_at` — дата конца триала;
- `plan_paid` — оплачен ли тариф (если да — пуши 1–4 для него выключены).

Планировщик раз в час: определяет для каждого владельца текущий застрявший шаг (по приоритету выше), проверяет тихие часы и «не отправляли ли уже эту отправку», и шлёт нужный вариант на нужном языке.

---

## На будущее (не сейчас)

- Пуш «магазин работает, но за неделю ноль заказов» — это уже про **живой** магазин, не про активацию. Можно добавить отдельным блоком, когда дойдём до удержания.
- Единый стиль картинок: первую утверждённую использовать как референс к остальным трём (как договаривались по контенту канала).
