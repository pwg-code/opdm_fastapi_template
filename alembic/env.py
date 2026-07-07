"""Alembic 异步迁移环境

模板支持 SQLite（开发）与 SQL Server（生产）异步驱动，通过
``DB_CONNECTION_STRING`` 自动切换。

首次使用：
    1. ``pip install -e ".[prod]"``（含 alembic + aioodbc）
    2. ``alembic revision --autogenerate -m "init"`` 生成首版迁移
    3. ``alembic upgrade head`` 应用迁移

注意：``app.models.__init__`` 中必须显式 import 所有业务模型，
Alembic 才能通过 ``SQLModel.metadata`` 发现它们。
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.models import __init__ as _models  # noqa: F401  — 确保所有 Model 元数据已加载
from sqlmodel import SQLModel

config = context.config
config.set_main_option("sqlalchemy.url", settings.DB_CONNECTION_STRING)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """离线模式：直接输出 SQL，不建立连接"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=url.startswith("sqlite"),
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    """在线模式：同步执行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=url.startswith("sqlite"),
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步执行迁移（适用于 async 驱动）"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()