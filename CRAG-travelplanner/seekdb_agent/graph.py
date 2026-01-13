"""
CRAG TravelPlanner Graph
========================
LangGraph 工作流定义 - 整合所有节点和中间件

工作流程:
1. route_start: 检测冷启动 → ask_user(问候) 或 collector(提取特征)
2. collector → validator: 提取并验证用户特征
3. route_after_validation: 特征缺失 → ask_user(补充) 或 search_agent(搜索)
4. search_agent: 执行搜索（内部包含 Grading/Refiner/Fallback 中间件）
5. generator: 生成最终响应

使用示例:
    from seekdb_agent.graph import app, create_crag_graph
    from langchain_core.messages import HumanMessage

    # 使用预编译的 app
    result = app.invoke({"messages": [HumanMessage(content="我想去杭州玩3天")]})

    # 或创建自定义配置的 graph
    custom_graph = create_crag_graph(include_fallback=False)
    result = custom_graph.invoke({"messages": [HumanMessage(content="...")]})
"""

from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from seekdb_agent.agents.search_agent import create_search_agent
from seekdb_agent.nodes import (
    ask_user_node,
    collector_node,
    generator_node,
    validator_node,
)
from seekdb_agent.state import CRAGState
from seekdb_agent.utils.progress import emit_progress


def route_start(state: CRAGState) -> str:
    """
    入口路由：检测冷启动

    判断逻辑：
    - 无用户消息 → 冷启动 → ask_user(发送问候语)
    - 有用户消息 → 正常流程 → collector(提取特征)

    Args:
        state: 当前工作流状态

    Returns:
        下一个节点名称: "ask_user" 或 "collector"
    """
    messages = state.get("messages", [])
    user_messages = [m for m in messages if isinstance(m, HumanMessage)]
    return "ask_user" if len(user_messages) == 0 else "collector"


def route_after_validation(state: CRAGState) -> str:
    """
    验证后路由：判断特征完整性

    判断逻辑：
    1. 核心字段缺失 → ask_user(补充核心信息)
    2. 核心完整但可选字段缺失且未询问 → ask_user(询问可选信息)
    3. 特征完整 → search_agent(执行搜索)

    Args:
        state: 当前工作流状态

    Returns:
        下一个节点名称: "ask_user" 或 "search_agent"
    """
    feature_complete = state.get("feature_complete", False)
    missing_features = state.get("missing_features", [])
    optional_asked = state.get("optional_asked", False)

    if not feature_complete:
        return "ask_user"

    if len(missing_features) > 0 and not optional_asked:
        return "ask_user"

    return "search_agent"


