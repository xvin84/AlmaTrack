from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite+aiosqlite:///./almatrack.db"

    # Web dashboard
    dashboard_login: str = "admin"
    dashboard_password: str = "almatrack2025"
    dashboard_secret_key: str = "change-me-in-production"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"

    # Flask
    flask_host: str = "0.0.0.0"
    flask_port: int = 5000

    # Year range
    enrollment_year_min: int = 2015
    enrollment_year_max: int = 2025

    # Pagination
    faculty_items_per_page: int = 5
    year_items_per_page: int = 6

    # ---------------------------------------------------------------------------
    # Premium emoji IDs (leave empty to use regular emoji fallback)
    # ---------------------------------------------------------------------------
    # How to find IDs: forward a custom emoji message to @getidsbot
    # Example: emoji_star = "5368324170671202286"
    emoji_star: str = ""        # ⭐
    emoji_fire: str = ""        # 🔥
    emoji_trophy: str = ""      # 🏆
    emoji_crown: str = ""       # 👑
    emoji_rocket: str = ""      # 🚀
    emoji_chart: str = ""       # 📈
    emoji_lock: str = ""        # 🔒
    emoji_sparkles: str = ""    # ✨
    emoji_medal: str = ""       # 🎖
    emoji_diamond: str = ""     # 💎


@lru_cache
def get_settings() -> Settings:
    return Settings()
