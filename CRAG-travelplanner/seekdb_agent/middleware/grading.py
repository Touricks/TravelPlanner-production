"""
Document Grading Middleware
===========================
评估 RAG 搜索结果的质量

Hook 机制：
- wrap_tool_call: 拦截 search_pois 调用，评估结果质量
- before_model: 将暂存的评估结果应用到 state
"""

import logging
from collections.abc import Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field

from seekdb_agent.state import CRAGState
from seekdb_agent.tools.search import get_last_search_results
from seekdb_agent.utils.progress import emit_progress

logger = logging.getLogger(__name__)


class GradeDocuments(BaseModel):
    """文档评估结果 Schema"""

    binary_score: str = Field(description="文档是否与查询相关，'yes' 或 'no'")
    reasoning: str = Field(description="评估理由的简要说明")
    must_visit_covered: bool = Field(
        default=True,
        description="用户指定的 must_visit 地点是否被搜索结果覆盖",
    )


# 评估 Prompt
GRADE_PROMPT = ChatPromptTemplate.from_template(
    """你是一个评估检索文档相关性的专家。

**检索到的文档：**
{document}

**用户查询：**
{question}

**用户必去地点（must_visit）：**
{must_visit}

**评估任务：**
1. 相关性评估：如果文档包含与查询相关的关键词或语义信息，给出 'yes'，否则 'no'
2. must_visit 覆盖检查：检查搜索结果是否包含用户指定的必去地点或相关区域的 POI
   - 如果 must_visit 为空，设置 must_visit_covered=true
   - 如果 must_visit 有内容但结果中完全没有相关 POI，设置 must_visit_covered=false
   - 如果 must_visit 中的地点至少部分被覆盖，设置 must_visit_covered=true

给出评分和简要理由。"""
)


def create_grader(llm: BaseChatModel) -> Any:
    """
    创建文档评估器

    Args:
        llm: LLM 实例

    Returns:
        带有结构化输出的评估链
    """
    return GRADE_PROMPT | llm.with_structured_output(GradeDocuments)


class DocumentGradingMiddleware(AgentMiddleware[CRAGState]):
    """
    文档质量评估 Middleware

    职责：
    - 拦截 search_pois 工具调用
    - 评估返回文档的相关性
    - 将评估结果暂存并在下次 LLM 调用前应用到 state

    工作流程：
    1. wrap_tool_call: 执行 tool → 评估 → 暂存到 _pending_grading
    2. before_model: 检测暂存 → 返回 dict 更新 state
    """

    state_schema = CRAGState

    def __init__(
        self,
        grader: Any,
        rag_tool_name: str = "search_pois",
    ):
        """
        初始化 Middleware

        Args:
            grader: 文档评估器（由 create_grader 创建）
            rag_tool_name: RAG 工具名称
        """
        self.grader = grader
        self.rag_tool_name = rag_tool_name
        self._pending_grading: dict[str, Any] | None = None
        self._current_must_visit: list[str] = []  # 暂存当前用户的 must_visit

    def before_model(
        self,
        state: CRAGState,
        runtime: Runtime,
    ) -> dict[str, Any] | None:
        """
        在 LLM 调用前，应用暂存的评估结果

        为什么需要这个 hook？
        - wrap_tool_call 必须返回 ToolMessage，不能直接更新 state
        - 通过实例变量 _pending_grading 桥接两个 hook
        """
        # 提取并暂存 must_visit（供 wrap_tool_call 使用）
        user_features = state.get("user_features")
        if user_features and hasattr(user_features, "must_visit"):
            self._current_must_visit = user_features.must_visit or []
        else:
            self._current_must_visit = []

        if self._pending_grading is not None:
            # 发射评估进度
            quality = self._pending_grading.get("result_quality", "unknown")
            emit_progress("grading", f"评估搜索结果质量: {quality}", 72, quality=quality)

            updates = self._pending_grading
            self._pending_grading = None  # 清空，避免重复应用
            return updates
        return None

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Any],
    ) -> ToolMessage | Any:
        """
        拦截工具调用，评估 RAG 结果质量

        Args:
            request: 工具调用请求
            handler: 原始处理器

        Returns:
            ToolMessage（必须返回此类型）
        """
        tool_name = request.tool_call.get("name", "")
        tool_args = request.tool_call.get("args", {})

        # 先执行工具
        result = handler(request)

        # 只评估 RAG 工具
        if tool_name == self.rag_tool_name and isinstance(result, ToolMessage):
            query = tool_args.get("query", "")
            doc_content = result.content

            # 获取结构化搜索结果（从 contextvar 读取）
            search_results = get_last_search_results()

            try:
                # 准备 must_visit 字符串
                must_visit_str = (
                    ", ".join(self._current_must_visit) if self._current_must_visit else "无"
                )

                # 评估文档相关性
                grade_result = self.grader.invoke(
                    {
                        "question": query,
                        "document": doc_content[:2000],  # 截断避免超长
                        "must_visit": must_visit_str,
                    }
                )

                # 处理可能的 None 响应
                if grade_result is None:
                    # 评估失败时仍保存搜索结果
                    self._pending_grading = {"search_results": search_results}
                    return result

                if not hasattr(grade_result, "binary_score"):
                    # 评估失败时仍保存搜索结果
                    self._pending_grading = {"search_results": search_results}
                    return result

                is_relevant = grade_result.binary_score.lower() == "yes"
                must_visit_covered = getattr(grade_result, "must_visit_covered", True)

                # 确定质量和错误类型
                if is_relevant and must_visit_covered:
                    quality = "good"
                    error_type = None
                elif not must_visit_covered and self._current_must_visit:
                    quality = "poor"
                    error_type = "missing_must_visit"
                else:
                    quality = "poor"
                    error_type = "irrelevant"

                # 详细日志输出
                logger.info(
                    "[Grading] query='%s', quality=%s, must_visit_covered=%s, reasoning=%s",
                    query[:50],
                    quality,
                    must_visit_covered,
                    grade_result.reasoning[:100] if hasattr(grade_result, "reasoning") else "N/A",
                )

                # 暂存评估结果（将在 before_model 中应用）
                self._pending_grading = {
                    "last_rag_query": query,
                    "result_quality": quality,
                    "error_type": error_type,
                    "search_results": search_results,  # 新增：保存结构化结果
                }

            except Exception:
                # 评估失败时仍保存搜索结果
                self._pending_grading = {"search_results": search_results}

        return result
