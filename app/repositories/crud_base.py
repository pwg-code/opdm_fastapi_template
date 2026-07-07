"""通用 CRUD Repository 基类

约束：
- 仓储类显式依赖 ``AsyncSession``，由调用方通过 FastAPI Depends 注入
- 不在仓储中触发任何事件、不调任何外部服务
- 不绑定变更日志 hook（业务派生 Service 可自行实现）
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.schemas.query import ConditionGroup, FieldCondition, FilterOperation, SortSpec

T = TypeVar("T")


class CrudRepo(Generic[T]):
    """通用 CRUD Repository 基类

    业务方派生时指定 ``model``：``class UserRepo(CrudRepo[User]): ...``
    """

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    # ── 单条查询 ──────────────────────────────────────────────

    async def get_by_id(self, entity_id: int) -> T | None:
        """按 ID 查询单条记录"""
        stmt = select(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_field(self, field_name: str, value: Any) -> T | None:
        """按单字段精确匹配查询"""
        column = getattr(self.model, field_name, None)
        if column is None:
            raise BadRequestError(f"未知字段: {field_name}")
        stmt = select(self.model).where(column == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_composite_field(
        self, fields: tuple[str, ...], values: dict[str, Any],
    ) -> T | None:
        """按多字段精确匹配查询（复合唯一约束场景）"""
        stmt = select(self.model)
        for field_name in fields:
            column = getattr(self.model, field_name, None)
            if column is None:
                raise BadRequestError(f"未知字段: {field_name}")
            stmt = stmt.where(column == values[field_name])
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── 条件 / 排序构建 ──────────────────────────────────────

    def _build_field_condition(self, fc: FieldCondition) -> Any:
        """将单个字段条件翻译为 SQLAlchemy 表达式"""
        column = getattr(self.model, fc.field, None)
        if column is None:
            raise BadRequestError(f"未知字段: {fc.field}")
        match fc.op:
            case FilterOperation.EQ:
                return column == fc.value
            case FilterOperation.NE:
                return column != fc.value
            case FilterOperation.LIKE:
                return column.ilike(f"%{fc.value}%")  # type: ignore[union-attr]
            case FilterOperation.IN:
                value = fc.value if isinstance(fc.value, list) else [fc.value]
                return column.in_(value)  # type: ignore[union-attr]
            case FilterOperation.GT:
                return column > fc.value
            case FilterOperation.LT:
                return column < fc.value
            case FilterOperation.GTE:
                return column >= fc.value
            case FilterOperation.LTE:
                return column <= fc.value

    def _build_condition_expression(self, cg: ConditionGroup) -> Any | None:
        """将条件组递归翻译为 SQLAlchemy 表达式"""
        if not cg.conditions:
            return None
        exprs: list[Any] = []
        for cond in cg.conditions:
            if isinstance(cond, FieldCondition):
                exprs.append(self._build_field_condition(cond))
            else:
                sub = self._build_condition_expression(cond)
                if sub is not None:
                    exprs.append(sub)
        if not exprs:
            return None
        if cg.logic == "and":
            return and_(*exprs)
        if cg.logic == "or":
            return or_(*exprs)
        if cg.logic == "not":
            return not_(and_(*exprs))
        return None

    def _apply_sort(self, stmt: Any, sort: SortSpec) -> Any:
        """将排序应用到 SQL 语句"""
        column = getattr(self.model, sort.field, None)
        if column is None:
            raise BadRequestError(f"未知排序字段: {sort.field}")
        if sort.order == "desc":
            return stmt.order_by(column.desc())  # type: ignore[union-attr]
        return stmt.order_by(column.asc())  # type: ignore[union-attr]

    # ── 列表 / 计数 ──────────────────────────────────────────

    async def list_paginated(
        self,
        *,
        condition_group: ConditionGroup | None = None,
        sort: SortSpec | None = None,
        offset: int = 0,
        limit: int = 20,
        extra_conditions: list[Any] | None = None,
    ) -> tuple[Sequence[T], int]:
        """分页查询（条件 / 排序 / 扩展条件 / 计数同事务）"""
        stmt: Any = select(self.model)

        if extra_conditions:
            for cond in extra_conditions:
                stmt = stmt.where(cond)

        if condition_group is not None:
            expr = self._build_condition_expression(condition_group)
            if expr is not None:
                stmt = stmt.where(expr)

        if sort is not None:
            stmt = self._apply_sort(stmt, sort)
        else:
            id_col = getattr(self.model, "id", None)
            if id_col is not None:
                stmt = stmt.order_by(id_col.desc())  # type: ignore[union-attr]

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        data_stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(data_stmt)
        rows = result.scalars().all()
        return rows, total

    async def count(
        self,
        *,
        condition_group: ConditionGroup | None = None,
        extra_conditions: list[Any] | None = None,
    ) -> int:
        """计数查询"""
        stmt: Any = select(func.count()).select_from(self.model)
        if extra_conditions:
            for cond in extra_conditions:
                stmt = stmt.where(cond)
        if condition_group is not None:
            expr = self._build_condition_expression(condition_group)
            if expr is not None:
                stmt = stmt.where(expr)
        return (await self.session.execute(stmt)).scalar_one()

    # ── 写操作 ───────────────────────────────────────────────

    async def create(self, entity: T) -> T:
        """创建记录（flush 后返回实例，不 commit）"""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: T) -> T:
        """更新记录（flush 后返回实例，不 commit）"""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity_id: int) -> bool:
        """物理删除（按 ID）；返回是否命中"""
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return False
        await self.session.delete(entity)
        await self.session.flush()
        return True


__all__ = ["CrudRepo"]