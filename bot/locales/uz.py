texts: dict[str, str] = {
    # language selection
    "choose_language": "Выберите язык / Tilni tanlang:",
    # welcome
    "welcome": (
        "Grammerce'ga xush kelibsiz! 🛍\n\n"
        "Biz tadbirkorlarga dasturlash bilimlarsiz tez onlayn-do'kon yaratishga yordam beramiz."
    ),
    "menu": "Asosiy menyu 👇",
    # personalised first-screen greeting
    "start_welcome": (
        "Salom, {name}! 👋\n"
        "Grammerce — 2 daqiqada Telegram'dagi do'koningiz. "
        "Saytsiz va dasturchisiz, savdodan 0% komissiya.\n\n"
        "✓ Tayyor vitrina va katalog\n"
        "✓ Click / Payme / Uzum to'lovi\n"
        "✓ Buyurtma va mijozlar bir joyda\n\n"
        "Demo · Yordam · grammerce.io"
    ),
    # main menu buttons
    "btn_create_shop": "🏪 Do'kon yaratish",
    "btn_demo": "👀 Demo",
    "btn_support": "💬 Yordam",
    "btn_lang_toggle": "🇷🇺 Русский",
    # demo
    "choose_niche": "Nishani tanlang — siz uchun demo-do'konni ochamiz:",
    "niche_coffee": "☕ Qahvaxona",
    "niche_clothes": "👗 Kiyim",
    "niche_flowers": "💐 Gullar",
    "niche_food": "🍔 Ovqat yetkazib berish",
    "niche_cosmetics": "💄 Kosmetika",
    "niche_electronics": "📱 Elektronika",
    "open_demo": "🛍 Demo-do'konni ochish",
    "back": "◀️ Orqaga",
    # create-shop CTA (one button — WebApp when configured, else consume_url link)
    "cta_create_shop_prompt": (
        "Do'kon yaratish uchun quyidagi tugmani bosing. Ro'yxatdan o'tish 2 daqiqa vaqt oladi."
    ),
    "cta_open_platform_btn": "✅ Platformani ochish",
    "register_error": "⚠️ Havola yaratib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.",
    # support — 3 savol: Narx / Muddat / Operator
    "support_intro": "Qanday yordam beramiz? Savolni tanlang yoki operatorga yozing:",
    # FAQ button labels
    "faq_price_btn": "💰 Narxi qancha?",
    "faq_timeline_btn": "⏱ Ishga tushirish muddati",
    "faq_live_operator_btn": "👤 Jonli operator",
    # FAQ answers (Setup Fee narx javobiga kiritilgan; API faqat operator orqali)
    "faq_price": (
        "Obuna oyiga 390 000 so'mdan: Start 390 000 · Business 650 000 · Premium 910 000. "
        "Barcha tariflar — 7 kun bepul.\n"
        "Alohida, bir martalik — ulanish: do'kon dizayni, tovarlarni yuklash, "
        "to'lovni sozlash, o'qitish.\n"
        "Savdodan komissiya — 0%. Batafsil: grammerce.io"
    ),
    "faq_timeline": (
        "Ishga tushirish 1–2 kunda: siz ariza qoldirasiz, biz do'konni yig'amiz va "
        "xodimni o'qitamiz. Keyin u 24/7 ishlaydi."
    ),
    "ask_question": (
        "✍️ Savolingizni yozing — operator tez orada javob beradi.\n\n"
        "Bir xabar = bitta tiket."
    ),
    "ticket_received": "✅ Savolingiz qabul qilindi! Operator siz bilan tez orada bog'lanadi.",
    "ticket_header": (
        "📩 Yangi tiket @{username}\n"
        "tg_id: {tg_id}\n"
        "lang: {lang}\n"
        "---\n"
    ),
    "error_generic": "⚠️ Nimadir noto'g'ri ketdi. Iltimos qayta urinib ko'ring.",
    # operator live-chat
    "operator_start_btn": "💬 Foydalanuvchi bilan chatni boshlash",
    "operator_end_btn": "🔴 Chatni tugatish",
    "operator_chat_started_admin": (
        "@{username} (tg_id: {tg_id}) bilan chat faol.\n\n"
        "Uning xabarlari shu yerga keladi. /endchat — tugatish."
    ),
    "operator_chat_started_user": "Operator ulandi! Savolingizni yozishingiz mumkin.",
    "operator_chat_ended_admin": "Chat tugadi.",
    "operator_chat_ended_user": "Operator chatni tugatdi. Savollaringiz bo'lsa — qayta yozing.",
    "operator_relay_prefix": "👤 Operator: ",
    "user_relay_prefix": "👤 @{username}: ",
    "operator_no_active_chat": "Foydalanuvchi bilan faol chat yo'q.",
}
