"""
Query Refiner Middleware
========================
检测 poor 质量结果，修正查询以改善搜索效果

Hook 机制：
- before_model: 检测 result_quality == "poor"，调用 LLM 修正查询
"""

import logging
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field

from seekdb_agent.state import CRAGState
from seekdb_agent.utils.progress import emit_progress

logger = logging.getLogger(__name__)


class RefinedQuery(BaseModel):
    """修正后的查询 Schema"""

    refined_query: str = Field(description="优化后的查询文本")
    modification_reason: str = Field(description="修正原因说明")


# 简化版 Refiner Prompt（用于 Middleware）
REFINER_SYSTEM_PROMPT = """你是一个查询优化专家。根据搜索失败的原因，生成改进的查询。

**修正策略：**
1. too_few（结果太少）：扩大搜索范围，添加相关关键词
2. semantic_drift（语义偏移）：添加明确限定词，聚焦核心意图
3. irrelevant（不相关）：基于用户特征重新构建查询
4. missing_must_visit（必去地点缺失）：将 must_visit 地点名加入查询，确保搜索覆盖用户指定的必去景点

**原则：**
- 避免重复已尝试的查询
- 保持语义一致性
- 优先考虑用户核心兴趣
- 对于 missing_must_visit，优先在查询中包含必去地点的名称"""


class QueryRefinerMiddleware(AgentMiddleware[CRAGState]):
    """
    查询修正 Middleware

    职责：
    - 检测 result_quality == "poor"
    - 在 retry 限制内调用 LLM 修正查询
    - 更新 refined_query 和 retry_count

    触发条件：
    - result_quality == "poor"
    - retry_count < max_retry
    - error_type is not None
    """

    state_schema = CRAGState

    def __init__(
        self,
        refiner_llm: BaseChatModel,
        max_retry: int = 1,
    ):
        """
        初始化 Middleware

        Args:
            refiner_llm: 用于修正查询的 LLM
            max_retry: 最大重试次数
        """
        self.refiner_llm = refiner_llm
        self.max_retry = max_retry
        self._refiner_chain = self._create_refiner_chain()

    def _create_refiner_chain(self) -> Any:
        """创建查询修正链"""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", REFINER_SYSTEM_PROMPT),
                (
                    "human",
                    """**原查询：** {original_query}
**失败类型：** {error_type}
**用户兴趣：** {interests}
**目的地：** {destination}
**必去地点：** {must_visit}
**已尝试查询：** {tried_queries}

请生成改进的查询。""",
                ),
            ]
        )
        return prompt | self.refiner_llm.with_structured_output(RefinedQuery)

    def before_model(
        self,
        state: CRAGState,
        runtime: Runtime,
    ) -> dict[str, Any] | None:
        """
        在 LLM 调用前检查是否需要修正查询

        触发条件：
        - quality == "poor"
        - retry_count < max_retry
        - error_type is not None
        """
        quality = state.get("result_quality")
        retry_count = state.get("retry_count", 0)
        error_type = state.get("error_type")

        should_refine = (
            quality == "poor" and retry_count < self.max_retry and error_type is not None
        )

        # 详细日志输出
        logger.info(
            "[Refiner] quality=%s, retry_count=%d, error_type=%s, should_refine=%s",
            quality,
            retry_count,
            error_type,
            should_refine,
        )

        if should_refine:
            # 发射优化进度
            emit_progress("refiner", f"优化搜索查询 (第{retry_count + 1}次)...", 50)

            refined = self._refine_query(state)
            if refined:
                logger.info("[Refiner] Refined query: %s", refined[:100])
                tried_queries = state.get("tried_queries", [])
                return {
                    "refined_query": refined,
                    "retry_count": retry_count + 1,
                    "tried_queries": tried_queries + [refined],
                }

        return None

    def _refine_query(self, state: CRAGState) -> str | None:
        """
        调用 LLM 修正查询

        Args:
            state: 当前状态

        Returns:
            修正后的查询，失败时返回 None
        """
        original_query = state.get("last_rag_query", "")
        error_type = state.get("error_type", "unknown")
        user_features = state.get("user_features")
        tried_queries = state.get("tried_queries", [])

        # 将 UserFeatures 转为字典
        if user_features is None:
            uf_dict: dict[str, Any] = {}
        elif hasattr(user_features, "model_dump"):
            uf_dict = user_features.model_dump()
        else:
            uf_dict = dict(user_features)

        try:
            must_visit = uf_dict.get("must_visit", [])
            result = self._refiner_chain.invoke(
                {
                    "original_query": original_query,
                    "error_type": error_type,
                    "interests": ", ".join(uf_dict.get("interests", [])),
                    "destination": uf_dict.get("destination") or "未知",
                    "must_visit": ", ".join(must_visit) if must_visit else "无",
                    "tried_queries": ", ".join(tried_queries) if tried_queries else "无",
                }
            )

            if result and hasattr(result, "refined_query"):
                return str(result.refined_query)

        except Exception:
            pass

        return None
