"""
Middleware Unit Tests
=====================
基于 benchmark_design_20260103.md 第二节设计

测试覆盖指标：
- 2.2 CRAG Self-Correction: Quality Detection, Fallback Trigger
- 2.3 Query Refinement: Refinement Success, Error Diagnosis

测试策略：
- 使用 Mock 模拟 LLM 响应，隔离外部依赖
- 验证触发条件逻辑（不依赖实际 LLM）
- 验证状态更新正确性
"""

from unittest.mock import MagicMock

import pytest

from seekdb_agent.middleware.fallback import FallbackMiddleware
from seekdb_agent.middleware.grading import (
    DocumentGradingMiddleware,
)
from seekdb_agent.middleware.refiner import QueryRefinerMiddleware
from seekdb_agent.state import CRAGState, POIResult

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_grader() -> MagicMock:
    """创建 Mock grader"""
    grader = MagicMock()
    return grader


@pytest.fixture
def mock_llm() -> MagicMock:
    """创建 Mock LLM"""
    llm = MagicMock()
    llm.with_structured_output = MagicMock(return_value=llm)
    return llm


@pytest.fixture
def mock_runtime() -> MagicMock:
    """创建 Mock Runtime"""
    return MagicMock()


@pytest.fixture
def sample_poi_results() -> list[POIResult]:
    """创建示例 POI 结果"""
    return [
        POIResult(
            id="poi_001",
            name="西湖",
            city="杭州",
            rating=4.8,
            primary_category="景点",
            score=0.95,
        ),
        POIResult(
            id="poi_002",
            name="灵隐寺",
            city="杭州",
            rating=4.6,
            primary_category="寺庙",
            score=0.88,
        ),
    ]


# ============================================================
# 2.2 CRAG Self-Correction: DocumentGradingMiddleware Tests
# ============================================================


