from fastapi import Request
from fastapi.responses import JSONResponse
from opdm_lib.auth import (
    AuthError,
    BusinessError,
    business_error_handler,
    auth_error_handler,
)


class NotFoundError(BusinessError):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)


class ConflictError(BusinessError):
    """业务冲突"""

    def __init__(self, message: str = "操作冲突"):
        super().__init__(code=409, message=message)


class BadRequestError(BusinessError):
    """请求参数非法"""

    def __init__(self, message: str = "请求参数错误"):
        super().__init__(code=400, message=message)


class ExternalServiceError(BusinessError):
    """外部服务调用失败"""

    def __init__(self, message: str = "外部服务调用失败", code: int = 503):
        super().__init__(code=code, message=message)


__all__ = [
    "AuthError",
    "BusinessError",
    "business_error_handler",
    "auth_error_handler",
    "NotFoundError",
    "ConflictError",
    "BadRequestError",
    "ExternalServiceError",
]
