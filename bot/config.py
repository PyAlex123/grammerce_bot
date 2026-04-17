from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    DATABASE_URL: str
    SUPPORT_CHAT_ID: int

    DEMO_URL_COFFEE: str = "https://demo.grammerce.io/coffee"
    DEMO_URL_CLOTHES: str = "https://demo.grammerce.io/clothes"
    DEMO_URL_FLOWERS: str = "https://demo.grammerce.io/flowers"
    DEMO_URL_FOOD: str = "https://demo.grammerce.io/food"
    DEMO_URL_COSMETICS: str = "https://demo.grammerce.io/cosmetics"
    DEMO_URL_ELECTRONICS: str = "https://demo.grammerce.io/electronics"

    @property
    def demo_urls(self) -> dict[str, str]:
        return {
            "coffee": self.DEMO_URL_COFFEE,
            "clothes": self.DEMO_URL_CLOTHES,
            "flowers": self.DEMO_URL_FLOWERS,
            "food": self.DEMO_URL_FOOD,
            "cosmetics": self.DEMO_URL_COSMETICS,
            "electronics": self.DEMO_URL_ELECTRONICS,
        }


settings = Settings()
