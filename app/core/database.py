"""
Database connection for Sora Pixel Art Generator - PostgreSQL
============================================================
Configuração otimizada para PostgreSQL com fallback para SQLite
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Determinar tipo de banco baseado na URL
is_postgresql = settings.DATABASE_URL.startswith("postgresql://")
is_sqlite = settings.DATABASE_URL.startswith("sqlite://")

# Configurar engine baseado no tipo de banco
if is_postgresql:
    # PostgreSQL com asyncpg
    async_database_url = settings.DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )

    # Engine para PostgreSQL
    engine = create_async_engine(
        async_database_url,
        echo=settings.POSTGRES_ECHO if hasattr(settings, 'POSTGRES_ECHO') else False,
        future=True,
        pool_size=getattr(settings, 'POSTGRES_POOL_SIZE', 10),
        max_overflow=getattr(settings, 'POSTGRES_MAX_OVERFLOW', 20),
        pool_pre_ping=True,  # Verificar conexões antes de usar
        pool_recycle=3600,   # Reciclar conexões a cada hora
    )

    logger.info("Database configured for PostgreSQL", url=async_database_url.split('@')[1] if '@' in async_database_url else async_database_url)

elif is_sqlite:
    # SQLite com aiosqlite
    async_database_url = settings.DATABASE_URL.replace(
        "sqlite://", "sqlite+aiosqlite://"
    )

    # Engine para SQLite
    engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
        future=True,
        poolclass=NullPool,  # SQLite não precisa de pool
    )

    logger.info("Database configured for SQLite", url=async_database_url)

else:
    raise ValueError(f"Unsupported database URL: {settings.DATABASE_URL}")

# Session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_database():
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create database tables"""
    try:
        logger.info("Creating database tables...")

        async with engine.begin() as conn:
            # Importar todos os models para garantir que estão registrados
            from app.models import (
                User, Job, Generation, Upload, SpriteSheet,
                Frame, Export, Preset, Metadata
            )

            # Criar todas as tabelas
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


async def check_database_connection():
    """Verifica conexão com o banco de dados"""
    try:
        async with engine.begin() as conn:
            if is_postgresql:
                result = await conn.execute(text("SELECT version()"))
                version = result.fetchone()
                logger.info("PostgreSQL connection OK", version=version[0].split()[1] if version else "Unknown")
            elif is_sqlite:
                result = await conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()
                logger.info("SQLite connection OK", version=version[0] if version else "Unknown")

        return True

    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False


async def init_database():
    """Inicializa banco de dados completo"""
    try:
        logger.info("Initializing database...")

        # Verificar conexão
        if not await check_database_connection():
            raise Exception("Database connection failed")

        # Criar tabelas
        await create_tables()

        # Verificar se tabelas foram criadas
        async with engine.begin() as conn:
            if is_postgresql:
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('users', 'jobs', 'generations', 'sprite_sheets', 'frames')
                """))
            else:
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' 
                    AND name IN ('users', 'jobs', 'generations', 'sprite_sheets', 'frames')
                """))

            table_count = result.fetchone()[0]
            logger.info("Database initialized", tables_created=table_count)

        return True

    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise


async def drop_all_tables():
    """Remove todas as tabelas (CUIDADO!)"""
    try:
        logger.warning("Dropping all database tables...")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("All database tables dropped")

    except Exception as e:
        logger.error("Failed to drop tables", error=str(e))
        raise


async def reset_database():
    """Reseta o banco completamente (CUIDADO!)"""
    try:
        logger.warning("Resetting database...")

        await drop_all_tables()
        await create_tables()

        logger.info("Database reset completed")

    except Exception as e:
        logger.error("Database reset failed", error=str(e))
        raise


# Utility functions para facilitar uso
async def execute_raw_sql(sql: str, params: dict = None):
    """Executa SQL raw"""
    try:
        async with engine.begin() as conn:
            if params:
                result = await conn.execute(text(sql), params)
            else:
                result = await conn.execute(text(sql))
            return result
    except Exception as e:
        logger.error("Raw SQL execution failed", sql=sql, error=str(e))
        raise


async def get_database_info():
    """Obtém informações do banco"""
    try:
        info = {
            "type": "postgresql" if is_postgresql else "sqlite",
            "url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL,
            "engine": str(engine.url),
            "pool_size": engine.pool.size() if hasattr(engine, 'pool') and hasattr(engine.pool, 'size') else "N/A",
            "tables": []
        }

        async with engine.begin() as conn:
            if is_postgresql:
                result = await conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' ORDER BY table_name
                """))
            else:
                result = await conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' ORDER BY name
                """))

            info["tables"] = [row[0] for row in result.fetchall()]

        return info

    except Exception as e:
        logger.error("Failed to get database info", error=str(e))
        return {"error": str(e)}