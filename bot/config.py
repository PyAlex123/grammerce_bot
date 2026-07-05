from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    DATABASE_URL: str
    SUPPORT_CHAT_ID: int

    PLATFORM_URL: str
    PLATFORM_BOT_SHARED_SECRET: str

    # Telegram Mini App (WebApp) URL of the platform cabinet. When set, the
    # "Создать магазин" CTA and lifecycle buttons become WebApp buttons that
    # auto-login the user via Telegram initData (no password, no consume_url).
    # When empty, the bot falls back to the consume_url one-shot link flow.
    PLATFORM_WEBAPP_URL: str = ""

    # Inbound webhook server (platform → bot lifecycle callbacks).
    # Auth reuses PLATFORM_BOT_SHARED_SECRET via the X-Bot-Secret header.
    BOT_WEBHOOK_HOST: str = "0.0.0.0"
    BOT_WEBHOOK_PORT: int = 8080

    # Public channel link (https://t.me/...). When set, the 2nd activation-push
    # send (pushes 1–3) shows a "Канал / Kanal" button. Empty → no channel button.
    CHANNEL_URL: str = ""

    # CustDev survey WebApp URL (research flow, not shown in main menu)
    SURVEY_WEBAPP_URL: str = "https://grammerce.io/research/survey"

    DEMO_BOT_COFFEE: str = "https://t.me/grammerce_coffee_bot"
    DEMO_BOT_CLOTHES: str = "https://t.me/grammerce_clothes_bot"
    DEMO_BOT_FLOWERS: str = "https://t.me/grammerce_flowers_bot"
    DEMO_BOT_FOOD: str = "https://t.me/grammerce_food_bot"
    DEMO_BOT_COSMETICS: str = "https://t.me/grammerce_cosmetics_bot"
    DEMO_BOT_ELECTRONICS: str = "https://t.me/grammerce_electronics_bot"

    @property
    def demo_urls(self) -> dict[str, str]:
        return {
            # "coffee": self.DEMO_BOT_COFFEE,      # TODO: включить когда будет демо-бот
            "clothes": self.DEMO_BOT_CLOTHES,
            "flowers": self.DEMO_BOT_FLOWERS,
            # "food": self.DEMO_BOT_FOOD,           # TODO: включить когда будет демо-бот
            # "cosmetics": self.DEMO_BOT_COSMETICS,  # TODO: включить когда будет демо-магазин косметики
            "electronics": self.DEMO_BOT_ELECTRONICS,
        }


settings = Settings()
