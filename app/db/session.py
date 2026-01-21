from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from collections.abc import AsyncGenerator
from app.core.config import settings


# Async engine and session for FastAPI (runtime)
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for async database sessions (FastAPI routes)."""
    async with AsyncSessionLocal() as session:
        yield session


sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    class_=Session
)


def get_sync_session() -> Session:
    """Get a synchronous database session (for import scripts)."""
    return SessionLocal()