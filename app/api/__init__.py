"""API 路由入口 — 默认空架子

业务方按需新增子模块::

    # app/api/users.py
    from fastapi import APIRouter
    router = APIRouter(prefix="/users", tags=["用户"])

    # app/api/__init__.py 中追加：
    from app.api.users import router as users_router
    api_router.include_router(users_router)
"""

from fastapi import APIRouter

router = APIRouter()

__all__ = ["router"]