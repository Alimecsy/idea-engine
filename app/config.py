from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str
    telegram_allowed_user_id: int
    telegram_webhook_secret: str
    groq_api_key: str
    notion_api_key: str
    notion_data_source_id: str

    whisper_model: str = "whisper-large-v3-turbo"
    metadata_model: str = "openai/gpt-oss-20b"
    notion_version: str = "2026-03-11"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
