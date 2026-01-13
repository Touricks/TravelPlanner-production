"""
Validator Node - 特征验证节点
==============================
检查用户特征完整性，采用两级字段分类策略

增强功能：
- 检测 LLM 可能脑补的"可疑默认值"
- 将可疑值视为缺失，要求用户确认

更新记录：
- 2026-01-09: 适配 Pydantic UserFeatures，使用 model_dump() 替代 dict()
"""

import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage

from seekdb_agent.state import CRAGState, UserFeatures
from seekdb_agent.utils.progress import emit_progress

# 配置日志
logger = logging.getLogger(__name__)

# LLM 常见的"脑补"默认值（需要用户确认）
# 注意：travel_days 需要特殊处理，因为用户可能真的说了具体天数
SUSPICIOUS_DEFAULTS: dict[str, list[str | int]] = {
    "budget_meal": ["medium", "moderate", "中等", "中"],
    "transportation": [
        "public transit",
        "public transportation",
        "公共交通",
        "public",
    ],
    "pois_per_day": [3],  # LLM 最常脑补的值
    "price_preference": ["medium", "moderate", "中等"],
}

# travel_days 的可疑值（当用户输入中没有数字时才检测）
SUSPICIOUS_TRAVEL_DAYS: list[int] = [3, 5, 7]


def _get_features_dict(user_features: UserFeatures | dict[str, Any] | None) -> dict[str, Any]:
    """
    将 UserFeatures 转换为字典

    Args:
        user_features: Pydantic UserFeatures 或 dict

    Returns:
        字典格式的特征
    """
    if user_features is None:
        return {}
    if isinstance(user_features, dict):
        return user_features
    # Pydantic BaseModel
    return user_features.model_dump()


def _user_mentioned_days(messages: list[Any]) -> bool:
    """
    检测用户输入中是否明确提到了天数

    匹配模式：
    - "5 days", "5-day", "5天"
    - "five days", "three days" 等英文数字
    - 数字 + day/days/天

    Args:
        messages: 消息列表

    Returns:
        bool: True 表示用户明确提到了天数
    """
    # 匹配模式
    patterns = [
        r"\d+\s*[-]?\s*days?",  # "5 days", "5-day", "5days"
        r"\d+\s*天",  # "5天"
        r"(one|two|three|four|five|six|seven|eight|nine|ten)\s*[-]?\s*days?",  # "five days"
    ]

    for msg in messages:
        # 获取消息内容
        if isinstance(msg, HumanMessage):
            content = str(msg.content).lower()
        elif isinstance(msg, dict):
            content = str(msg.get("content", "")).lower()
        else:
            continue

        # 检查是否匹配任何模式
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

    return False


def _is_field_missing(
    user_features: UserFeatures | dict[str, Any] | None,
    field: str,
    check_suspicious: bool = True,
) -> bool:
    """
    检查字段是否缺失（包括可疑默认值检测）

    Args:
        user_features: 用户特征 (Pydantic 或 dict)
        field: 字段名
        check_suspicious: 是否检测可疑默认值

    Returns:
        bool: True表示字段缺失或可疑，False表示字段有效

    逻辑：
        - 列表字段（interests, must_visit, dietary_options）：
          检查是否为 None 或空列表
        - 整数字段（travel_days, pois_per_day）：检查是否为 None 或 0
        - 字符串字段（其他）：检查是否为 None 或空字符串
        - 可疑默认值检测：如果值在 SUSPICIOUS_DEFAULTS 中，视为缺失
    """
    features_dict = _get_features_dict(user_features)

    value = features_dict.get(field)

    # 列表字段：检查是否为空列表或 None
    if field in ["interests", "must_visit", "dietary_options"]:
        return not value or (isinstance(value, list) and len(value) == 0)

    # 整数字段：检查是否为 None 或 0
    elif field in ["travel_days", "pois_per_day"]:
        if value is None or value == 0:
            return True
        # 检测可疑默认值
        if check_suspicious and field in SUSPICIOUS_DEFAULTS:
            if value in SUSPICIOUS_DEFAULTS[field]:
                logger.warning(
                    "[Validator] 检测到可疑默认值: %s=%s (可能是 LLM 脑补)",
                    field,
                    value,
                )
                return True
        return False

    # 字符串字段：检查是否为 None 或空字符串
    else:
        if not value or value == "":
            return True
        # 检测可疑默认值
        if check_suspicious and field in SUSPICIOUS_DEFAULTS:
            # 转为小写比较
            value_lower = str(value).lower().strip()
            suspicious_values = [str(v).lower() for v in SUSPICIOUS_DEFAULTS[field]]
            if value_lower in suspicious_values:
                logger.warning(
                    "[Validator] 检测到可疑默认值: %s=%s (可能是 LLM 脑补)",
                    field,
                    value,
                )
                return True
        return False


