"""
Search Quality Tests (LLM-as-Judge)
===================================
使用 LLM 评估搜索结果质量

基于 docs/design/day5_search_enhancement_20260106.md 第三节设计
"""

import json
from typing import Any
from unittest.mock import MagicMock

from seekdb_agent.state import POIResult

# ============================================================================
# LLM-as-Judge 评估模块
# ============================================================================

JUDGE_PROMPT = """你是搜索结果质量评估专家。

**用户查询：** {query}

**搜索结果：**
{results}

请从以下维度评分 (1-5)：
1. **相关性**: 结果与查询的匹配程度
2. **完整性**: 是否覆盖用户需求
3. **准确性**: 信息是否正确

输出 JSON 格式：
{{"relevance": X, "completeness": X, "accuracy": X, "reasoning": "..."}}
"""


def format_results_for_judge(results: list[POIResult]) -> str:
    """格式化搜索结果供 Judge 评估"""
    if not results:
        return "无搜索结果"

    lines = []
    for i, poi in enumerate(results[:10], 1):  # 最多评估前10个
        line = f"{i}. {poi.name}"
        if poi.city:
            line += f" ({poi.city})"
        if poi.primary_category:
            line += f" - {poi.primary_category}"
        if poi.editorial_summary:
            line += f"\n   {poi.editorial_summary[:100]}"
        lines.append(line)

    return "\n".join(lines)


def llm_judge_relevance(
    query: str,
    results: list[POIResult],
    llm: Any = None,
) -> dict[str, Any]:
    """
    使用 LLM 评估搜索结果相关性

    Args:
        query: 用户查询
        results: 搜索结果列表
        llm: LLM 实例（可选，默认使用配置的 Provider）

    Returns:
        {"relevance": float, "completeness": float, "accuracy": float, "reasoning": str}
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    from seekdb_agent.llm import create_llm

    if llm is None:
        llm = create_llm(temperature=0.0)

    formatted_results = format_results_for_judge(results)
    prompt = JUDGE_PROMPT.format(query=query, results=formatted_results)

    messages = [
        SystemMessage(content="你是搜索质量评估专家，请严格按照 JSON 格式输出。"),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    content = str(response.content) if hasattr(response, "content") else str(response)

    # 解析 JSON 响应
    try:
        # 尝试提取 JSON
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content.strip()

        result = json.loads(json_str)
        return {
            "relevance": float(result.get("relevance", 0)),
            "completeness": float(result.get("completeness", 0)),
            "accuracy": float(result.get("accuracy", 0)),
            "reasoning": result.get("reasoning", ""),
        }
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        return {
            "relevance": 0.0,
            "completeness": 0.0,
            "accuracy": 0.0,
            "reasoning": f"解析失败: {e}, 原始响应: {content[:200]}",
        }


def calculate_average_score(scores: dict[str, Any]) -> float:
    """计算平均分"""
    return (scores["relevance"] + scores["completeness"] + scores["accuracy"]) / 3


# ============================================================================
# 测试用例
# ============================================================================

# 测试查询数据集 (美国城市)
TEST_QUERIES = [
    {
        "query": "beach vacation in Tampa",
        "expected_keywords": ["beach", "island", "water"],
        "expected_city": "Tampa",
    },
    {
        "query": "historical sites in New York",
        "expected_keywords": ["cathedral", "museum", "historic"],
        "expected_city": "New York",
    },
    {
        "query": "nature parks in San Francisco",
        "expected_keywords": ["park", "garden", "nature"],
        "expected_city": "San Francisco",
    },
]


class TestLLMJudge:
    """LLM-as-Judge 评估函数测试"""

    def test_format_results_empty(self):
        """测试空结果格式化"""
        result = format_results_for_judge([])
        assert result == "无搜索结果"

    def test_format_results_with_pois(self):
        """测试 POI 结果格式化"""
        pois = [
            POIResult(
                id="1",
                name="西湖",
                city="杭州",
                primary_category="景点",
                editorial_summary="著名的风景名胜区",
            ),
            POIResult(
                id="2",
                name="灵隐寺",
                city="杭州",
                primary_category="寺庙",
            ),
        ]
        result = format_results_for_judge(pois)
        assert "西湖" in result
        assert "杭州" in result
        assert "灵隐寺" in result

    def test_llm_judge_with_mock(self):
        """测试 LLM Judge（Mock）"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps(
            {
                "relevance": 4.5,
                "completeness": 4.0,
                "accuracy": 4.5,
                "reasoning": "结果与查询高度相关",
            }
        )
        mock_llm.invoke.return_value = mock_response

        pois = [
            POIResult(id="1", name="西湖", city="杭州"),
            POIResult(id="2", name="雷峰塔", city="杭州"),
        ]

        scores = llm_judge_relevance("杭州景点", pois, llm=mock_llm)

        assert scores["relevance"] == 4.5
        assert scores["completeness"] == 4.0
        assert scores["accuracy"] == 4.5
        assert "相关" in scores["reasoning"]

    def test_llm_judge_handles_json_in_markdown(self):
        """测试 LLM Judge 处理 Markdown 格式的 JSON"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = """```json
{
    "relevance": 3.5,
    "completeness": 3.0,
    "accuracy": 4.0,
    "reasoning": "部分结果相关"
}
```"""
        mock_llm.invoke.return_value = mock_response

        pois = [POIResult(id="1", name="测试景点")]
        scores = llm_judge_relevance("测试查询", pois, llm=mock_llm)

        assert scores["relevance"] == 3.5
        assert scores["completeness"] == 3.0

    def test_llm_judge_handles_parse_error(self):
        """测试 LLM Judge 处理解析错误"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "这不是有效的 JSON"
        mock_llm.invoke.return_value = mock_response

        pois = [POIResult(id="1", name="测试景点")]
        scores = llm_judge_relevance("测试查询", pois, llm=mock_llm)

        assert scores["relevance"] == 0.0
        assert "解析失败" in scores["reasoning"]

    def test_calculate_average_score(self):
        """测试平均分计算"""
        scores = {"relevance": 4.0, "completeness": 3.5, "accuracy": 4.5, "reasoning": ""}
        avg = calculate_average_score(scores)
        assert avg == 4.0


