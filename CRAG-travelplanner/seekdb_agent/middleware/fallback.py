"""
Fallback Middleware
===================
Use Google Gemini web search as fallback after retry exhaustion

Design Points:
- Pass existing POIs as context
- Provide complete user feature information
- Gemini can: 1) Utilize existing POIs; 2) Supplement with web search

Hook Mechanism:
- before_model: Detect retry_count >= max_retry, trigger Gemini generation
"""

import logging
from collections.abc import Sequence
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from seekdb_agent.llm import create_fallback_llm
from seekdb_agent.state import CRAGState, POIResult
from seekdb_agent.tools.search import get_last_search_results_raw

logger = logging.getLogger(__name__)

# Fallback Prompt - With complete user features
FALLBACK_PROMPT = """**IMPORTANT: You MUST respond in English only.**

You are a professional travel advisor. Database search encountered difficulties. Please provide recommendations using existing information and web search capabilities.

**Previously Found POIs (for reference):**
{existing_pois}

**User's Complete Requirements:**
- Destination: {destination}
- Travel days: {travel_days} days
- Interest preferences: {interests}
- Dining budget: {budget_meal}
- Transportation: {transportation}
- Attractions per day: {pois_per_day}
- Must-visit attractions: {must_visit}
- Dietary preferences: {dietary_options}

**Requirements:**
1. If existing POIs meet the needs, prioritize recommending them
2. Use web search to supplement more attractions matching user preferences
3. Organize itinerary according to user's travel days and attractions per day
4. Consider user's budget and transportation preferences
5. Output format should reference the existing POI information structure"""


