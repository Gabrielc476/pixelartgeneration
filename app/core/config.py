"""
Configurações do Sora Pixel Art Generator
=========================================
"""

from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # OpenAI
    OPENAI_API_KEY: str = Field(..., description="Chave da API OpenAI")

    # Database (PostgreSQL)
    DATABASE_URL: str = Field(default="postgresql://sora_user:sora_password@localhost:5432/sora_pixel_art")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Security
    SECRET_KEY: str = Field(..., description="Chave secreta para JWT")

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])

    # Development
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")

    # Storage
    STORAGE_LOCAL_PATH: str = Field(default="./storage")
    UPLOAD_MAX_SIZE: int = Field(default=10485760)  # 10MB

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_PERIOD: int = Field(default=3600)

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()