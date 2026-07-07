"""通用 CRUD Schema 基类

业务方按需派生：
- ``BaseRead``：响应体字段集（必填，缺省值无意义）
- ``BaseCreate``：创建请求体字段集（必填，调用方必须显式传入）
- ``BaseUpdate``：更新请求体字段集（全部可选，调用方只传变化字段）
"""

from pydantic import BaseModel, ConfigDict


class BaseRead(BaseModel):
    """响应体 Schema 基类

    启用 ``from_attributes=True`` 以支持 ``model_validate(orm_entity)``。
    """

    model_config = ConfigDict(from_attributes=True)


class BaseCreate(BaseModel):
    """创建请求体 Schema 基类 — 全部字段必填"""

    model_config = ConfigDict(extra="forbid")


class BaseUpdate(BaseModel):
    """更新请求体 Schema 基类 — 全部字段可选（部分更新语义）"""

    model_config = ConfigDict(extra="forbid")


__all__ = ["BaseRead", "BaseCreate", "BaseUpdate"]