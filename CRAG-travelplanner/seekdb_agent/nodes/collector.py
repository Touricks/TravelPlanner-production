"""
Collector Node - 特征提取节点
==============================
从用户消息中提取结构化的旅游偏好信息

设计模式：
- State中的messages已经是list[BaseMessage]，无需转换
- 直接使用state["messages"]，与SystemMessage组合
- LangChain自动处理消息类型

更新记录：
- 2026-01-09: 切换 structured_output LLM 从 Qwen 到 Gemini，减少幻觉
- 2026-01-09: UserFeatures 改为 Pydantic，删除类型转换代码
- 2026-01-09: 使用 llm/factory.py 统一配置管理，去除硬编码
"""

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from seekdb_agent.llm import create_llm
from seekdb_agent.prompts.collector import COLLECTOR_PROMPT
from seekdb_agent.state import CRAGState, UserFeatures
from seekdb_agent.utils.progress import emit_progress

# 配置日志
logger = logging.getLogger(__name__)


def _get_llm() -> BaseChatModel:
    """
    获取配置好的 LLM 实例

    使用统一的 create_llm 工厂函数，
    通过环境变量配置 Provider（默认 Qwen）

    temperature=0 确保特征提取的确定性
    """
    return create_llm(temperature=0.0)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _extract_features_with_retry(messages: list[Any]) -> UserFeatures:
    """
    使用LLM提取特征，带重试机制

    Args:
        messages: LangChain消息对象列表

    Returns:
        UserFeatures: 提取的结构化特征 (Pydantic BaseModel)

    Raises:
        Exception: LLM调用失败或解析失败
    """
    llm = _get_llm()

    # 直接使用 UserFeatures Pydantic Model
    structured_llm = llm.with_structured_output(UserFeatures)

    # 调用 LLM
    result = structured_llm.invoke(messages)

    # 处理返回结果
    if result is None:
        return UserFeatures()

    # 如果返回的是 dict，转换为 UserFeatures
    if isinstance(result, dict):
        return UserFeatures(**result)

    # 如果已经是 UserFeatures，直接返回
    if isinstance(result, UserFeatures):
        return result

    # Gemini 可能返回其他 BaseModel，转换为 UserFeatures
    return UserFeatures(**result.model_dump())


def collector_node(state: CRAGState) -> dict[str, Any]:
    """
    Collector节点：从用户消息中提取结构化特征

    LangGraph标准模式：
    - State继承自AgentState，messages自动是list[BaseMessage]
    - 无需任何格式转换，直接使用
    - 返回dict格式的更新，LangGraph自动合并

    输入（从state读取）：
        - messages: list[BaseMessage]  # 用户对话历史（自动类型）

    输出（更新到state）：
        - user_features: 提取的结构化用户特征

    工作流程：
        1. 构建包含COLLECTOR_PROMPT的消息列表
        2. 调用LLM进行特征提取（使用structured output）
        3. 返回提取的UserFeatures

    异常处理：
        - 使用 tenacity 进行重试（最多3次）
        - 如果所有重试失败，返回默认空特征
    """
    # 发射进度
    emit_progress("collector", "Understanding your travel preferences...", 10)

    # 记录输入消息
    input_messages = state.get("messages", [])
    logger.info("[Collector] 开始特征提取")
    logger.info("[Collector] 输入消息数量: %d", len(input_messages))
    for i, msg in enumerate(input_messages):
        msg_type = type(msg).__name__
        # 兼容 BaseMessage 对象和 dict 格式
        if hasattr(msg, "content"):
            content_str = str(msg.content)
        elif isinstance(msg, dict):
            content_str = str(msg.get("content", ""))
        else:
            content_str = str(msg)
        content = content_str[:100] + "..." if len(content_str) > 100 else content_str
        logger.info("[Collector] 消息[%d] (%s): %s", i, msg_type, content)

    # 1. 构建消息列表 - 直接使用state中的BaseMessage对象
    messages = [
        SystemMessage(content=COLLECTOR_PROMPT),
        *input_messages,  # ← 已经是list[BaseMessage]，无需转换！
    ]

    # 2. 调用LLM提取特征（带重试）
    try:
        user_features = _extract_features_with_retry(messages)
        logger.info("[Collector] 特征提取成功")
        logger.info("[Collector] 提取结果: %s", user_features.model_dump())
        emit_progress("collector", "Preferences collected", 15)
    except Exception as e:
        # 重试全部失败，返回默认空特征
        logger.error("[Collector] 特征提取失败: %s", e)
        user_features = UserFeatures()

    # 3. 返回更新的状态
    return {"user_features": user_features}
