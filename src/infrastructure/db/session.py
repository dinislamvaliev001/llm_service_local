# src/infrastructure/db/session.py
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel
from collections.abc import AsyncGenerator
from src.config.settings import settings

engine = create_async_engine(
    settings.async_db_url,
    echo=(settings.app_env == "development"),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        # Включаем расширение pgvector
        # await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(SQLModel.metadata.create_all)