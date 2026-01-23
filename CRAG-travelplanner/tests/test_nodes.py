"""
单元测试 - Nodes
================
测试 Collector、Validator、AskUser 节点的功能
"""

from unittest.mock import MagicMock, patch

from seekdb_agent.nodes.ask_user import ask_user_node
from seekdb_agent.nodes.collector import collector_node
from seekdb_agent.nodes.validator import validator_node
from seekdb_agent.state import UserFeatures

# ==================== Collector Node Tests ====================


@patch("seekdb_agent.nodes.collector._extract_features_with_retry")
def test_collector_extracts_complete_features(mock_extract):
    """测试完整特征提取功能"""
    # Mock LLM 返回
    mock_extract.return_value = UserFeatures(
        destination="杭州",
        travel_days=3,
        interests=["历史文化", "美食"],
        budget_meal=50,
        transportation="公共交通",
        pois_per_day=3,
        must_visit=["西湖"],
        dietary_options=[],
        price_preference=None,
    )

    # 构建测试状态
    state = {
        "messages": [{"role": "user", "content": "我想去杭州玩3天，预算中等，喜欢历史文化和美食"}],
    }

    # 调用节点
    result = collector_node(state)

    # 验证结果 - UserFeatures 现在是 Pydantic，使用属性访问
    user_features = result["user_features"]
    assert user_features.destination == "杭州"
    assert user_features.travel_days == 3
    assert user_features.budget_meal == 50
    assert "历史文化" in user_features.interests
    assert "美食" in user_features.interests
    assert user_features.transportation == "公共交通"
    assert user_features.pois_per_day == 3


@patch("seekdb_agent.nodes.collector._extract_features_with_retry")
def test_collector_extracts_partial_features(mock_extract):
    """测试部分特征提取"""
    # Mock LLM 返回（部分字段缺失）
    mock_extract.return_value = UserFeatures(
        destination="杭州",
        travel_days=None,
        interests=["历史文化"],
        budget_meal=None,
        transportation=None,
        pois_per_day=None,
        must_visit=[],
        dietary_options=[],
        price_preference=None,
    )

    state = {
        "messages": [{"role": "user", "content": "我想去杭州看历史文化景点"}],
    }

    result = collector_node(state)

    # UserFeatures 现在是 Pydantic，使用属性访问
    user_features = result["user_features"]
    assert user_features.destination == "杭州"
    assert user_features.travel_days is None
    assert "历史文化" in user_features.interests
    assert user_features.budget_meal is None


@patch("seekdb_agent.nodes.collector._extract_features_with_retry")
def test_collector_handles_llm_failure(mock_extract):
    """测试 LLM 失败时的异常处理"""
    # Mock LLM 抛出异常
    mock_extract.side_effect = Exception("LLM connection failed")

    state = {
        "messages": [{"role": "user", "content": "我想去杭州旅游"}],
    }

    result = collector_node(state)

    # 验证返回默认空特征 - UserFeatures 现在是 Pydantic，使用属性访问
    user_features = result["user_features"]
    assert user_features.destination is None
    assert user_features.travel_days is None
    assert user_features.interests == []


# ==================== Validator Node Tests ====================


def test_validator_complete_features():
    """测试完整特征验证 - 所有 6 个必填字段都存在"""
    from langchain_core.messages import HumanMessage

    state = {
        "messages": [HumanMessage(content="我想去杭州玩3天")],  # 明确提到天数
        "user_features": UserFeatures(
            destination="杭州",
            travel_days=3,
            interests=["历史文化", "美食"],
            budget_meal=100,  # 使用非可疑值
            transportation="自驾",  # 使用非可疑值
            pois_per_day=4,  # 使用非可疑值
            must_visit=[],
            dietary_options=[],
            price_preference=None,
        ),
    }

    result = validator_node(state)

    assert result["feature_complete"] is True
    assert result["missing_features"] == ["must_visit", "dietary_options"]


