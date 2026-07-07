"""业务异常体系 — 4 类基础 + 透传 opdm_lib.auth 的 AuthError

约束：
- 不引入任何业务专属异常（车间隔离 / EAV / SN / 导入 / Excel 等）
- 业务方如需更细分异常，请在本文件扩展并继承 ``BusinessError``
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from opdm_lib.auth import (
    AuthError,
    BusinessError,
    auth_error_handler,
    business_error_handler,
)


class NotFoundError(BusinessError):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(code=404, message=message)


class ConflictError(BusinessError):
    """业务冲突（唯一约束违反、并发冲突等）"""

    def __init__(self, message: str = "操作冲突") -> None:
        super().__init__(code=409, message=message)


class BadRequestError(BusinessError):
    """请求参数非法"""

    def __init__(self, message: str = "请求参数错误") -> None:
        super().__init__(code=400, message=message)


class ExternalServiceError(BusinessError):
    """外部服务调用失败"""

    def __init__(self, message: str = "外部服务调用失败", code: int = 503) -> None:
        super().__init__(code=code, message=message)


async def _business_error_response(request: Request, exc: BusinessError) -> JSONResponse:
    """将 BusinessError 转为统一 ApiResponse 结构

    覆盖 opdm_lib.auth 默认 handler 的输出形态，使全栈响应一致。
    """
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


async def _auth_error_response(request: Request, exc: AuthError) -> JSONResponse:
    """AuthError → 统一 ApiResponse 结构（401）"""
    return JSONResponse(
        status_code=401,
        content={"code": 401, "message": exc.message, "data": None},
    )


__all__ = [
    "AuthError",
    "BusinessError",
    "NotFoundError",
    "ConflictError",
    "BadRequestError",
    "ExternalServiceError",
    "_business_error_response",
    "_auth_error_response",
    # 兼容旧导出（仅在 type-check 时可能被引用；运行时被覆盖为统一结构）
    "business_error_handler",
    "auth_error_handler",
]