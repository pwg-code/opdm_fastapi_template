from dotenv import load_dotenv

load_dotenv()

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opdm_lib.auth import close_auth, init_auth
from sqlalchemy.exc import IntegrityError

from app.config import settings

# 配置 root logger，使 LOG_LEVEL 环境变量生效
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

from app.api import router as api_router
from app.core.exceptions import (
    AuthError,
    BadRequestError,
    BusinessError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
)
from app.core.integrity import _parse_integrity_error
from app.core.redis_client import close_redis_client, get_redis_client
from app.database.session import dispose_engine, init_db
from app.schemas.response import ApiResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 — 启动 / 关闭钩子

    启动顺序：
      1. 数据库表（仅 ``APP_ENV=development`` 调 ``init_db``，生产由 alembic 管理）
      2. opdm_lib.auth（JWT + Redis + PermissionReloader，未配置 REDIS_URL 时跳过）
      3. 业务级 Redis 客户端（懒创建）

    关闭顺序：业务 Redis → auth → DB 引擎。
    """
    logger.info("正在启动 %s ...", settings.SERVICE_NAME)

    if settings.APP_ENV == "development":
        await init_db()
        logger.info("数据库表已自动创建 (dev mode)")

    if settings.REDIS_URL:
        try:
            await init_auth(
                secret_key=settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM,
                redis_url=settings.REDIS_URL,
                reloader_base_url=settings.AUTH_SERVICE_URL,
                reloader_service_token=settings.SERVICE_TOKEN,
            )
            logger.info("opdm_lib.auth 已初始化")
        except Exception:
            logger.warning(
                "opdm_lib.auth 初始化失败（get_current_user 将不可用）", exc_info=True,
            )
    else:
        logger.info("REDIS_URL 未配置，跳过 opdm_lib.auth 初始化")

    await get_redis_client()
    yield

    await close_redis_client()
    await close_auth()
    await dispose_engine()
    logger.info("服务已关闭")


def _json_error(status: int, code: int, message: str, data: Any = None) -> JSONResponse:
    """构造统一 ApiResponse 结构的错误响应"""
    return JSONResponse(
        status_code=status,
        content=ApiResponse[Any].fail(code=code, message=message, data=data).model_dump(),
    )


async def _business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
    """业务异常 → ApiResponse.fail"""
    return _json_error(status=exc.code, code=exc.code, message=exc.message)


async def _auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    """认证异常 → 401 ApiResponse.fail"""
    return _json_error(status=401, code=401, message=exc.message)


async def _integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """IntegrityError → 解析后 ApiResponse.fail（默认 409）"""
    logger.exception("IntegrityError: %s", exc)
    status, message = _parse_integrity_error(exc)
    return _json_error(status=status, code=status, message=message)


async def _validation_error_handler(
    request: Request, exc: RequestValidationError,
) -> JSONResponse:
    """Pydantic 校验失败 → 400 ApiResponse.fail（data 携带原始错误详情）"""
    return _json_error(
        status=400,
        code=400,
        message="请求参数校验失败",
        data={"errors": exc.errors()},
    )


async def _fallback_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """未捕获异常 → 500 ApiResponse.fail（统一日志）"""
    logger.exception("未捕获异常: %s", exc)
    return _json_error(status=500, code=500, message="服务器内部错误")


def create_app() -> FastAPI:
    """FastAPI 应用工厂"""
    app = FastAPI(
        title=settings.SERVICE_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS（沿用模板默认；按业务需求收紧）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 异常处理器（顺序无关；FastAPI 按 MRO 匹配）
    app.add_exception_handler(NotFoundError, _business_error_handler)
    app.add_exception_handler(ConflictError, _business_error_handler)
    app.add_exception_handler(BadRequestError, _business_error_handler)
    app.add_exception_handler(ExternalServiceError, _business_error_handler)
    app.add_exception_handler(BusinessError, _business_error_handler)
    app.add_exception_handler(AuthError, _auth_error_handler)
    app.add_exception_handler(IntegrityError, _integrity_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(Exception, _fallback_error_handler)

    # 业务路由（默认空架子；业务方在 app/api 下追加子路由后引入）
    if api_router.routes:
        app.include_router(api_router)

    # 健康检查（不依赖任何业务依赖）
    @app.get("/health", tags=["系统"])
    async def health_check() -> ApiResponse[dict[str, str]]:
        return ApiResponse[dict[str, str]].ok(
            data={"status": "ok", "service": settings.SERVICE_NAME},
        )

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