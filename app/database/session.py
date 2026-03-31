from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import settings

if settings.is_sqlite:
    engine = create_async_engine(
        settings.DB_CONNECTION_STRING,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        settings.DB_CONNECTION_STRING,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """FastAPI 依赖注入 — 提供数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """创建所有表（仅开发环境，生产使用 Alembic）"""
    async with engine.begin() as conn:
        if settings.is_sqlite:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=5000"))
            await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(SQLModel.metadata.create_all)