def create_search_agent_node(
    include_grading: bool = True,
    include_refiner: bool = True,
    include_fallback: bool = True,
    max_retry: int = 2,
) -> Any:
    """
    创建 search_agent 节点函数

    包装 create_search_agent 工厂函数，使其适配 LangGraph 节点接口。
    支持配置中间件组合。

    Args:
        include_grading: 是否启用质量评估
        include_refiner: 是否启用查询修正
        include_fallback: 是否启用 Fallback
        max_retry: 最大重试次数

    Returns:
        节点函数
    """
    agent = create_search_agent(
        include_grading=include_grading,
        include_refiner=include_refiner,
        include_fallback=include_fallback,
        max_retry=max_retry,
    )

    def search_agent_node(state: CRAGState) -> dict[str, Any]:
        """
        搜索代理节点

        执行 POI 搜索，内部包含：
        - DocumentGradingMiddleware: 评估搜索结果质量
        - QueryRefinerMiddleware: 修正低质量查询
        - FallbackMiddleware: 兜底生成

        Args:
            state: 当前工作流状态

        Returns:
            状态更新字典
        """
        import sys

        from langchain_core.messages import ToolMessage

        from seekdb_agent.tools.search import (
            clear_last_search_results,
            get_last_search_results,
            set_user_features_for_search,
        )

        # 发射进度
        emit_progress("search", "正在搜索景点数据库...", 25)

        print("[SEARCH_AGENT] === ENTRY ===", file=sys.stderr, flush=True)

        # Clear any stale search results from previous invocations
        clear_last_search_results()

        # Set user features for dynamic top_k calculation
        raw_features = state.get("user_features")
        features_dict: dict[str, Any] | None = None
        if raw_features:
            if hasattr(raw_features, "model_dump"):
                features_dict = raw_features.model_dump()
            elif hasattr(raw_features, "items"):
                features_dict = dict(raw_features)  # type: ignore[arg-type]
        set_user_features_for_search(features_dict)

        result = agent.invoke(state)
        result_dict = dict(result) if hasattr(result, "items") else result

        # CRITICAL FIX: Middleware.before_model may not be called after the last tool call,
        # so search_results might not be in the result. Try multiple strategies.
        search_results_from_agent = result_dict.get("search_results", [])
        search_results_from_contextvar = get_last_search_results()

        print(
            f"[SEARCH_AGENT] result keys: {list(result_dict.keys())}", file=sys.stderr, flush=True
        )
        print(
            f"[SEARCH_AGENT] search_results from agent: {len(search_results_from_agent)}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"[SEARCH_AGENT] search_results from contextvar: {len(search_results_from_contextvar)}",
            file=sys.stderr,
            flush=True,
        )

        # Strategy 1: Use contextvar results if agent result is empty
        if not search_results_from_agent and search_results_from_contextvar:
            print("[SEARCH_AGENT] Using contextvar search_results", file=sys.stderr, flush=True)
            result_dict["search_results"] = search_results_from_contextvar
        # Strategy 2: Parse from ToolMessage if both are empty
        elif not search_results_from_agent and not search_results_from_contextvar:
            # Look for search_pois tool results in messages
            messages = result_dict.get("messages", [])
            last_tool_result = None
            for msg in reversed(messages):
                if isinstance(msg, ToolMessage) and msg.name == "search_pois":
                    last_tool_result = msg.content
                    break

            if last_tool_result and "Found" in str(last_tool_result):
                print(
                    "[SEARCH_AGENT] Tool was called but results not captured. Check middleware.",
                    file=sys.stderr,
                    flush=True,
                )
                # We can't recover structured data from text, but at least we know search worked
                # The generator will need to handle this via fallback

        # 发射搜索完成进度
        final_count = len(result_dict.get("search_results", []))
        emit_progress("search", f"找到 {final_count} 个景点", 70, count=final_count)

        return result_dict

    return search_agent_node


def create_crag_graph(
    include_grading: bool = True,
    include_refiner: bool = True,
    include_fallback: bool = True,
    max_retry: int = 2,
) -> Any:
    """
    创建 CRAG 工作流

    构建完整的 LangGraph StateGraph，包含：
    - 4个纯函数节点: collector, validator, ask_user, generator
    - 1个 Agent 节点: search_agent (可配置中间件)
    - 条件路由: route_start, route_after_validation

    Args:
        include_grading: 是否启用质量评估 Middleware
        include_refiner: 是否启用查询修正 Middleware
        include_fallback: 是否启用 Fallback Middleware
        max_retry: 最大重试次数

    Returns:
        编译后的 LangGraph 应用

    Examples:
        # 生产环境（全功能）
        app = create_crag_graph()

        # 测试环境（无 Fallback）
        app = create_crag_graph(include_fallback=False)

        # 调试环境（只评估，不修正）
        app = create_crag_graph(include_refiner=False, include_fallback=False)
    """
    workflow = StateGraph(CRAGState)

    search_agent_node = create_search_agent_node(
        include_grading=include_grading,
        include_refiner=include_refiner,
        include_fallback=include_fallback,
        max_retry=max_retry,
    )

    workflow.add_node("ask_user", ask_user_node)
    workflow.add_node("collector", collector_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("search_agent", search_agent_node)
    workflow.add_node("generator", generator_node)

    workflow.set_conditional_entry_point(
        route_start,
        {"ask_user": "ask_user", "collector": "collector"},
    )

    workflow.add_edge("ask_user", END)
    workflow.add_edge("collector", "validator")

    workflow.add_conditional_edges(
        "validator",
        route_after_validation,
        {"ask_user": "ask_user", "search_agent": "search_agent"},
    )

    workflow.add_edge("search_agent", "generator")
    workflow.add_edge("generator", END)

    return workflow.compile()


app = create_crag_graph()

__all__ = [
    "app",
    "create_crag_graph",
    "route_start",
    "route_after_validation",
]