def test_validator_complete_all_fields():
    """测试所有字段（包括可选字段）都完整"""
    from langchain_core.messages import HumanMessage

    state = {
        "messages": [HumanMessage(content="我想去杭州玩3天")],  # 明确提到天数
        "user_features": UserFeatures(
            destination="杭州",
            travel_days=3,
            interests=["历史文化", "美食"],
            budget_meal=100,  # 使用非可疑值
            transportation="自驾",  # 使用非可疑值
            pois_per_day=4,  # 使用非可疑值
            must_visit=["西湖"],
            dietary_options=["中餐"],
            price_preference="高端",  # 使用非可疑值
        ),
    }

    result = validator_node(state)

    assert result["feature_complete"] is True
    assert result["missing_features"] == []


def test_validator_missing_single_core_field():
    """测试缺失单个核心字段"""
    from langchain_core.messages import HumanMessage

    state = {
        "messages": [HumanMessage(content="我想去杭州玩3天")],  # 明确提到天数
        "user_features": UserFeatures(
            destination="杭州",
            travel_days=3,
            interests=["历史文化"],
            budget_meal=50,
            transportation="公共交通",
            pois_per_day=None,  # 缺失
            must_visit=[],
            dietary_options=[],
            price_preference=None,
        ),
    }

    result = validator_node(state)

    assert result["feature_complete"] is False
    assert "pois_per_day" in result["missing_features"]
    assert "must_visit" in result["missing_features"]
    assert "dietary_options" in result["missing_features"]


def test_validator_missing_multiple_core_fields():
    """测试缺失多个核心字段"""
    from langchain_core.messages import HumanMessage

    state = {
        "messages": [HumanMessage(content="我想去杭州玩3天")],  # 明确提到天数
        "user_features": UserFeatures(
            destination="杭州",
            travel_days=3,
            interests=[],  # 缺失
            budget_meal=None,  # 缺失
            transportation=None,  # 缺失
            pois_per_day=None,  # 缺失
            must_visit=[],
            dietary_options=[],
            price_preference=None,
        ),
    }

    result = validator_node(state)

    assert result["feature_complete"] is False
    assert len(result["missing_features"]) == 6  # 4 个核心 + 2 个可选
    assert "interests" in result["missing_features"]
    assert "budget_meal" in result["missing_features"]
    assert "transportation" in result["missing_features"]
    assert "pois_per_day" in result["missing_features"]


def test_validator_empty_values():
    """测试空值处理（空字符串、0、空列表、None）"""
    state = {
        "user_features": UserFeatures(
            destination="",  # 空字符串
            travel_days=0,  # 0
            interests=[],  # 空列表
            budget_meal=None,  # None
            transportation="自驾",  # 使用非可疑值
            pois_per_day=4,  # 使用非可疑值
            must_visit=[],
            dietary_options=[],
            price_preference=None,
        )
    }

    result = validator_node(state)

    assert result["feature_complete"] is False
    assert "destination" in result["missing_features"]
    assert "travel_days" in result["missing_features"]
    assert "interests" in result["missing_features"]
    assert "budget_meal" in result["missing_features"]


def test_validator_optional_fields_dont_block():
    """测试可选字段缺失不阻塞（feature_complete 仍为 True）"""
    from langchain_core.messages import HumanMessage

    state = {
        "messages": [HumanMessage(content="我想去杭州玩3天")],  # 明确提到天数
        "user_features": UserFeatures(
            destination="杭州",
            travel_days=3,
            interests=["历史文化"],
            budget_meal=100,  # 使用非可疑值
            transportation="自驾",  # 使用非可疑值
            pois_per_day=4,  # 使用非可疑值
            must_visit=[],  # 可选字段缺失
            dietary_options=[],  # 可选字段缺失
            price_preference=None,
        ),
    }

    result = validator_node(state)

    # 核心字段完整，所以 feature_complete = True
    assert result["feature_complete"] is True
    # 但 missing_features 包含可选字段
    assert "must_visit" in result["missing_features"]
    assert "dietary_options" in result["missing_features"]
    assert len(result["missing_features"]) == 2


# ==================== AskUser Node Tests ====================


