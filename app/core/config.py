"""Application settings loaded from environment variables / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "European Freight & Logistics Assistant API"
    api_v1_prefix: str = "/api/v1"

    # SQLite by default so the app runs with zero external services.
    # Swap for a PostgreSQL DSN in production: postgresql+psycopg://user:pass@host/db
    database_url: str = "sqlite:///./app.db"

    secret_key: str = "dev-insecure-secret-change-me"
    access_token_expire_minutes: int = 12 * 60
    jwt_algorithm: str = "HS256"

    # Comma separated list of allowed browser origins.
    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
