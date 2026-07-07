"""通用 CRUD Service 基类

约束：
- 不在 Service 中触发任何外部副作用（不调 Redis 写、不调 EventPublisher、
  不调 HTTP、不直接 commit）；提交由 ``get_session`` 依赖负责
- 不发布变更日志 hook；如需审计请派生新 Service 在 ``create`` / ``update``
  中显式发布事件
- 不绑定车间隔离、不绑定 EAV；这些是业务专属能力，按需派生
"""

import logging
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from app.core.exceptions import NotFoundError
from app.repositories.crud_base import CrudRepo
from app.schemas.query import ConditionGroup, ListQuery

logger = logging.getLogger(__name__)

M = TypeVar("M")


class CrudService(Generic[M]):
    """通用 CRUD Service 基类

    业务方派生时显式绑定仓储类型::

        class UserService(CrudService[User]):
            def __init__(self, repo: CrudRepo[User]) -> None:
                super().__init__(repo)

    基类负责 1:1 转发仓储调用，业务方在派生类中扩展业务规则。
    """

    def __init__(self, repo: CrudRepo[M]) -> None:
        self.repo = repo

    async def get_by_id(self, entity_id: int) -> M | None:
        """按 ID 查询；返回 ORM 实例或 None"""
        return await self.repo.get_by_id(entity_id)

    async def get_or_404(self, entity_id: int) -> M:
        """按 ID 查询；未命中抛 ``NotFoundError``"""
        entity = await self.repo.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError(f"{self.repo.model.__name__} #{entity_id} 不存在")
        return entity

    async def list_paginated(
        self,
        query: ListQuery,
        *,
        extra_conditions: list[Any] | None = None,
    ) -> tuple[Sequence[M], int]:
        """分页查询（透传仓储）"""
        return await self.repo.list_paginated(
            condition_group=query.condition_group,
            sort=query.sort,
            offset=query.offset,
            limit=query.limit,
            extra_conditions=extra_conditions,
        )

    async def count(
        self,
        *,
        condition_group: ConditionGroup | None = None,
        extra_conditions: list[Any] | None = None,
    ) -> int:
        """计数查询（透传仓储）"""
        return await self.repo.count(
            condition_group=condition_group,
            extra_conditions=extra_conditions,
        )

    async def create(self, entity: M) -> M:
        """创建记录（flush，不 commit）"""
        return await self.repo.create(entity)

    async def update(self, entity: M) -> M:
        """更新记录（flush，不 commit）"""
        return await self.repo.update(entity)

    async def delete(self, entity_id: int) -> bool:
        """删除记录"""
        return await self.repo.delete(entity_id)


__all__ = ["CrudService"]