@patch("seekdb_agent.nodes.ask_user._get_llm")
def test_ask_user_generates_question_for_core_fields(mock_get_llm):
    """测试为核心必填字段生成提问"""
    # Mock LLM 返回
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content="好的，为了给您推荐合适的景点，我还需要了解：\n1. 您计划在杭州停留几天呢？\n2. 您对餐饮的预算大概是怎样的？"
    )
    mock_get_llm.return_value = mock_llm

    state = {
        "messages": [{"role": "user", "content": "我想去杭州旅游"}],
        "user_features": UserFeatures(
            destination="杭州",
            travel_days=None,
            interests=["历史文化"],
            budget_meal=None,
            transportation="公共交通",
            pois_per_day=3,
            must_visit=[],
            dietary_options=[],
            price_preference=None,
        ),
        "missing_features": ["travel_days", "budget_meal", "must_visit", "dietary_options"],
    }

    result = ask_user_node(state)

    # 验证生成了 AI 消息
    assert len(result["messages"]) == 1
    assert "旅" in result["messages"][0].content or "天" in result["messages"][0].content

    # 因为有核心字段缺失，不应设置 optional_asked
    assert "optional_asked" not in result or result["optional_asked"] is False


@patch("seekdb_agent.nodes.ask_user._get_llm")
def test_ask_user_generates_question_for_optional_fields_only(mock_get_llm):
    """测试只为可选字段生成提问（应设置 optional_asked）"""
    # Mock LLM 返回
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content="明白了！如果您有特别想去的景点或饮食偏好，欢迎告诉我 😊"
    )
    mock_get_llm.return_value = mock_llm

    from langchain_core.messages import HumanMessage

    state = {
        "messages": [HumanMessage(content="我想去杭州玩3天")],
        "user_features": UserFeatures(
            destination="杭州",
            travel_days=3,
            interests=["历史文化"],
            budget_meal=50,
            transportation="公共交通",
            pois_per_day=3,
            must_visit=[],  # 可选字段缺失
            dietary_options=[],  # 可选字段缺失
            price_preference=None,
        ),
        "missing_features": ["must_visit", "dietary_options"],
    }

    result = ask_user_node(state)

    # 验证生成了 AI 消息
    assert len(result["messages"]) == 1

    # 因为只有可选字段缺失，应设置 optional_asked = True
    assert result["optional_asked"] is True


@patch("seekdb_agent.nodes.ask_user._get_llm")
def test_ask_user_with_mixed_missing_fields(mock_get_llm):
    """测试核心和可选字段都缺失（不应设置 optional_asked）"""
    # Mock LLM 返回
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="为了推荐景点，我需要了解您的旅行天数和预算。")
    mock_get_llm.return_value = mock_llm

    state = {
        "messages": [{"role": "user", "content": "我想去杭州"}],
        "user_features": UserFeatures(
            destination="杭州",
            travel_days=None,  # 核心字段缺失
            interests=["历史文化"],
            budget_meal=None,  # 核心字段缺失
            transportation="公共交通",
            pois_per_day=3,
            must_visit=[],  # 可选字段缺失
            dietary_options=[],  # 可选字段缺失
            price_preference=None,
        ),
        "missing_features": ["travel_days", "budget_meal", "must_visit", "dietary_options"],
    }

    result = ask_user_node(state)

    # 验证生成了 AI 消息
    assert len(result["messages"]) == 1

    # 因为有核心字段缺失，不应设置 optional_asked
    assert "optional_asked" not in result or result["optional_asked"] is False


# ==================== Validator Input Detection Tests ====================
# 测试 validator 对用户输入的识别能力（2026-01-23 添加）


