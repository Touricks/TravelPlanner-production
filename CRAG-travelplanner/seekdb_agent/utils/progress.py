"""
Progress Callback Module
========================
SSE 进度推送的 ContextVar 回调机制

使用方式:
1. API 端点设置回调: token = set_progress_callback(callback)
2. 节点/中间件发射进度: emit_progress("stage", "message", percent)
3. API 端点清理回调: reset_progress_callback(token)

更新记录:
- 2026-01-12: 初始实现，支持 SSE 进度推送
"""

import contextvars
import logging
import sys
from collections.abc import Callable
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("progress")

# 进度回调 ContextVar（线程/协程安全）
_progress_callback: contextvars.ContextVar[Callable[[dict[str, Any]], None] | None] = (
    contextvars.ContextVar("progress_callback", default=None)
)

# Module-level fallback（跨 Agent 边界）
_module_progress_callback: Callable[[dict[str, Any]], None] | None = None


def set_progress_callback(
    callback: Callable[[dict[str, Any]], None] | None,
) -> contextvars.Token[Callable[[dict[str, Any]], None] | None]:
    """
    设置进度回调函数

    Args:
        callback: 接收进度事件的回调函数，签名为 (event: dict) -> None

    Returns:
        ContextVar token，用于后续 reset

    Example:
        token = set_progress_callback(lambda e: queue.put_nowait(e))
        try:
            result = workflow.invoke(state)
        finally:
            reset_progress_callback(token)
    """
    global _module_progress_callback
    _module_progress_callback = callback
    return _progress_callback.set(callback)


def reset_progress_callback(
    token: contextvars.Token[Callable[[dict[str, Any]], None] | None],
) -> None:
    """
    重置进度回调（清理 ContextVar）

    Args:
        token: set_progress_callback 返回的 token
    """
    global _module_progress_callback
    _progress_callback.reset(token)
    _module_progress_callback = None


def get_progress_callback() -> Callable[[dict[str, Any]], None] | None:
    """
    获取当前进度回调（优先 ContextVar，回退 module-level）

    Returns:
        回调函数，或 None（未设置）
    """
    global _module_progress_callback
    callback = _progress_callback.get(None)
    if callback is not None:
        return callback
    return _module_progress_callback


def emit_progress(
    stage: str,
    message: str,
    percent: int = 0,
    **extra: Any,
) -> None:
    """
    发射进度事件

    如果已设置回调，则调用回调发送事件；否则仅记录日志。

    Args:
        stage: 当前阶段标识（collector/validator/search/grading/generator）
        message: 用户可读的进度消息
        percent: 进度百分比 (0-100)
        **extra: 额外数据（如 count, quality 等）

    Example:
        emit_progress("search", "Searching attractions database...", 25)
        emit_progress("search", "Found 18 attractions", 70, count=18)
    """
    event = {
        "stage": stage,
        "message": message,
        "percent": percent,
        **extra,
    }

    callback = get_progress_callback()
    if callback:
        try:
            callback(event)
            logger.debug(f"Progress emitted: {stage} ({percent}%)")
        except Exception as e:
            logger.warning(f"Failed to emit progress: {e}")
    else:
        # 无回调时仅记录日志（用于调试）
        logger.info(f"[Progress] {stage}: {message} ({percent}%)")
