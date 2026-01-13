"""
Search POI Tool
===============
包装 db/search.py 的 hybrid_search 为 LangChain @tool

关系说明：
db/search.py     →  hybrid_search() 核心逻辑（Day 3 已完成）
       ↓
tools/search.py  →  @tool search_pois() 包装层（Day 5）
       ↓
LangChain Agent  →  可发现并调用 search_pois
"""

import contextvars
import logging
import sys
from typing import Any

from langchain.tools import tool

from seekdb_agent.db.connection import get_hybrid_store
from seekdb_agent.db.search import hybrid_search
from seekdb_agent.state import POIResult, UserFeatures

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    stream=sys.stderr,
)
search_logger = logging.getLogger("search_pois")

# 上下文变量：暂存最近一次搜索的结构化结果（线程/协程安全）
# 注意：default=None 避免可变默认值问题（ruff B039）
_last_search_results: contextvars.ContextVar[list[dict[str, Any]] | None] = contextvars.ContextVar(
    "last_search_results", default=None
)

# Module-level fallback storage for when contextvar doesn't work across Agent boundaries
# This is a workaround for LangChain Agent's internal execution context isolation
_module_search_results: list[dict[str, Any]] | None = None

# 上下文变量：用户特征（用于动态计算 top_k）
_current_user_features: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "current_user_features", default=None
)
_module_user_features: dict[str, Any] | None = None

# 默认值常量
DEFAULT_TOP_K = 20
MIN_TOP_K = 10
MAX_TOP_K = 50


def get_last_search_results() -> list[dict[str, Any]]:
    """获取最近一次搜索的结构化结果（优先 contextvar，回退 module-level）"""
    global _module_search_results
    result = _last_search_results.get()
    if result is not None:
        return result
    # Fallback to module-level storage
    return _module_search_results if _module_search_results is not None else []


def get_last_search_results_raw() -> list[dict[str, Any]] | None:
    """
    获取最近一次搜索的原始结果（优先 contextvar，回退 module-level）

    Returns:
        - None: 尚未执行搜索
        - []: 搜索已执行但无结果
        - [...]: 搜索已执行且有结果
    """
    global _module_search_results
    result = _last_search_results.get()
    if result is not None:
        return result
    return _module_search_results


def search_was_executed() -> bool:
    """检查本轮是否已执行搜索（用于 Fallback 触发判断）"""
    global _module_search_results
    return _last_search_results.get() is not None or _module_search_results is not None


def clear_last_search_results() -> None:
    """清空暂存结果（用于测试隔离）"""
    global _module_search_results
    _last_search_results.set(None)
    _module_search_results = None


def set_user_features_for_search(user_features: dict[str, Any] | None) -> None:
    """
    设置当前用户特征（供 search_pois 动态计算 top_k）

    Args:
        user_features: 用户特征字典，包含 travel_days, pois_per_day 等
    """
    global _module_user_features
    _current_user_features.set(user_features)
    _module_user_features = user_features
    if user_features:
        search_logger.info(
            f"Set user_features: travel_days={user_features.get('travel_days')}, "
            f"pois_per_day={user_features.get('pois_per_day')}"
        )


def get_user_features_for_search() -> dict[str, Any] | None:
    """获取当前用户特征（优先 contextvar，回退 module-level）"""
    global _module_user_features
    result = _current_user_features.get()
    if result is not None:
        return result
    return _module_user_features


def calculate_dynamic_top_k(user_features: dict[str, Any] | None) -> int:
    """
    根据用户特征动态计算 top_k

    计算逻辑：
    - 基础需求: travel_days × pois_per_day
    - 冗余系数: 1.5 (提供备选)
    - 限制范围: [MIN_TOP_K, MAX_TOP_K]

    Args:
        user_features: 用户特征字典

    Returns:
        计算后的 top_k 值
    """
    if not user_features:
        return DEFAULT_TOP_K

    travel_days = user_features.get("travel_days") or 3
    pois_per_day = user_features.get("pois_per_day") or 4

    # 基础需求 + 50% 冗余（提供备选）
    base_need = travel_days * pois_per_day
    calculated = int(base_need * 1.5)

    # 限制在合理范围内
    result = max(MIN_TOP_K, min(calculated, MAX_TOP_K))

    search_logger.info(
        f"Dynamic top_k: {travel_days} days × {pois_per_day} POIs/day × 1.5 = {calculated} → clamped to {result}"
    )

    return result


