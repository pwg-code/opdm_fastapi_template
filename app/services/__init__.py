"""Service 层入口 — 仅导出通用基类"""

from app.services.crud_base import CrudService

__all__ = ["CrudService"]