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
    # admin notification — new platform registration
    "admin_new_registration": (
        "🎉 Platformada yangi ro'yxatdan o'tish!\n\n"
        "Ism: {name}\n"
        "Manba: {utm}\n"
        "Vaqt: {time}"
    ),
    "admin_utm_unknown": "ko'rsatilmagan",
    # lifecycle notifications to the user (§6.5)
    "notify_store_created": (
        "🎉 Do'kon yaratildi! Endi tovar qo'shish qoldi. "
        "Kabinetni oching va birinchi tovarlarni yuklang — bir necha daqiqa."
    ),
    "btn_open_cabinet": "🏪 Kabinetni ochish",
    "btn_menu_button": "Grammerce",
    "notify_new_order": (
        "🛒 Yangi buyurtma №{order_number}! "
        "Xaridor: {customer_name}, {phone}. Summa: {amount}. "
        "Tasdiqlash uchun oching."
    ),
    "btn_open_order": "📦 Buyurtmani ochish",
    "notify_low_products": (
        "Do'koningizda {product_count} ta tovar bor. Ko'proq qo'shing — "
        "xaridorlarga tanlash osonroq bo'ladi. Yordam kerak bo'lsa — operatorga yozing."
    ),
    "btn_add_products": "➕ Tovar qo'shish",
    # activation pushes (funnel reminders) — see mdS/grammerce_push_notifications.md
    # Push 1 — entered, no store
    "push1_s1": (
        "🛍 Telegram'dagi do'koningiz — bir necha bosishda\n\n"
        "Siz kirdingiz, lekin hali do'kon yaratmadingiz. Vitrina, savat va "
        "to'lovni biz yig'amiz — faqat boshlash kerak."
    ),
    "push1_s2": (
        "💡 Qanday ishlashini tushunmadingizmi?\n\n"
        "Do'kon yaratish — haqiqatan bir necha daqiqa, saytsiz va kodsiz. Avval "
        "boshqalar Telegram'da qanday sotishini ko'rmoqchi bo'lsangiz — "
        "kanalimizga kiring, u yerda tahlil va misollar bor."
    ),
    # Push 2 — store created, no product
    "push2_s1": (
        "📦 Do'kon tayyor, lekin javonlar bo'sh\n\n"
        "Birinchi mahsulotni qo'shing — rasm, nomi, narxi. U paydo bo'lishi "
        "bilan vitrinani mijozlarga ko'rsatish mumkin."
    ),
    "push2_s2": (
        "🛒 Bitta mahsulot — va do'kon jonlanadi\n\n"
        "Hammasini birato'la yuklash shart emas: bittadan boshlang, qolganini "
        "keyin qo'shasiz. Rasm va tavsif bilan yordam kerakmi? Kanalda mahsulot "
        "kartasini sotiladigan qilib bezash bo'yicha qisqa tahlil bor."
    ),
    # Push 3 — product uploaded, training not done
    "push3_s1": (
        "🎓 Bitta qadam qoldi\n\n"
        "Mahsulotlar joyida — endi qisqa o'qish, va buyurtmalarni o'zingiz qabul "
        "qilib yurita olasiz. Tez va aniq."
    ),
    "push3_s2": (
        "✅ Bugun ishga tushing\n\n"
        "Birinchi buyurtmalargacha — atigi bitta qisqa o'qish. Qotib qoldingizmi? "
        "@PyAleX'ga yozing, bir necha daqiqada o'tishga yordam beramiz, yoki "
        "kanalga kiring — u yerda hammasi qanday ishlashini ko'rsatamiz."
    ),
    # Push 4 — trial ending (service)
    "push4_s1": (
        "⏳ Bepul davrdan 2 kun qoldi\n\n"
        "Do'koningiz allaqachon ishlayapti — to'xtab qolmasligi uchun tarif "
        "tanlang. Start — 390 000 · Business — 650 000 · Premium — 910 000 "
        "so'm/oy. Savdodan komissiya hamon 0%.\n\n"
        "Savollar: @PyAleX"
    ),
    "push4_s2": (
        "⚠️ Ertaga sinov davri tugaydi\n\n"
        "Do'kon va mijozlar bazasi sizda uzilishsiz qolishi uchun — bugun "
        "uzaytiring. Bu bir daqiqa oladi.\n\n"
        "Savollar: @PyAleX"
    ),
    # push CTA buttons
    "push_btn_create": "🏪 Do'kon yaratish",
    "push_btn_add_product": "📦 Mahsulot qo'shish",
    "push_btn_training": "🎓 O'qishni o'tish",
    "push_btn_tariff": "💳 Tarif tanlash",
    "push_btn_channel": "📣 Kanal",
}
