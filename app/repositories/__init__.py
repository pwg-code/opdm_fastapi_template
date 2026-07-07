"""Repository 层入口 — 仅导出通用基类"""

from app.repositories.crud_base import CrudRepo

__all__ = ["CrudRepo"]