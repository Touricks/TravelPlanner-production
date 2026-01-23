"""
Validator Node - 特征验证节点
==============================
检查用户特征完整性，采用两级字段分类策略

增强功能：
- 检测 LLM 可能脑补的"可疑默认值"
- 将可疑值视为缺失，要求用户确认
- LLM 辅助验证：当正则无法识别时，使用 LLM 判断用户是否确认了字段值

更新记录：
- 2026-01-09: 适配 Pydantic UserFeatures，使用 model_dump() 替代 dict()
- 2026-01-22: 添加 LLM 辅助验证，解决简短回复无法识别的问题
"""

import logging
import os
import re
from functools import lru_cache
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from seekdb_agent.llm import create_llm
from seekdb_agent.prompts.validator import FIELD_VALIDATION_PROMPT
from seekdb_agent.state import CRAGState, UserFeatures
from seekdb_agent.utils.progress import emit_progress

# 配置日志
logger = logging.getLogger(__name__)

# ==================== LLM 辅助验证配置 ====================

# 环境变量开关：是否启用 LLM 辅助验证（默认启用）
LLM_VALIDATION_ENABLED = os.getenv("LLM_VALIDATION_ENABLED", "true").lower() == "true"


class FieldMentionValidation(BaseModel):
    """LLM 字段确认验证结果"""

    user_confirmed: bool = Field(description="用户是否确认了该字段值")
    confidence: str = Field(default="high", description="置信度: high/medium/low")
    reasoning: str = Field(default="", description="判断理由")


# 字段描述映射（用于 LLM 理解字段含义）
FIELD_DESCRIPTIONS: dict[str, str] = {
    "pois_per_day": "Number of attractions/POIs to visit per day (integer)",
    "travel_days": "Total trip duration in days (integer)",
    "budget_meal": "Meal budget level or amount (e.g., 'medium', 50)",
    "transportation": "Preferred transportation method (e.g., 'public transit', 'driving')",
    "interests": "List of travel interests (e.g., ['history', 'food'])",
    "destination": "Travel destination city/location",
    "must_visit": "Specific places the user must visit",
    "dietary_options": "Dietary preferences or restrictions",
    "price_preference": "Overall price/budget preference level",
}


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


def _user_mentioned_pois_per_day(messages: list[Any]) -> bool:
    """
    检测用户输入中是否明确提到了每天景点数量

    匹配模式：
    - "3 POIs per day", "3-4 POIs", "3 attractions"
    - "3个景点", "每天3个", "3-4个景点"
    - 数字 + POI/attraction/spot/place/景点
    - 简短回复 "3-4" 或 "3" 作为对 POI 数量问题的回答

    Args:
        messages: 消息列表

    Returns:
        bool: True 表示用户明确提到了每天景点数
    """
    # 明确的 POI 数量模式
    explicit_patterns = [
        r"\d+\s*[-]?\s*\d*\s*pois?\b",  # "3 POIs", "3-4 POIs", "3POIs"
        r"\d+\s*[-]?\s*\d*\s*attractions?\b",  # "3 attractions", "3-4 attractions"
        r"\d+\s*[-]?\s*\d*\s*spots?\b",  # "3 spots"
        r"\d+\s*[-]?\s*\d*\s*places?\b",  # "3 places per day"
        r"\d+\s*[-]?\s*\d*\s*个\s*景点",  # "3个景点", "3-4个景点"
        r"每天\s*\d+",  # "每天3个"
        r"\d+\s*per\s*day",  # "3 per day"
    ]

    # 简短数字回复模式（如 "3-4" 或 "3"）
    short_number_pattern = r"^\s*\d+\s*[-–—]?\s*\d*\s*[;,]?"

    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = str(msg.content).lower()
        elif isinstance(msg, dict):
            content = str(msg.get("content", "")).lower()
        else:
            continue

        # 检查明确模式
        for pattern in explicit_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        # 检查简短数字回复（通常是对 "每天几个景点" 问题的回答）
        # 只有当消息以数字开头时才匹配（避免误匹配）
        if re.match(short_number_pattern, content):
            # 确保这是一个简短回复（不是长句子）
            # 如 "3-4; No must-see" 或 "3-4"
            if len(content) < 30:
                logger.debug("[Validator] 检测到简短数字回复作为 pois_per_day: %s", content)
                return True

    return False


# ==================== LLM 辅助验证函数 ====================


def _format_conversation_context(messages: list[Any], last_n: int = 4) -> str:
    """
    格式化对话上下文用于 LLM 验证

    Args:
        messages: 消息列表
        last_n: 只取最后 N 条消息（默认 4 条）

    Returns:
        格式化的对话字符串
    """
    recent_messages = messages[-last_n:] if len(messages) > last_n else messages
    formatted = []

    for msg in recent_messages:
        # 判断消息类型
        if isinstance(msg, HumanMessage):
            role = "User"
            content = str(msg.content)
        elif isinstance(msg, AIMessage):
            role = "AI"
            content = str(msg.content)
        elif isinstance(msg, dict):
            role = msg.get("role", "unknown").capitalize()
            if role == "Assistant":
                role = "AI"
            content = str(msg.get("content", ""))
        else:
            continue

        # 截断过长的消息
        if len(content) > 500:
            content = content[:500] + "..."

        formatted.append(f"{role}: {content}")

    return "\n".join(formatted)


