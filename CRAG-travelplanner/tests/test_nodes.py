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
