"""统一 API 响应包装 Schema"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应包装

    顶层结构 ``{data, code, message}``，与 HTTP 状态码无关的语义编码；
    业务错误通过 ``code`` 与 ``message`` 表达，HTTP 状态由异常处理器映射。
    """

    data: T = Field(description="业务数据")
    code: int = Field(200, description="业务状态码；200 表示成功，其他为业务异常")
    message: str = Field("success", description="业务消息")

    @classmethod
    def ok(cls, data: T, message: str = "success") -> "ApiResponse[T]":
        """构造成功响应"""
        return cls(data=data, code=200, message=message)

    @classmethod
    def fail(cls, code: int, message: str, data: T | None = None) -> "ApiResponse[T]":
        """构造失败响应（``data`` 默认占位 None）"""
        return cls(data=data, code=code, message=message)  # type: ignore[arg-type]


class ItemList(BaseModel, Generic[T]):
    """通用列表包装（无分页信息，用于下拉选项等小列表端点）"""

    items: list[T] = Field(description="数据列表")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页列表响应包装（带 total）"""

    items: list[T] = Field(description="数据列表")
    total: int = Field(description="总记录数")


__all__ = ["ApiResponse", "ItemList", "PaginatedResponse"]