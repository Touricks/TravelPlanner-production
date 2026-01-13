"""
集成测试 - LangGraph 工作流
===========================
测试 graph.py 的端到端工作流

测试场景:
1. 冷启动测试 - 空消息返回问候语
2. 完整流程测试 - 用户消息 → 特征提取 → 验证 → 搜索 → 生成
3. 补充信息测试 - 特征缺失 → 询问 → END
4. 路由函数测试 - route_start, route_after_validation
"""

from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from seekdb_agent.graph import (
    create_crag_graph,
    route_after_validation,
    route_start,
)
from seekdb_agent.state import CRAGState, UserFeatures


class TestRouteStart:
    """测试入口路由函数"""

    def test_cold_start_no_messages(self):
        """冷启动：无消息 → ask_user"""
        state: CRAGState = {"messages": []}
        assert route_start(state) == "ask_user"

    def test_cold_start_only_ai_messages(self):
        """冷启动：只有 AI 消息 → ask_user"""
        state: CRAGState = {"messages": [AIMessage(content="欢迎使用旅游助手！")]}
        assert route_start(state) == "ask_user"

    def test_has_user_message(self):
        """有用户消息 → collector"""
        state: CRAGState = {"messages": [HumanMessage(content="我想去杭州玩")]}
        assert route_start(state) == "collector"

    def test_mixed_messages(self):
        """混合消息（包含用户消息） → collector"""
        state: CRAGState = {
            "messages": [
                AIMessage(content="欢迎！"),
                HumanMessage(content="我想去杭州玩3天"),
            ]
        }
        assert route_start(state) == "collector"


class TestRouteAfterValidation:
    """测试验证后路由函数"""

    def test_feature_incomplete(self):
        """核心特征不完整 → ask_user"""
        state: CRAGState = {
            "messages": [],
            "feature_complete": False,
            "missing_features": ["travel_days", "budget_meal"],
        }
        assert route_after_validation(state) == "ask_user"

    def test_feature_complete_no_optional_missing(self):
        """特征完整，无缺失 → search_agent"""
        state: CRAGState = {
            "messages": [],
            "feature_complete": True,
            "missing_features": [],
        }
        assert route_after_validation(state) == "search_agent"

    def test_feature_complete_optional_missing_not_asked(self):
        """核心完整但可选缺失且未询问 → ask_user"""
        state: CRAGState = {
            "messages": [],
            "feature_complete": True,
            "missing_features": ["must_visit", "dietary_options"],
            "optional_asked": False,
        }
        assert route_after_validation(state) == "ask_user"

    def test_feature_complete_optional_missing_already_asked(self):
        """核心完整，可选缺失但已询问 → search_agent"""
        state: CRAGState = {
            "messages": [],
            "feature_complete": True,
            "missing_features": ["must_visit", "dietary_options"],
            "optional_asked": True,
        }
        assert route_after_validation(state) == "search_agent"


class TestColdStartWorkflow:
    """测试冷启动工作流"""

    @patch("seekdb_agent.nodes.ask_user._get_llm")
    def test_cold_start_returns_greeting(self, mock_get_llm):
        """冷启动返回问候语"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="您好！我是旅游助手，请问您想去哪里旅游？")
        mock_get_llm.return_value = mock_llm

        graph = create_crag_graph()

        result = graph.invoke({"messages": []})

        assert len(result["messages"]) > 0
        last_message = result["messages"][-1]
        assert isinstance(last_message, AIMessage)


class TestFeatureExtractionWorkflow:
    """测试特征提取工作流"""

    @patch("seekdb_agent.nodes.ask_user._get_llm")
    @patch("seekdb_agent.nodes.collector._extract_features_with_retry")
    def test_incomplete_features_asks_user(self, mock_extract, mock_ask_llm):
        """特征不完整时询问用户"""
        mock_extract.return_value = UserFeatures(
            destination="杭州",
            travel_days=None,
            interests=["历史文化"],
            budget_meal=None,
            transportation=None,
            pois_per_day=None,
            must_visit=[],
            dietary_options=[],
        )

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="请问您计划在杭州停留几天？")
        mock_ask_llm.return_value = mock_llm

        graph = create_crag_graph()

        result = graph.invoke({"messages": [HumanMessage(content="我想去杭州看历史景点")]})

        assert result.get("feature_complete") is False
        assert len(result.get("missing_features", [])) > 0


class TestCompleteWorkflow:
    """测试完整工作流"""

    @patch("seekdb_agent.nodes.collector._extract_features_with_retry")
    def test_complete_features_triggers_validation(self, mock_extract):
        """特征完整时验证通过"""
        mock_extract.return_value = UserFeatures(
            destination="杭州",
            travel_days=3,
            interests=["历史文化", "美食"],
            budget_meal=100,  # 使用非可疑值
            transportation="自驾",  # 使用非可疑值
            pois_per_day=4,  # 使用非可疑值
            must_visit=["西湖"],
            dietary_options=["中餐"],
        )

        from seekdb_agent.nodes.collector import collector_node
        from seekdb_agent.nodes.validator import validator_node

        state = {"messages": [HumanMessage(content="我想去杭州玩3天，预算中等")]}
        collector_result = collector_node(state)
        state.update(collector_result)

        validator_result = validator_node(state)

        assert validator_result.get("feature_complete") is True
        assert validator_result.get("missing_features") == []


class TestGraphConfiguration:
    """测试 Graph 配置选项"""

    def test_create_graph_default_config(self):
        """默认配置创建 Graph"""
        graph = create_crag_graph()
        assert graph is not None

    def test_create_graph_no_fallback(self):
        """无 Fallback 配置创建 Graph"""
        graph = create_crag_graph(include_fallback=False)
        assert graph is not None

    def test_create_graph_no_refiner(self):
        """无 Refiner 配置创建 Graph"""
        graph = create_crag_graph(include_refiner=False)
        assert graph is not None

    def test_create_graph_minimal(self):
        """最小配置（只有 Grading）创建 Graph"""
        graph = create_crag_graph(
            include_grading=True,
            include_refiner=False,
            include_fallback=False,
        )
        assert graph is not None

    def test_create_graph_custom_retry(self):
        """自定义重试次数创建 Graph"""
        graph = create_crag_graph(max_retry=5)
        assert graph is not None


class TestAppExport:
    """测试模块导出"""

    def test_app_import(self):
        """测试 app 可以从模块导入"""
        from seekdb_agent import app

        assert app is not None

    def test_create_crag_graph_import(self):
        """测试 create_crag_graph 可以从模块导入"""
        from seekdb_agent import create_crag_graph

        assert callable(create_crag_graph)

    def test_state_types_import(self):
        """测试状态类型可以导入"""
        from seekdb_agent import CRAGState, POIResult, UserFeatures

        assert CRAGState is not None
        assert POIResult is not None
        assert UserFeatures is not None
