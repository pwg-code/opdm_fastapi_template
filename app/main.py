from dotenv import load_dotenv

load_dotenv()

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.session import init_db
from app.core.exceptions import (
    BusinessError,
    AuthError,
    business_error_handler,
    auth_error_handler,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"正在启动 {settings.SERVICE_NAME}...")

    # 初始化数据库（开发环境自动建表，生产使用 Alembic）
    if settings.APP_ENV == "development":
        await init_db()
        logger.info("数据库表已创建 (dev mode)")

    # TODO: 在此添加启动初始化逻辑（如初始化默认数据等）

    yield

    # TODO: 在此添加关闭清理逻辑
    logger.info("服务已关闭")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.SERVICE_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 异常处理器（子类必须在父类之前注册，确保子类优先匹配）
    app.add_exception_handler(BusinessError, business_error_handler)
    app.add_exception_handler(AuthError, auth_error_handler)

    # TODO: 注册路由
    # from app.api.xxx import router as xxx_router
    # app.include_router(xxx_router)

    # 健康检查
    @app.get("/health", tags=["系统"])
    async def health_check():
        return {"status": "ok", "service": settings.SERVICE_NAME}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
