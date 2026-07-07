from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置 — 通过环境变量或 .env 文件加载

    所有字符串字段默认值使用 ``{XXX}`` 占位符，开发者首次 clone 后需按
    README「占位符替换清单」替换为实际值，或在 .env 中显式覆盖。
    """

    # ── 服务信息 ──
    SERVICE_NAME: str = "{SERVICE_NAME}"
    SERVICE_PORT: int = 8000
    SERVICE_WORKERS: int = 2

    # ── 运行环境 ──
    DEBUG: bool = False
    APP_ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    # ── 数据库 ──
    DB_CONNECTION_STRING: str = "sqlite+aiosqlite:///./data/app.db"

    # ── Redis（可选）──
    # 未配置或留空时，业务级 redis 客户端返回 None 并降级为 no-op；
    # 但 opdm_lib.auth 仍会按 REDIS_URL 初始化（无值则跳过）。
    REDIS_URL: str | None = None

    # ── 认证服务 ──
    AUTH_SERVICE_URL: str = "http://{AUTH_SERVICE_HOST}:8001"
    SERVICE_TOKEN: str = "{SERVICE_TOKEN}"
    JWT_SECRET_KEY: str = "{JWT_SECRET_KEY}"
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