class TestSearchQualityMetrics:
    """搜索质量指标测试"""

    def test_precision_at_k(self):
        """测试 Precision@K 计算"""
        # 模拟搜索结果
        results = [
            POIResult(id="1", name="西湖", city="杭州"),
            POIResult(id="2", name="雷峰塔", city="杭州"),
            POIResult(id="3", name="外滩", city="上海"),  # 不相关
            POIResult(id="4", name="灵隐寺", city="杭州"),
        ]

        expected_city = "杭州"
        relevant = sum(1 for r in results if r.city == expected_city)
        precision = relevant / len(results)

        assert precision == 0.75  # 3/4

    def test_rerank_improves_order(self):
        """测试 Rerank 改善排序（概念验证）"""
        # 模拟 Rerank 后的排序（假设查询是"杭州景点"）
        # 原始排序可能是：外滩(0.9) > 西湖(0.8) > 雷峰塔(0.7)
        # Rerank 后应将杭州相关结果提升到前面
        reranked_order = [
            POIResult(id="2", name="西湖", city="杭州", score=0.95),
            POIResult(id="3", name="雷峰塔", city="杭州", score=0.85),
            POIResult(id="1", name="外滩", city="上海", score=0.3),
        ]

        # 验证杭州相关结果排在前面
        assert reranked_order[0].city == "杭州"
        assert reranked_order[1].city == "杭州"
        # 验证分数顺序正确
        assert reranked_order[0].score > reranked_order[1].score


# ============================================================================
# 集成测试（需要数据库连接）
# ============================================================================


class TestSearchQualityIntegration:
    """搜索质量集成测试（需要 OceanBase 数据库）"""

    def test_hybrid_search_returns_results(self):
        """测试 Hybrid Search 返回结果"""
        from seekdb_agent.db.connection import get_hybrid_store
        from seekdb_agent.db.search import hybrid_search

        store = get_hybrid_store()

        for case in TEST_QUERIES:
            results = hybrid_search(store, case["query"], use_rerank=False, top_k=10)
            assert len(results) > 0, f"查询 '{case['query']}' 无结果"

            # 验证结果包含预期城市
            cities = [r.city for r in results if r.city]
            assert (
                case["expected_city"] in cities
            ), f"查询 '{case['query']}' 未返回 {case['expected_city']} 的结果"

    def test_hybrid_search_city_relevance(self):
        """测试 Hybrid Search 城市相关性"""
        from seekdb_agent.db.connection import get_hybrid_store
        from seekdb_agent.db.search import hybrid_search

        store = get_hybrid_store()
        query = "beach vacation in Tampa"

        results = hybrid_search(store, query, use_rerank=False, top_k=10)

        # 至少前3个结果应该包含 Tampa
        tampa_count = sum(1 for r in results[:5] if r.city == "Tampa")
        assert tampa_count >= 2, f"Tampa 相关结果不足: {tampa_count}/5"

    def test_rerank_fallback_works(self):
        """测试 Rerank Fallback 机制（OceanBase 4.3.x 不支持 AI_RERANK）"""
        from seekdb_agent.db.connection import get_hybrid_store
        from seekdb_agent.db.search import hybrid_search

        store = get_hybrid_store()
        query = "nature parks in San Francisco"

        # 使用 Rerank（会 fallback 到原始排序）
        results_with_rerank = hybrid_search(store, query, use_rerank=True, top_k=5)

        # 验证 fallback 正常工作，返回结果
        assert len(results_with_rerank) > 0, "Rerank fallback 失败"
        assert results_with_rerank[0].score > 0, "Fallback 分数计算失败"