class TestUserMentionedPoisPerDay:
    """测试 _user_mentioned_pois_per_day 函数的输入识别能力

    背景：用户回复 "3-4; No must-see;" 时，validator 无法识别这是对
    pois_per_day 问题的回答，导致 feature_complete 始终为 False。
    """

    def test_explicit_pois_format(self):
        """测试明确的 POI 格式"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _user_mentioned_pois_per_day

        test_cases = [
            ("3 POIs per day", True),
            ("3-4 POIs", True),
            ("4 attractions", True),
            ("3 spots per day", True),
            ("5 places", True),
            ("3个景点", True),
            ("每天3个", True),
            ("3 per day", True),
        ]

        for content, expected in test_cases:
            messages = [HumanMessage(content=content)]
            result = _user_mentioned_pois_per_day(messages)
            assert result == expected, f"Failed for: {content!r}, expected {expected}, got {result}"

    def test_short_number_replies(self):
        """测试简短数字回复（对问题的直接回答）

        这是最常见的用户回复场景：AI 问 "每天几个景点"，用户直接回复数字。
        """
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _user_mentioned_pois_per_day

        test_cases = [
            ("3-4; No must-see;", True),  # 实际用户输入（触发 bug 的场景）
            ("3-4", True),
            ("3", True),
            ("4-5", True),
            ("2–3", True),  # en-dash
            ("3;", True),
            ("4,", True),
        ]

        for content, expected in test_cases:
            messages = [HumanMessage(content=content)]
            result = _user_mentioned_pois_per_day(messages)
            assert result == expected, f"Failed for: {content!r}, expected {expected}, got {result}"

    def test_negative_cases(self):
        """测试不应匹配的情况"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _user_mentioned_pois_per_day

        test_cases = [
            ("hello world", False),
            ("I want to visit Atlanta", False),
            ("yes please", False),
            ("no dietary restrictions", False),
            # 长句子不应被简短数字模式匹配
            ("I would like to visit around 3 museums and some restaurants", False),
        ]

        for content, expected in test_cases:
            messages = [HumanMessage(content=content)]
            result = _user_mentioned_pois_per_day(messages)
            assert result == expected, f"Failed for: {content!r}, expected {expected}, got {result}"


class TestUserMentionedDays:
    """测试 _user_mentioned_days 函数的输入识别能力"""

    def test_explicit_days_format(self):
        """测试明确的天数格式"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _user_mentioned_days

        test_cases = [
            ("3 days", True),
            ("5-day trip", True),
            ("3天", True),
            ("five days", True),
            ("I want to stay for 3 days", True),
            ("a 7 day vacation", True),
        ]

        for content, expected in test_cases:
            messages = [HumanMessage(content=content)]
            result = _user_mentioned_days(messages)
            assert result == expected, f"Failed for: {content!r}, expected {expected}, got {result}"

    def test_negative_cases(self):
        """测试不应匹配的情况"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _user_mentioned_days

        test_cases = [
            ("hello world", False),
            ("I want to visit Atlanta", False),
            ("yes please", False),
        ]

        for content, expected in test_cases:
            messages = [HumanMessage(content=content)]
            result = _user_mentioned_days(messages)
            assert result == expected, f"Failed for: {content!r}, expected {expected}, got {result}"


class TestValidatorWithShortReplies:
    """测试 validator_node 处理简短用户回复的能力

    端到端测试：确保用户的简短回复能正确设置 feature_complete。
    """

    def test_short_pois_reply_sets_feature_complete(self):
        """测试简短 POI 回复正确设置 feature_complete=True"""
        from langchain_core.messages import HumanMessage

        state = {
            "messages": [
                HumanMessage(content="I want to visit Atlanta for 3 days"),
                HumanMessage(content="history; mid-range about 30; car-rental;"),
                HumanMessage(content="3-4; No must-see;"),  # 关键：简短数字回复
            ],
            "user_features": UserFeatures(
                destination="Atlanta, GA",
                travel_days=3,
                interests=["history"],
                budget_meal=30,
                transportation="car-rental",
                pois_per_day=3,  # 从用户输入 "3-4" 提取
                must_visit=[],
                dietary_options=[],
                price_preference=None,
            ),
        }

        result = validator_node(state)

        # 核心字段应该完整
        assert result["feature_complete"] is True, (
            f"feature_complete should be True, but got False. "
            f"Missing: {result.get('missing_features', [])}"
        )


# ==================== LLM 辅助验证测试 (2026-01-22 添加) ====================


