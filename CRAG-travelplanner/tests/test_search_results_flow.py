"""
Search Results Flow Tests
=========================
验证 search_results 从 search_pois 到 CRAGState 的完整数据流

测试场景：
1. contextvar 暂存机制
2. GradingMiddleware 读取并写入 state
3. 端到端数据流验证

创建时间: 2026-01-08
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import ToolMessage

from seekdb_agent.middleware.grading import DocumentGradingMiddleware
from seekdb_agent.state import POIResult
from seekdb_agent.tools.search import (
    clear_last_search_results,
    get_last_search_results,
)

# ============================================================
# Fixtures
# ============================================================


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


@pytest.fixture
def mock_grader() -> MagicMock:
    """创建 Mock grader，返回 'yes'"""
    grader = MagicMock()
    mock_result = MagicMock()
    mock_result.binary_score = "yes"
    mock_result.reasoning = "Documents are relevant"
    grader.invoke = MagicMock(return_value=mock_result)
    return grader


@pytest.fixture(autouse=True)
def clean_contextvar():
    """每个测试前后清理 contextvar"""
    clear_last_search_results()
    yield
    clear_last_search_results()


# ============================================================
# 1. ContextVar 暂存机制测试
# ============================================================


class TestContextVarMechanism:
    """测试 contextvar 暂存机制"""

    def test_initial_state_is_empty(self):
        """初始状态应为空列表"""
        results = get_last_search_results()
        assert results == []

    def test_clear_resets_to_empty(self, sample_poi_results: list[POIResult]):
        """clear 函数应重置为空列表"""
        # 模拟设置值
        from seekdb_agent.tools.search import _last_search_results

        _last_search_results.set([poi.model_dump() for poi in sample_poi_results])

        # 验证已设置
        assert len(get_last_search_results()) == 2

        # 清空
        clear_last_search_results()
        assert get_last_search_results() == []

    def test_search_pois_stores_results(self, sample_poi_results: list[POIResult]):
        """search_pois 执行后应暂存结构化结果"""
        from seekdb_agent.tools.search import _last_search_results

        # 模拟 search_pois 的行为（设置 contextvar）
        _last_search_results.set([poi.model_dump() for poi in sample_poi_results])

        results = get_last_search_results()
        assert len(results) == 2
        assert results[0]["name"] == "西湖"
        assert results[1]["name"] == "灵隐寺"


# ============================================================
# 2. GradingMiddleware 集成测试
# ============================================================


class TestGradingMiddlewareSearchResults:
    """测试 GradingMiddleware 正确保存 search_results"""

    def test_pending_grading_includes_search_results(
        self,
        mock_grader: MagicMock,
        sample_poi_results: list[POIResult],
    ):
        """wrap_tool_call 后 _pending_grading 应包含 search_results"""
        from seekdb_agent.tools.search import _last_search_results

        # 设置 contextvar（模拟 search_pois 已执行）
        poi_dicts = [poi.model_dump() for poi in sample_poi_results]
        _last_search_results.set(poi_dicts)

        # 创建 middleware
        middleware = DocumentGradingMiddleware(
            grader=mock_grader,
            rag_tool_name="search_pois",
        )

        # 构造请求
        request = MagicMock()
        request.tool_call = {
            "name": "search_pois",
            "args": {"query": "杭州景点"},
        }

        # 构造 handler 返回 ToolMessage
        tool_message = ToolMessage(
            content="Found 2 POIs:\n1. 西湖\n2. 灵隐寺",
            tool_call_id="test_call_id",
        )
        handler = MagicMock(return_value=tool_message)

        # 执行
        middleware.wrap_tool_call(request, handler)

        # 验证 _pending_grading 包含 search_results
        assert middleware._pending_grading is not None
        assert "search_results" in middleware._pending_grading
        assert len(middleware._pending_grading["search_results"]) == 2
        assert middleware._pending_grading["search_results"][0]["name"] == "西湖"

    def test_pending_grading_includes_quality_and_results(
        self,
        mock_grader: MagicMock,
        sample_poi_results: list[POIResult],
    ):
        """_pending_grading 应同时包含 result_quality 和 search_results"""
        from seekdb_agent.tools.search import _last_search_results

        poi_dicts = [poi.model_dump() for poi in sample_poi_results]
        _last_search_results.set(poi_dicts)

        middleware = DocumentGradingMiddleware(
            grader=mock_grader,
            rag_tool_name="search_pois",
        )

        request = MagicMock()
        request.tool_call = {
            "name": "search_pois",
            "args": {"query": "杭州景点"},
        }

        tool_message = ToolMessage(
            content="Found 2 POIs",
            tool_call_id="test_call_id",
        )
        handler = MagicMock(return_value=tool_message)

        middleware.wrap_tool_call(request, handler)

        # 验证同时包含两者
        assert middleware._pending_grading["result_quality"] == "good"
        assert len(middleware._pending_grading["search_results"]) == 2

    def test_grading_failure_still_saves_search_results(
        self,
        sample_poi_results: list[POIResult],
    ):
        """即使评估失败，也应保存 search_results"""
        from seekdb_agent.tools.search import _last_search_results

        poi_dicts = [poi.model_dump() for poi in sample_poi_results]
        _last_search_results.set(poi_dicts)

        # 创建会抛出异常的 grader
        failing_grader = MagicMock()
        failing_grader.invoke = MagicMock(side_effect=Exception("Grading failed"))

        middleware = DocumentGradingMiddleware(
            grader=failing_grader,
            rag_tool_name="search_pois",
        )

        request = MagicMock()
        request.tool_call = {
            "name": "search_pois",
            "args": {"query": "杭州景点"},
        }

        tool_message = ToolMessage(
            content="Found 2 POIs",
            tool_call_id="test_call_id",
        )
        handler = MagicMock(return_value=tool_message)

        # 执行（不应抛出异常）
        middleware.wrap_tool_call(request, handler)

        # 验证 search_results 仍被保存
        assert middleware._pending_grading is not None
        assert "search_results" in middleware._pending_grading
        assert len(middleware._pending_grading["search_results"]) == 2


# ============================================================
# 3. before_model 状态更新测试
# ============================================================


class TestBeforeModelStateUpdate:
    """测试 before_model 正确更新 state"""

    def test_before_model_returns_search_results(
        self,
        mock_grader: MagicMock,
        sample_poi_results: list[POIResult],
    ):
        """before_model 应返回包含 search_results 的 dict"""
        from seekdb_agent.tools.search import _last_search_results

        poi_dicts = [poi.model_dump() for poi in sample_poi_results]
        _last_search_results.set(poi_dicts)

        middleware = DocumentGradingMiddleware(
            grader=mock_grader,
            rag_tool_name="search_pois",
        )

        # 先执行 wrap_tool_call 设置 _pending_grading
        request = MagicMock()
        request.tool_call = {
            "name": "search_pois",
            "args": {"query": "杭州景点"},
        }
        tool_message = ToolMessage(content="Found 2 POIs", tool_call_id="test")
        handler = MagicMock(return_value=tool_message)
        middleware.wrap_tool_call(request, handler)

        # 执行 before_model
        mock_state = MagicMock()
        mock_runtime = MagicMock()
        updates = middleware.before_model(mock_state, mock_runtime)

        # 验证返回值包含 search_results
        assert updates is not None
        assert "search_results" in updates
        assert len(updates["search_results"]) == 2

        # 验证 _pending_grading 已清空
        assert middleware._pending_grading is None
