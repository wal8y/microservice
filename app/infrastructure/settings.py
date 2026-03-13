from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration.

    Values can be overridden via environment variables.
    """

    app_name: str = "Quran Microservice"
    environment: str = Field(default="development", description="Environment name")

    # Quran JSON CDN base
    quran_cdn_base: AnyHttpUrl = Field(
        default="https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/",
        description="Base URL for Quran JSON assets",
    )

    default_language: str = "ar"

    # CORS configuration
    cors_allowed_origins: List[str] = Field(
        default=["*"], description="Allowed origins for CORS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

