"""数据库连接与会话管理 — 单库（主库）"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_engine_from_config
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

if settings.is_sqlite:
    engine = async_engine_from_config(
        {
            "sqlalchemy.url": settings.DB_CONNECTION_STRING,
            "sqlalchemy.echo": settings.DEBUG,
        },
        connect_args={"check_same_thread": False},
    )
else:
    engine = async_engine_from_config(
        {
            "sqlalchemy.url": settings.DB_CONNECTION_STRING,
            "sqlalchemy.echo": settings.DEBUG,
            "sqlalchemy.pool_size": 10,
            "sqlalchemy.max_overflow": 20,
            "sqlalchemy.pool_recycle": 3600,
            "sqlalchemy.pool_pre_ping": True,
        },
    )

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """FastAPI 依赖注入 — 提供数据库会话（自动 commit / rollback）"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """开发环境自动建表（生产环境请使用 ``alembic upgrade head``）"""
    from sqlmodel import SQLModel

    async with engine.begin() as conn:
        if settings.is_sqlite:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=5000"))
            await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(SQLModel.metadata.create_all)


async def dispose_engine() -> None:
    """应用关闭时释放连接池"""
    await engine.dispose()


__all__ = [
    "engine",
    "async_session_factory",
    "get_session",
    "init_db",
    "dispose_engine",
]