class TestFormatConversationContext:
    """测试对话上下文格式化函数"""

    def test_format_human_messages(self):
        """测试格式化 HumanMessage"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _format_conversation_context

        messages = [
            HumanMessage(content="I want to visit Atlanta"),
            HumanMessage(content="3-4 POIs per day"),
        ]

        result = _format_conversation_context(messages)

        assert "User: I want to visit Atlanta" in result
        assert "User: 3-4 POIs per day" in result

    def test_format_mixed_messages(self):
        """测试格式化混合消息类型"""
        from langchain_core.messages import AIMessage, HumanMessage

        from seekdb_agent.nodes.validator import _format_conversation_context

        messages = [
            HumanMessage(content="I want to visit Atlanta"),
            AIMessage(content="How many attractions per day?"),
            HumanMessage(content="3-4"),
        ]

        result = _format_conversation_context(messages)

        assert "User: I want to visit Atlanta" in result
        assert "AI: How many attractions per day?" in result
        assert "User: 3-4" in result

    def test_format_truncates_long_messages(self):
        """测试截断过长消息"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _format_conversation_context

        long_content = "x" * 600
        messages = [HumanMessage(content=long_content)]

        result = _format_conversation_context(messages)

        # 应该被截断并添加 "..."
        assert len(result) < 600
        assert "..." in result

    def test_format_respects_last_n(self):
        """测试 last_n 参数限制消息数量"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _format_conversation_context

        messages = [HumanMessage(content=f"Message {i}") for i in range(10)]

        result = _format_conversation_context(messages, last_n=2)

        # 只应包含最后 2 条消息
        assert "Message 8" in result
        assert "Message 9" in result
        assert "Message 0" not in result


class TestLLMFieldValidation:
    """测试 LLM 字段验证函数

    注意：这些测试需要 mock LLM 调用
    """

    @patch("seekdb_agent.nodes.validator._get_validation_llm")
    def test_llm_validates_confirmed_value(self, mock_get_llm):
        """测试 LLM 正确识别用户确认的值"""
        from langchain_core.messages import AIMessage, HumanMessage

        from seekdb_agent.nodes.validator import (
            FieldMentionValidation,
            _llm_validate_field_mention,
        )

        # Mock LLM 返回确认
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = FieldMentionValidation(
            user_confirmed=True,
            confidence="high",
            reasoning="User replied '3-4' to POI question",
        )
        mock_llm.with_structured_output.return_value = mock_structured
        mock_get_llm.return_value = mock_llm

        messages = [
            AIMessage(content="How many attractions per day?"),
            HumanMessage(content="3-4"),
        ]

        result = _llm_validate_field_mention(messages, "pois_per_day", 3)

        assert result is True

    @patch("seekdb_agent.nodes.validator._get_validation_llm")
    def test_llm_validates_unconfirmed_value(self, mock_get_llm):
        """测试 LLM 正确识别未确认的值"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import (
            FieldMentionValidation,
            _llm_validate_field_mention,
        )

        # Mock LLM 返回未确认
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = FieldMentionValidation(
            user_confirmed=False,
            confidence="high",
            reasoning="User never mentioned POIs per day",
        )
        mock_llm.with_structured_output.return_value = mock_structured
        mock_get_llm.return_value = mock_llm

        messages = [
            HumanMessage(content="I want to visit Atlanta"),
        ]

        result = _llm_validate_field_mention(messages, "pois_per_day", 3)

        assert result is False

    @patch("seekdb_agent.nodes.validator._get_validation_llm")
    def test_llm_handles_exception(self, mock_get_llm):
        """测试 LLM 调用失败时的异常处理"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _llm_validate_field_mention

        # Mock LLM 抛出异常
        mock_llm = MagicMock()
        mock_llm.with_structured_output.side_effect = Exception("LLM error")
        mock_get_llm.return_value = mock_llm

        messages = [HumanMessage(content="3-4")]

        # 应该返回 False（保守策略）
        result = _llm_validate_field_mention(messages, "pois_per_day", 3)

        assert result is False

    @patch("seekdb_agent.nodes.validator.LLM_VALIDATION_ENABLED", False)
    def test_llm_disabled_returns_false(self):
        """测试 LLM 验证禁用时返回 False"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _llm_validate_field_mention

        messages = [HumanMessage(content="3-4")]

        result = _llm_validate_field_mention(messages, "pois_per_day", 3)

        assert result is False


