from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置 — 通过环境变量或 .env 文件加载"""

    # ── 服务信息 ──
    SERVICE_NAME: str = "opdm-fastapi-template"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000

    # ── 运行环境 ──
    DEBUG: bool = False
    APP_ENV: str = "production"

    # ── 日志 ──
    LOGGING_LEVEL: str = "INFO"
    LOGGING_FORMAT: str = "json"
    LOGGING_REQUEST_LOG: bool = True

    # ── 数据库 ──
    DB_CONNECTION_STRING: str = "sqlite+aiosqlite:///./data/app.db"

    # ── Redis（可选）──
    # 未配置或留空时，业务级 redis 客户端返回 None 并降级为 no-op；
    # 但 opdm_lib.auth 仍会按 REDIS_URL 初始化（无值则跳过）。
    REDIS_URL: str | None = None

    # ── 认证服务 ──
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    SERVICE_TOKEN: str = "C6dT2oAt8LPhVZR0uLrw1-n1ICLQ6bPDUgMKzP2ecvU"
    JWT_SECRET_KEY: str = "d4dbb39c-3241-11f0-a6d4-88aeddacf41a"
    JWT_ALGORITHM: str = "HS256"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

    @property
    def is_sqlite(self) -> bool:
        """判断当前是否使用 SQLite"""
        return "sqlite" in self.DB_CONNECTION_STRING


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