class FallbackMiddleware(AgentMiddleware[CRAGState]):
    """
    Fallback Middleware - 使用 Gemini 联网搜索

    职责：
    - 检测搜索失败情况，触发 Gemini 兜底生成
    - 将已搜索 POI + 完整用户特征传入 Gemini
    - 生成最终响应（结合数据库结果 + 联网信息）

    触发条件（满足任一即可）：
    1. result_quality == "poor" AND retry_count >= max_retry AND not fallback_triggered
    2. search_results 为空 AND quality 已设置 AND not fallback_triggered（立即兜底）

    条件2的原因：空结果意味着数据库无匹配 POI，修正查询无济于事，应立即使用 Gemini 联网搜索
    """

    state_schema = CRAGState

    def __init__(
        self,
        fallback_llm: BaseChatModel | None = None,
        max_retry: int = 2,
    ):
        """
        初始化 Middleware

        Args:
            fallback_llm: Fallback LLM（推荐 Gemini）
            max_retry: 触发 fallback 的重试阈值
        """
        self.fallback_llm = fallback_llm or self._create_gemini()
        self.max_retry = max_retry

    def _create_gemini(self) -> BaseChatModel:
        """
        创建 Fallback LLM 实例

        优先级由 LLM_FALLBACK_PROVIDER 环境变量控制，
        默认优先 Gemini，然后 OpenAI，最后回退到 Qwen
        """
        return create_fallback_llm(temperature=0.7)

    def before_model(
        self,
        state: CRAGState,
        runtime: Runtime,
    ) -> dict[str, Any] | None:
        """
        在 LLM 调用前检查是否需要触发 fallback

        触发条件（满足任一即可）：
        1. quality == "poor" AND retry_count >= max_retry AND not fallback_triggered
        2. search_results 为空 AND not fallback_triggered（立即兜底，无需等待重试）
        """
        quality = state.get("result_quality")
        retry_count = state.get("retry_count", 0)
        fallback_triggered = state.get("fallback_triggered", False)

        # 从 contextvar 读取搜索结果（避免 state 更新时序问题）
        # GradingMiddleware.before_model 可能与本 hook 在同一轮运行，
        # 此时 state 尚未更新，但 contextvar 已在 wrap_tool_call 中设置
        #
        # 使用 get_last_search_results_raw 区分：
        # - None: 尚未执行搜索 → 不触发 fallback
        # - []: 搜索已执行但无结果 → 触发 fallback
        # - [...]: 搜索已执行且有结果 → 根据 quality 判断
        search_results_raw = get_last_search_results_raw()
        search_was_done = search_results_raw is not None
        search_results = search_results_raw if search_results_raw else []

        # 条件1：质量差且重试次数耗尽
        poor_quality_exhausted = (
            quality == "poor" and retry_count >= self.max_retry and not fallback_triggered
        )

        # 条件2：搜索结果为空（立即触发，无需等待重试）
        # 原因：空结果意味着数据库无匹配 POI，修正查询无济于事
        # 使用 search_was_done 确保搜索已执行（contextvar 已设置）
        empty_results = len(search_results) == 0 and search_was_done and not fallback_triggered

        should_fallback = poor_quality_exhausted or empty_results

        # 详细日志输出
        logger.info(
            "[Fallback] quality=%s, retry_count=%d, search_results=%d, "
            "poor_exhausted=%s, empty=%s, should_fallback=%s",
            quality,
            retry_count,
            len(search_results),
            poor_quality_exhausted,
            empty_results,
            should_fallback,
        )

        if should_fallback:
            logger.warning("[Fallback] TRIGGERED - generating with fallback LLM")
            response = self._generate_with_fallback(state)
            return {
                "fallback_triggered": True,
                "final_response": response,
            }

        return None

    def _generate_with_fallback(self, state: CRAGState) -> str:
        """
        使用 Fallback LLM 生成响应

        Args:
            state: 当前状态

        Returns:
            生成的响应文本
        """
        # 获取已搜索的 POI
        search_results = state.get("search_results", [])
        existing_pois = self._format_existing_pois(search_results)

        # 获取用户特征并转为字典
        user_features = state.get("user_features")
        if user_features is None:
            uf: dict[str, Any] = {}
        elif hasattr(user_features, "model_dump"):
            uf = user_features.model_dump()
        else:
            uf = dict(user_features)

        # 构建 prompt
        prompt = FALLBACK_PROMPT.format(
            existing_pois=existing_pois or "None",
            destination=uf.get("destination") or "Unknown",
            travel_days=uf.get("travel_days") or "Not specified",
            interests=", ".join(uf.get("interests", [])) or "Not specified",
            budget_meal=uf.get("budget_meal") or "Not specified",
            transportation=uf.get("transportation") or "Not specified",
            pois_per_day=uf.get("pois_per_day") or "Not specified",
            must_visit=", ".join(uf.get("must_visit", [])) or "None",
            dietary_options=", ".join(uf.get("dietary_options", [])) or "None",
        )

        # 获取原始用户查询
        messages = state.get("messages", [])
        user_query = ""
        for msg in messages:
            if hasattr(msg, "type") and msg.type == "human":
                content = msg.content
                user_query = str(content) if isinstance(content, str) else str(content)
                break

        try:
            response = self.fallback_llm.invoke(
                [
                    SystemMessage(content=prompt),
                    HumanMessage(
                        content=f"Please recommend travel attractions for me: {user_query}"
                    ),
                ]
            )
            # 处理响应类型
            if hasattr(response, "content"):
                return str(response.content)
            return str(response)
        except Exception as e:
            return f"Sorry, search encountered difficulties. Please try describing your needs again. Error: {e!s}"

    def _format_existing_pois(self, results: Sequence[POIResult | dict[str, Any]]) -> str:
        """
        格式化已搜索的 POI 供 Fallback LLM 参考

        Args:
            results: POI 搜索结果列表（支持 POIResult 或 dict）

        Returns:
            格式化的 POI 文本
        """
        if not results:
            return ""

        lines = []
        for poi in results[:20]:  # 最多传入 20 个
            # Support both POIResult and dict
            if isinstance(poi, dict):
                name = poi.get("name", "Unknown")
                city = poi.get("city")
                primary_category = poi.get("primary_category")
                rating = poi.get("rating")
            else:
                name = poi.name
                city = poi.city
                primary_category = poi.primary_category
                rating = poi.rating

            line = f"- {name}"
            if city:
                line += f" ({city})"
            if primary_category:
                line += f": {primary_category}"
            if rating:
                line += f", Rating {rating}"
            lines.append(line)

        return "\n".join(lines)
