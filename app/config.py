from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Internship Aggregator"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./jobs.db"

    admin_secret: str = "change-admin-secret"

    telegram_bot_token: str = ""
    base_url: str = "http://127.0.0.1:8000"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    enable_scheduler: bool = True
    enable_telegram_bot: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
