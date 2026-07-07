"""通用列表查询 Schema"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class FilterOperation(str, Enum):
    """查询运算符枚举"""

    EQ = "eq"
    NE = "ne"
    LIKE = "like"
    IN = "in"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"

    @property
    def description(self) -> str:
        descriptions: dict["FilterOperation", str] = {
            FilterOperation.EQ: "等于",
            FilterOperation.NE: "不等于",
            FilterOperation.LIKE: "模糊匹配",
            FilterOperation.IN: "包含于",
            FilterOperation.GT: "大于",
            FilterOperation.LT: "小于",
            FilterOperation.GTE: "大于等于",
            FilterOperation.LTE: "小于等于",
        }
        return descriptions[self]


class FieldCondition(BaseModel):
    """单个字段上的单个条件"""

    field: str = Field(..., description="字段名")
    op: FilterOperation = Field(..., description="运算符")
    value: str | int | float | bool | list[str | int | float] | None = Field(
        None, description="比较值；in 运算符时为数组"
    )


class ConditionGroup(BaseModel):
    """条件组，支持 AND/OR/NOT 递归嵌套"""

    logic: Literal["and", "or", "not"] = Field("and", description="逻辑运算符")
    conditions: list["FieldCondition | ConditionGroup"] = Field(
        default_factory=list, description="子条件列表"
    )


ConditionGroup.model_rebuild()


class SortSpec(BaseModel):
    """排序规格"""

    field: str = Field(..., description="排序字段名")
    order: Literal["asc", "desc"] = Field(
        "desc", description="排序方向；默认倒序（最新优先）"
    )


class ListQuery(BaseModel):
    """通用列表查询基类

    业务方按需继承并扩展字段；字段名经 ``CrudRepo._build_field_condition``
    反射到 ORM 列，未命中抛出 ``BadRequestError``。
    """

    condition_group: ConditionGroup | None = Field(None, description="查询条件组")
    sort: SortSpec | None = Field(None, description="排序规格")
    offset: int = Field(0, ge=0, description="偏移量")
    limit: int = Field(20, ge=1, le=500, description="每页数量")


__all__ = [
    "FilterOperation",
    "FieldCondition",
    "ConditionGroup",
    "SortSpec",
    "ListQuery",
]