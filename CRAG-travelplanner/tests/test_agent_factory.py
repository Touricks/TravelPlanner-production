"""
单元测试 - Agent 工厂函数
=========================
测试 create_search_agent 工厂函数的各种配置

测试场景:
1. 全功能配置（默认）
2. 无 Fallback 配置
3. 无 Refiner 配置
4. 只有 Grading 配置
5. 自定义重试次数
6. 自定义 LLM
"""

from unittest.mock import MagicMock, patch

from seekdb_agent.agents.search_agent import (
    SEARCH_AGENT_SYSTEM_PROMPT,
    create_search_agent,
    get_fallback_llm,
    get_llm,
)


class TestCreateSearchAgent:
    """测试 create_search_agent 工厂函数"""

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_grader_instance")
    @patch("seekdb_agent.agents.search_agent.get_llm")
    @patch("seekdb_agent.agents.search_agent.get_fallback_llm")
    def test_default_config_all_middleware(
        self, mock_fallback_llm, mock_llm, mock_grader, mock_create_agent
    ):
        """默认配置：包含所有 Middleware"""
        mock_llm.return_value = MagicMock()
        mock_grader.return_value = MagicMock()
        mock_fallback_llm.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent()

        mock_create_agent.assert_called_once()
        call_args = mock_create_agent.call_args

        middleware_list = call_args.kwargs.get("middleware", [])
        assert len(middleware_list) == 3

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_grader_instance")
    @patch("seekdb_agent.agents.search_agent.get_llm")
    def test_no_fallback_config(self, mock_llm, mock_grader, mock_create_agent):
        """无 Fallback 配置：只有 Grading + Refiner"""
        mock_llm.return_value = MagicMock()
        mock_grader.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent(include_fallback=False)

        mock_create_agent.assert_called_once()
        call_args = mock_create_agent.call_args

        middleware_list = call_args.kwargs.get("middleware", [])
        assert len(middleware_list) == 2

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_grader_instance")
    @patch("seekdb_agent.agents.search_agent.get_llm")
    def test_no_refiner_config(self, mock_llm, mock_grader, mock_create_agent):
        """无 Refiner 配置：只有 Grading + Fallback"""
        mock_llm.return_value = MagicMock()
        mock_grader.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent(include_refiner=False, include_fallback=False)

        mock_create_agent.assert_called_once()
        call_args = mock_create_agent.call_args

        middleware_list = call_args.kwargs.get("middleware", [])
        assert len(middleware_list) == 1

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_grader_instance")
    @patch("seekdb_agent.agents.search_agent.get_llm")
    def test_grading_only_config(self, mock_llm, mock_grader, mock_create_agent):
        """只有 Grading 配置"""
        mock_llm.return_value = MagicMock()
        mock_grader.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent(
            include_grading=True,
            include_refiner=False,
            include_fallback=False,
        )

        mock_create_agent.assert_called_once()
        call_args = mock_create_agent.call_args

        middleware_list = call_args.kwargs.get("middleware", [])
        assert len(middleware_list) == 1

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_llm")
    def test_no_middleware_config(self, mock_llm, mock_create_agent):
        """无任何 Middleware 配置"""
        mock_llm.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent(
            include_grading=False,
            include_refiner=False,
            include_fallback=False,
        )

        mock_create_agent.assert_called_once()
        call_args = mock_create_agent.call_args

        middleware_list = call_args.kwargs.get("middleware", [])
        assert len(middleware_list) == 0

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_grader_instance")
    @patch("seekdb_agent.agents.search_agent.get_llm")
    @patch("seekdb_agent.agents.search_agent.get_fallback_llm")
    def test_custom_max_retry(self, mock_fallback_llm, mock_llm, mock_grader, mock_create_agent):
        """自定义重试次数"""
        mock_llm.return_value = MagicMock()
        mock_grader.return_value = MagicMock()
        mock_fallback_llm.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent(max_retry=5)

        mock_create_agent.assert_called_once()

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_grader_instance")
    @patch("seekdb_agent.agents.search_agent.get_fallback_llm")
    def test_custom_llm(self, mock_fallback_llm, mock_grader, mock_create_agent):
        """使用自定义 LLM"""
        custom_llm = MagicMock()
        mock_grader.return_value = MagicMock()
        mock_fallback_llm.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent(llm=custom_llm)

        mock_create_agent.assert_called_once()
        call_args = mock_create_agent.call_args

        assert call_args.kwargs.get("model") == custom_llm


class TestAgentConfiguration:
    """测试 Agent 配置参数"""

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_grader_instance")
    @patch("seekdb_agent.agents.search_agent.get_llm")
    @patch("seekdb_agent.agents.search_agent.get_fallback_llm")
    def test_system_prompt_passed(
        self, mock_fallback_llm, mock_llm, mock_grader, mock_create_agent
    ):
        """验证 system_prompt 正确传递"""
        mock_llm.return_value = MagicMock()
        mock_grader.return_value = MagicMock()
        mock_fallback_llm.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent()

        call_args = mock_create_agent.call_args
        assert call_args.kwargs.get("system_prompt") == SEARCH_AGENT_SYSTEM_PROMPT

    @patch("seekdb_agent.agents.search_agent.create_agent")
    @patch("seekdb_agent.agents.search_agent.get_grader_instance")
    @patch("seekdb_agent.agents.search_agent.get_llm")
    @patch("seekdb_agent.agents.search_agent.get_fallback_llm")
    def test_tools_passed(self, mock_fallback_llm, mock_llm, mock_grader, mock_create_agent):
        """验证 tools 正确传递"""
        mock_llm.return_value = MagicMock()
        mock_grader.return_value = MagicMock()
        mock_fallback_llm.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()

        create_search_agent()

        call_args = mock_create_agent.call_args
        tools = call_args.kwargs.get("tools", [])
        assert len(tools) == 1


class TestSystemPrompt:
    """测试系统提示词"""

    def test_system_prompt_contains_search_pois(self):
        """系统提示词包含 search_pois 工具说明"""
        assert "search_pois" in SEARCH_AGENT_SYSTEM_PROMPT

    def test_system_prompt_contains_search_strategy(self):
        """系统提示词包含搜索策略"""
        assert "balanced" in SEARCH_AGENT_SYSTEM_PROMPT or "搜索" in SEARCH_AGENT_SYSTEM_PROMPT

    def test_system_prompt_contains_response_requirements(self):
        """系统提示词包含响应要求"""
        assert "推荐" in SEARCH_AGENT_SYSTEM_PROMPT or "景点" in SEARCH_AGENT_SYSTEM_PROMPT


class TestLLMFactoryFunctions:
    """测试 LLM 工厂函数"""

    @patch("seekdb_agent.agents.search_agent.get_cached_llm")
    def test_get_llm_returns_cached(self, mock_cached_llm):
        """get_llm 返回缓存的 LLM"""
        mock_llm = MagicMock()
        mock_cached_llm.return_value = mock_llm

        get_llm.cache_clear()

        result = get_llm()

        mock_cached_llm.assert_called_once_with(temperature=0.7)
        assert result == mock_llm

    @patch("seekdb_agent.agents.search_agent._create_fallback_llm")
    def test_get_fallback_llm(self, mock_create_fallback):
        """get_fallback_llm 调用 _create_fallback_llm"""
        mock_llm = MagicMock()
        mock_create_fallback.return_value = mock_llm

        result = get_fallback_llm()

        mock_create_fallback.assert_called_once_with(temperature=0.7)
        assert result == mock_llm