class TestSuspiciousValueConfirmation:
    """测试组合验证函数 _is_suspicious_value_confirmed"""

    def test_regex_confirms_pois_per_day(self):
        """测试正则能确认 pois_per_day"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _is_suspicious_value_confirmed

        messages = [HumanMessage(content="3-4 POIs per day")]

        result = _is_suspicious_value_confirmed(messages, "pois_per_day", 3)

        # 正则应该匹配，返回 True
        assert result is True

    def test_regex_confirms_travel_days(self):
        """测试正则能确认 travel_days"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _is_suspicious_value_confirmed

        messages = [HumanMessage(content="I want to stay for 5 days")]

        result = _is_suspicious_value_confirmed(messages, "travel_days", 5)

        # 正则应该匹配，返回 True
        assert result is True

    @patch("seekdb_agent.nodes.validator._llm_validate_field_mention")
    def test_falls_back_to_llm_when_regex_fails(self, mock_llm_validate):
        """测试正则失败时回退到 LLM"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _is_suspicious_value_confirmed

        # 用户说 "yes" 但没有明确的 POI 模式
        messages = [HumanMessage(content="yes, sounds good")]
        mock_llm_validate.return_value = True

        result = _is_suspicious_value_confirmed(messages, "pois_per_day", 3)

        # 应该调用 LLM 验证
        mock_llm_validate.assert_called_once()
        assert result is True

    def test_short_number_reply_confirmed_by_regex(self):
        """测试简短数字回复被正则确认"""
        from langchain_core.messages import HumanMessage

        from seekdb_agent.nodes.validator import _is_suspicious_value_confirmed

        messages = [HumanMessage(content="3-4; No must-see;")]

        result = _is_suspicious_value_confirmed(messages, "pois_per_day", 3)

        # 应该被正则匹配
        assert result is True


class TestValidatorNodeWithLLM:
    """测试 validator_node 与 LLM 验证的集成

    端到端测试：确保 LLM 验证正确集成到 validator_node
    """

    @patch("seekdb_agent.nodes.validator._llm_validate_field_mention")
    def test_validator_uses_llm_for_suspicious_values(self, mock_llm_validate):
        """测试 validator 对可疑值使用 LLM 验证"""
        from langchain_core.messages import HumanMessage

        # Mock LLM 返回确认
        mock_llm_validate.return_value = True

        state = {
            "messages": [
                HumanMessage(content="I want to visit Atlanta"),
                # 没有明确的 pois_per_day 模式，但 LLM 会确认
            ],
            "user_features": UserFeatures(
                destination="Atlanta, GA",
                travel_days=5,  # 非可疑值
                interests=["history"],
                budget_meal=30,
                transportation="car-rental",
                pois_per_day=3,  # 可疑值，需要 LLM 验证
                must_visit=[],
                dietary_options=[],
                price_preference=None,
            ),
        }

        result = validator_node(state)

        # LLM 确认了 pois_per_day=3，应该通过
        assert result["feature_complete"] is True

    def test_validator_passes_with_regex_confirmed_suspicious_value(self):
        """测试正则确认的可疑值能通过验证"""
        from langchain_core.messages import HumanMessage

        state = {
            "messages": [
                HumanMessage(content="I want to visit Atlanta for 3 days"),
                HumanMessage(content="history; mid-range about 30; car-rental;"),
                HumanMessage(content="3-4; No must-see;"),  # 正则能匹配
            ],
            "user_features": UserFeatures(
                destination="Atlanta, GA",
                travel_days=3,
                interests=["history"],
                budget_meal=30,
                transportation="car-rental",
                pois_per_day=3,  # 可疑值，但正则能确认
                must_visit=[],
                dietary_options=[],
                price_preference=None,
            ),
        }

        result = validator_node(state)

        assert result["feature_complete"] is True

    @patch("seekdb_agent.nodes.validator._llm_validate_field_mention")
    def test_validator_marks_missing_when_llm_rejects(self, mock_llm_validate):
        """测试 LLM 拒绝时标记字段为缺失"""
        from langchain_core.messages import HumanMessage

        # Mock LLM 返回未确认
        mock_llm_validate.return_value = False

        state = {
            "messages": [
                HumanMessage(content="I want to visit Atlanta"),
                # 没有任何关于 pois_per_day 的信息
            ],
            "user_features": UserFeatures(
                destination="Atlanta, GA",
                travel_days=5,  # 非可疑值
                interests=["history"],
                budget_meal=30,
                transportation="car-rental",
                pois_per_day=3,  # 可疑值，LLM 未确认
                must_visit=[],
                dietary_options=[],
                price_preference=None,
            ),
        }

        result = validator_node(state)

        # LLM 未确认 pois_per_day=3，应该标记为缺失
        assert result["feature_complete"] is False
        assert "pois_per_day" in result["missing_features"]
