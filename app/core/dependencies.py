"""通用依赖注入入口 — 仅透传 opdm_lib.auth

业务方按需扩展：在本文件追加 ``get_xxx_service`` 工厂。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis_client
from app.database.session import get_session

# ── 透传 opdm_lib.auth ────────────────────────────────────────
from opdm_lib.auth import (
    RequireAllPermissions,
    RequireAnyPermission,
    RequirePermission,
    RequireRole,
    TokenPayload,
    get_current_user,
    require_permission,
)

# ── 通用基础设施依赖 ─────────────────────────────────────────
__all__ = [
    # 认证 / 权限（透传 opdm_lib.auth）
    "get_current_user",
    "TokenPayload",
    "RequirePermission",
    "RequireAnyPermission",
    "RequireAllPermissions",
    "RequireRole",
    "require_permission",
    # 数据库
    "get_session",
    "AsyncSession",
    # Redis（业务级单例，未配置时返回 None）
    "get_redis_client",
]