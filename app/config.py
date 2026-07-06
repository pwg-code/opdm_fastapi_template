from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置 — 通过环境变量或 .env 文件加载"""

    # ── 服务信息 ──
    SERVICE_NAME: str = "my-service"
    SERVICE_PORT: int = 8000
    DEBUG: bool = False
    APP_ENV: str = "development"

    # ── 数据库 ──
    DB_CONNECTION_STRING: str = "sqlite+aiosqlite:///./data/app.db"

# ── 认证服务 ──
    AUTH_SERVICE_URL: str = "http://localhost:8001"

    # ── 服务间认�?──
    SERVICE_TOKEN: str = ""

    # ── JWT ──
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/1"

    # ── 日志 ──
    LOG_LEVEL: str = "INFO"

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
