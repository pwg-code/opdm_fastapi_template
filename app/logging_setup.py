"""loguru 统一日志封装（根级横切，对齐 opdm_wdm_testdata_pipeline）

- 导出 ``logger``（loguru 单例）与 ``configure_logger(level, fmt)``
- 格式：``json``（默认，生产推荐）/ ``text``（开发），均输出到 stderr
- 时间戳统一 UTC ISO8601（``Z`` 结尾）；事件风格为小写蛇形英文名 + key=value 扩展字段
- 本模块不落盘（容器 stdout/stderr 由平台采集），不做标准库→loguru 桥接
  （opdm_lib 内部标准库日志各自为政），供任何模块引用。

注意：模块名刻意避开 ``logging``（标准库同名会劫持第三方库内部
``import logging``，脚本模式 ``uv run app/main.py`` 下触发循环导入），
故命名为 ``logging_setup``。
"""

import json
import sys
from datetime import timezone
from typing import TYPE_CHECKING, Any

from loguru import logger as _logger

if TYPE_CHECKING:
    from loguru import Message


def _json_sink(message: "Message") -> None:
    record = message.record
    log_entry: dict[str, Any] = {
        "timestamp": record["time"].astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "level": record["level"].name,
        "event": record["message"],
    }
    extra = record["extra"]
    for key, value in extra.items():
        if key not in log_entry:
            log_entry[key] = value
    sys.stderr.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")


def _text_sink(message: "Message") -> None:
    record = message.record
    extra_str = " ".join(f"{k}={v}" for k, v in record["extra"].items())
    sys.stderr.write(
        f"{record['time'].astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')} "
        f"{record['level'].name} "
        f"{record['message']} "
        f"{extra_str}\n"
    )


def configure_logger(level: str = "INFO", fmt: str = "json") -> None:
    """（重）配置根 logger：先清空既有 sink，再按格式添加单一 sink。"""
    _logger.remove()
    sink = _json_sink if fmt == "json" else _text_sink
    _logger.add(sink, level=level)  # type: ignore[arg-type]


logger = _logger

configure_logger()


__all__ = ["logger", "configure_logger"]
