"""业务级 Redis 客户端单例 + 降级

约束：
- 与 ``opdm_lib.auth`` 内部 Redis 完全独立；本客户端供业务代码使用
- 未配置 ``REDIS_URL`` 或初始化失败时返回 ``None``，调用方需做 ``None`` 守卫
"""

import asyncio

import redis.asyncio as redis

from app.config import settings
from app.logging_setup import logger

_client: redis.Redis | None = None
_lock = asyncio.Lock()


async def get_redis_client() -> redis.Redis | None:
    """获取 Redis 客户端单例（异步懒创建）

    Returns:
        客户端实例；未配置 ``REDIS_URL`` 或初始化失败时返回 ``None``。
    """
    global _client
    if _client is not None:
        return _client

    if not settings.REDIS_URL:
        return None

    async with _lock:
        if _client is not None:
            return _client
        try:
            _client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                protocol=2,
            )
            await _client.ping()
            logger.info("Redis 客户端已建立连接")
        except Exception:
            logger.opt(exception=True).warning(
                "Redis 客户端初始化失败，业务调用将降级为 no-op",
            )
            _client = None
    return _client


async def close_redis_client() -> None:
    """关闭 Redis 客户端（应用关闭时调用，幂等）"""
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:
            logger.opt(exception=True).warning("Redis 客户端关闭失败")
        finally:
            _client = None


__all__ = ["get_redis_client", "close_redis_client"]