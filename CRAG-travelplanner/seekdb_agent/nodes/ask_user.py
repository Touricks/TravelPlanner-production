"""
AskUser Node - 用户询问节点
============================
支持两种场景：
1. 冷启动问候语（首次对话，无用户消息时）
2. 补充信息提问（字段缺失时）

设计模式：
- State中的messages已经是list[BaseMessage]，无需转换
- 直接返回AIMessage对象添加到messages
- LangGraph自动处理消息合并

更新记录：
- 2026-01-09: 使用 llm/factory.py 统一配置管理，去除硬编码
"""

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from seekdb_agent.llm import create_llm
from seekdb_agent.prompts.ask_user import ASK_USER_PROMPT, GREETING_PROMPT
from seekdb_agent.state import CRAGState


def _get_llm() -> BaseChatModel:
    """
    获取配置好的LLM实例

    使用 llm/factory.py 统一创建，配置从环境变量读取
    """
    return create_llm(temperature=0.7)  # 生成提问需要一定的创造性


def ask_user_node(state: CRAGState) -> dict[str, Any]:
    """
    AskUser节点：生成用户交互提问

    支持两种场景：
    1. **冷启动问候**（无用户消息时）
       - 使用 GREETING_PROMPT
       - 生成欢迎语，引导用户开始描述旅行计划

    2. **补充信息提问**（有用户消息，字段缺失时）
       - 使用 ASK_USER_PROMPT
       - 根据缺失字段生成补充提问

    LangGraph标准模式：
    - State中messages已经是list[BaseMessage]
    - 直接使用，无需转换
    - 返回AIMessage对象，LangGraph自动添加到messages

    输入（从state读取）：
        - messages: 历史对话（list[BaseMessage]）
        - missing_features: 所有缺失字段（核心+可选）
        - user_features: 已知特征

    输出（更新到state）：
        - messages: 添加一条 AI 消息（AIMessage对象）
        - optional_asked: bool（如果只询问可选字段，设为 True）

    工作流程：
        1. 检测是否为冷启动（无用户消息）
        2. 根据场景选择对应的 Prompt
        3. 调用 LLM 生成回复
        4. 返回 AI 消息
    """
    messages = state.get("messages", [])

    # 检测是否为冷启动（没有用户消息）
    user_messages = [m for m in messages if isinstance(m, HumanMessage)]

    if len(user_messages) == 0:
        # ===== 场景 1：冷启动问候 =====
        system_msg = SystemMessage(content=GREETING_PROMPT)

        # 调用 LLM 生成欢迎语
        llm = _get_llm()
        response = llm.invoke([system_msg])

        return {
            "messages": [AIMessage(content=response.content)],
        }

    else:
        # ===== 场景 2：补充信息提问 =====
        missing_fields = state.get("missing_features", [])
        user_features = state.get("user_features")

        # 分类缺失字段
        core_required = [
            "destination",
            "travel_days",
            "interests",
            "budget_meal",
            "transportation",
            "pois_per_day",
        ]

        core_missing = [f for f in missing_fields if f in core_required]
        optional_missing = [f for f in missing_fields if f not in core_required]

        # 1. 将 user_features 转为字典格式（Pydantic -> dict）
        if user_features is None:
            user_features_dict: dict[str, Any] = {}
        elif hasattr(user_features, "model_dump"):
            user_features_dict = user_features.model_dump()
        else:
            user_features_dict = dict(user_features)

        # 2. 构建 Prompt
        prompt = ASK_USER_PROMPT.format(
            core_missing=core_missing,
            optional_missing=optional_missing,
            user_features=user_features_dict,
        )

        # 3. 构建消息列表 - 直接使用state中的BaseMessage对象
        prompt_messages: list = [SystemMessage(content=prompt)]

        # 添加用户消息历史（最近3条，避免上下文过长）
        recent_messages = messages[-3:]
        prompt_messages.extend(recent_messages)  # ← 已经是list[BaseMessage]，直接extend！

        # 4. 调用 LLM 生成提问
        llm = _get_llm()
        response = llm.invoke(prompt_messages)

        # 5. 准备返回值
        result: dict[str, Any] = {
            "messages": [AIMessage(content=response.content)],  # ← 直接返回AIMessage对象！
        }

        # 6. 如果只询问可选字段，设置标志（避免重复询问）
        if len(core_missing) == 0 and len(optional_missing) > 0:
            result["optional_asked"] = True

        return result
