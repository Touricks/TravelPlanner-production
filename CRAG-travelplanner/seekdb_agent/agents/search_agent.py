"""
Search Agent Factory
====================
创建可配置的 CRAG 搜索代理

工厂模式优势：
- 生产环境：agent = create_search_agent()  # 全功能
- 测试环境：agent = create_search_agent(include_refiner=False)  # 按需组合

使用示例：
    # 生产环境（全功能）
    agent = create_search_agent()
    result = agent.invoke(state)

    # Testing API（只评估质量）
    agent = create_search_agent(include_grading=True, include_refiner=False)
"""

from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel

from seekdb_agent.llm import create_fallback_llm as _create_fallback_llm
from seekdb_agent.llm import get_cached_llm
from seekdb_agent.middleware.fallback import FallbackMiddleware
from seekdb_agent.middleware.grading import (
    DocumentGradingMiddleware,
    create_grader,
)
from seekdb_agent.middleware.refiner import QueryRefinerMiddleware
from seekdb_agent.state import CRAGState
from seekdb_agent.tools.search import search_pois

load_dotenv()

# Agent System Prompt
SEARCH_AGENT_SYSTEM_PROMPT = """你是一个专业的旅游助手，帮助用户搜索和推荐旅游景点。

**重要：你必须使用 search_pois 工具搜索数据库，不要凭空编造 POI 信息！**

**可用工具：**
- search_pois: 搜索 POI 数据库（景点、餐厅、酒店等）

**必须遵守的工作流程：**
1. 【必须】首先调用 search_pois 工具搜索相关 POI
2. 根据目的地构建搜索查询（如 "Miami beach attractions"）
3. 如果首次搜索结果不理想，尝试调整关键词再搜索
4. 只能基于 search_pois 返回的真实结果进行推荐

**搜索策略：**
- balanced 模式：通用查询（默认）
- semantic 模式：概念搜索，适合模糊描述
- keyword 模式：关键词搜索
- exact 模式：精确匹配名称

**禁止事项：**
- 禁止不调用 search_pois 就直接生成推荐
- 禁止编造不存在于搜索结果中的 POI
- 禁止使用虚构的 POI ID"""


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """
    获取主 LLM 实例

    Returns:
        BaseChatModel 实例（默认通义千问，可通过 LLM_PROVIDER 切换）
    """
    return get_cached_llm(temperature=0.7)


@lru_cache(maxsize=1)
def get_grader_instance() -> Any:
    """
    获取文档评估器实例

    Returns:
        Grader chain
    """
    return create_grader(get_llm())


def get_fallback_llm() -> BaseChatModel:
    """
    获取 Fallback LLM 实例

    优先级由 LLM_FALLBACK_PROVIDER 环境变量控制，
    默认优先 Gemini，然后 OpenAI，最后回退到 Qwen

    Returns:
        Fallback LLM 实例
    """
    return _create_fallback_llm(temperature=0.7)


def create_search_agent(
    include_grading: bool = True,
    include_refiner: bool = True,
    include_fallback: bool = True,
    max_retry: int = 2,
    llm: BaseChatModel | None = None,
) -> Any:
    """
    创建可配置的 CRAG 搜索代理

    Args:
        include_grading: 是否启用质量评估 Middleware
        include_refiner: 是否启用查询修正 Middleware
        include_fallback: 是否启用 Fallback Middleware
        max_retry: 最大重试次数（用于 refiner 和 fallback）
        llm: 自定义 LLM 实例（默认使用通义千问）

    Returns:
        配置好的 Agent 实例

    Examples:
        # 生产环境（全功能）
        agent = create_search_agent()

        # 测试：只评估质量
        agent = create_search_agent(
            include_grading=True,
            include_refiner=False,
            include_fallback=False
        )

        # 测试：评估 + 修正，但不要 fallback
        agent = create_search_agent(
            include_grading=True,
            include_refiner=True,
            include_fallback=False,
            max_retry=1
        )
    """
    # 获取 LLM
    model = llm or get_llm()

    # 构建 Middleware 列表（使用 Any 类型避免类型推断问题）
    middleware: list[Any] = []

    if include_grading:
        grader = get_grader_instance()
        middleware.append(
            DocumentGradingMiddleware(
                grader=grader,
                rag_tool_name="search_pois",
            )
        )

    if include_refiner:
        middleware.append(
            QueryRefinerMiddleware(
                refiner_llm=model,
                max_retry=max_retry,
            )
        )

    if include_fallback:
        fallback_llm = get_fallback_llm()
        middleware.append(
            FallbackMiddleware(
                fallback_llm=fallback_llm,
                max_retry=max_retry,
            )
        )

    # 创建 Agent
    return create_agent(
        model=model,
        tools=[search_pois],
        middleware=middleware,
        state_schema=CRAGState,
        system_prompt=SEARCH_AGENT_SYSTEM_PROMPT,
    )
