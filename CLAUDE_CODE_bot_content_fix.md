# Fix: Тексты бота — устранение галлюцинаций

## Проблема
Claude Code сгенерировал выдуманные тексты: несуществующий API с фейковым `docs.grammerce.io`, цены в долларах ($29) вместо сумов, 14 дней trial вместо 7, обещание «автоматической авторизации». Нужна замена всех текстов на проверенные + правило, что все строки живут только в `locales/`.

## Решения
- Все тексты бота — только через `locales/ru.py` и `locales/uz.py`, никаких inline-строк в хэндлерах
- Никаких выдуманных URL, цен, фич — только те, что в этом MD
- В FAQ-ответах НЕТ кнопки «Назад» — Reply-клавиатура (Создать магазин / Смотреть демо / Поддержка) постоянно видна снизу, этого достаточно
- CTA «Создать магазин» — без обещаний автоавторизации и магических ссылок

## Тексты RU

**Клик по «🏪 Создать магазин»:**
> Для создания магазина нажмите кнопку ниже. Регистрация займёт 2 минуты.
> Кнопка: `✅ Открыть платформу` → deep link на `admin.grammerce.io/sign-up?utm_*&tg_user_id=...`

**Клик по «💬 Поддержка» — инлайн-кнопки:**
> Чем можем помочь? Выберите вопрос или напишите оператору:
> `💰 Сколько стоит?` · `🛠 Setup Fee` · `⏱ Сроки запуска` · `🔌 Есть ли API?` · `👤 Живой оператор`

**💰 Сколько стоит?**
> Подписка от 390 000 сум/мес. Три тарифа: Start (390 000), Business (650 000), Premium (910 000). Все тарифы — 7 дней бесплатно.
> Подробнее: grammerce.io

**🛠 Setup Fee**
> Разовая оплата за запуск: загрузка товаров, настройка Click/Payme/Uzum, сборка Telegram-бота, обучение персонала.
> Для первых 100 клиентов — 3 900 000 сум (вместо 6 500 000).

**⏱ Сроки запуска**
> Готовый магазин за 1–2 дня после оплаты Setup Fee. Наш менеджер загружает товары и настраивает интеграции — программировать ничего не нужно.

**🔌 Есть ли API?**
> Открытый API в разработке. Сейчас работаем через готовые интеграции: Click, Payme, Uzum, МойСклад, Billz, Jowi, Azma Finance.

## Тексты UZ

**«🏪 Do'kon yaratish» bosilganda:**
> Do'kon yaratish uchun quyidagi tugmani bosing. Ro'yxatdan o'tish 2 daqiqa vaqt oladi.
> Tugma: `✅ Platformani ochish` → deep link

**«💬 Qo'llab-quvvatlash» bosilganda — inline tugmalar:**
> Nima yordam bera olamiz? Savolni tanlang yoki operatorga yozing:
> `💰 Narxi qancha?` · `🛠 Setup Fee` · `⏱ Muddatlari` · `🔌 API bormi?` · `👤 Jonli operator`

**💰 Narxi qancha?**
> Obuna oyiga 390 000 so'mdan. Uchta tarif: Start (390 000), Business (650 000), Premium (910 000). Barcha tariflar — 7 kun bepul.
> Batafsil: grammerce.io

**🛠 Setup Fee**
> Do'konni ishga tushirish uchun bir martalik to'lov: tovarlar yuklash, Click/Payme/Uzum sozlash, Telegram-bot yig'ish, xodimlarni o'qitish.
> Birinchi 100 mijoz uchun — 3 900 000 so'm (6 500 000 o'rniga).

**⏱ Ishga tushirish muddatlari**
> Tayyor do'kon Setup Fee to'langandan keyin 1–2 kun ichida. Menejer tovarlarni yuklaydi va integratsiyalarni sozlaydi — dasturlash shart emas.

**🔌 API bormi?**
> Ochiq API ishlab chiqilmoqda. Hozircha tayyor integratsiyalar orqali ishlaymiz: Click, Payme, Uzum, MoySklad, Billz, Jowi, Azma Finance.

## Ключи в locales (единые для RU и UZ)
`cta_create_shop_prompt`, `cta_open_platform_btn`, `support_intro`, `faq_buttons_row1`, `faq_buttons_row2`, `faq_price`, `faq_setup_fee`, `faq_timeline`, `faq_api`, `faq_live_operator_btn`

## Этапы
0. Найти в коде все inline-русские и узбекские строки в хэндлерах бота (grep по кириллице и по паттернам UZ) → `AUDIT_BOT_TEXTS.md` ⛔ СТОП
1. Обновить `locales/ru.py` и `locales/uz.py` всеми текстами из секций выше по ключам ⛔ СТОП
2. Заменить все inline-строки в хэндлерах бота на вызовы из `locales/` ⛔ СТОП
3. Удалить кнопку «Назад» / «Orqaga» из всех FAQ-ответов — после ответа пользователь видит только нижнюю Reply-клавиатуру ⛔ СТОП
4. Автотесты: каждый FAQ-callback возвращает точный текст из `locales/`, нет кнопки «Назад», в выдаче бота нигде не встречается `$`, `docs.grammerce.io`, `/pricing`, `автоматически авторизованы`, `5 минут`, `14 дней` ⛔ СТОП

## Правила работы по этапам
- Каждый этап: автотест (pytest) → рекомендации по ручному тестированию в чате → ⛔ СТОП → правки по фидбэку → коммит и пуш → следующий этап
- Формат коммита: `fix(bot): описание этапа`
- Ветка: `git checkout -b bot-content-fix`
- После этапа 4 — ручная проверка всех 4 FAQ в реальном боте на RU и UZ