class TestDocumentGradingMiddleware:
    """
    测试文档评估 Middleware

    对应指标：Quality Detection Accuracy ≥ 0.85
    """

    def test_before_model_no_pending(self, mock_grader: MagicMock, mock_runtime: MagicMock) -> None:
        """测试无暂存结果时 before_model 返回 None"""
        middleware = DocumentGradingMiddleware(grader=mock_grader)
        state: CRAGState = {"messages": []}

        result = middleware.before_model(state, mock_runtime)

        assert result is None

    def test_before_model_with_pending_good(
        self, mock_grader: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试有暂存的 good 评估结果时正确返回"""
        middleware = DocumentGradingMiddleware(grader=mock_grader)
        middleware._pending_grading = {
            "last_rag_query": "杭州景点",
            "result_quality": "good",
            "error_type": None,
        }
        state: CRAGState = {"messages": []}

        result = middleware.before_model(state, mock_runtime)

        assert result is not None
        assert result["result_quality"] == "good"
        assert result["error_type"] is None
        # 验证暂存已清空
        assert middleware._pending_grading is None

    def test_before_model_with_pending_poor(
        self, mock_grader: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试有暂存的 poor 评估结果时正确返回"""
        middleware = DocumentGradingMiddleware(grader=mock_grader)
        middleware._pending_grading = {
            "last_rag_query": "火星旅游",
            "result_quality": "poor",
            "error_type": "irrelevant",
        }
        state: CRAGState = {"messages": []}

        result = middleware.before_model(state, mock_runtime)

        assert result is not None
        assert result["result_quality"] == "poor"
        assert result["error_type"] == "irrelevant"

    def test_pending_cleared_after_apply(
        self, mock_grader: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试暂存结果应用后被清空，避免重复应用"""
        middleware = DocumentGradingMiddleware(grader=mock_grader)
        middleware._pending_grading = {"result_quality": "good"}
        state: CRAGState = {"messages": []}

        # 第一次调用
        middleware.before_model(state, mock_runtime)
        # 第二次调用应返回 None
        result = middleware.before_model(state, mock_runtime)

        assert result is None


# ============================================================
# 2.3 Query Refinement: QueryRefinerMiddleware Tests
# ============================================================


class TestQueryRefinerMiddleware:
    """
    测试查询修正 Middleware

    对应指标：
    - Refinement Success Rate ≥ 0.60
    - Error Diagnosis Accuracy ≥ 0.80
    - Avg Retry Count ≤ 1.5
    """

    def test_trigger_condition_quality_poor(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试触发条件：quality=poor, retry_count < max, error_type 存在"""
        middleware = QueryRefinerMiddleware(refiner_llm=mock_llm, max_retry=2)

        # Mock refiner chain 返回结果
        mock_result = MagicMock()
        mock_result.refined_query = "杭州西湖景点推荐"
        middleware._refiner_chain = MagicMock(return_value=mock_result)
        middleware._refiner_chain.invoke = MagicMock(return_value=mock_result)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 0,
            "error_type": "too_few",
            "last_rag_query": "杭州",
            "user_features": {"destination": "杭州", "interests": ["历史"]},
            "tried_queries": [],
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is not None
        assert "refined_query" in result
        assert result["retry_count"] == 1

    def test_no_trigger_when_quality_good(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试 quality=good 时不触发修正"""
        middleware = QueryRefinerMiddleware(refiner_llm=mock_llm, max_retry=2)

        state: CRAGState = {
            "messages": [],
            "result_quality": "good",
            "retry_count": 0,
            "error_type": None,
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is None

    def test_no_trigger_when_max_retry_reached(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试达到 max_retry 时不再触发修正"""
        middleware = QueryRefinerMiddleware(refiner_llm=mock_llm, max_retry=2)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 2,  # 已达到 max_retry
            "error_type": "too_few",
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is None

    def test_no_trigger_when_error_type_none(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试 error_type=None 时不触发修正"""
        middleware = QueryRefinerMiddleware(refiner_llm=mock_llm, max_retry=2)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 0,
            "error_type": None,  # 无错误类型
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is None

    def test_retry_count_increment(self, mock_llm: MagicMock, mock_runtime: MagicMock) -> None:
        """测试每次修正后 retry_count 正确递增"""
        middleware = QueryRefinerMiddleware(refiner_llm=mock_llm, max_retry=3)

        mock_result = MagicMock()
        mock_result.refined_query = "修正后的查询"
        middleware._refiner_chain = MagicMock()
        middleware._refiner_chain.invoke = MagicMock(return_value=mock_result)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 1,
            "error_type": "semantic_drift",
            "last_rag_query": "原查询",
            "user_features": {},
            "tried_queries": ["查询1"],
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is not None
        assert result["retry_count"] == 2

    def test_tried_queries_accumulation(self, mock_llm: MagicMock, mock_runtime: MagicMock) -> None:
        """测试 tried_queries 列表正确累积"""
        middleware = QueryRefinerMiddleware(refiner_llm=mock_llm, max_retry=3)

        mock_result = MagicMock()
        mock_result.refined_query = "新查询"
        middleware._refiner_chain = MagicMock()
        middleware._refiner_chain.invoke = MagicMock(return_value=mock_result)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 0,
            "error_type": "too_few",
            "last_rag_query": "原查询",
            "user_features": {},
            "tried_queries": ["旧查询1", "旧查询2"],
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is not None
        assert len(result["tried_queries"]) == 3
        assert "新查询" in result["tried_queries"]


# ============================================================
# 2.2 CRAG Self-Correction: FallbackMiddleware Tests
# ============================================================


class TestFallbackMiddleware:
    """
    测试 Fallback Middleware

    对应指标：
    - Fallback Trigger Rate 10-20%
    - Correction Improvement ≥ 20%
    """

    def test_trigger_condition_all_met(self, mock_llm: MagicMock, mock_runtime: MagicMock) -> None:
        """测试所有触发条件满足时正确触发 fallback"""
        middleware = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        # Mock LLM 响应
        mock_response = MagicMock()
        mock_response.content = "Gemini 生成的旅游建议..."
        mock_llm.invoke = MagicMock(return_value=mock_response)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 2,  # >= max_retry
            "fallback_triggered": False,
            "search_results": [],
            "user_features": {"destination": "杭州"},
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is not None
        assert result["fallback_triggered"] is True
        assert "final_response" in result

    def test_no_trigger_when_quality_good(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试 quality=good 时不触发 fallback"""
        middleware = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        state: CRAGState = {
            "messages": [],
            "result_quality": "good",
            "retry_count": 2,
            "fallback_triggered": False,
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is None

    def test_no_trigger_when_retry_not_exhausted(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试 retry 未耗尽时不触发 fallback"""
        middleware = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 1,  # < max_retry
            "fallback_triggered": False,
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is None

    def test_no_trigger_when_already_triggered(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试已触发过 fallback 时不重复触发"""
        middleware = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 2,
            "fallback_triggered": True,  # 已触发
        }

        result = middleware.before_model(state, mock_runtime)

        assert result is None

    def test_format_existing_pois(
        self, mock_llm: MagicMock, sample_poi_results: list[POIResult]
    ) -> None:
        """测试 POI 格式化方法"""
        middleware = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        formatted = middleware._format_existing_pois(sample_poi_results)

        assert "西湖" in formatted
        assert "杭州" in formatted
        assert "4.8" in formatted

    def test_format_empty_pois(self, mock_llm: MagicMock) -> None:
        """测试空 POI 列表格式化"""
        middleware = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        formatted = middleware._format_existing_pois([])

        assert formatted == ""

    def test_fallback_includes_user_features(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """测试 fallback 时正确传入用户特征"""
        middleware = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        mock_response = MagicMock()
        mock_response.content = "基于您的偏好..."
        mock_llm.invoke = MagicMock(return_value=mock_response)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 2,
            "fallback_triggered": False,
            "search_results": [],
            "user_features": {
                "destination": "北京",
                "travel_days": 3,
                "interests": ["历史", "美食"],
                "budget_meal": 50,
            },
        }

        result = middleware.before_model(state, mock_runtime)

        # 验证 LLM 被调用
        assert mock_llm.invoke.called
        assert result is not None


# ============================================================
# Integration-like Tests (触发条件组合测试)
# ============================================================


class TestMiddlewareTriggerConditions:
    """
    测试 Middleware 触发条件的边界情况

    对应 2.3 Avg Retry Count ≤ 1.5 指标验证
    """

    def test_refiner_to_fallback_transition(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """
        测试 Refiner → Fallback 转换逻辑

        场景：retry_count 从 1 → 2 后，Refiner 不再触发，Fallback 应触发
        """
        refiner = QueryRefinerMiddleware(refiner_llm=mock_llm, max_retry=2)
        fallback = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        # 状态：retry_count = 2, quality = poor
        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 2,
            "error_type": "too_few",
            "fallback_triggered": False,
            "search_results": [],
            "user_features": {},
        }

        # Refiner 不应触发
        refiner_result = refiner.before_model(state, mock_runtime)
        assert refiner_result is None

        # Fallback 应触发
        mock_response = MagicMock()
        mock_response.content = "Fallback 响应"
        mock_llm.invoke = MagicMock(return_value=mock_response)

        fallback_result = fallback.before_model(state, mock_runtime)
        assert fallback_result is not None
        assert fallback_result["fallback_triggered"] is True

    def test_first_retry_triggers_refiner_not_fallback(
        self, mock_llm: MagicMock, mock_runtime: MagicMock
    ) -> None:
        """
        测试第一次重试只触发 Refiner，不触发 Fallback
        """
        refiner = QueryRefinerMiddleware(refiner_llm=mock_llm, max_retry=2)
        fallback = FallbackMiddleware(fallback_llm=mock_llm, max_retry=2)

        mock_result = MagicMock()
        mock_result.refined_query = "修正查询"
        refiner._refiner_chain = MagicMock()
        refiner._refiner_chain.invoke = MagicMock(return_value=mock_result)

        state: CRAGState = {
            "messages": [],
            "result_quality": "poor",
            "retry_count": 0,
            "error_type": "too_few",
            "fallback_triggered": False,
            "last_rag_query": "原查询",
            "user_features": {},
            "tried_queries": [],
        }

        # Refiner 应触发
        refiner_result = refiner.before_model(state, mock_runtime)
        assert refiner_result is not None

        # Fallback 不应触发
        fallback_result = fallback.before_model(state, mock_runtime)
        assert fallback_result is None