def validator_node(state: CRAGState) -> dict[str, Any]:
    """
    Validator节点：验证用户特征完整性（两级字段分类）

    字段分类策略：
        1. 核心必填字段（6个）：缺失会导致 feature_complete = False
           - destination（目的地）
           - travel_days（旅行天数）
           - interests（兴趣列表）
           - budget_meal（餐饮预算）
           - transportation（交通偏好）
           - pois_per_day（每天游览景点数量）

        2. 可选推荐字段（2个）：缺失会加入 missing_features，但不阻塞流程
           - must_visit（必去景点）
           - dietary_options（饮食偏好）

    输入（从state读取）：
        - user_features: 提取的用户特征

    输出（更新到state）：
        - feature_complete: bool（只看核心必填字段）
        - missing_features: list[str]（包含所有缺失字段：核心+可选）

    工作流逻辑：
        - 如果 feature_complete = True 且 missing_features 为空：
          → 直接进入搜索
        - 如果 feature_complete = True 但 missing_features 有可选字段：
          → 可以选择温和提示一次，或直接搜索
        - 如果 feature_complete = False：
          → 必须进入 AskUser，等待补充核心字段
    """
    # 发射进度
    emit_progress("validator", "Validating travel parameters...", 20)

    user_features = state.get("user_features")
    messages = state.get("messages", [])
    logger.info("[Validator] 开始验证特征完整性")
    logger.info("[Validator] 输入特征: %s", _get_features_dict(user_features))

    # 检测用户是否明确提到了天数
    user_mentioned_days = _user_mentioned_days(messages)
    logger.info("[Validator] 用户是否提到天数: %s", user_mentioned_days)

    # 核心必填字段（6个）- 缺失会阻塞
    core_required_fields = [
        "destination",
        "travel_days",
        "interests",
        "budget_meal",
        "transportation",
        "pois_per_day",
    ]

    # 可选推荐字段（2个）- 缺失不阻塞，但会提示
    optional_recommended_fields = [
        "must_visit",
        "dietary_options",
    ]

    missing = []
    core_missing = []

    # 检查核心必填字段
    for field in core_required_fields:
        if _is_field_missing(user_features, field):
            core_missing.append(field)
            missing.append(field)
        # 特殊处理 travel_days：如果用户没提到天数，检测可疑值
        elif field == "travel_days" and not user_mentioned_days:
            features_dict = _get_features_dict(user_features)
            value = features_dict.get("travel_days")
            if value in SUSPICIOUS_TRAVEL_DAYS:
                logger.warning(
                    "[Validator] 检测到可疑 travel_days=%s (用户未提到天数，可能是 LLM 脑补)",
                    value,
                )
                core_missing.append(field)
                missing.append(field)

    # 检查可选推荐字段
    for field in optional_recommended_fields:
        if _is_field_missing(user_features, field):
            missing.append(field)  # 加入 missing，但不影响 feature_complete

    feature_complete = len(core_missing) == 0

    logger.info("[Validator] 核心字段缺失: %s", core_missing)
    logger.info("[Validator] 所有缺失字段: %s", missing)
    logger.info("[Validator] feature_complete: %s", feature_complete)

    # 返回验证结果
    return {
        "feature_complete": feature_complete,  # 只看核心字段
        "missing_features": missing,  # 包含所有缺失字段（核心+可选）
    }
