texts: dict[str, str] = {
    # language selection
    "choose_language": "Выберите язык / Tilni tanlang:",
    # welcome
    "welcome": (
        "Добро пожаловать в Grammerce! 🛍\n\n"
        "Мы помогаем предпринимателям создавать онлайн-магазины быстро и без навыков разработки."
    ),
    "menu": "Главное меню 👇",
    # personalised first-screen greeting
    "start_welcome": (
        "Привет, {name}! 👋\n"
        "Grammerce — ваш магазин в Telegram за 2 минуты. "
        "Без сайта и разработчиков, 0% комиссии с продаж.\n\n"
        "✓ Готовая витрина и каталог\n"
        "✓ Оплата Click / Payme / Uzum\n"
        "✓ Заказы и клиенты в одном месте\n\n"
        "Демо · Поддержка · grammerce.io"
    ),
    # main menu buttons
    "btn_create_shop": "🏪 Создать магазин",
    "btn_demo": "👀 Демо",
    "btn_support": "💬 Поддержка",
    "btn_lang_toggle": "🇺🇿 O'zbekcha",
    # demo
    "choose_niche": "Выберите нишу — откроем демо-магазин для вас:",
    "niche_coffee": "☕ Кофейня",
    "niche_clothes": "👗 Одежда",
    "niche_flowers": "💐 Цветы",
    "niche_food": "🍔 Доставка еды",
    "niche_cosmetics": "💄 Косметика",
    "niche_electronics": "📱 Электроника",
    "open_demo": "🛍 Открыть демо-магазин",
    "back": "◀️ Назад",
    # create-shop CTA (one button — WebApp when configured, else consume_url link)
    "cta_create_shop_prompt": (
        "Для создания магазина нажмите кнопку ниже. Регистрация займёт 2 минуты."
    ),
    "cta_open_platform_btn": "✅ Открыть платформу",
    "register_error": "⚠️ Не удалось создать ссылку. Попробуйте чуть позже.",
    # support — 3 questions: Цена / Сроки / Оператор
    "support_intro": "Чем помочь? Выберите вопрос или напишите оператору:",
    # FAQ button labels
    "faq_price_btn": "💰 Сколько стоит?",
    "faq_timeline_btn": "⏱ Сроки запуска",
    "faq_live_operator_btn": "👤 Живой оператор",
    # FAQ answers (Setup Fee folded into price; API only via operator)
    "faq_price": (
        "Подписка от 390 000 сум/мес: Start 390 000 · Business 650 000 · Premium 910 000. "
        "Все тарифы — 7 дней бесплатно.\n"
        "Отдельно, разово — подключение: дизайн магазина, загрузка товаров, "
        "настройка оплаты, обучение.\n"
        "Комиссии с продаж — 0%. Подробнее: grammerce.io"
    ),
    "faq_timeline": (
        "Запуск за 1–2 дня: вы оставляете заявку, мы собираем магазин и обучаем "
        "сотрудника. Дальше он работает 24/7."
    ),
    "ask_question": (
        "✍️ Напишите ваш вопрос — оператор ответит в ближайшее время.\n\n"
        "Одно сообщение = один тикет."
    ),
    "ticket_received": "✅ Ваш вопрос принят! Оператор свяжется с вами в ближайшее время.",
    "ticket_header": (
        "📩 Новый тикет от @{username}\n"
        "tg_id: {tg_id}\n"
        "lang: {lang}\n"
        "---\n"
    ),
    "error_generic": "⚠️ Что-то пошло не так. Попробуйте ещё раз.",
    # operator live-chat
    "operator_start_btn": "💬 Начать чат с пользователем",
    "operator_end_btn": "🔴 Завершить чат",
    "operator_chat_started_admin": (
        "Чат с @{username} (tg_id: {tg_id}) активен.\n\n"
        "Его сообщения будут приходить сюда. /endchat — завершить."
    ),
    "operator_chat_started_user": "Оператор подключился! Можете написать ваш вопрос.",
    "operator_chat_ended_admin": "Чат завершён.",
    "operator_chat_ended_user": "Оператор завершил чат. Если остались вопросы — напишите снова.",
    "operator_relay_prefix": "👤 Оператор: ",
    "user_relay_prefix": "👤 @{username}: ",
    "operator_no_active_chat": "Нет активного чата с пользователем.",
    # admin notification — new platform registration
    "admin_new_registration": (
        "🎉 Новая регистрация на платформе!\n\n"
        "Имя: {name}\n"
        "Источник: {utm}\n"
        "Время: {time}"
    ),
    "admin_utm_unknown": "не указан",
}
