"""Configuración de la aplicación."""

from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core import get_app_logger

logger = get_app_logger("settings")


class Settings(BaseSettings):
    app_name: str = "app"
    debug: bool = False
    db_url: str = ""
    log_level: str = "INFO"
    log_file: str = "logs/app.json"
    sentry_dsn: str = ""
    environment: str = "development"
    DATABASE_URL: str = ""
    DATABASE_URL_REGISTER: str = ""
    COOKIE_SECRET: str = "change-me-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación."""
    try:
        return Settings()
    except ValidationError as e:
        for error in e.errors():
            # Extrae y formatea el nombre de la variable con error
            field_name = str(error["loc"][0]).upper()
            logger.error(f"Variable de entorno faltante o inválida: {field_name}")
        raise SystemExit(1) from e


settings = get_settings()
