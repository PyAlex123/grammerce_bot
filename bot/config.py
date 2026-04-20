from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    DATABASE_URL: str
    SUPPORT_CHAT_ID: int

    PLATFORM_URL: str
    PLATFORM_BOT_SHARED_SECRET: str

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
            "cosmetics": self.DEMO_BOT_COSMETICS,
            "electronics": self.DEMO_BOT_ELECTRONICS,
        }


settings = Settings()
