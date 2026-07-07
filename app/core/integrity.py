"""SQLAlchemy IntegrityError 友好解析

基于 ``{table_name: {constraint_key: 友好消息}}`` 配置字典，将数据库驱动的
原始约束错误翻译为业务可读消息；未命中走 409 + 默认消息。

约束键支持两种写法：
- 单列：``"code"``
- 多列：``"workshop_code,name"``（与 SQLAlchemy 约束声明顺序一致）

业务方按需扩展 ``register_constraint_message``，示例::

    from app.core.integrity import register_constraint_message

    register_constraint_message("tb_user", "username", "用户名已存在")
    register_constraint_message("tb_user", "email", "邮箱已被注册")
"""

import logging
import re

from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

# 默认约束消息（按计划 G6 保留为空字典，业务方按需注入）
_DEFAULT_TABLE_CONSTRAINT_MESSAGES: dict[str, dict[str, str]] = {}

# SQLite / SQL Server 通用 UNIQUE 约束错误正则（覆盖列单字段与多字段）
_UNIQUE_CONSTRAINT_RE = re.compile(
    r"UNIQUE constraint failed: (\w+)\.(\w+)(?:,\s*\1\.(\w+))*"
)

# SQL Server 风格的 UNIQUE KEY 约束（错误信息包含约束名）
_MSSQL_UNIQUE_RE = re.compile(
    r"Violation of UNIQUE KEY constraint '([^']+)'"
)


def register_constraint_message(table_name: str, column_key: str, message: str) -> None:
    """注册表-列（组合）到友好消息的映射"""
    _DEFAULT_TABLE_CONSTRAINT_MESSAGES.setdefault(table_name, {})[column_key] = message


def _parse_integrity_error(error: IntegrityError) -> tuple[int, str]:
    """解析 IntegrityError → (http_status, friendly_message)

    未命中任何映射时返回 ``(409, "数据冲突")``。
    """
    raw = str(error.orig) if error.orig else str(error)

    match = _UNIQUE_CONSTRAINT_RE.search(raw)
    if match:
        table_name = match.group(1)
        columns: list[str] = [match.group(2)]
        if match.group(3):
            columns.append(match.group(3))
        column_key = ",".join(columns)
        constraint_map = _DEFAULT_TABLE_CONSTRAINT_MESSAGES.get(table_name, {})
        friendly_msg = constraint_map.get(column_key) or constraint_map.get(columns[0])
        if friendly_msg is not None:
            duplicate_value = match.group(0).split(": ", 1)[1] if ": " in match.group(0) else column_key
            return 409, f"{friendly_msg}: {duplicate_value}"
        logger.warning("未配置的表约束: table=%s columns=%s", table_name, column_key)
        return 409, f"数据冲突: {table_name}.{column_key}"

    mssql_match = _MSSQL_UNIQUE_RE.search(raw)
    if mssql_match:
        constraint_name = mssql_match.group(1)
        logger.warning("未解析的 MSSQL 唯一约束: %s", constraint_name)
        return 409, "数据冲突，违反唯一约束"

    logger.warning("无法解析 IntegrityError: %s", raw)
    return 409, "数据冲突"


__all__ = [
    "register_constraint_message",
    "_parse_integrity_error",
]