@lru_cache(maxsize=1)
def _get_validation_llm() -> BaseChatModel:
    """
    获取用于字段验证的 LLM 实例（带缓存）

    使用低 temperature 确保一致性
    """
    return create_llm(temperature=0.0)


def _llm_validate_field_mention(
    messages: list[Any],
    field_name: str,
    field_value: Any,
) -> bool:
    """
    使用 LLM 验证用户是否确认了字段值

    Args:
        messages: 对话消息列表
        field_name: 字段名称
        field_value: 字段当前值

    Returns:
        bool: True 表示用户确认了该值，False 表示未确认
    """
    if not LLM_VALIDATION_ENABLED:
        logger.debug("[Validator] LLM 验证已禁用，跳过")
        return False

    try:
        # 格式化对话上下文
        conversation_context = _format_conversation_context(messages)

        # 获取字段描述
        field_description = FIELD_DESCRIPTIONS.get(field_name, f"Field '{field_name}' value")

        # 构建 prompt
        prompt = FIELD_VALIDATION_PROMPT.format(
            field_name=field_name,
            field_value=field_value,
            field_description=field_description,
            conversation_context=conversation_context,
        )

        # 调用 LLM
        llm = _get_validation_llm()
        structured_llm = llm.with_structured_output(FieldMentionValidation)

        messages_to_llm = [SystemMessage(content=prompt)]
        result = structured_llm.invoke(messages_to_llm)

        if result is None:
            logger.warning("[Validator] LLM 验证返回 None")
            return False

        # 处理返回结果
        user_confirmed: bool = False
        confidence: str = "unknown"
        reasoning: str = ""

        if isinstance(result, dict):
            user_confirmed = bool(result.get("user_confirmed", False))
            confidence = str(result.get("confidence", "unknown"))
            reasoning = str(result.get("reasoning", ""))
        elif isinstance(result, FieldMentionValidation):
            user_confirmed = result.user_confirmed
            confidence = result.confidence
            reasoning = result.reasoning
        elif hasattr(result, "user_confirmed"):
            # Gemini 可能返回其他 BaseModel 类型
            user_confirmed = bool(getattr(result, "user_confirmed", False))
            confidence = str(getattr(result, "confidence", "unknown"))
            reasoning = str(getattr(result, "reasoning", ""))

        logger.info(
            "[Validator] LLM 验证 %s=%s: confirmed=%s (confidence=%s, reason=%s)",
            field_name,
            field_value,
            user_confirmed,
            confidence,
            reasoning,
        )

        return user_confirmed

    except Exception as e:
        logger.warning("[Validator] LLM 验证失败: %s，回退到保守策略", e)
        # 出错时保守处理：视为未确认
        return False


def _is_suspicious_value_confirmed(
    messages: list[Any],
    field_name: str,
    field_value: Any,
) -> bool:
    """
    组合验证：检查可疑值是否被用户确认

    验证流程：
    1. 先用正则检测用户是否明确提到了该字段
    2. 如果正则未匹配，使用 LLM 进行验证

    Args:
        messages: 对话消息列表
        field_name: 字段名称
        field_value: 字段当前值

    Returns:
        bool: True 表示用户确认了该值，False 表示未确认
    """
    # Step 1: 正则检测
    if field_name == "pois_per_day":
        if _user_mentioned_pois_per_day(messages):
            logger.debug("[Validator] %s 通过正则验证确认", field_name)
            return True
    elif field_name == "travel_days":
        if _user_mentioned_days(messages):
            logger.debug("[Validator] %s 通过正则验证确认", field_name)
            return True

    # Step 2: 正则未匹配，尝试 LLM 验证
    logger.info(
        "[Validator] %s=%s 正则未匹配，尝试 LLM 验证",
        field_name,
        field_value,
    )
    return _llm_validate_field_mention(messages, field_name, field_value)


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
    logger.info("[Validator] LLM 辅助验证: %s", "启用" if LLM_VALIDATION_ENABLED else "禁用")

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
    features_dict = _get_features_dict(user_features)

    # 检查核心必填字段
    for field in core_required_fields:
        value = features_dict.get(field)

        # Step 1: 基础缺失检查（不检测可疑值）
        if _is_field_missing(user_features, field, check_suspicious=False):
            core_missing.append(field)
            missing.append(field)
            continue

        # Step 2: 可疑值检查 + LLM 验证
        # 检查是否在 SUSPICIOUS_DEFAULTS 中
        is_suspicious = False
        if field in SUSPICIOUS_DEFAULTS:
            if field in ["travel_days", "pois_per_day"]:
                # 整数字段：直接比较
                is_suspicious = value in SUSPICIOUS_DEFAULTS[field]
            else:
                # 字符串字段：转小写比较
                value_lower = str(value).lower().strip()
                suspicious_values = [str(v).lower() for v in SUSPICIOUS_DEFAULTS[field]]
                is_suspicious = value_lower in suspicious_values

        # travel_days 特殊处理：额外检查 SUSPICIOUS_TRAVEL_DAYS
        if field == "travel_days" and value in SUSPICIOUS_TRAVEL_DAYS:
            is_suspicious = True

        # 如果值可疑，使用组合验证（正则 + LLM）
        if is_suspicious:
            logger.info(
                "[Validator] 检测到可疑值 %s=%s，进行组合验证",
                field,
                value,
            )
            if not _is_suspicious_value_confirmed(messages, field, value):
                logger.warning(
                    "[Validator] 可疑值 %s=%s 未被用户确认，标记为缺失",
                    field,
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