def clear_user_features_for_search() -> None:
    """清空用户特征（用于测试隔离）"""
    global _module_user_features
    _current_user_features.set(None)
    _module_user_features = None


@tool
def search_pois(query: str, search_mode: str = "balanced") -> str:
    """搜索 POI 数据库（Hybrid Search: Vector + Sparse + Fulltext）

    使用 OceanBase Hybrid Search 搜索旅游景点、餐厅、酒店等 POI。
    支持语义搜索、关键词搜索和精确匹配的混合模式。

    Args:
        query: 搜索查询文本（如 "beach vacation Tampa", "历史文化景点"）
        search_mode: 搜索模式，可选值：
            - balanced: 通用查询 (40% vector, 30% sparse, 30% fulltext)
            - semantic: 概念搜索，适合模糊描述 (70% vector)
            - keyword: 关键词搜索，适合特定词汇 (60% sparse)
            - exact: 精确匹配，适合名称搜索 (70% fulltext)

    Returns:
        格式化的 POI 列表（供 LLM 阅读）

    Examples:
        >>> search_pois("beach vacation Tampa")
        "Found 20 POIs:\\n1. Clearwater Beach..."

        >>> search_pois("杭州西湖", search_mode="exact")
        "Found 5 POIs:\\n1. West Lake..."
    """
    # 获取 Hybrid Store
    store = get_hybrid_store()

    # 动态计算 top_k（基于用户特征）
    user_features_dict = get_user_features_for_search()
    top_k = calculate_dynamic_top_k(user_features_dict)

    # 转换为 UserFeatures 对象（用于目的地过滤）
    user_features: UserFeatures | None = None
    if user_features_dict:
        try:
            user_features = UserFeatures(**user_features_dict)
        except Exception as e:
            search_logger.warning(f"Failed to create UserFeatures: {e}")

    # 执行 Hybrid Search（禁用 rerank 以减少延迟，OceanBase AI_RERANK 模型未配置）
    results = hybrid_search(
        store=store,
        query=query,
        user_features=user_features,  # 传递用户特征（用于目的地过滤）
        search_mode=search_mode,  # type: ignore[arg-type]
        top_k=top_k,
        use_rerank=False,  # 暂时禁用 rerank
    )

    # DEBUG: 日志输出搜索结果
    search_logger.info(f"query='{query}', mode='{search_mode}', results_count={len(results)}")
    if results:
        search_logger.info(f"first result: {results[0].name} ({results[0].city})")

    # 暂存结构化结果（供 GradingMiddleware 读取写入 state）
    # 同时写入 contextvar 和 module-level 变量，确保跨 Agent 边界可访问
    global _module_search_results
    results_dict = [poi.model_dump() for poi in results]
    _last_search_results.set(results_dict)
    _module_search_results = results_dict
    search_logger.info(f"Stored {len(results_dict)} results in both contextvar and module-level")

    # 格式化结果供 LLM 阅读
    return _format_results_for_llm(results)


def _format_results_for_llm(results: list[POIResult]) -> str:
    """
    格式化搜索结果供 LLM 阅读

    Args:
        results: POI 搜索结果列表

    Returns:
        格式化的文本，易于 LLM 理解和引用
    """
    if not results:
        return "No POIs found matching the query."

    lines = [f"Found {len(results)} POIs:\n"]

    for i, poi in enumerate(results, 1):
        # 基本信息
        lines.append(f"{i}. {poi.name}")

        # 位置
        if poi.city or poi.state:
            location = ", ".join(filter(None, [poi.city, poi.state]))
            lines.append(f"   Location: {location}")

        # 评分
        if poi.rating is not None:
            reviews = f" ({poi.reviews_count} reviews)" if poi.reviews_count else ""
            lines.append(f"   Rating: {poi.rating}{reviews}")

        # 分类
        if poi.primary_category:
            lines.append(f"   Category: {poi.primary_category}")

        # 价格
        if poi.price_level is not None:
            price_map = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
            price_str = price_map.get(poi.price_level, str(poi.price_level))
            lines.append(f"   Price: {price_str}")

        # 描述
        if poi.editorial_summary:
            summary = poi.editorial_summary[:150]
            if len(poi.editorial_summary) > 150:
                summary += "..."
            lines.append(f"   Description: {summary}")

        lines.append("")  # 空行分隔

    return "\n".join(lines)
