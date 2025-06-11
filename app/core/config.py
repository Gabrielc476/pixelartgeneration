"""
Configurações do Sora Pixel Art Generator - VERSÃO SIMPLIFICADA
==============================================================
"""

import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel


class Settings(BaseModel):
    """Configurações da aplicação"""

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./sora_pixel_art.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "desenvolvimento-apenas-nao-usar-em-producao"

    # CORS - como lista de strings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Development
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Storage
    STORAGE_LOCAL_PATH: str = "./storage"
    UPLOAD_MAX_SIZE: int = 10485760  # 10MB

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600

    def __init__(self, **kwargs):
        # Carregar do .env manualmente para evitar problemas do pydantic-settings
        super().__init__(**self._load_from_env(**kwargs))

    def _load_from_env(self, **kwargs):
        """Carrega configurações do .env manualmente"""

        # Valores padrão
        values = {
            "OPENAI_API_KEY": "",
            "DATABASE_URL": "sqlite:///./sora_pixel_art.db",
            "REDIS_URL": "redis://localhost:6379/0",
            "SECRET_KEY": "desenvolvimento-apenas-nao-usar-em-producao",
            "CORS_ORIGINS": ["http://localhost:3000"],
            "DEBUG": True,
            "LOG_LEVEL": "INFO",
            "STORAGE_LOCAL_PATH": "./storage",
            "UPLOAD_MAX_SIZE": 10485760,
            "RATE_LIMIT_ENABLED": True,
            "RATE_LIMIT_REQUESTS": 100,
            "RATE_LIMIT_PERIOD": 3600
        }

        # Carregar do arquivo .env se existir
        try:
            from pathlib import Path
            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text(encoding='utf-8').splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Processar tipos específicos
                        if key == "CORS_ORIGINS":
                            # Converter string separada por vírgulas em lista
                            if ',' in value:
                                values[key] = [origin.strip() for origin in value.split(',') if origin.strip()]
                            else:
                                values[key] = [value] if value else ["http://localhost:3000"]
                        elif key in ["DEBUG", "RATE_LIMIT_ENABLED"]:
                            values[key] = value.lower() in ('true', '1', 'yes', 'on')
                        elif key in ["UPLOAD_MAX_SIZE", "RATE_LIMIT_REQUESTS", "RATE_LIMIT_PERIOD"]:
                            try:
                                values[key] = int(value)
                            except ValueError:
                                pass  # Manter valor padrão
                        else:
                            values[key] = value
        except Exception as e:
            print(f"Aviso: Erro ao carregar .env: {e}")

        # Sobrescrever com kwargs se fornecidos
        values.update(kwargs)

        return values


@lru_cache()
def get_settings() -> Settings:
    return Settings()